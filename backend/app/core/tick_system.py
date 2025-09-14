"""
Galactic Empire - Real-time Tick System

This module implements the real-time tick system for processing game events
at regular intervals, ported from the original C code.
"""

import asyncio
import time
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TickType(Enum):
    """Types of tick processing"""
    SHIP_PROCESSING = "ship_processing"      # TICKTIME - 6 seconds
    MOVEMENT_PROCESSING = "movement_processing"  # TICKTIME2 - 1 second  
    PLANET_PROCESSING = "planet_processing"  # PLANTIME - 55 seconds
    CYBERTRON_PROCESSING = "cybertron_processing"  # CYBTICKTIME - 6 seconds


@dataclass
class TickConfig:
    """Configuration for tick processing"""
    tick_type: TickType
    interval_seconds: float
    max_ticks_per_cycle: int = 100
    enabled: bool = True


@dataclass
class TickStats:
    """Statistics for tick processing"""
    total_ticks: int = 0
    last_tick_time: float = 0
    average_interval: float = 0
    errors: int = 0


class TickProcessor:
    """Base class for tick processors"""
    
    def __init__(self, name: str):
        self.name = name
        self.stats = TickStats()
        self.enabled = True
    
    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single tick - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_stats(self) -> TickStats:
        """Get processing statistics"""
        return self.stats


class ShipTickProcessor(TickProcessor):
    """Processes ship-related ticks (shields, cloaking, repairs, etc.)"""
    
    def __init__(self):
        super().__init__("ship_processor")
    
    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process ship tick - equivalent to warrtia() in original"""
        try:
            # Get all active ships
            ships = tick_data.get('ships', [])
            results = []
            
            for ship in ships:
                if not ship.get('active', False):
                    continue
                
                # Process ship systems
                ship_result = await self._process_ship_systems(ship)
                results.append(ship_result)
            
            self.stats.total_ticks += 1
            self.stats.last_tick_time = time.time()
            
            return {
                'processed_ships': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in ship tick processing: {e}")
            self.stats.errors += 1
            return {'error': str(e)}
    
    async def _process_ship_systems(self, ship: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual ship systems"""
        # This would call functions like:
        # - fluxstat() - flux system processing
        # - repairship() - ship repair processing  
        # - shieldstat() - shield processing
        # - cloakstat() - cloaking processing
        
        return {
            'ship_id': ship.get('id'),
            'processed': True,
            'timestamp': time.time()
        }


class MovementTickProcessor(TickProcessor):
    """Processes movement-related ticks (ship movement, rotation, acceleration)"""
    
    def __init__(self):
        super().__init__("movement_processor")
    
    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process movement tick - equivalent to warrti2a() in original"""
        try:
            ships = tick_data.get('ships', [])
            results = []
            
            # Process ships in batches (original used clicker % 3)
            clicker = tick_data.get('clicker', 0)
            batch_size = 3
            
            for i in range(clicker, len(ships), batch_size):
                ship = ships[i]
                if not ship.get('active', False):
                    continue
                
                # Process movement
                ship_result = await self._process_ship_movement(ship)
                results.append(ship_result)
            
            # Update clicker for next tick
            next_clicker = (clicker + 1) % batch_size
            
            self.stats.total_ticks += 1
            self.stats.last_tick_time = time.time()
            
            return {
                'processed_ships': len(results),
                'next_clicker': next_clicker,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in movement tick processing: {e}")
            self.stats.errors += 1
            return {'error': str(e)}
    
    async def _process_ship_movement(self, ship: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual ship movement"""
        # This would call functions like:
        # - rotateship() - ship rotation
        # - accel() - ship acceleration
        # - moveship() - ship movement
        # - destruct() - self-destruct countdown
        
        return {
            'ship_id': ship.get('id'),
            'movement_processed': True,
            'timestamp': time.time()
        }


class PlanetTickProcessor(TickProcessor):
    """Processes planet-related ticks (planet updates, resource generation)"""
    
    def __init__(self):
        super().__init__("planet_processor")
    
    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process planet tick - equivalent to plarti() in original"""
        try:
            # Get all planets
            planets = tick_data.get('planets', [])
            results = []
            
            for planet in planets:
                # Process planet systems
                planet_result = await self._process_planet_systems(planet)
                results.append(planet_result)
            
            self.stats.total_ticks += 1
            self.stats.last_tick_time = time.time()
            
            return {
                'processed_planets': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in planet tick processing: {e}")
            self.stats.errors += 1
            return {'error': str(e)}
    
    async def _process_planet_systems(self, planet: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual planet systems"""
        # This would handle:
        # - Planet resource generation
        # - Population growth
        # - Item production
        # - Economic updates
        
        return {
            'planet_id': planet.get('id'),
            'processed': True,
            'timestamp': time.time()
        }


