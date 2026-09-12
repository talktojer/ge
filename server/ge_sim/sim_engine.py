"""
ge-sim: Galactic Empire Simulation Engine
Asyncio-based world simulation with 6s ship tick and 55s planet tick.
"""
import asyncio
import structlog
import os
from datetime import datetime
from ge_sim.event_publisher import EventPublisher

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
    
    async def start(self):
        """Start simulation loops."""
        self.running = True
        logger.info("sim_engine_start", 
                   message="ge-sim starting",
                   ship_tick_interval=self.ship_tick_interval,
                   planet_tick_interval=self.planet_tick_interval)
        
        # Connect to Redis for event publishing
        await self.event_publisher.connect()
        
        # TODO: Connect to Postgres (asyncpg)
        
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
        # TODO: Close database connections
    
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
        TODO:
        1. Load all active ships from Postgres
        2. Apply movement physics (position += velocity * 6s)
        3. Resolve combat damage (phasor/torpedo hits)
        4. Recharge shields, energy (per ship stats)
        5. Track torpedo/missile positions
        6. Check mine proximity
        7. Kill ships at 100% damage
        8. Write updated ship states to Postgres
        9. Publish ship deltas to Redis (sector:{x}:{y}:ship_moved)
        
        Phase C2c: Publish stub events to demonstrate tick→delta pipeline.
        """
        logger.debug("ship_tick_process", 
                    tick=self.ship_tick_count,
                    message="Processing ship tick")
        
        # Stub: Publish a sector delta for testing
        # In a real implementation, this would iterate over sectors with active ships
        # For now, publish to sector 1 (ID format from C2a)
        stub_events = [
            {
                "event_type": "heartbeat",
                "tick": self.ship_tick_count,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Ship tick {self.ship_tick_count} (6s interval)"
            },
            {
                "event_type": "ship_moved",
                "ship_id": 201,
                "old_position": {"x": 5, "y": 5},
                "new_position": {
                    "x": 5 + (self.ship_tick_count % 3),
                    "y": 5 + (self.ship_tick_count % 2)
                },
                "heading": 90.0,
                "speed": 5.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        # Publish to sector 1 (matches C2a stub data)
        await self.event_publisher.publish_sector_delta(sector_id=1, events=stub_events)
        
        logger.info("ship_tick_complete",
                   tick=self.ship_tick_count,
                   events_published=len(stub_events))
    
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
        TODO:
        1. Load all owned planets from Postgres
        2. Run production multipliers (Men, Fighters, Gold, Food per rates)
        3. Collect taxes from population
        4. Check spy discovery/intel
        5. Update population growth
        6. Write updated planet states to Postgres
        7. Publish planet deltas to Redis (planet:{id}:production_ready)
        8. Queue push notifications (production ready, stockpile full)
        
        Phase C2c: Publish stub events to demonstrate tick→delta pipeline.
        """
        logger.debug("planet_tick_process",
                    tick=self.planet_tick_count,
                    message="Processing planet tick")
        
        # Stub: Publish a planet production event
        # In a real implementation, this would iterate over all owned planets
        stub_production = {
            "planet_id": 101,
            "tick": self.planet_tick_count,
            "timestamp": datetime.utcnow().isoformat(),
            "item_deltas": {
                "men": 100,
                "food": 50,
                "missiles": 10
            },
            "tax_collected": 500
        }
        
        await self.event_publisher.publish_planet_production_complete(
            planet_id=101,
            production_data=stub_production
        )
        
        # Also publish to sector delta for sector 1 (where planet 101 is located per C2a)
        planet_events = [{
            "event_type": "planet_production",
            "tick": self.planet_tick_count,
            "timestamp": datetime.utcnow().isoformat(),
            "planet_id": 101,
            "item_deltas": stub_production["item_deltas"],
            "tax_collected": stub_production["tax_collected"]
        }]
        
        await self.event_publisher.publish_sector_delta(sector_id=1, events=planet_events)
        
        logger.info("planet_tick_complete",
                   tick=self.planet_tick_count,
                   planet_events_published=1)

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
