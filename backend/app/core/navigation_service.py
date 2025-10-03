"""
Galactic Empire - Navigation Service

This module provides navigation-related services including sector navigation,
cargo management, ship maintenance, and other missing commands from the original game.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.coordinates import Coordinate, get_sector, distance, bearing
from app.core.game_config import game_config
from app.models.ship import Ship, ShipClass
from app.models.planet import Planet
from app.models.user import User
from app.models.user_account import UserAccount

logger = logging.getLogger(__name__)


class NavigationService:
    """Service for navigation-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_navigation(self, current_position: Coordinate, 
                           target_position: Coordinate) -> Dict[str, Any]:
        """Calculate navigation information between two points"""
        try:
            # Calculate distance
            dist = distance(current_position, target_position)
            
            # Calculate bearing
            bear = bearing(current_position, target_position)
            
            # Estimate travel time (assuming average speed)
            # This would need to be calculated based on ship's actual speed
            estimated_time = dist / 50000.0  # Rough estimate in game ticks
            
            return {
                "distance": dist,
                "bearing": bear,
                "estimated_time": estimated_time,
                "current_sector": get_sector(current_position),
                "target_sector": get_sector(target_position)
            }
            
        except Exception as e:
            logger.error(f"Error calculating navigation: {e}")
            raise
    
    def jettison_cargo(self, ship_id: int, item_type: str, 
                      quantity: Optional[int] = None) -> Dict[str, Any]:
        """Jettison cargo from ship"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Map item types to ship attributes
            item_mapping = {
                "men": "men",
                "tro": "troops", 
                "mis": "missiles",
                "tor": "torpedoes",
                "ion": "ion_cannons",
                "flu": "flux_pods",
                "foo": "food",
                "fig": "fighters",
                "dec": "decoys",
                "min": "mines",
                "jam": "jammers",
                "zip": "zippers",
                "gol": "gold"
            }
            
            if item_type not in item_mapping:
                return {"success": False, "message": f"Unknown item type: {item_type}"}
            
            # Get current quantity
            attr_name = item_mapping[item_type]
            current_quantity = getattr(ship, attr_name, 0)
            
            if current_quantity <= 0:
                return {"success": False, "message": f"No {item_type} to jettison"}
            
            # Determine quantity to jettison
            if quantity is None:
                jettison_quantity = current_quantity  # Jettison all
            else:
                jettison_quantity = min(quantity, current_quantity)
            
            # Update ship cargo
            new_quantity = current_quantity - jettison_quantity
            setattr(ship, attr_name, new_quantity)
            
            # Update ship weight (if applicable)
            # This would need to be implemented based on item weights
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Jettisoned {jettison_quantity} {item_type}",
                "jettisoned": jettison_quantity,
                "remaining": new_quantity
            }
            
        except Exception as e:
            logger.error(f"Error jettisoning cargo: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Jettison failed: {str(e)}"}
    
    def request_maintenance(self, ship_id: int, planet_id: Optional[int] = None) -> Dict[str, Any]:
        """Request ship maintenance"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Determine maintenance location
            if planet_id:
                planet = self.db.query(Planet).filter(Planet.id == planet_id).first()
                if not planet:
                    return {"success": False, "message": "Planet not found"}
                
                # Check if ship is in orbit around the planet
                planet_distance = distance(
                    Coordinate(ship.x_coord, ship.y_coord),
                    Coordinate(planet.x_coord, planet.y_coord)
                )
                
                if planet_distance > 250:
                    return {"success": False, "message": "Ship must be within 250 units of planet for maintenance"}
                
                # Check if planet belongs to user or is Zygor
                user = self.db.query(User).filter(User.id == ship.user_id).first()
                if planet.owner_id != user.id and planet.id != 1:  # Assuming Zygor is planet ID 1
                    return {"success": False, "message": "Can only get maintenance at own planets or Zygor"}
                
                # Calculate cost based on location
                if planet.id == 1:  # Zygor
                    cost = 2500
                else:
                    cost = 200
                    
            else:
                # Use current planet if in orbit
                current_sector = get_sector(Coordinate(ship.x_coord, ship.y_coord))
                planets = self.db.query(Planet).filter(
                    Planet.sector_x == current_sector.x,
                    Planet.sector_y == current_sector.y
                ).all()
                
                if not planets:
                    return {"success": False, "message": "No planet available for maintenance"}
                
                # Find closest planet
                closest_planet = None
                min_distance = float('inf')
                
                for planet in planets:
                    planet_distance = distance(
                        Coordinate(ship.x_coord, ship.y_coord),
                        Coordinate(planet.x_coord, planet.y_coord)
                    )
                    if planet_distance < min_distance and planet_distance <= 250:
                        min_distance = planet_distance
                        closest_planet = planet
                
                if not closest_planet:
                    return {"success": False, "message": "No planet within 250 units for maintenance"}
                
                # Check ownership
                user = self.db.query(User).filter(User.id == ship.user_id).first()
                if closest_planet.owner_id != user.id and closest_planet.id != 1:
                    return {"success": False, "message": "Can only get maintenance at own planets or Zygor"}
                
                cost = 200 if closest_planet.id != 1 else 2500
            
            # Check if user has enough cash
            user_account = self.db.query(UserAccount).filter(UserAccount.user_id == ship.user_id).first()
            if not user_account or user_account.cash < cost:
                return {"success": False, "message": f"Insufficient funds. Cost: {cost} credits"}
            
            # Deduct cost
            user_account.cash -= cost
            
            # Calculate repair time based on damage
            damage_percent = ship.damage / 100.0 if ship.damage else 0
            repair_time = int(damage_percent * 60)  # Up to 60 ticks for full repair
            
            # Start repair process (this would need to be implemented in the game engine)
            # For now, we'll just log the request
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Maintenance requested. Cost: {cost} credits",
                "cost": cost,
                "repair_time": repair_time
            }
            
        except Exception as e:
            logger.error(f"Error requesting maintenance: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Maintenance request failed: {str(e)}"}
    
    def purchase_new_equipment(self, ship_id: int, equipment_type: str, 
                              class_number: int) -> Dict[str, Any]:
        """Purchase new ship, shield, or phaser system"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Check if ship is at Zygor (sector 0,0)
            current_sector = get_sector(Coordinate(ship.x_coord, ship.y_coord))
            if current_sector.x != 0 or current_sector.y != 0:
                return {"success": False, "message": "Must be at Zygor (sector 0,0) to purchase equipment"}
            
            # Check if ship is in orbit around Zygor
            zygor_distance = distance(
                Coordinate(ship.x_coord, ship.y_coord),
                Coordinate(0, 0)  # Zygor coordinates
            )
            
            if zygor_distance > 250:
                return {"success": False, "message": "Must be within 250 units of Zygor to purchase equipment"}
            
            # Get user account
            user_account = self.db.query(UserAccount).filter(UserAccount.user_id == ship.user_id).first()
            if not user_account:
                return {"success": False, "message": "User account not found"}
            
            # Calculate cost based on equipment type and class
            if equipment_type == "ship":
                cost = self._calculate_ship_cost(class_number)
                equipment_name = self._get_ship_class_name(class_number)
            elif equipment_type == "shield":
                cost = self._calculate_shield_cost(class_number)
                equipment_name = f"Mark-{class_number} Shield"
            elif equipment_type == "phaser":
                cost = self._calculate_phaser_cost(class_number)
                equipment_name = f"Mark-{class_number} Phaser"
            else:
                return {"success": False, "message": f"Unknown equipment type: {equipment_type}"}
            
            # Check if user has enough cash
            if user_account.cash < cost:
                return {"success": False, "message": f"Insufficient funds. Cost: {cost} credits"}
            
            # Purchase equipment
            if equipment_type == "ship":
                # Update ship class
                ship.shpclass = class_number
                # Update ship capabilities based on new class
                self._update_ship_capabilities(ship, class_number)
            elif equipment_type == "shield":
                # Update shield system
                ship.max_shields = self._get_shield_capacity(class_number)
            elif equipment_type == "phaser":
                # Update phaser system
                ship.max_phasers = self._get_phaser_capacity(class_number)
            
            # Deduct cost
            user_account.cash -= cost
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Purchased {equipment_name} for {cost} credits",
                "cost": cost,
                "new_equipment": {
                    "type": equipment_type,
                    "class": class_number,
                    "name": equipment_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error purchasing equipment: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Purchase failed: {str(e)}"}
    
    def sell_goods(self, ship_id: int, item_type: str, quantity: int) -> Dict[str, Any]:
        """Sell goods back to Zygor"""
        try:
            ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
            if not ship:
                return {"success": False, "message": "Ship not found"}
            
            # Check if ship is at Zygor
            current_sector = get_sector(Coordinate(ship.x_coord, ship.y_coord))
            if current_sector.x != 0 or current_sector.y != 0:
                return {"success": False, "message": "Must be at Zygor (sector 0,0) to sell goods"}
            
            # Map item types to ship attributes
            item_mapping = {
                "men": "men",
                "tro": "troops", 
                "mis": "missiles",
                "tor": "torpedoes",
                "ion": "ion_cannons",
                "flu": "flux_pods",
                "foo": "food",
                "fig": "fighters",
                "dec": "decoys",
                "min": "mines",
                "jam": "jammers",
                "zip": "zippers",
                "gol": "gold"
            }
            
            if item_type not in item_mapping:
                return {"success": False, "message": f"Unknown item type: {item_type}"}
            
            # Get current quantity
            attr_name = item_mapping[item_type]
            current_quantity = getattr(ship, attr_name, 0)
            
            if current_quantity <= 0:
                return {"success": False, "message": f"No {item_type} to sell"}
            
            # Determine quantity to sell
            sell_quantity = min(quantity, current_quantity)
            
            # Calculate payment (base price with transfer tax)
            base_price = self._get_item_base_price(item_type)
            transfer_tax_rate = 0.1  # 10% transfer tax
            payment = int(sell_quantity * base_price * (1 - transfer_tax_rate))
            transfer_tax = int(sell_quantity * base_price * transfer_tax_rate)
            
            # Update ship cargo
            new_quantity = current_quantity - sell_quantity
            setattr(ship, attr_name, new_quantity)
            
            # Add payment to user account
            user_account = self.db.query(UserAccount).filter(UserAccount.user_id == ship.user_id).first()
            if user_account:
                user_account.cash += payment
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Sold {sell_quantity} {item_type} for {payment} credits (transfer tax: {transfer_tax})",
                "sold": sell_quantity,
                "payment": payment,
                "transfer_tax": transfer_tax
            }
            
        except Exception as e:
            logger.error(f"Error selling goods: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Sell failed: {str(e)}"}
    
    def set_communication_frequency(self, user_id: int, channel: str, 
                                   frequency: Optional[str] = None) -> Dict[str, Any]:
        """Set communication channel frequency"""
        try:
            # Get user account
            user_account = self.db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
            if not user_account:
                return {"success": False, "message": "User account not found"}
            
            # Validate channel
            if channel.upper() not in ["A", "B", "C"]:
                return {"success": False, "message": "Channel must be A, B, or C"}
            
            # Set frequency
            if frequency is None or frequency.lower() == "hail":
                freq_value = "hail"
            else:
                try:
                    freq_value = int(frequency)
                    if freq_value < 1 or freq_value > 99999:
                        return {"success": False, "message": "Frequency must be between 1 and 99999"}
                except ValueError:
                    return {"success": False, "message": "Invalid frequency format"}
            
            # Update user account with frequency settings
            # This would need to be added to the UserAccount model
            # For now, we'll just log the change
            
            logger.info(f"User {user_id} set channel {channel} to frequency {freq_value}")
            
            return {
                "success": True,
                "message": f"Channel {channel} set to {freq_value}",
                "frequency": freq_value
            }
            
        except Exception as e:
            logger.error(f"Error setting frequency: {e}")
            return {"success": False, "message": f"Frequency setting failed: {str(e)}"}
    
    def get_online_players(self, show_all: bool = False) -> List[Dict[str, Any]]:
        """Get list of online players"""
        try:
            # Get active users (this would need to be enhanced with actual online status)
            users = self.db.query(User).filter(User.is_active == True).all()
            
            players = []
            for user in users:
                # Get user's ship
                ship = self.db.query(Ship).filter(
                    Ship.user_id == user.id,
                    Ship.status == 1  # Active
                ).first()
                
                if ship:
                    current_sector = get_sector(Coordinate(ship.x_coord, ship.y_coord))
                    
                    players.append({
                        "user_id": user.id,
                        "username": user.username,
                        "ship_name": ship.shipname,
                        "sector": {
                            "x": current_sector.x,
                            "y": current_sector.y
                        },
                        "ship_class": ship.shpclass,
                        "status": "online"  # This would need actual online status tracking
                    })
            
            return players
            
        except Exception as e:
            logger.error(f"Error getting online players: {e}")
            return []
    
    def _calculate_ship_cost(self, class_number: int) -> int:
        """Calculate ship cost based on class number"""
        # Base costs for different ship classes
        ship_costs = {
            1: 50000,    # Interceptor
            2: 100000,   # Light Freighter
            3: 200000,   # Heavy Freighter
            4: 500000,   # Destroyer
            5: 1000000,  # Star Cruiser
            6: 2000000,  # Battle Cruiser
            7: 5000000,  # Frigate
            8: 10000000, # Dreadnought
            9: 20000000, # Flagship
            10: 1500000, # Cyborg
            11: 3000000  # Droid
        }
        return ship_costs.get(class_number, 1000000)
    
    def _calculate_shield_cost(self, class_number: int) -> int:
        """Calculate shield cost based on class number"""
        return class_number * 50000
    
    def _calculate_phaser_cost(self, class_number: int) -> int:
        """Calculate phaser cost based on class number"""
        return class_number * 75000
    
    def _get_ship_class_name(self, class_number: int) -> str:
        """Get ship class name based on class number"""
        ship_names = {
            1: "Interceptor",
            2: "Light Freighter",
            3: "Heavy Freighter",
            4: "Destroyer",
            5: "Star Cruiser",
            6: "Battle Cruiser",
            7: "Frigate",
            8: "Dreadnought",
            9: "Flagship",
            10: "Cybertron",
            11: "Droid"
        }
        return ship_names.get(class_number, "Unknown")
    
    def _get_shield_capacity(self, class_number: int) -> int:
        """Get shield capacity based on class number"""
        return class_number * 100
    
    def _get_phaser_capacity(self, class_number: int) -> int:
        """Get phaser capacity based on class number"""
        return class_number * 50
    
    def _update_ship_capabilities(self, ship: Ship, class_number: int):
        """Update ship capabilities based on new class"""
        # This would need to be implemented based on ship class definitions
        pass
    
    def _get_item_base_price(self, item_type: str) -> int:
        """Get base price for item type"""
        prices = {
            "men": 2,
            "tro": 1,
            "mis": 20,
            "tor": 7,
            "ion": 33,
            "flu": 200,
            "foo": 2,
            "fig": 50,
            "dec": 18,
            "min": 50,
            "jam": 50,
            "zip": 50,
            "gol": 100
        }
        return prices.get(item_type, 10)
