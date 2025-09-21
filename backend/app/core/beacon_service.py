"""
Galactic Empire - Beacon Service

This module handles beacon deployment, messaging, and communication operations
including beacon management, message broadcasting, and sector communication.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import math

from ..models.beacon import Beacon, BeaconConstants
from ..models.user import User
from ..core.coordinates import calculate_distance, calculate_bearing


class BeaconService:
    """Service for beacon operations"""
    
    def __init__(self):
        self.beacon_range = 5000  # Range for beacon detection
        self.max_message_length = BeaconConstants.BEACONMSGSZ  # 75 characters
        self.beacon_types = {
            0: "General",      # General communication
            1: "Distress",     # Distress call
            2: "Trade",        # Trading beacon
            3: "Navigation",   # Navigation aid
            4: "Warning",      # Warning beacon
            5: "Team",         # Team communication
            6: "Alliance",     # Alliance communication
            7: "Spy",          # Spy communication
            8: "Military",     # Military coordination
            9: "Emergency"     # Emergency broadcast
        }
    
    def deploy_beacon(self, db: Session, user_id: int, x_coord: float, y_coord: float, 
                     message: str, beacon_type: int = 0, priority: int = 0, 
                     is_public: bool = True, expires_hours: int = None) -> Dict[str, Any]:
        """
        Deploy a beacon at specified coordinates
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate message length
        if len(message) > self.max_message_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message too long. Maximum {self.max_message_length} characters."
            )
        
        # Validate beacon type
        if beacon_type not in self.beacon_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid beacon type. Valid types: {list(self.beacon_types.keys())}"
            )
        
        # Check for existing beacon at same location (within 100 units)
        existing_beacon = db.query(Beacon).filter(
            Beacon.is_active == True,
            Beacon.x_coord.between(x_coord - 100, x_coord + 100),
            Beacon.y_coord.between(y_coord - 100, y_coord + 100)
        ).first()
        
        if existing_beacon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Beacon already exists at this location"
            )
        
        # Calculate expiration time
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Create beacon
        beacon = Beacon(
            x_coord=x_coord,
            y_coord=y_coord,
            plnum=0,  # Not planet-based
            beacon_message=message,
            owner_id=user_id,
            is_active=True,
            is_public=is_public,
            beacon_type=beacon_type,
            priority=priority,
            expires_at=expires_at
        )
        
        db.add(beacon)
        db.commit()
        db.refresh(beacon)
        
        return {
            "id": beacon.id,
            "x_coord": beacon.x_coord,
            "y_coord": beacon.y_coord,
            "message": beacon.beacon_message,
            "beacon_type": beacon.beacon_type,
            "beacon_type_name": self.beacon_types[beacon.beacon_type],
            "priority": beacon.priority,
            "is_public": beacon.is_public,
            "expires_at": beacon.expires_at.isoformat() if beacon.expires_at else None,
            "created_at": beacon.created_at.isoformat(),
            "owner": user.userid
        }
    
    def find_beacons_in_range(self, db: Session, x_coord: float, y_coord: float, 
                            range_limit: float = None, beacon_type: int = None) -> List[Dict[str, Any]]:
        """Find beacons within range of a position"""
        if range_limit is None:
            range_limit = self.beacon_range
        
        # Build query
        query = db.query(Beacon).filter(
            Beacon.is_active == True,
            Beacon.expires_at.isnot(None) | (Beacon.expires_at > datetime.utcnow())
        )
        
        # Filter by beacon type if specified
        if beacon_type is not None:
            query = query.filter(Beacon.beacon_type == beacon_type)
        
        beacons = query.all()
        
        # Filter by distance and calculate bearing
        nearby_beacons = []
        for beacon in beacons:
            distance = calculate_distance(x_coord, y_coord, beacon.x_coord, beacon.y_coord)
            if distance <= range_limit:
                nearby_beacons.append({
                    "id": beacon.id,
                    "x_coord": beacon.x_coord,
                    "y_coord": beacon.y_coord,
                    "message": beacon.beacon_message,
                    "beacon_type": beacon.beacon_type,
                    "beacon_type_name": self.beacon_types[beacon.beacon_type],
                    "priority": beacon.priority,
                    "is_public": beacon.is_public,
                    "distance": distance,
                    "bearing": calculate_bearing(x_coord, y_coord, beacon.x_coord, beacon.y_coord),
                    "created_at": beacon.created_at.isoformat(),
                    "expires_at": beacon.expires_at.isoformat() if beacon.expires_at else None,
                    "owner": beacon.owner.userid if beacon.owner else "Unknown"
                })
        
        # Sort by priority (higher first) then by distance
        nearby_beacons.sort(key=lambda x: (-x["priority"], x["distance"]))
        
        return nearby_beacons
    
    def get_beacon_message(self, db: Session, x_coord: float, y_coord: float) -> Dict[str, Any]:
        """Get beacon message at specific coordinates"""
        # Find beacon at exact coordinates (within 50 units)
        beacon = db.query(Beacon).filter(
            Beacon.is_active == True,
            Beacon.x_coord.between(x_coord - 50, x_coord + 50),
            Beacon.y_coord.between(y_coord - 50, y_coord + 50),
            Beacon.expires_at.isnot(None) | (Beacon.expires_at > datetime.utcnow())
        ).first()
        
        if not beacon:
            return {
                "found": False,
                "message": "No beacon found at this location"
            }
        
        return {
            "found": True,
            "id": beacon.id,
            "message": beacon.beacon_message,
            "beacon_type": beacon.beacon_type,
            "beacon_type_name": self.beacon_types[beacon.beacon_type],
            "priority": beacon.priority,
            "is_public": beacon.is_public,
            "created_at": beacon.created_at.isoformat(),
            "expires_at": beacon.expires_at.isoformat() if beacon.expires_at else None,
            "owner": beacon.owner.userid if beacon.owner else "Unknown"
        }
    
    def update_beacon_message(self, db: Session, beacon_id: int, user_id: int, 
                            new_message: str) -> Dict[str, Any]:
        """Update beacon message (owner only)"""
        beacon = db.query(Beacon).filter(
            Beacon.id == beacon_id,
            Beacon.owner_id == user_id,
            Beacon.is_active == True
        ).first()
        
        if not beacon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beacon not found or you don't own it"
            )
        
        # Validate message length
        if len(new_message) > self.max_message_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message too long. Maximum {self.max_message_length} characters."
            )
        
        old_message = beacon.beacon_message
        beacon.beacon_message = new_message
        db.commit()
        
        return {
            "message": "Beacon message updated successfully",
            "beacon_id": beacon.id,
            "old_message": old_message,
            "new_message": new_message,
            "updated_at": beacon.updated_at.isoformat()
        }
    
    def remove_beacon(self, db: Session, beacon_id: int, user_id: int) -> Dict[str, Any]:
        """Remove a beacon (owner only)"""
        beacon = db.query(Beacon).filter(
            Beacon.id == beacon_id,
            Beacon.owner_id == user_id,
            Beacon.is_active == True
        ).first()
        
        if not beacon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beacon not found or you don't own it"
            )
        
        beacon.is_active = False
        db.commit()
        
        return {
            "message": "Beacon removed successfully",
            "beacon_id": beacon.id,
            "location": {
                "x_coord": beacon.x_coord,
                "y_coord": beacon.y_coord
            }
        }
    
    def get_user_beacons(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all beacons owned by a user"""
        beacons = db.query(Beacon).filter(
            Beacon.owner_id == user_id,
            Beacon.is_active == True
        ).order_by(Beacon.created_at.desc()).all()
        
        return [
            {
                "id": beacon.id,
                "x_coord": beacon.x_coord,
                "y_coord": beacon.y_coord,
                "message": beacon.beacon_message,
                "beacon_type": beacon.beacon_type,
                "beacon_type_name": self.beacon_types[beacon.beacon_type],
                "priority": beacon.priority,
                "is_public": beacon.is_public,
                "created_at": beacon.created_at.isoformat(),
                "expires_at": beacon.expires_at.isoformat() if beacon.expires_at else None,
                "is_expired": beacon.expires_at and beacon.expires_at < datetime.utcnow()
            }
            for beacon in beacons
        ]
    
    def broadcast_message(self, db: Session, user_id: int, message: str, 
                         beacon_type: int = 0, priority: int = 5) -> Dict[str, Any]:
        """Broadcast a message to all nearby beacons (team/alliance communication)"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user's current position (from their ship)
        # This would need to be integrated with ship position system
        # For now, we'll use a placeholder
        
        # Validate message
        if len(message) > self.max_message_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message too long. Maximum {self.max_message_length} characters."
            )
        
        # Find nearby beacons within broadcast range
        # This would need ship position integration
        # For now, return a placeholder response
        
        return {
            "message": "Message broadcast initiated",
            "broadcast_type": self.beacon_types[beacon_type],
            "priority": priority,
            "message_preview": message[:50] + "..." if len(message) > 50 else message,
            "note": "Beacon system requires ship position integration"
        }
    
    def get_beacon_statistics(self, db: Session) -> Dict[str, Any]:
        """Get beacon system statistics"""
        total_beacons = db.query(Beacon).filter(Beacon.is_active == True).count()
        expired_beacons = db.query(Beacon).filter(
            Beacon.is_active == True,
            Beacon.expires_at < datetime.utcnow()
        ).count()
        
        # Count by type
        type_counts = {}
        for beacon_type, type_name in self.beacon_types.items():
            count = db.query(Beacon).filter(
                Beacon.beacon_type == beacon_type,
                Beacon.is_active == True
            ).count()
            type_counts[type_name] = count
        
        # Recent beacons (last 24 hours)
        recent_beacons = db.query(Beacon).filter(
            Beacon.is_active == True,
            Beacon.created_at > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return {
            "total_active_beacons": total_beacons,
            "expired_beacons": expired_beacons,
            "recent_beacons_24h": recent_beacons,
            "beacons_by_type": type_counts,
            "max_message_length": self.max_message_length,
            "beacon_range": self.beacon_range
        }
    
    def cleanup_expired_beacons(self, db: Session) -> Dict[str, Any]:
        """Remove expired beacons"""
        expired_beacons = db.query(Beacon).filter(
            Beacon.is_active == True,
            Beacon.expires_at < datetime.utcnow()
        ).all()
        
        count = 0
        for beacon in expired_beacons:
            beacon.is_active = False
            count += 1
        
        db.commit()
        
        return {
            "message": f"Cleaned up {count} expired beacons",
            "expired_count": count
        }


# Global beacon service instance
beacon_service = BeaconService()
