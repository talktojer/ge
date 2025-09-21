"""
Galactic Empire - Planetary Service

This service integrates planetary systems with the database and provides
comprehensive planet management functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from ..models.planet import Planet, PlanetItem, Sector
from ..models.item import Item, ItemType
from ..models.user import User
from .planetary_systems import (
    PlanetManagement, PlanetStats, ProductionResult, ColonizationResult,
    EnvironmentType, ResourceType, PlanetStatus
)
from .coordinates import Coordinate, distance

logger = logging.getLogger(__name__)


class PlanetaryService:
    """Main service for planetary operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.planet_management = PlanetManagement()
    
    def get_planet_by_id(self, planet_id: int) -> Optional[Planet]:
        """Get planet by ID"""
        return self.db.query(Planet).filter(Planet.id == planet_id).first()
    
    def get_planets_in_sector(self, xsect: int, ysect: int) -> List[Planet]:
        """Get all planets in a sector"""
        return self.db.query(Planet).filter(
            and_(Planet.xsect == xsect, Planet.ysect == ysect)
        ).all()
    
    def get_user_planets(self, user_id: int) -> List[Planet]:
        """Get all planets owned by a user"""
        return self.db.query(Planet).filter(Planet.owner_id == user_id).all()
    
    def get_uncolonized_planets(self, limit: int = 100) -> List[Planet]:
        """Get uncolonized planets available for colonization"""
        return self.db.query(Planet).filter(
            Planet.owner_id.is_(None)
        ).limit(limit).all()
    
    def get_planets_near_position(self, x: float, y: float, 
                                max_distance: float = 100000.0) -> List[Tuple[Planet, float]]:
        """Get planets near a position with their distances"""
        try:
            all_planets = self.db.query(Planet).all()
            nearby_planets = []
            
            position = Coordinate(x, y)
            
            for planet in all_planets:
                planet_pos = Coordinate(planet.x_coord, planet.y_coord)
                dist = distance(position, planet_pos)
                
                if dist <= max_distance:
                    nearby_planets.append((planet, dist))
            
            # Sort by distance
            nearby_planets.sort(key=lambda x: x[1])
            
            return nearby_planets
            
        except Exception as e:
            logger.error(f"Error getting planets near position: {e}")
            return []
    
    def get_planet_items(self, planet_id: int) -> List[PlanetItem]:
        """Get all items for a planet"""
        return self.db.query(PlanetItem).filter(
            PlanetItem.planet_id == planet_id
        ).all()
    
    def get_planet_item(self, planet_id: int, item_type_id: int) -> Optional[PlanetItem]:
        """Get specific item for a planet"""
        return self.db.query(PlanetItem).filter(
            and_(
                PlanetItem.planet_id == planet_id,
                PlanetItem.item_id == item_type_id
            )
        ).first()
    
    def colonize_planet(self, planet_id: int, user_id: int, 
                       population_to_send: int) -> Dict[str, Any]:
        """Colonize a planet"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet:
                return {"success": False, "message": "Planet not found"}
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Use planet management system to validate colonization
            result = self.planet_management.colonize_planet(planet, user, population_to_send)
            
            if result.success:
                # Update database
                planet.owner_id = user_id
                planet.userid = user.userid
                
                # Deduct cost and population from user
                user.cash -= result.cost
                user.population -= result.population_sent
                
                # Initialize planet with starting population
                # Note: In a full implementation, we'd track planet population separately
                # For now, we'll use the user's population system
                
                # Set default tax rate
                planet.tax_rate = 10  # 10% default tax rate
                
                self.db.commit()
                
                return {
                    "success": True,
                    "message": result.message,
                    "cost": result.cost,
                    "population_sent": result.population_sent,
                    "planet_id": planet_id
                }
            else:
                return {
                    "success": False,
                    "message": result.message,
                    "cost": result.cost
                }
                
        except Exception as e:
            logger.error(f"Error colonizing planet: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Colonization error: {str(e)}"}
    
    def set_tax_rate(self, planet_id: int, user_id: int, new_tax_rate: int) -> Dict[str, Any]:
        """Set planet tax rate"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet:
                return {"success": False, "message": "Planet not found"}
            
            if planet.owner_id != user_id:
                return {"success": False, "message": "You don't own this planet"}
            
            # Validate tax rate
            result = self.planet_management.set_tax_rate(planet, new_tax_rate)
            
            if result["success"]:
                # Update database
                planet.tax_rate = new_tax_rate
                self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting tax rate: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Tax rate error: {str(e)}"}
    
    def set_beacon_message(self, planet_id: int, user_id: int, message: str) -> Dict[str, Any]:
        """Set planet beacon message"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet:
                return {"success": False, "message": "Planet not found"}
            
            if planet.owner_id != user_id:
                return {"success": False, "message": "You don't own this planet"}
            
            # Validate message
            result = self.planet_management.set_beacon_message(planet, message)
            
            if result["success"]:
                # Update database
                planet.beacon_message = message
                self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting beacon message: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Beacon message error: {str(e)}"}
    
    def set_item_production(self, planet_id: int, user_id: int, 
                           item_type_id: int, production_rate: int) -> Dict[str, Any]:
        """Set item production rate for a planet"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet:
                return {"success": False, "message": "Planet not found"}
            
            if planet.owner_id != user_id:
                return {"success": False, "message": "You don't own this planet"}
            
            if production_rate < 0 or production_rate > 100:
                return {"success": False, "message": "Production rate must be between 0 and 100"}
            
            # Get or create planet item
            planet_item = self.get_planet_item(planet_id, item_type_id)
            if not planet_item:
                planet_item = PlanetItem(
                    planet_id=planet_id,
                    item_id=item_type_id,
                    quantity=0,
                    rate=production_rate
                )
                self.db.add(planet_item)
            else:
                planet_item.rate = production_rate
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Production rate set to {production_rate}",
                "item_type_id": item_type_id,
                "production_rate": production_rate
            }
            
        except Exception as e:
            logger.error(f"Error setting item production: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Production error: {str(e)}"}
    
    def trade_items(self, planet_id: int, user_id: int, item_type_id: int,
                   action: str, quantity: int) -> Dict[str, Any]:
        """Trade items with a planet"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet:
                return {"success": False, "message": "Planet not found"}
            
            # Get item type for pricing
            item_type = self.db.query(ItemType).filter(ItemType.id == item_type_id).first()
            if not item_type:
                return {"success": False, "message": "Item type not found"}
            
            # Get planet item inventory
            planet_item = self.get_planet_item(planet_id, item_type_id)
            if not planet_item:
                planet_item = PlanetItem(
                    planet_id=planet_id,
                    item_id=item_type_id,
                    quantity=0
                )
                self.db.add(planet_item)
            
            # Calculate prices
            prices = self.planet_management.economy.calculate_item_prices(
                planet, item_type_id, item_type.base_price, planet_item.quantity
            )
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            if action == "buy":
                # User buys from planet
                total_cost = prices["sell_price"] * quantity
                
                if user.cash < total_cost:
                    return {"success": False, "message": "Insufficient funds"}
                
                if planet_item.quantity < quantity:
                    return {"success": False, "message": "Insufficient items available"}
                
                # Execute transaction
                user.cash -= total_cost
                planet.cash += total_cost
                planet_item.quantity -= quantity
                
                # TODO: Add items to user inventory
                
                message = f"Bought {quantity} {item_type.name} for {total_cost} credits"
                
            elif action == "sell":
                # User sells to planet
                total_payment = prices["buy_price"] * quantity
                
                # TODO: Check user inventory for items
                # For now, assume user has the items
                
                if planet.cash < total_payment:
                    return {"success": False, "message": "Planet has insufficient funds"}
                
                # Execute transaction
                user.cash += total_payment
                planet.cash -= total_payment
                planet_item.quantity += quantity
                
                # TODO: Remove items from user inventory
                
                message = f"Sold {quantity} {item_type.name} for {total_payment} credits"
                
            else:
                return {"success": False, "message": "Invalid action. Use 'buy' or 'sell'"}
            
            self.db.commit()
            
            return {
                "success": True,
                "message": message,
                "quantity": quantity,
                "unit_price": prices["sell_price"] if action == "buy" else prices["buy_price"],
                "total_amount": total_cost if action == "buy" else total_payment,
                "user_cash": user.cash,
                "planet_cash": planet.cash
            }
            
        except Exception as e:
            logger.error(f"Error in item trading: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Trading error: {str(e)}"}
    
    def get_planet_status(self, planet_id: int) -> Dict[str, Any]:
        """Get comprehensive planet status"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet:
                return {"success": False, "message": "Planet not found"}
            
            # Get planet items
            planet_items = self.get_planet_items(planet_id)
            
            # Calculate population (placeholder - would be tracked separately in full implementation)
            population = 10000 if planet.owner_id else 0
            
            # Get planet stats
            stats = self.planet_management.get_planet_status(planet, population)
            
            # Get item inventory
            item_inventory = []
            for planet_item in planet_items:
                item_type = self.db.query(ItemType).filter(ItemType.id == planet_item.item_id).first()
                if item_type:
                    prices = self.planet_management.economy.calculate_item_prices(
                        planet, planet_item.item_id, item_type.base_price, planet_item.quantity
                    )
                    
                    item_inventory.append({
                        "item_id": planet_item.item_id,
                        "item_name": item_type.name,
                        "quantity": planet_item.quantity,
                        "production_rate": planet_item.rate,
                        "buy_price": prices["buy_price"],
                        "sell_price": prices["sell_price"],
                        "sell_to_allies": planet_item.sell_to_allies,
                        "reserve": planet_item.reserve
                    })
            
            return {
                "success": True,
                "planet_info": {
                    "id": stats.planet_id,
                    "name": stats.name,
                    "owner_id": stats.owner_id,
                    "position": stats.position,
                    "sector": stats.sector,
                    "environment": stats.environment.name,
                    "resource": stats.resource.name,
                    "beacon_message": stats.beacon_message
                },
                "economics": {
                    "population": stats.population,
                    "cash": stats.cash,
                    "debt": stats.debt,
                    "tax_rate": stats.tax_rate,
                    "tax_collected": stats.tax_collected,
                    "technology_level": stats.technology_level
                },
                "inventory": item_inventory,
                "last_attack": stats.last_attack.isoformat() if stats.last_attack else None
            }
            
        except Exception as e:
            logger.error(f"Error getting planet status: {e}")
            return {"success": False, "message": f"Status error: {str(e)}"}
    
    def process_planet_tick(self, planet_id: int) -> Dict[str, Any]:
        """Process planet systems for one tick"""
        try:
            planet = self.get_planet_by_id(planet_id)
            if not planet or not planet.owner_id:
                return {"success": False, "message": "Planet not found or uncolonized"}
            
            # Get planet items
            planet_items = self.get_planet_items(planet_id)
            
            # Calculate population (placeholder)
            population = 10000
            
            # Process production
            production_result = self.planet_management.process_planet_tick(
                planet, planet_items, population
            )
            
            # Update planet items with production
            for item_type_id, quantity_produced in production_result.items_produced.items():
                planet_item = self.get_planet_item(planet_id, item_type_id)
                if planet_item:
                    planet_item.quantity += quantity_produced
            
            # Update planet finances
            planet.cash += production_result.cash_generated
            planet.tax += production_result.tax_collected
            
            self.db.commit()
            
            return {
                "success": True,
                "planet_id": planet_id,
                "items_produced": production_result.items_produced,
                "population_change": production_result.population_change,
                "cash_generated": production_result.cash_generated,
                "tax_collected": production_result.tax_collected,
                "production_value": production_result.total_production_value
            }
            
        except Exception as e:
            logger.error(f"Error processing planet tick: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Tick processing error: {str(e)}"}
    
    def get_sector_info(self, xsect: int, ysect: int) -> Dict[str, Any]:
        """Get information about a sector"""
        try:
            # Get sector
            sector = self.db.query(Sector).filter(
                and_(Sector.xsect == xsect, Sector.ysect == ysect)
            ).first()
            
            # Get planets in sector
            planets = self.get_planets_in_sector(xsect, ysect)
            
            planet_info = []
            for planet in planets:
                planet_info.append({
                    "id": planet.id,
                    "name": planet.name,
                    "owner": planet.userid,
                    "position": (planet.x_coord, planet.y_coord),
                    "environment": EnvironmentType(planet.environment).name,
                    "resource": ResourceType(planet.resource).name,
                    "beacon_message": planet.beacon_message[:20] + "..." if len(planet.beacon_message) > 20 else planet.beacon_message
                })
            
            return {
                "success": True,
                "sector": {
                    "coordinates": (xsect, ysect),
                    "type": sector.type if sector else 1,
                    "num_planets": len(planets)
                },
                "planets": planet_info
            }
            
        except Exception as e:
            logger.error(f"Error getting sector info: {e}")
            return {"success": False, "message": f"Sector error: {str(e)}"}
    
    def search_planets(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search planets by name or owner"""
        try:
            planets = self.db.query(Planet).filter(
                or_(
                    Planet.name.ilike(f"%{query}%"),
                    Planet.userid.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            results = []
            for planet in planets:
                results.append({
                    "id": planet.id,
                    "name": planet.name,
                    "owner": planet.userid,
                    "sector": (planet.xsect, planet.ysect),
                    "position": (planet.x_coord, planet.y_coord),
                    "environment": EnvironmentType(planet.environment).name,
                    "resource": ResourceType(planet.resource).name,
                    "is_colonized": planet.owner_id is not None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching planets: {e}")
            return []
