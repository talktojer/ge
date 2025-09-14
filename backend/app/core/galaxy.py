"""
Galactic Empire - Galaxy Map System

This module implements the sector-based galaxy map system with a 30x15 grid
(6000x6000 sectors total), ported from the original C code.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math
from .coordinates import Coordinate, Sector, get_sector, same_sector


class SectorType(Enum):
    """Types of sectors in the galaxy"""
    NORMAL = "normal"
    NEUTRAL = "neutral"  # Sector 0,0 - Galactic Command
    WORMHOLE = "wormhole"


class PlanetType(Enum):
    """Types of planetary objects"""
    PLANET = "planet"
    WORMHOLE = "wormhole"
    ASTEROID = "asteroid"


@dataclass
class PlanetObject:
    """Planetary object in a sector"""
    planet_id: int
    coord: Coordinate
    planet_type: PlanetType
    name: str
    environment: int = 0
    resources: int = 0
    owner: Optional[str] = None
    population: int = 0
    items: Dict[str, int] = None  # Item quantities
    
    def __post_init__(self):
        if self.items is None:
            self.items = {}


@dataclass
class GalaxySector:
    """A sector in the galaxy"""
    sector: Sector
    sector_type: SectorType
    num_planets: int
    planets: List[PlanetObject]
    beacon_message: Optional[str] = None
    owner: Optional[str] = None


class GalaxyMap:
    """Main galaxy map system"""
    
    def __init__(self, galaxy_radius: int = 300):
        self.galaxy_radius = galaxy_radius  # UNIVMAX from original
        self.sectors: Dict[Tuple[int, int], GalaxySector] = {}
        self.neutral_sector = Sector(0, 0)
        
        # Galaxy generation parameters
        self.planet_odds = 3  # 1 in 3 chance of planets per sector
        self.max_planets_per_sector = 9
        self.neutral_planets = self._create_neutral_planets()
    
    def _create_neutral_planets(self) -> List[PlanetObject]:
        """Create the special planets in sector 0,0 (Galactic Command)"""
        planets = []
        
        # Create neutral planets with specific coordinates
        neutral_coords = [
            (0.0, 0.0),      # Center
            (1000.0, 1000.0), # Corner
            (2000.0, 2000.0), # Another corner
            # Add more as needed
        ]
        
        for i, (x, y) in enumerate(neutral_coords):
            planet = PlanetObject(
                planet_id=i + 1,
                coord=Coordinate(x, y),
                planet_type=PlanetType.PLANET,
                name=f"Galactic Command {i + 1}",
                environment=100,  # Perfect environment
                resources=100,    # Perfect resources
                owner="Galactic Command",
                population=1000000
            )
            planets.append(planet)
        
        return planets
    
    def get_sector(self, coord: Coordinate) -> GalaxySector:
        """Get or create a sector for the given coordinate"""
        sector = get_sector(coord)
        sector_key = (sector.x, sector.y)
        
        if sector_key not in self.sectors:
            self.sectors[sector_key] = self._create_sector(sector)
        
        return self.sectors[sector_key]
    
    def _create_sector(self, sector: Sector) -> GalaxySector:
        """Create a new sector with planets"""
        # Check if this is the neutral sector
        if sector.x == 0 and sector.y == 0:
            return GalaxySector(
                sector=sector,
                sector_type=SectorType.NEUTRAL,
                num_planets=len(self.neutral_planets),
                planets=self.neutral_planets.copy()
            )
        
        # Generate planets for normal sectors
        planets = []
        
        # Determine number of planets (1 in 3 chance, 0-9 planets)
        if random.randint(1, self.planet_odds) == 1:
            num_planets = random.randint(0, self.max_planets_per_sector)
            
            for i in range(num_planets):
                planet = self._generate_planet(sector, i + 1)
                planets.append(planet)
        
        return GalaxySector(
            sector=sector,
            sector_type=SectorType.NORMAL,
            num_planets=len(planets),
            planets=planets
        )
    
    def _generate_planet(self, sector: Sector, planet_num: int) -> PlanetObject:
        """Generate a random planet in a sector"""
        # Generate random coordinates within the sector (0-9999)
        x = random.uniform(0, 9999)
        y = random.uniform(0, 9999)
        
        # Convert to absolute coordinates
        abs_x = sector.x + (x / 10000.0)
        abs_y = sector.y + (y / 10000.0)
        
        # Random planet type (mostly planets, some wormholes)
        planet_type = PlanetType.PLANET
        if random.randint(1, 20) == 1:  # 1 in 20 chance of wormhole
            planet_type = PlanetType.WORMHOLE
        
        # Generate environment and resources (1-100)
        environment = random.randint(1, 100)
        resources = random.randint(1, 100)
        
        # Generate planet name
        name = f"Planet {sector.x},{sector.y}-{planet_num}"
        if planet_type == PlanetType.WORMHOLE:
            name = f"Wormhole {sector.x},{sector.y}-{planet_num}"
        
        return PlanetObject(
            planet_id=planet_num,
            coord=Coordinate(abs_x, abs_y),
            planet_type=planet_type,
            name=name,
            environment=environment,
            resources=resources,
            population=random.randint(0, 1000000)
        )
    
    def get_planets_in_sector(self, coord: Coordinate) -> List[PlanetObject]:
        """Get all planets in the sector containing the given coordinate"""
        sector = self.get_sector(coord)
        return sector.planets
    
    def get_planet_at_coord(self, coord: Coordinate) -> Optional[PlanetObject]:
        """Get the planet at the exact coordinate, if any"""
        planets = self.get_planets_in_sector(coord)
        
        # Find planet closest to coordinate (within some tolerance)
        tolerance = 100.0  # Within 100 units
        closest_planet = None
        min_distance = float('inf')
        
        for planet in planets:
            distance = math.sqrt(
                (planet.coord.x - coord.x) ** 2 + 
                (planet.coord.y - coord.y) ** 2
            )
            if distance < tolerance and distance < min_distance:
                min_distance = distance
                closest_planet = planet
        
        return closest_planet
    
    def get_sector_info(self, coord: Coordinate) -> Dict:
        """Get information about a sector"""
        sector = self.get_sector(coord)
        
        return {
            'sector_x': sector.sector.x,
            'sector_y': sector.sector.y,
            'sector_type': sector.sector_type.value,
            'num_planets': sector.num_planets,
            'planets': [
                {
                    'planet_id': p.planet_id,
                    'name': p.name,
                    'type': p.planet_type.value,
                    'coord': {'x': p.coord.x, 'y': p.coord.y},
                    'environment': p.environment,
                    'resources': p.resources,
                    'owner': p.owner,
                    'population': p.population
                }
                for p in sector.planets
            ],
            'beacon_message': sector.beacon_message,
            'owner': sector.owner
        }
    
    def set_beacon_message(self, coord: Coordinate, message: str):
        """Set a beacon message for a sector"""
        sector = self.get_sector(coord)
        sector.beacon_message = message
    
    def get_beacon_message(self, coord: Coordinate) -> Optional[str]:
        """Get beacon message for a sector"""
        sector = self.get_sector(coord)
        return sector.beacon_message
    
    def is_neutral_sector(self, coord: Coordinate) -> bool:
        """Check if a coordinate is in the neutral sector (0,0)"""
        sector = get_sector(coord)
        return sector.x == 0 and sector.y == 0
    
    def get_galaxy_bounds(self) -> Tuple[Coordinate, Coordinate]:
        """Get the bounds of the galaxy"""
        min_coord = Coordinate(-self.galaxy_radius, -self.galaxy_radius)
        max_coord = Coordinate(self.galaxy_radius, self.galaxy_radius)
        return min_coord, max_coord
    
    def is_in_galaxy(self, coord: Coordinate) -> bool:
        """Check if a coordinate is within galaxy bounds"""
        return (-self.galaxy_radius <= coord.x <= self.galaxy_radius and
                -self.galaxy_radius <= coord.y <= self.galaxy_radius)
    
    def get_sectors_in_range(self, center: Coordinate, range_sectors: int) -> List[GalaxySector]:
        """Get all sectors within a given range of sectors"""
        sectors = []
        center_sector = get_sector(center)
        
        for x in range(center_sector.x - range_sectors, center_sector.x + range_sectors + 1):
            for y in range(center_sector.y - range_sectors, center_sector.y + range_sectors + 1):
                if abs(x) <= self.galaxy_radius and abs(y) <= self.galaxy_radius:
                    sector_key = (x, y)
                    if sector_key in self.sectors:
                        sectors.append(self.sectors[sector_key])
        
        return sectors
    
    def get_galaxy_statistics(self) -> Dict:
        """Get statistics about the galaxy"""
        total_sectors = len(self.sectors)
        total_planets = sum(sector.num_planets for sector in self.sectors.values())
        
        planet_types = {}
        for sector in self.sectors.values():
            for planet in sector.planets:
                planet_type = planet.planet_type.value
                planet_types[planet_type] = planet_types.get(planet_type, 0) + 1
        
        return {
            'total_sectors': total_sectors,
            'total_planets': total_planets,
            'planet_types': planet_types,
            'galaxy_radius': self.galaxy_radius,
            'max_sectors': (self.galaxy_radius * 2 + 1) ** 2
        }
