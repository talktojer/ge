"""
Galactic Empire - Spy Service

This module handles spy operations including spy deployment, intelligence gathering,
and spy management on planets.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import random

from ..models.user import User
from ..models.ship import Ship
from ..models.planet import Planet
from ..models.item import Item
from ..models.mail import Mail


class SpyService:
    """Service for spy operations"""
    
    def __init__(self):
        self.spy_catch_base_odds = 50  # Base odds for spy being caught
        self.spy_report_odds = 10  # 10% chance per tick of getting intelligence
        self.spy_disappear_odds = 5  # 5% chance per tick of spy disappearing
        self.spy_accuracy_base = 50  # Base accuracy of spy reports
        self.spy_accuracy_variance = 48  # Variance in spy accuracy
    
    def deploy_spy(self, db: Session, user_id: int, ship_id: int, planet_id: int) -> Dict[str, Any]:
        """
        Deploy a spy on an enemy planet
        """
        # Get user and ship
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        ship = db.query(Ship).filter(Ship.id == ship_id, Ship.owner_id == user_id).first()
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found"
            )
        
        # Get planet
        planet = db.query(Planet).filter(Planet.id == planet_id).first()
        if not planet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planet not found"
            )
        
        # Check if ship is in orbit (where < 10 means in space, >= 10 means orbiting planet)
        if ship.where < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship must be in orbit around a planet to deploy spy"
            )
        
        # Check if ship is orbiting the target planet
        planet_number = ship.where - 10  # Convert from ship position to planet number
        if planet_number != planet.plnum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship must be in orbit around the target planet"
            )
        
        # Check if user owns the planet (can't spy on own planet)
        if planet.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deploy spy on your own planet"
            )
        
        # Check if ship has spy items
        spy_item = db.query(Item).filter(
            Item.owner_id == user_id,
            Item.item_type_id == 12,  # I_SPY from original code
            Item.quantity > 0
        ).first()
        
        if not spy_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No spy units available on ship"
            )
        
        # Check if planet already has a spy
        if planet.spy_owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Planet already has a spy deployed"
            )
        
        # Deploy spy
        spy_item.quantity -= 1
        planet.spy_owner_id = user_id
        planet.spy_deployed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": f"Spy successfully deployed on planet {planet.name}",
            "planet_id": planet.id,
            "planet_name": planet.name,
            "spy_deployed_at": planet.spy_deployed_at.isoformat(),
            "spies_remaining": spy_item.quantity
        }
    
    def process_spy_activities(self, db: Session, planet_id: int) -> Dict[str, Any]:
        """
        Process spy activities on a planet (called during tick processing)
        Returns information about spy actions taken
        """
        planet = db.query(Planet).filter(Planet.id == planet_id).first()
        if not planet or not planet.spy_owner_id:
            return {"spy_actions": []}
        
        spy_actions = []
        
        # Check if spy gets caught
        if self._check_spy_caught(db, planet):
            spy_actions.append(self._handle_spy_caught(db, planet))
            return {"spy_actions": spy_actions}
        
        # Check if spy disappears
        if random.randint(1, 100) <= self.spy_disappear_odds:
            spy_actions.append(self._handle_spy_disappears(db, planet))
            return {"spy_actions": spy_actions}
        
        # Check if spy finds intelligence
        if random.randint(1, 100) <= self.spy_report_odds:
            spy_actions.append(self._generate_intelligence_report(db, planet))
        
        return {"spy_actions": spy_actions}
    
    def _check_spy_caught(self, db: Session, planet: Planet) -> bool:
        """Check if spy gets caught based on planet's spy count"""
        # Get planet's spy count (defensive spies)
        spy_count = db.query(Item).filter(
            Item.planet_id == planet.id,
            Item.item_type_id == 12,  # I_SPY
            Item.quantity > 0
        ).first()
        
        defensive_spies = spy_count.quantity if spy_count else 0
        
        if defensive_spies > 0:
            # Calculate odds: (50/spy_count) + 1
            odds = (self.spy_catch_base_odds // defensive_spies) + 1
            return random.randint(1, odds) == 1
        
        return False
    
    def _handle_spy_caught(self, db: Session, planet: Planet) -> Dict[str, Any]:
        """Handle spy being caught"""
        spy_owner = db.query(User).filter(User.id == planet.spy_owner_id).first()
        
        # Send mail to spy owner
        spy_owner_message = f"Your spy on planet {planet.name} in sector ({planet.xsect},{planet.ysect}) has been caught and executed!"
        
        spy_owner_mail = Mail(
            sender_id=None,  # System message
            recipient_id=planet.spy_owner_id,
            userid="SYSTEM",
            class_type=3,  # MAIL_CLASS_DISTRESS
            type=0,
            topic="** Official Protest **",
            string1=spy_owner_message,
            name1=planet.name,
            name2="",
            int1=planet.xsect,
            int2=planet.ysect,
            int3=0,
            is_read=False,
            is_deleted=False
        )
        
        # Send mail to planet owner
        planet_owner = db.query(User).filter(User.id == planet.owner_id).first()
        planet_owner_message = f"A spy belonging to {spy_owner.userid} has been caught and executed on planet {planet.name} in sector ({planet.xsect},{planet.ysect})!"
        
        planet_owner_mail = Mail(
            sender_id=None,  # System message
            recipient_id=planet.owner_id,
            userid="SYSTEM",
            class_type=3,  # MAIL_CLASS_DISTRESS
            type=0,
            topic="** Official Protest **",
            string1=planet_owner_message,
            name1=planet.name,
            name2=spy_owner.userid,
            int1=planet.xsect,
            int2=planet.ysect,
            int3=0,
            is_read=False,
            is_deleted=False
        )
        
        db.add(spy_owner_mail)
        db.add(planet_owner_mail)
        
        # Remove spy
        planet.spy_owner_id = None
        planet.spy_deployed_at = None
        
        db.commit()
        
        return {
            "action": "spy_caught",
            "message": f"Spy caught on planet {planet.name}",
            "spy_owner": spy_owner.userid,
            "planet_owner": planet_owner.userid,
            "planet_name": planet.name,
            "sector": f"({planet.xsect},{planet.ysect})"
        }
    
    def _handle_spy_disappears(self, db: Session, planet: Planet) -> Dict[str, Any]:
        """Handle spy disappearing mysteriously"""
        spy_owner = db.query(User).filter(User.id == planet.spy_owner_id).first()
        
        # Send mail to spy owner
        spy_owner_message = f"Your spy on planet {planet.name} in sector ({planet.xsect},{planet.ysect}) has disappeared without a trace. No further reports will be received."
        
        spy_owner_mail = Mail(
            sender_id=None,  # System message
            recipient_id=planet.spy_owner_id,
            userid="SYSTEM",
            class_type=2,  # MAIL_CLASS_INFO
            type=0,
            topic="Spy Report",
            string1=spy_owner_message,
            name1=planet.name,
            name2="",
            int1=planet.xsect,
            int2=planet.ysect,
            int3=0,
            is_read=False,
            is_deleted=False
        )
        
        db.add(spy_owner_mail)
        
        # Remove spy
        planet.spy_owner_id = None
        planet.spy_deployed_at = None
        
        db.commit()
        
        return {
            "action": "spy_disappeared",
            "message": f"Spy disappeared on planet {planet.name}",
            "spy_owner": spy_owner.userid,
            "planet_name": planet.name,
            "sector": f"({planet.xsect},{planet.ysect})"
        }
    
    def _generate_intelligence_report(self, db: Session, planet: Planet) -> Dict[str, Any]:
        """Generate an intelligence report from spy"""
        spy_owner = db.query(User).filter(User.id == planet.spy_owner_id).first()
        
        # Find an item to report on
        planet_items = db.query(Item).filter(
            Item.planet_id == planet.id,
            Item.quantity > 0
        ).all()
        
        if not planet_items:
            return {"action": "no_intelligence", "message": "No items found to report on"}
        
        # Pick a random item
        reported_item = random.choice(planet_items)
        actual_quantity = reported_item.quantity
        
        # Calculate spy accuracy (50% + random 0-48%)
        accuracy = self.spy_accuracy_base + random.randint(0, self.spy_accuracy_variance)
        accuracy_factor = (100 - accuracy) / 100.0
        
        # Calculate reported quantity with inaccuracy
        reported_quantity = int(actual_quantity * (1.0 + random.uniform(-accuracy_factor, accuracy_factor)))
        reported_quantity = max(0, reported_quantity)  # Can't report negative quantities
        
        # Create intelligence message
        intelligence_message = f"Intelligence Report from {planet.name}:\n"
        intelligence_message += f"Item: {reported_item.item_type.name}\n"
        intelligence_message += f"Reported Quantity: {reported_quantity}\n"
        intelligence_message += f"Accuracy: {accuracy}%\n"
        intelligence_message += f"Note: Intelligence may not be completely accurate."
        
        # Send mail to spy owner
        spy_mail = Mail(
            sender_id=None,  # System message
            recipient_id=planet.spy_owner_id,
            userid="SYSTEM",
            class_type=2,  # MAIL_CLASS_INFO
            type=0,
            topic="Intelligence Report",
            string1=intelligence_message,
            name1=planet.name,
            name2=reported_item.item_type.name,
            int1=planet.xsect,
            int2=planet.ysect,
            int3=reported_quantity,
            is_read=False,
            is_deleted=False
        )
        
        db.add(spy_mail)
        db.commit()
        
        return {
            "action": "intelligence_report",
            "message": f"Intelligence report generated for {planet.name}",
            "spy_owner": spy_owner.userid,
            "planet_name": planet.name,
            "reported_item": reported_item.item_type.name,
            "actual_quantity": actual_quantity,
            "reported_quantity": reported_quantity,
            "accuracy": accuracy
        }
    
    def get_spy_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get spy deployment status for a user"""
        # Get planets where user has spies deployed
        spy_planets = db.query(Planet).filter(
            Planet.spy_owner_id == user_id
        ).all()
        
        spy_deployments = []
        for planet in spy_planets:
            spy_deployments.append({
                "planet_id": planet.id,
                "planet_name": planet.name,
                "sector": f"({planet.xsect},{planet.ysect})",
                "planet_owner": planet.owner.userid if planet.owner else "Unknown",
                "deployed_at": planet.spy_deployed_at.isoformat() if planet.spy_deployed_at else None,
                "duration": (datetime.utcnow() - planet.spy_deployed_at).days if planet.spy_deployed_at else 0
            })
        
        # Get spy items available
        spy_items = db.query(Item).filter(
            Item.owner_id == user_id,
            Item.item_type_id == 12,  # I_SPY
            Item.quantity > 0
        ).first()
        
        available_spies = spy_items.quantity if spy_items else 0
        
        return {
            "active_spies": len(spy_deployments),
            "available_spies": available_spies,
            "spy_deployments": spy_deployments
        }
    
    def get_planet_spy_info(self, db: Session, planet_id: int, user_id: int) -> Dict[str, Any]:
        """Get spy information for a specific planet"""
        planet = db.query(Planet).filter(Planet.id == planet_id).first()
        if not planet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planet not found"
            )
        
        # Check if user has spy deployed
        has_spy = planet.spy_owner_id == user_id
        
        # Check if planet has defensive spies
        defensive_spies = db.query(Item).filter(
            Item.planet_id == planet_id,
            Item.item_type_id == 12,  # I_SPY
            Item.quantity > 0
        ).first()
        
        defensive_spy_count = defensive_spies.quantity if defensive_spies else 0
        
        result = {
            "planet_id": planet.id,
            "planet_name": planet.name,
            "has_spy_deployed": has_spy,
            "defensive_spy_count": defensive_spy_count,
            "spy_deployed_at": planet.spy_deployed_at.isoformat() if planet.spy_deployed_at else None
        }
        
        if has_spy:
            result["spy_duration"] = (datetime.utcnow() - planet.spy_deployed_at).days if planet.spy_deployed_at else 0
        
        return result
    
    def get_spy_statistics(self, db: Session) -> Dict[str, Any]:
        """Get spy system statistics"""
        total_active_spies = db.query(Planet).filter(Planet.spy_owner_id.isnot(None)).count()
        
        # Count spies by owner
        spy_owners = {}
        spy_planets = db.query(Planet).filter(Planet.spy_owner_id.isnot(None)).all()
        
        for planet in spy_planets:
            owner_id = planet.spy_owner_id
            if owner_id not in spy_owners:
                spy_owners[owner_id] = {
                    "user_id": owner_id,
                    "user_name": planet.spy_owner.userid if planet.spy_owner else "Unknown",
                    "spy_count": 0
                }
            spy_owners[owner_id]["spy_count"] += 1
        
        return {
            "total_active_spies": total_active_spies,
            "spy_owners": list(spy_owners.values()),
            "spy_catch_odds": self.spy_catch_base_odds,
            "spy_report_odds": self.spy_report_odds,
            "spy_disappear_odds": self.spy_disappear_odds
        }


# Global spy service instance
spy_service = SpyService()
