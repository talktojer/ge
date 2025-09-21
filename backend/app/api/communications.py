"""
Communication API endpoints for mail, distress calls, and messaging
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.communication_service import CommunicationService, MessageType
from ..models.user import User
from ..models.mail import Mail, MailClass

router = APIRouter(prefix="/api/communications", tags=["communications"])

# ================== REQUEST/RESPONSE MODELS ==================

class MailResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    sender_name: str
    topic: str
    content: str
    is_read: bool
    created_at: str
    mail_type: int
    
    class Config:
        from_attributes = True

class SendMailRequest(BaseModel):
    recipient_id: int
    topic: str
    message: str

class DistressCallRequest(BaseModel):
    distress_type: int
    planet_name: Optional[str] = None
    attacker_name: Optional[str] = None
    ship_name: Optional[str] = None
    sector_x: Optional[int] = None
    sector_y: Optional[int] = None
    troop_count: Optional[int] = None

class TeamMessageRequest(BaseModel):
    message: str

class ScanRequest(BaseModel):
    scan_type: str  # 'ships', 'planets', 'sector'
    scan_range: Optional[int] = None

class ScanResult(BaseModel):
    scan_type: str
    results: List[Dict[str, Any]]

class UserStatsResponse(BaseModel):
    user_id: int
    userid: str
    score: int
    kills: int
    cash: int
    population: int
    team: Optional[str]
    ship_count: int
    planet_count: int
    total_population: int
    total_troops: int

class GameStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_ships: int
    total_planets: int
    total_teams: int
    top_players: List[Dict[str, Any]]
    top_teams: List[Dict[str, Any]]

# ================== MAIL ENDPOINTS ==================

@router.get("/mail", response_model=List[MailResponse])
async def get_mail(
    include_read: bool = True,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all mail for the current user"""
    try:
        comm_service = CommunicationService(db)
        mail_list = comm_service.get_user_mail(
            current_user.id, 
            include_read=include_read,
            include_deleted=include_deleted
        )
        
        return [
            MailResponse(
                id=mail.id,
                sender_id=mail.sender_id,
                recipient_id=mail.recipient_id,
                sender_name=mail.sender.userid if mail.sender else "System",
                topic=mail.topic,
                content=_format_mail_content(mail),
                is_read=mail.is_read,
                created_at=mail.created_at.isoformat(),
                mail_type=mail.type
            )
            for mail in mail_list
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving mail: {str(e)}"
        )