class CybertronTickProcessor(TickProcessor):
    """Processes Cybertron AI ticks"""
    
    def __init__(self):
        super().__init__("cybertron_processor")
    
    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Cybertron tick - equivalent to autortia() in original"""
        try:
            # Get Cybertron ships
            cybertron_ships = tick_data.get('cybertron_ships', [])
            results = []
            
            for ship in cybertron_ships:
                if not ship.get('active', False):
                    continue
                
                # Process Cybertron AI
                ship_result = await self._process_cybertron_ai(ship)
                results.append(ship_result)
            
            self.stats.total_ticks += 1
            self.stats.last_tick_time = time.time()
            
            return {
                'processed_cybertron': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in Cybertron tick processing: {e}")
            self.stats.errors += 1
            return {'error': str(e)}
    
    async def _process_cybertron_ai(self, ship: Dict[str, Any]) -> Dict[str, Any]:
        """Process Cybertron AI decision making"""
        # This would handle:
        # - AI decision making
        # - Attack patterns
        # - Movement decisions
        # - Combat tactics
        
        return {
            'ship_id': ship.get('id'),
            'ai_processed': True,
            'timestamp': time.time()
        }


class TickSystem:
    """Main tick system coordinator"""
    
    def __init__(self):
        self.processors: Dict[TickType, TickProcessor] = {}
        self.configs: Dict[TickType, TickConfig] = {}
        self.running = False
        self.tasks: Dict[TickType, asyncio.Task] = {}
        
        # Initialize default configurations
        self._setup_default_configs()
        self._setup_default_processors()
    
    def _setup_default_configs(self):
        """Setup default tick configurations"""
        self.configs = {
            TickType.SHIP_PROCESSING: TickConfig(
                tick_type=TickType.SHIP_PROCESSING,
                interval_seconds=6.0,  # TICKTIME
                max_ticks_per_cycle=100
            ),
            TickType.MOVEMENT_PROCESSING: TickConfig(
                tick_type=TickType.MOVEMENT_PROCESSING,
                interval_seconds=1.0,  # TICKTIME2
                max_ticks_per_cycle=100
            ),
            TickType.PLANET_PROCESSING: TickConfig(
                tick_type=TickType.PLANET_PROCESSING,
                interval_seconds=55.0,  # PLANTIME
                max_ticks_per_cycle=50
            ),
            TickType.CYBERTRON_PROCESSING: TickConfig(
                tick_type=TickType.CYBERTRON_PROCESSING,
                interval_seconds=6.0,  # CYBTICKTIME
                max_ticks_per_cycle=20
            )
        }
    
    def _setup_default_processors(self):
        """Setup default tick processors"""
        self.processors = {
            TickType.SHIP_PROCESSING: ShipTickProcessor(),
            TickType.MOVEMENT_PROCESSING: MovementTickProcessor(),
            TickType.PLANET_PROCESSING: PlanetTickProcessor(),
            TickType.CYBERTRON_PROCESSING: CybertronTickProcessor()
        }
    
    async def start(self):
        """Start the tick system"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting tick system...")
        
        # Start all tick processors
        for tick_type, config in self.configs.items():
            if config.enabled:
                task = asyncio.create_task(
                    self._run_tick_processor(tick_type, config)
                )
                self.tasks[tick_type] = task
        
        logger.info("Tick system started")
    
    async def stop(self):
        """Stop the tick system"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping tick system...")
        
        # Cancel all tasks
        for task in self.tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        
        logger.info("Tick system stopped")
    
    async def _run_tick_processor(self, tick_type: TickType, config: TickConfig):
        """Run a single tick processor"""
        processor = self.processors[tick_type]
        
        while self.running:
            try:
                start_time = time.time()
                
                # Get tick data (this would come from database/game state)
                tick_data = await self._get_tick_data(tick_type)
                
                # Process the tick
                result = await processor.process_tick(tick_data)
                
                # Update statistics
                processor.stats.total_ticks += 1
                processor.stats.last_tick_time = start_time
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, config.interval_seconds - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in {tick_type.value} processor: {e}")
                processor.stats.errors += 1
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _get_tick_data(self, tick_type: TickType) -> Dict[str, Any]:
        """Get data for tick processing"""
        # This would query the database for relevant data
        # For now, return empty data
        return {
            'ships': [],
            'planets': [],
            'cybertron_ships': [],
            'clicker': 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all processors"""
        stats = {}
        for tick_type, processor in self.processors.items():
            stats[tick_type.value] = {
                'stats': processor.get_stats(),
                'enabled': processor.enabled
            }
        return stats
    
    def set_processor_enabled(self, tick_type: TickType, enabled: bool):
        """Enable or disable a tick processor"""
        if tick_type in self.processors:
            self.processors[tick_type].enabled = enabled
            self.configs[tick_type].enabled = enabled
