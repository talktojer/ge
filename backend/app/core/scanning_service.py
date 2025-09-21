"""
Enhanced scanning service that integrates with battle interface and communication systems
Provides comprehensive scanning and detection capabilities for ships, planets, and sectors
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .battle_interface import RangeScanner, ScannerType, ScanResult, TacticalDisplay, TacticalDisplayMode
from .coordinates import Coordinate, distance_between_coords, bearing_between_coords, get_sector
from ..models.ship import Ship, ShipClass
from ..models.planet import Planet
from ..models.mine import Mine
from ..models.beacon import Beacon
from ..models.wormhole import Wormhole
from ..models.user import User

logger = logging.getLogger(__name__)

class ScanningService:
    """Enhanced scanning service with database integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.range_scanner = RangeScanner()
        
    def scan_ships_detailed(self, scanner_ship_id: int, scanner_type: ScannerType = ScannerType.LONG_RANGE) -> List[Dict[str, Any]]:
        """Perform detailed ship scan with full information"""
        try:
            scanner_ship = self.db.query(Ship).filter(Ship.id == scanner_ship_id).first()
            if not scanner_ship:
                raise ValueError("Scanner ship not found")
                
            # Get scanner range based on ship class and scanner type
            base_range = self.range_scanner.scanner_ranges.get(scanner_type, 50000.0)
            ship_range_multiplier = getattr(scanner_ship.ship_class, 'scan_range_multiplier', 1.0) if scanner_ship.ship_class else 1.0
            effective_range = base_range * ship_range_multiplier
            
            # Get all ships in the same sector
            ships_in_sector = self.db.query(Ship).filter(
                Ship.sector_x == scanner_ship.sector_x,
                Ship.sector_y == scanner_ship.sector_y,
                Ship.id != scanner_ship_id,
                Ship.status != 'destroyed'
            ).all()
            
            scanned_ships = []
            
            for ship in ships_in_sector:
                # Calculate distance
                distance = distance_between_coords(
                    scanner_ship.coord_x, scanner_ship.coord_y,
                    ship.coord_x, ship.coord_y
                ) * 10000  # Convert to original scale
                
                if distance > effective_range:
                    continue
                    
                # Check cloaking effectiveness
                cloak_effectiveness = self._calculate_cloak_effectiveness(
                    ship, scanner_ship, scanner_type, distance
                )
                
                if cloak_effectiveness >= 1.0:  # Fully cloaked
                    continue
                    
                # Calculate bearing
                ship_bearing = bearing_between_coords(
                    scanner_ship.coord_x, scanner_ship.coord_y,
                    ship.coord_x, ship.coord_y
                )
                
                # Determine information accuracy based on range and cloak
                info_accuracy = self._calculate_scan_accuracy(distance, effective_range, cloak_effectiveness)
                
                scan_data = {
                    'ship_id': ship.id,
                    'ship_name': ship.name,
                    'owner': ship.owner.userid if ship.owner else "Unknown",
                    'owner_id': ship.owner_id,
                    'ship_class': ship.ship_class.name if ship.ship_class else "Unknown",
                    'ship_type': ship.ship_class.type_name if ship.ship_class else "Unknown",
                    'distance': round(distance),
                    'bearing': round(ship_bearing),
                    'heading': ship.heading,
                    'speed': ship.speed if info_accuracy > 0.7 else None,
                    'sector_x': ship.sector_x,
                    'sector_y': ship.sector_y,
                    'coordinates': {
                        'x': ship.coord_x if info_accuracy > 0.8 else None,
                        'y': ship.coord_y if info_accuracy > 0.8 else None
                    },
                    'shields_up': ship.shields_up if info_accuracy > 0.6 else None,
                    'shield_type': ship.shield_type if info_accuracy > 0.8 else None,
                    'damage': ship.damage if info_accuracy > 0.7 else None,
                    'energy': ship.energy if info_accuracy > 0.9 else None,
                    'cloak_level': ship.cloak_level if info_accuracy > 0.95 else None,
                    'team': ship.owner.team.name if ship.owner and ship.owner.team and info_accuracy > 0.5 else None,
                    'team_id': ship.owner.team_id if ship.owner and info_accuracy > 0.5 else None,
                    'kills': ship.owner.kills if ship.owner and info_accuracy > 0.8 else None,
                    'last_seen': datetime.utcnow().isoformat(),
                    'scan_confidence': info_accuracy,
                    'is_cloaked': ship.cloak_level > 0,
                    'cloak_effectiveness': cloak_effectiveness,
                    'threat_level': self._assess_threat_level(ship, scanner_ship),
                    'scanner_type': scanner_type.value
                }
                
                # Add detailed ship systems if scan is very accurate
                if info_accuracy > 0.85:
                    scan_data.update({
                        'weapons': {
                            'phasers': ship.phasers,
                            'torpedoes': ship.torpedoes,
                            'missiles': ship.missiles,
                            'ion_cannons': ship.ion_cannons
                        },
                        'cargo': {
                            'current_weight': ship.cargo_weight,
                            'max_capacity': ship.ship_class.cargo_capacity if ship.ship_class else None
                        },
                        'systems': {
                            'jammer': ship.jammer_level if hasattr(ship, 'jammer_level') else 0,
                            'decoys': ship.decoys if hasattr(ship, 'decoys') else 0
                        }
                    })
                
                scanned_ships.append(scan_data)
            
            # Sort by distance
            scanned_ships.sort(key=lambda x: x['distance'])
            
            logger.info(f"Ship scan completed: {len(scanned_ships)} ships detected by ship {scanner_ship_id}")
            return scanned_ships
            
        except Exception as e:
            logger.error(f"Error in detailed ship scan: {str(e)}")
            raise
    
    def scan_planets_detailed(self, scanner_ship_id: int) -> List[Dict[str, Any]]:
        """Perform detailed planet scan"""
        try:
            scanner_ship = self.db.query(Ship).filter(Ship.id == scanner_ship_id).first()
            if not scanner_ship:
                raise ValueError("Scanner ship not found")
                
            # Get planets in current sector
            planets = self.db.query(Planet).filter(
                Planet.sector_x == scanner_ship.sector_x,
                Planet.sector_y == scanner_ship.sector_y,
                Planet.type == 'planet'
            ).all()
            
            scanned_planets = []
            
            for planet in planets:
                distance = distance_between_coords(
                    scanner_ship.coord_x, scanner_ship.coord_y,
                    planet.coord_x, planet.coord_y
                ) * 10000
                
                planet_bearing = bearing_between_coords(
                    scanner_ship.coord_x, scanner_ship.coord_y,
                    planet.coord_x, planet.coord_y
                )
                
                # Planet scan accuracy decreases with distance
                scan_accuracy = max(0.3, 1.0 - (distance / 200000.0))
                
                scan_data = {
                    'planet_id': planet.id,
                    'planet_name': planet.name,
                    'owner': planet.owner.userid if planet.owner else None,
                    'owner_id': planet.owner_id,
                    'distance': round(distance),
                    'bearing': round(planet_bearing),
                    'sector_x': planet.sector_x,
                    'sector_y': planet.sector_y,
                    'coordinates': {
                        'x': planet.coord_x,
                        'y': planet.coord_y
                    },
                    'environment': planet.environment if scan_accuracy > 0.4 else None,
                    'resource_factor': planet.resource_factor if scan_accuracy > 0.6 else None,
                    'population': planet.population if scan_accuracy > 0.5 else self._estimate_population(planet.population, scan_accuracy),
                    'troops': planet.troops if scan_accuracy > 0.7 else None,
                    'team': planet.owner.team.name if planet.owner and planet.owner.team and scan_accuracy > 0.5 else None,
                    'beacon_message': planet.beacon_message if scan_accuracy > 0.8 else None,
                    'scan_confidence': scan_accuracy,
                    'last_scanned': datetime.utcnow().isoformat(),
                    'colonized': planet.owner_id is not None
                }
                
                # Add military assets if scan is good enough
                if scan_accuracy > 0.6:
                    scan_data['military'] = {
                        'missiles': planet.missiles if scan_accuracy > 0.7 else self._estimate_quantity(planet.missiles, scan_accuracy),
                        'torpedoes': planet.torpedoes if scan_accuracy > 0.7 else self._estimate_quantity(planet.torpedoes, scan_accuracy),
                        'fighters': planet.fighters if scan_accuracy > 0.8 else None,
                        'ion_cannons': planet.ion_cannons if scan_accuracy > 0.8 else None
                    }
                
                # Add resource information if scan is very accurate
                if scan_accuracy > 0.75:
                    scan_data['resources'] = {
                        'food': planet.food,
                        'ore': planet.ore,
                        'fuel': planet.fuel,
                        'colonists': planet.colonists,
                        'equipment': planet.equipment
                    }
                
                scanned_planets.append(scan_data)
            
            scanned_planets.sort(key=lambda x: x['distance'])
            
            logger.info(f"Planet scan completed: {len(scanned_planets)} planets detected by ship {scanner_ship_id}")
            return scanned_planets
            
        except Exception as e:
            logger.error(f"Error in detailed planet scan: {str(e)}")
            raise
    
    def scan_sector_comprehensive(self, scanner_ship_id: int) -> Dict[str, Any]:
        """Perform comprehensive sector scan including all objects"""
        try:
            scanner_ship = self.db.query(Ship).filter(Ship.id == scanner_ship_id).first()
            if not scanner_ship:
                raise ValueError("Scanner ship not found")
            
            sector_x, sector_y = scanner_ship.sector_x, scanner_ship.sector_y
            
            # Scan all types of objects
            ships = self.scan_ships_detailed(scanner_ship_id, ScannerType.LONG_RANGE)
            planets = self.scan_planets_detailed(scanner_ship_id)
            mines = self._scan_mines(scanner_ship)
            beacons = self._scan_beacons(scanner_ship)
            wormholes = self._scan_wormholes(scanner_ship)
            
            # Generate sector summary
            sector_summary = {
                'sector': {'x': sector_x, 'y': sector_y},
                'scanner_ship': {
                    'id': scanner_ship.id,
                    'name': scanner_ship.name,
                    'position': {
                        'x': scanner_ship.coord_x,
                        'y': scanner_ship.coord_y
                    }
                },
                'scan_time': datetime.utcnow().isoformat(),
                'objects': {
                    'ships': ships,
                    'planets': planets,
                    'mines': mines,
                    'beacons': beacons,
                    'wormholes': wormholes
                },
                'counts': {
                    'ships': len(ships),
                    'planets': len(planets),
                    'mines': len(mines),
                    'beacons': len(beacons),
                    'wormholes': len(wormholes),
                    'total_objects': len(ships) + len(planets) + len(mines) + len(beacons) + len(wormholes)
                },
                'threat_assessment': self._assess_sector_threats(ships, planets),
                'strategic_value': self._assess_sector_value(planets, mines, wormholes)
            }
            
            return sector_summary
            
        except Exception as e:
            logger.error(f"Error in comprehensive sector scan: {str(e)}")
            raise
    
    def scan_hyperspace(self, scanner_ship_id: int) -> Dict[str, Any]:
        """Perform hyperspace scan for long-range detection"""
        try:
            scanner_ship = self.db.query(Ship).filter(Ship.id == scanner_ship_id).first()
            if not scanner_ship:
                raise ValueError("Scanner ship not found")
                
            # Hyperspace scan covers multiple sectors
            scan_radius = 3  # Scan 3 sectors in each direction
            current_sector = (scanner_ship.sector_x, scanner_ship.sector_y)
            
            detected_objects = []
            
            for dx in range(-scan_radius, scan_radius + 1):
                for dy in range(-scan_radius, scan_radius + 1):
                    target_sector_x = current_sector[0] + dx
                    target_sector_y = current_sector[1] + dy
                    
                    # Skip current sector (already scanned)
                    if dx == 0 and dy == 0:
                        continue
                    
                    # Scan this sector for major objects
                    sector_objects = self._scan_remote_sector(
                        target_sector_x, target_sector_y, scanner_ship
                    )
                    detected_objects.extend(sector_objects)
            
            return {
                'scan_type': 'hyperspace',
                'scanner_ship_id': scanner_ship_id,
                'scan_center': current_sector,
                'scan_radius': scan_radius,
                'scan_time': datetime.utcnow().isoformat(),
                'detected_objects': detected_objects,
                'total_detections': len(detected_objects)
            }
            
        except Exception as e:
            logger.error(f"Error in hyperspace scan: {str(e)}")
            raise
    
    def _scan_mines(self, scanner_ship: Ship) -> List[Dict[str, Any]]:
        """Scan for mines in current sector"""
        mines = self.db.query(Mine).filter(
            Mine.sector_x == scanner_ship.sector_x,
            Mine.sector_y == scanner_ship.sector_y,
            Mine.is_active == True
        ).all()
        
        mine_data = []
        for mine in mines:
            distance = distance_between_coords(
                scanner_ship.coord_x, scanner_ship.coord_y,
                mine.coord_x, mine.coord_y
            ) * 10000
            
            # Mines are harder to detect
            if distance < 75000 and mine.cloak_level < 5:  # Only detect close, poorly cloaked mines
                mine_data.append({
                    'mine_id': mine.id,
                    'owner': mine.owner.userid if mine.owner else "Unknown",
                    'distance': round(distance),
                    'bearing': round(bearing_between_coords(
                        scanner_ship.coord_x, scanner_ship.coord_y,
                        mine.coord_x, mine.coord_y
                    )),
                    'type': mine.mine_type,
                    'estimated_damage': mine.damage_potential if distance < 50000 else None
                })
        
        return mine_data
    
    def _scan_beacons(self, scanner_ship: Ship) -> List[Dict[str, Any]]:
        """Scan for beacons in current sector"""
        beacons = self.db.query(Beacon).filter(
            Beacon.sector_x == scanner_ship.sector_x,
            Beacon.sector_y == scanner_ship.sector_y,
            Beacon.is_active == True
        ).all()
        
        beacon_data = []
        for beacon in beacons:
            distance = distance_between_coords(
                scanner_ship.coord_x, scanner_ship.coord_y,
                beacon.coord_x, beacon.coord_y
            ) * 10000
            
            beacon_data.append({
                'beacon_id': beacon.id,
                'owner': beacon.owner.userid if beacon.owner else "Unknown",
                'distance': round(distance),
                'bearing': round(bearing_between_coords(
                    scanner_ship.coord_x, scanner_ship.coord_y,
                    beacon.coord_x, beacon.coord_y
                )),
                'message': beacon.message if distance < 100000 else None,
                'type': beacon.beacon_type
            })
        
        return beacon_data
    
    def _scan_wormholes(self, scanner_ship: Ship) -> List[Dict[str, Any]]:
        """Scan for wormholes in current sector"""
        wormholes = self.db.query(Wormhole).filter(
            Wormhole.sector_x == scanner_ship.sector_x,
            Wormhole.sector_y == scanner_ship.sector_y,
            Wormhole.is_active == True
        ).all()
        
        wormhole_data = []
        for wormhole in wormholes:
            distance = distance_between_coords(
                scanner_ship.coord_x, scanner_ship.coord_y,
                wormhole.coord_x, wormhole.coord_y
            ) * 10000
            
            wormhole_data.append({
                'wormhole_id': wormhole.id,
                'distance': round(distance),
                'bearing': round(bearing_between_coords(
                    scanner_ship.coord_x, scanner_ship.coord_y,
                    wormhole.coord_x, wormhole.coord_y
                )),
                'destination_sector': {
                    'x': wormhole.dest_sector_x,
                    'y': wormhole.dest_sector_y
                } if distance < 50000 else None,  # Only reveal destination if close
                'stability': wormhole.stability if distance < 25000 else None
            })
        
        return wormhole_data
    
    def _scan_remote_sector(self, sector_x: int, sector_y: int, scanner_ship: Ship) -> List[Dict[str, Any]]:
        """Scan a remote sector for major objects (hyperspace scan)"""
        objects = []
        
        # Only detect major objects at long range
        # Large ships
        major_ships = self.db.query(Ship).filter(
            Ship.sector_x == sector_x,
            Ship.sector_y == sector_y,
            Ship.status != 'destroyed'
        ).join(ShipClass).filter(
            ShipClass.tonnage > 50000  # Only large ships
        ).all()
        
        for ship in major_ships:
            if ship.cloak_level < 3:  # Only unclaked or lightly cloaked
                objects.append({
                    'type': 'ship',
                    'id': ship.id,
                    'name': ship.name,
                    'sector': {'x': sector_x, 'y': sector_y},
                    'owner': ship.owner.userid if ship.owner else "Unknown",
                    'ship_class': ship.ship_class.name if ship.ship_class else "Unknown",
                    'confidence': 0.6
                })
        
        # Colonized planets
        colonized_planets = self.db.query(Planet).filter(
            Planet.sector_x == sector_x,
            Planet.sector_y == sector_y,
            Planet.owner_id.isnot(None)
        ).all()
        
        for planet in colonized_planets:
            objects.append({
                'type': 'planet',
                'id': planet.id,
                'name': planet.name,
                'sector': {'x': sector_x, 'y': sector_y},
                'owner': planet.owner.userid if planet.owner else "Unknown",
                'confidence': 0.8
            })
        
        return objects
    
    def _calculate_cloak_effectiveness(self, target_ship: Ship, scanner_ship: Ship, 
                                     scanner_type: ScannerType, distance: float) -> float:
        """Calculate how effectively a ship is cloaked against this scan"""
        base_cloak = target_ship.cloak_level / 10.0  # 0.0 to 1.0
        
        # Distance reduces cloak effectiveness
        distance_factor = min(1.0, distance / 100000.0)  # Closer = harder to cloak
        
        # Scanner type effectiveness
        scanner_effectiveness = {
            ScannerType.SHORT_RANGE: 0.8,
            ScannerType.LONG_RANGE: 0.6,
            ScannerType.TACTICAL: 0.9,
            ScannerType.HYPERSPACE: 0.4,
            ScannerType.CLOAK_DETECTOR: 1.2
        }.get(scanner_type, 0.6)
        
        # Scanner ship's detection capability
        scanner_skill = getattr(scanner_ship.ship_class, 'scanner_effectiveness', 1.0) if scanner_ship.ship_class else 1.0
        
        effective_cloak = base_cloak * (1.0 - distance_factor * 0.3) / (scanner_effectiveness * scanner_skill)
        return max(0.0, min(1.0, effective_cloak))
    
    def _calculate_scan_accuracy(self, distance: float, max_range: float, cloak_effectiveness: float) -> float:
        """Calculate scan accuracy based on distance and cloaking"""
        range_accuracy = 1.0 - (distance / max_range)
        cloak_penalty = cloak_effectiveness * 0.5
        return max(0.1, min(1.0, range_accuracy - cloak_penalty))
    
    def _assess_threat_level(self, target_ship: Ship, scanner_ship: Ship) -> str:
        """Assess threat level of scanned ship"""
        if not target_ship.owner or not scanner_ship.owner:
            return "unknown"
            
        # Same team = no threat
        if target_ship.owner.team_id == scanner_ship.owner.team_id:
            return "friendly"
            
        # Compare ship capabilities
        target_power = self._estimate_ship_power(target_ship)
        scanner_power = self._estimate_ship_power(scanner_ship)
        
        power_ratio = target_power / max(scanner_power, 1)
        
        if power_ratio > 1.5:
            return "high"
        elif power_ratio > 0.8:
            return "medium"
        else:
            return "low"
    
    def _estimate_ship_power(self, ship: Ship) -> float:
        """Estimate ship combat power"""
        if not ship.ship_class:
            return 100.0
            
        # Simple power estimate based on ship class and weapons
        base_power = ship.ship_class.tonnage / 1000.0
        weapon_power = (ship.phasers * 10 + ship.torpedoes * 15 + 
                       ship.missiles * 12 + ship.ion_cannons * 20)
        
        return base_power + weapon_power
    
    def _assess_sector_threats(self, ships: List[Dict], planets: List[Dict]) -> Dict[str, Any]:
        """Assess overall threat level in sector"""
        threat_levels = [ship.get('threat_level', 'unknown') for ship in ships]
        hostile_count = sum(1 for level in threat_levels if level in ['high', 'medium'])
        
        return {
            'total_ships': len(ships),
            'hostile_ships': hostile_count,
            'threat_level': 'high' if hostile_count > 2 else 'medium' if hostile_count > 0 else 'low',
            'colonized_planets': sum(1 for planet in planets if planet.get('colonized', False)),
            'military_assets': sum(1 for planet in planets if planet.get('military', {}).get('missiles', 0) > 0)
        }
    
    def _assess_sector_value(self, planets: List[Dict], mines: List[Dict], wormholes: List[Dict]) -> Dict[str, Any]:
        """Assess strategic value of sector"""
        colonized_planets = sum(1 for planet in planets if planet.get('colonized', False))
        resource_planets = sum(1 for planet in planets 
                             if planet.get('resource_factor', 0) > 1.0)
        
        return {
            'colonized_planets': colonized_planets,
            'resource_rich_planets': resource_planets,
            'active_mines': len(mines),
            'wormhole_access': len(wormholes),
            'strategic_value': 'high' if (colonized_planets > 2 or len(wormholes) > 0) 
                             else 'medium' if colonized_planets > 0 
                             else 'low'
        }
    
    def _estimate_population(self, actual_population: int, accuracy: float) -> Optional[str]:
        """Estimate population when scan isn't accurate enough for exact numbers"""
        if accuracy < 0.3:
            return None
            
        if actual_population < 1000:
            return "Small settlement"
        elif actual_population < 10000:
            return "Town"
        elif actual_population < 100000:
            return "City"
        elif actual_population < 1000000:
            return "Large city"
        else:
            return "Major population center"
    
    def _estimate_quantity(self, actual_quantity: int, accuracy: float) -> Optional[str]:
        """Estimate military quantities when scan isn't accurate"""
        if accuracy < 0.5:
            return None
            
        if actual_quantity == 0:
            return "None detected"
        elif actual_quantity < 10:
            return "Small stockpile"
        elif actual_quantity < 100:
            return "Moderate stockpile"
        else:
            return "Large stockpile"