@router.post("/mail/send")
async def send_mail(
    request: SendMailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a mail message to another player"""
    try:
        comm_service = CommunicationService(db)
        
        content_data = {
            'string1': request.message,
            'name1': current_user.userid
        }
        
        mail = comm_service.send_mail(
            sender_id=current_user.id,
            recipient_id=request.recipient_id,
            mail_class=MailClass.PLSTATS,  # General message class
            mail_type=0,  # User message
            topic=request.topic,
            content_data=content_data
        )
        
        return {"message": "Mail sent successfully", "mail_id": mail.id}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending mail: {str(e)}"
        )

@router.post("/mail/{mail_id}/read")
async def mark_mail_read(
    mail_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a mail message as read"""
    try:
        comm_service = CommunicationService(db)
        success = comm_service.mark_mail_read(mail_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mail not found or not accessible"
            )
            
        return {"message": "Mail marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking mail as read: {str(e)}"
        )

@router.delete("/mail/{mail_id}")
async def delete_mail(
    mail_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a mail message"""
    try:
        comm_service = CommunicationService(db)
        success = comm_service.delete_mail(mail_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mail not found or not accessible"
            )
            
        return {"message": "Mail deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting mail: {str(e)}"
        )

# ================== DISTRESS CALL ENDPOINTS ==================

@router.post("/distress")
async def send_distress_call(
    request: DistressCallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a distress call to team members"""
    try:
        comm_service = CommunicationService(db)
        
        location_data = {
            'planet_name': request.planet_name or '',
            'attacker_name': request.attacker_name or '',
            'ship_name': request.ship_name or '',
            'sector_x': request.sector_x or 0,
            'sector_y': request.sector_y or 0,
            'troop_count': request.troop_count or 0
        }
        
        sent_messages = comm_service.send_distress_call(
            current_user.id,
            request.distress_type,
            location_data
        )
        
        return {
            "message": f"Distress call sent to {len(sent_messages)} team members",
            "recipients": len(sent_messages)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending distress call: {str(e)}"
        )

# ================== TEAM COMMUNICATION ENDPOINTS ==================

@router.post("/team/message")
async def send_team_message(
    request: TeamMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to all team members"""
    try:
        comm_service = CommunicationService(db)
        sent_messages = comm_service.send_team_message(current_user.id, request.message)
        
        return {
            "message": f"Message sent to {len(sent_messages)} team members",
            "recipients": len(sent_messages)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending team message: {str(e)}"
        )

# ================== SCANNING ENDPOINTS ==================

@router.post("/scan", response_model=ScanResult)
async def perform_scan(
    request: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform various types of scans using enhanced scanning service"""
    try:
        from ..core.scanning_service import ScanningService
        from ..core.battle_interface import ScannerType
        
        # Get user's current ship
        from ..models.ship import Ship
        ship = db.query(Ship).filter(
            Ship.owner_id == current_user.id,
            Ship.is_active == True
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active ship found"
            )
        
        scanning_service = ScanningService(db)
        results = []
        
        if request.scan_type == "ships":
            scanner_type = ScannerType.LONG_RANGE  # Default
            if request.scan_range:
                if request.scan_range <= 50000:
                    scanner_type = ScannerType.SHORT_RANGE
                elif request.scan_range <= 100000:
                    scanner_type = ScannerType.TACTICAL
                elif request.scan_range > 200000:
                    scanner_type = ScannerType.HYPERSPACE
            
            results = scanning_service.scan_ships_detailed(ship.id, scanner_type)
            
        elif request.scan_type == "planets":
            results = scanning_service.scan_planets_detailed(ship.id)
            
        elif request.scan_type == "sector":
            results = scanning_service.scan_sector_comprehensive(ship.id)
            
        elif request.scan_type == "hyperspace":
            results = scanning_service.scan_hyperspace(ship.id)
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid scan type. Use 'ships', 'planets', 'sector', or 'hyperspace'"
            )
            
        return ScanResult(
            scan_type=request.scan_type,
            results=results if isinstance(results, list) else [results]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing scan: {str(e)}"
        )

@router.get("/scan/tactical/{ship_id}")
async def get_tactical_display(
    ship_id: int,
    display_mode: str = "combat",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tactical display for specified ship"""
    try:
        from ..core.scanning_service import ScanningService
        from ..models.ship import Ship
        
        # Verify ship ownership
        ship = db.query(Ship).filter(
            Ship.id == ship_id,
            Ship.owner_id == current_user.id
        ).first()
        
        if not ship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ship not found or not owned by user"
            )
        
        scanning_service = ScanningService(db)
        
        if display_mode == "sector":
            tactical_data = scanning_service.scan_sector_comprehensive(ship_id)
        else:
            # Default to detailed ship and planet scans
            ships = scanning_service.scan_ships_detailed(ship_id)
            planets = scanning_service.scan_planets_detailed(ship_id)
            tactical_data = {
                'display_mode': display_mode,
                'ship_position': {
                    'x': ship.coord_x,
                    'y': ship.coord_y,
                    'sector_x': ship.sector_x,
                    'sector_y': ship.sector_y
                },
                'objects': {
                    'ships': ships,
                    'planets': planets
                },
                'scan_time': datetime.utcnow().isoformat()
            }
        
        return tactical_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tactical display: {str(e)}"
        )

# ================== REPORTING ENDPOINTS ==================

@router.get("/stats/user", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics (own stats or another user's if specified)"""
    try:
        comm_service = CommunicationService(db)
        target_user_id = user_id or current_user.id
        
        stats = comm_service.get_user_statistics(target_user_id)
        
        return UserStatsResponse(**stats)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user statistics: {str(e)}"
        )

@router.get("/stats/team")
async def get_team_roster(
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team roster and statistics"""
    try:
        comm_service = CommunicationService(db)
        target_team_id = team_id or current_user.team_id
        
        if not target_team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No team specified and user is not in a team"
            )
            
        roster = comm_service.get_team_roster(target_team_id)
        
        return {
            "team_id": target_team_id,
            "member_count": len(roster),
            "members": roster
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving team roster: {str(e)}"
        )

@router.get("/stats/game", response_model=GameStatsResponse)
async def get_game_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get game-wide statistics"""
    try:
        comm_service = CommunicationService(db)
        stats = comm_service.get_game_statistics()
        
        return GameStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving game statistics: {str(e)}"
        )

# ================== HELPER FUNCTIONS ==================

def _format_mail_content(mail: Mail) -> str:
    """Format mail content based on mail type"""
    if mail.type == MessageType.MESG02:
        return f"Distress message from {mail.name1} in Sector {mail.int1} {mail.int2}, they were attacked by Commander {mail.name2} in The {mail.string1} with {mail.long1} troops. They successfully defended the planet."
    
    elif mail.type == MessageType.MESG03:
        return f"Distress message from {mail.name1} in Sector {mail.int1} {mail.int2}, they were attacked by Commander {mail.name2} in The {mail.string1} with {mail.long1} troops. They have surrendered the planet."
    
    elif mail.type == MessageType.MESG04:
        return f"Distress message from {mail.name1} in Sector {mail.int1} {mail.int2}, they were attacked by Commander {mail.name2} in The {mail.string1} with {mail.long1} fighters. They successfully defended the planet."
    
    elif mail.type == MessageType.MESG05:
        return f"Distress message from {mail.name1} in Sector {mail.int1} {mail.int2}, they were attacked by Commander {mail.name2} in The {mail.string1} with {mail.long1} fighters. They have surrendered the planet."
    
    elif mail.type == MessageType.MESG06:
        return f"Distress message from {mail.name1} in Sector {mail.int1} {mail.int2}, The food supply is extremely low and {mail.long1} troops have starved to death."
    
    elif mail.type == MessageType.MESG07:
        return f"Distress message from {mail.name1} in Sector {mail.int1} {mail.int2}, The food supply is extremely low and {mail.long1} civilians have starved to death."
    
    elif mail.type == MessageType.MESG08:
        return f"Message from {mail.name1} in Sector {mail.int1} {mail.int2}, The population has reached the maximum sustainable on this planet. Implementing birth control procedures. Population now {mail.long1}."
    
    elif mail.type == MessageType.MESG20:
        return f"Production Report from {mail.name1} in Sector {mail.int1} {mail.int2}. See detailed financial information in mail status."
    
    elif mail.type == 0:  # User message
        return f"Message from {mail.name1}: {mail.string1}"
    
    else:
        return f"System message: {mail.string1 or mail.topic}"
