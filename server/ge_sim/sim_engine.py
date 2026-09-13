"""
ge-sim: Galactic Empire Simulation Engine
Asyncio-based world simulation with 6s ship tick and 55s planet tick.
"""
import asyncio
import structlog
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from ge_sim.event_publisher import EventPublisher
from database.models import Ship, Planet, Sector

logger = structlog.get_logger()

class SimulationEngine:
    """
    Main simulation engine.
    Runs two concurrent loops: ship tick (6s) and planet tick (55s).
    """
    
    def __init__(self):
        self.running = False
        # Support env var override for testing, but default to ADR-specified intervals
        self.ship_tick_interval = float(os.getenv("SHIP_TICK_INTERVAL", "6.0"))
        self.planet_tick_interval = float(os.getenv("PLANET_TICK_INTERVAL", "55.0"))
        self.event_publisher = EventPublisher()
        self.ship_tick_count = 0
        self.planet_tick_count = 0
        self.db_engine = None
        self.async_session = None
    
    async def start(self):
        """Start simulation loops."""
        self.running = True
        logger.info("sim_engine_start", 
                   message="ge-sim starting",
                   ship_tick_interval=self.ship_tick_interval,
                   planet_tick_interval=self.planet_tick_interval)
        
        # Connect to Redis for event publishing
        await self.event_publisher.connect()
        
        # Connect to Postgres
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:dev@localhost:5432/galactic_empire")
        self.db_engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.db_engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("database_connected", message="Connected to Postgres")
        
        # Run both ticks concurrently
        await asyncio.gather(
            self.ship_tick_loop(),
            self.planet_tick_loop(),
        )
    
    async def stop(self):
        """Stop simulation loops."""
        self.running = False
        logger.info("sim_engine_stop", message="ge-sim stopping")
        # Close Redis connection
        await self.event_publisher.close()
        # Close database connection
        if self.db_engine:
            await self.db_engine.dispose()
            logger.info("database_closed", message="Database connection closed")
    
    async def ship_tick_loop(self):
        """
        6-second ship tick loop.
        Processes all active ships: movement, combat, shields, energy.
        """
        while self.running:
            tick_start = datetime.utcnow()
            self.ship_tick_count += 1
            logger.info("ship_tick_start", 
                       tick=self.ship_tick_count,
                       time=tick_start.isoformat())
            
            try:
                await self.process_ship_tick()
            except Exception as e:
                logger.error("ship_tick_error", 
                           tick=self.ship_tick_count,
                           error=str(e))
            
            # Sleep until next tick (6s interval)
            elapsed = (datetime.utcnow() - tick_start).total_seconds()
            sleep_time = max(0, self.ship_tick_interval - elapsed)
            
            if elapsed > self.ship_tick_interval:
                logger.warning("ship_tick_slow",
                             tick=self.ship_tick_count,
                             elapsed_seconds=elapsed,
                             target_interval=self.ship_tick_interval)
            
            await asyncio.sleep(sleep_time)
    
    async def process_ship_tick(self):
        """
        Process one ship tick.
        Phase C3: Load ships from Postgres, apply simple updates, write back, publish deltas.
        
        Full combat/physics reserved for later phases.
        """
        logger.debug("ship_tick_process", 
                    tick=self.ship_tick_count,
                    message="Processing ship tick")
        
        async with self.async_session() as session:
            # Load all active ships (not docked, damage < 100)
            result = await session.execute(
                select(Ship).where(Ship.is_docked == 0).where(Ship.damage < 100.0)
            )
            ships = result.scalars().all()
            
            logger.debug("ships_loaded", count=len(ships), tick=self.ship_tick_count)
            
            # Group ships by sector for event publishing
            sector_events = {}
            
            for ship in ships:
                old_x, old_y = ship.position_x, ship.position_y
                
                # Simple stub movement: ships drift slightly based on heading
                # Real physics would be: position += velocity * dt
                # For now: small periodic movement to show state changes
                if ship.speed > 0:
                    # Simple movement based on tick count (stub)
                    ship.position_x = old_x + (self.ship_tick_count % 3) if self.ship_tick_count % 2 == 0 else old_x
                    ship.position_y = old_y + (self.ship_tick_count % 2) if self.ship_tick_count % 3 == 0 else old_y
                
                # Recharge energy (simple stub: +5% per tick, capped at 100)
                ship.energy = min(100.0, ship.energy + 5.0)
                
                # Recharge shields (simple stub: +3% per tick, capped at 100)
                ship.shields = min(100.0, ship.shields + 3.0)
                
                # Track sector ID (for now, we'll use sector 1)
                # In a real implementation, look up sector by position
                sector_id = 1
                
                # Build event if position changed
                if ship.position_x != old_x or ship.position_y != old_y:
                    if sector_id not in sector_events:
                        sector_events[sector_id] = []
                    
                    sector_events[sector_id].append({
                        "event_type": "ship_moved",
                        "ship_id": ship.id,
                        "old_position": {"x": old_x, "y": old_y},
                        "new_position": {"x": ship.position_x, "y": ship.position_y},
                        "heading": ship.heading,
                        "speed": ship.speed,
                        "energy": ship.energy,
                        "shields": ship.shields,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Write updated ship states back to database
            await session.commit()
            
            # Add heartbeat to each sector that has events
            for sector_id in sector_events:
                sector_events[sector_id].insert(0, {
                    "event_type": "heartbeat",
                    "tick": self.ship_tick_count,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Ship tick {self.ship_tick_count} (6s interval)"
                })
            
            # Publish sector deltas
            total_events = 0
            for sector_id, events in sector_events.items():
                await self.event_publisher.publish_sector_delta(sector_id=sector_id, events=events)
                total_events += len(events)
            
            logger.info("ship_tick_complete",
                       tick=self.ship_tick_count,
                       ships_processed=len(ships),
                       events_published=total_events)
    
    async def planet_tick_loop(self):
        """
        55-second planet tick loop.
        Processes all owned planets: production, taxes, spies, population.
        """
        while self.running:
            tick_start = datetime.utcnow()
            self.planet_tick_count += 1
            logger.info("planet_tick_start",
                       tick=self.planet_tick_count,
                       time=tick_start.isoformat())
            
            try:
                await self.process_planet_tick()
            except Exception as e:
                logger.error("planet_tick_error",
                           tick=self.planet_tick_count,
                           error=str(e))
            
            # Sleep until next tick (55s interval)
            elapsed = (datetime.utcnow() - tick_start).total_seconds()
            sleep_time = max(0, self.planet_tick_interval - elapsed)
            
            if elapsed > self.planet_tick_interval:
                logger.warning("planet_tick_slow",
                             tick=self.planet_tick_count,
                             elapsed_seconds=elapsed,
                             target_interval=self.planet_tick_interval)
            
            await asyncio.sleep(sleep_time)
    
    async def process_planet_tick(self):
        """
        Process one planet tick.
        Phase C3: Load planets from Postgres, apply simple production, write back, publish deltas.
        
        Full production formulas, spies, population growth reserved for later phases.
        """
        logger.debug("planet_tick_process",
                    tick=self.planet_tick_count,
                    message="Processing planet tick")
        
        async with self.async_session() as session:
            # Load all owned planets
            result = await session.execute(
                select(Planet).where(Planet.owner_id.isnot(None))
            )
            planets = result.scalars().all()
            
            logger.debug("planets_loaded", count=len(planets), tick=self.planet_tick_count)
            
            # Group events by sector for publishing
            sector_events = {}
            
            for planet in planets:
                # Simple production: add items based on production_rates
                production_rates = planet.production_rates or {}
                item_deltas = {}
                
                for item_type, rate in production_rates.items():
                    # Simple stub: produce rate amount per tick
                    delta = int(rate)
                    if delta > 0:
                        current_stocks = planet.item_stocks or {}
                        current_stocks[item_type] = current_stocks.get(item_type, 0) + delta
                        planet.item_stocks = current_stocks
                        item_deltas[item_type] = delta
                
                # Collect taxes (stub: tax_rate% of population)
                tax_collected = 0
                if planet.population and planet.tax_rate:
                    tax_collected = int(planet.population * planet.tax_rate / 100.0)
                    planet.treasury = (planet.treasury or 0) + tax_collected
                
                # Build production event if anything was produced
                if item_deltas or tax_collected > 0:
                    production_data = {
                        "planet_id": planet.id,
                        "tick": self.planet_tick_count,
                        "timestamp": datetime.utcnow().isoformat(),
                        "item_deltas": item_deltas,
                        "tax_collected": tax_collected
                    }
                    
                    # Publish to planet-specific channel
                    await self.event_publisher.publish_planet_production_complete(
                        planet_id=planet.id,
                        production_data=production_data
                    )
                    
                    # Also add to sector delta (use sector 1 for now; real impl would look up)
                    sector_id = planet.sector_id
                    if sector_id not in sector_events:
                        sector_events[sector_id] = []
                    
                    sector_events[sector_id].append({
                        "event_type": "planet_production",
                        "planet_id": planet.id,
                        "tick": self.planet_tick_count,
                        "timestamp": datetime.utcnow().isoformat(),
                        "item_deltas": item_deltas,
                        "tax_collected": tax_collected
                    })
            
            # Write updated planet states back to database
            await session.commit()
            
            # Publish sector deltas
            total_events = 0
            for sector_id, events in sector_events.items():
                await self.event_publisher.publish_sector_delta(sector_id=sector_id, events=events)
                total_events += len(events)
            
            logger.info("planet_tick_complete",
                       tick=self.planet_tick_count,
                       planets_processed=len(planets),
                       events_published=total_events)

async def main():
    """Entry point for ge-sim service."""
    logger.info("ge_sim_main", message="Galactic Empire Simulation Engine")
    
    engine = SimulationEngine()
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("ge_sim_interrupt", message="Received interrupt signal")
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
