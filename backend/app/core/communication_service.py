"""
Communication service for mail, distress calls, and messaging systems
Based on original MAIL, MAILSTAT structures and message handling
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from ..models.mail import Mail, MailStatus, MailClass
from ..models.user import User
from ..models.ship import Ship
from ..models.planet import Planet
from ..models.team import Team
from ..core.coordinates import distance
from ..core.database import get_db
import logging

logger = logging.getLogger(__name__)

class MessageType:
    """Message type constants from original code"""
    # Distress messages
    MESG02 = 2   # Planet attacked with troops - defended
    MESG03 = 3   # Planet attacked with troops - surrendered  
    MESG04 = 4   # Planet attacked with fighters - defended
    MESG05 = 5   # Planet attacked with fighters - surrendered
    MESG06 = 6   # Food shortage - troops starved
    MESG07 = 7   # Food shortage - civilians starved
    
    # Status messages
    MESG08 = 8   # Population reached maximum
    MESG09 = 9   # Missile storage full
    MESG10 = 10  # Torpedo storage full
    MESG11 = 11  # Ion cannon storage full
    MESG12 = 12  # Fighter storage full
    MESG13 = 13  # Flux pod storage full
    MESG14 = 14  # Food storage full
    MESG15 = 15  # Ore storage full
    MESG16 = 16  # Colonist storage full
    MESG17 = 17  # Equipment storage full
    MESG18 = 18  # Fuel storage full
    MESG19 = 19  # Ship destroyed message
    MESG19A = 191 # Ship destroyed by planet
    MESG19B = 192 # Ship self-destructed
    MESG20 = 20  # Production report
    MESG30 = 30  # General status message

class CommunicationService:
    """Service for handling all communication systems"""
    
    def __init__(self, db: Session):
        self.db = db
        
    # ================== MAIL SYSTEM ==================
    
    def send_mail(self, sender_id: int, recipient_id: int, mail_class: int, 
                  mail_type: int, topic: str, content_data: Dict[str, Any]) -> Mail:
        """Send a mail message to another player"""
        try:
            # Get recipient info
            recipient = self.db.query(User).filter(User.id == recipient_id).first()
            if not recipient:
                raise ValueError(f"Recipient with id {recipient_id} not found")
                
            # Create mail record
            mail = Mail(
                sender_id=sender_id,
                recipient_id=recipient_id,
                userid=recipient.userid,
                class_type=mail_class,
                type=mail_type,
                topic=topic,
                dtime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                string1=content_data.get('string1', ''),
                name1=content_data.get('name1', ''),
                name2=content_data.get('name2', ''),
                int1=content_data.get('int1', 0),
                int2=content_data.get('int2', 0),
                int3=content_data.get('int3', 0),
                long1=content_data.get('long1', 0),
                long2=content_data.get('long2', 0),
                long3=content_data.get('long3', 0)
            )
            
            self.db.add(mail)
            self.db.commit()
            self.db.refresh(mail)
            
            logger.info(f"Mail sent from user {sender_id} to user {recipient_id}, topic: {topic}")
            return mail
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending mail: {str(e)}")
            raise
    
    def get_user_mail(self, user_id: int, include_read: bool = True, 
                      include_deleted: bool = False) -> List[Mail]:
        """Get all mail for a user"""
        query = self.db.query(Mail).filter(Mail.recipient_id == user_id)
        
        if not include_read:
            query = query.filter(Mail.is_read == False)
            
        if not include_deleted:
            query = query.filter(Mail.is_deleted == False)
            
        return query.order_by(desc(Mail.created_at)).all()
    
    def mark_mail_read(self, mail_id: int, user_id: int) -> bool:
        """Mark a mail message as read"""
        mail = self.db.query(Mail).filter(
            and_(Mail.id == mail_id, Mail.recipient_id == user_id)
        ).first()
        
        if mail:
            mail.is_read = True
            self.db.commit()
            return True
        return False
    
    def delete_mail(self, mail_id: int, user_id: int) -> bool:
        """Mark a mail message as deleted"""
        mail = self.db.query(Mail).filter(
            and_(Mail.id == mail_id, Mail.recipient_id == user_id)
        ).first()
        
        if mail:
            mail.is_deleted = True
            self.db.commit()
            return True
        return False
    
    # ================== DISTRESS CALLS ==================
    
    def send_distress_call(self, sender_id: int, distress_type: int, 
                          location_data: Dict[str, Any]) -> List[Mail]:
        """Send distress call to team members"""
        try:
            sender = self.db.query(User).filter(User.id == sender_id).first()
            if not sender or not sender.team_id:
                raise ValueError("Sender not found or not in a team")
                
            # Get team members
            team_members = self.db.query(User).filter(
                and_(User.team_id == sender.team_id, User.id != sender_id)
            ).all()
            
            sent_messages = []
            
            for member in team_members:
                content_data = {
                    'name1': location_data.get('planet_name', ''),
                    'name2': location_data.get('attacker_name', ''),
                    'string1': location_data.get('ship_name', ''),
                    'int1': location_data.get('sector_x', 0),
                    'int2': location_data.get('sector_y', 0),
                    'long1': location_data.get('troop_count', 0)
                }
                
                mail = self.send_mail(
                    sender_id=sender_id,
                    recipient_id=member.id,
                    mail_class=MailClass.DISTRESS,
                    mail_type=distress_type,
                    topic="Distress Message",
                    content_data=content_data
                )
                sent_messages.append(mail)
                
            logger.info(f"Distress call sent from user {sender_id} to {len(team_members)} team members")
            return sent_messages
            
        except Exception as e:
            logger.error(f"Error sending distress call: {str(e)}")
            raise
    
    def send_planet_attack_distress(self, planet_id: int, attacker_id: int, 
                                   attack_type: str, troops_or_fighters: int,
                                   defended: bool) -> List[Mail]:
        """Send distress call for planet attack"""
        planet = self.db.query(Planet).filter(Planet.id == planet_id).first()
        attacker = self.db.query(User).filter(User.id == attacker_id).first()
        
        if not planet or not attacker:
            raise ValueError("Planet or attacker not found")
            
        # Determine message type based on attack type and outcome
        if attack_type == "troops":
            distress_type = MessageType.MESG02 if defended else MessageType.MESG03
        else:  # fighters
            distress_type = MessageType.MESG04 if defended else MessageType.MESG05
            
        location_data = {
            'planet_name': planet.name,
            'attacker_name': attacker.userid,
            'ship_name': f"Ship_{attacker_id}",  # Would need ship lookup
            'sector_x': planet.sector_x,
            'sector_y': planet.sector_y,
            'troop_count': troops_or_fighters
        }
        
        return self.send_distress_call(planet.owner_id, distress_type, location_data)
    
    def send_starvation_distress(self, planet_id: int, casualties: int, 
                                casualty_type: str) -> List[Mail]:
        """Send distress call for starvation casualties"""
        planet = self.db.query(Planet).filter(Planet.id == planet_id).first()
        if not planet:
            raise ValueError("Planet not found")
            
        distress_type = MessageType.MESG06 if casualty_type == "troops" else MessageType.MESG07
        
        location_data = {
            'planet_name': planet.name,
            'sector_x': planet.sector_x,
            'sector_y': planet.sector_y,
            'troop_count': casualties
        }
        
        return self.send_distress_call(planet.owner_id, distress_type, location_data)
    
    # ================== STATUS MESSAGES ==================
    
    def send_status_message(self, user_id: int, message_type: int, 
                           status_data: Dict[str, Any]) -> Mail:
        """Send status message to user"""
        content_data = {
            'name1': status_data.get('location_name', ''),
            'int1': status_data.get('sector_x', 0),
            'int2': status_data.get('sector_y', 0),
            'long1': status_data.get('quantity', 0)
        }
        
        return self.send_mail(
            sender_id=0,  # System message
            recipient_id=user_id,
            mail_class=MailClass.PLSTATS,
            mail_type=message_type,
            topic="Status Message",
            content_data=content_data
        )
    
    def send_production_report(self, user_id: int, planet_id: int, 
                              financial_data: Dict[str, Any],
                              item_quantities: Dict[str, int]) -> Mail:
        """Send production report to planet owner"""
        planet = self.db.query(Planet).filter(Planet.id == planet_id).first()
        if not planet:
            raise ValueError("Planet not found")
            
        # Create mail status record for production report
        mail_status = MailStatus(
            user_id=user_id,
            userid=planet.owner.userid if planet.owner else "",
            class_type=MailClass.PRODRPT,
            type=MessageType.MESG20,
            topic="Production Report",
            name1=planet.name,
            int1=planet.sector_x,
            int2=planet.sector_y,
            cash=financial_data.get('cash', 0),
            debt=financial_data.get('debt', 0),
            tax=financial_data.get('tax', 0)
        )
        
        self.db.add(mail_status)
        
        # Also send as regular mail
        content_data = {
            'name1': planet.name,
            'int1': planet.sector_x,
            'int2': planet.sector_y
        }
        
        mail = self.send_mail(
            sender_id=0,  # System message
            recipient_id=user_id,
            mail_class=MailClass.PRODRPT,
            mail_type=MessageType.MESG20,
            topic="Production Report",
            content_data=content_data
        )
        
        self.db.commit()
        return mail
    
    # ================== TEAM COMMUNICATION ==================
    
    def send_team_message(self, sender_id: int, message: str) -> List[Mail]:
        """Send message to all team members"""
        sender = self.db.query(User).filter(User.id == sender_id).first()
        if not sender or not sender.team_id:
            raise ValueError("Sender not found or not in a team")
            
        team_members = self.db.query(User).filter(
            and_(User.team_id == sender.team_id, User.id != sender_id)
        ).all()
        
        sent_messages = []
        
        for member in team_members:
            content_data = {
                'string1': message,
                'name1': sender.userid
            }
            
            mail = self.send_mail(
                sender_id=sender_id,
                recipient_id=member.id,
                mail_class=MailClass.PLSTATS,  # Team communication class
                mail_type=0,  # Regular team message
                topic="Team Message",
                content_data=content_data
            )
            sent_messages.append(mail)
            
        return sent_messages
    
    # ================== SCANNING SYSTEMS ==================
    # Note: Enhanced scanning is now handled by ScanningService
    # These methods are kept for backward compatibility
    
    def scan_ships_in_range(self, scanner_ship_id: int, scan_range: int) -> List[Dict[str, Any]]:
        """Scan for ships within range - uses enhanced scanning service"""
        from .scanning_service import ScanningService
        from .battle_interface import ScannerType
        
        scanning_service = ScanningService(self.db)
        return scanning_service.scan_ships_detailed(scanner_ship_id, ScannerType.LONG_RANGE)
    
    def scan_planets_in_sector(self, ship_id: int) -> List[Dict[str, Any]]:
        """Scan for planets in current sector - uses enhanced scanning service"""
        from .scanning_service import ScanningService
        
        scanning_service = ScanningService(self.db)
        return scanning_service.scan_planets_detailed(ship_id)
    
    # ================== REPORTING SYSTEMS ==================
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        # Get user's ships
        ships = self.db.query(Ship).filter(Ship.owner_id == user_id).all()
        
        # Get user's planets
        planets = self.db.query(Planet).filter(Planet.owner_id == user_id).all()
        
        return {
            'user_id': user_id,
            'userid': user.userid,
            'score': user.score,
            'kills': user.kills,
            'cash': user.cash,
            'population': user.population,
            'team': user.team.name if user.team else None,
            'ship_count': len(ships),
            'planet_count': len(planets),
            'total_population': sum(p.population for p in planets),
            'total_troops': sum(p.troops for p in planets),
            'last_active': user.last_login
        }
    
    def get_team_roster(self, team_id: int) -> List[Dict[str, Any]]:
        """Get team member roster with statistics"""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError("Team not found")
            
        members = self.db.query(User).filter(User.team_id == team_id).all()
        
        roster = []
        for member in members:
            member_stats = self.get_user_statistics(member.id)
            roster.append(member_stats)
            
        # Sort by score descending
        roster.sort(key=lambda x: x['score'], reverse=True)
        return roster
    
    def get_game_statistics(self) -> Dict[str, Any]:
        """Get game-wide statistics"""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.last_login.isnot(None)).count()
        total_ships = self.db.query(Ship).filter(Ship.status != 'destroyed').count()
        total_planets = self.db.query(Planet).filter(Planet.owner_id.isnot(None)).count()
        total_teams = self.db.query(Team).filter(Team.is_active == True).count()
        
        # Top players by score
        top_players = self.db.query(User).order_by(desc(User.score)).limit(10).all()
        
        # Top teams by score
        top_teams = self.db.query(Team).order_by(desc(Team.score)).limit(5).all()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_ships': total_ships,
            'total_planets': total_planets,
            'total_teams': total_teams,
            'top_players': [{'userid': p.userid, 'score': p.score} for p in top_players],
            'top_teams': [{'name': t.name, 'score': t.score, 'members': t.member_count} 
                         for t in top_teams]
        }

# Helper functions for message formatting (would be expanded)
def format_distress_message(message_type: int, data: Dict[str, Any]) -> str:
    """Format distress message based on type"""
    templates = {
        MessageType.MESG02: "Distress message from {planet} in Sector {x} {y}, they were attacked by Commander {attacker} in The {ship} with {troops} troops. They successfully defended the planet.",
        MessageType.MESG03: "Distress message from {planet} in Sector {x} {y}, they were attacked by Commander {attacker} in The {ship} with {troops} troops. They have surrendered the planet.",
        MessageType.MESG04: "Distress message from {planet} in Sector {x} {y}, they were attacked by Commander {attacker} in The {ship} with {fighters} fighters. They successfully defended the planet.",
        MessageType.MESG05: "Distress message from {planet} in Sector {x} {y}, they were attacked by Commander {attacker} in The {ship} with {fighters} fighters. They have surrendered the planet.",
        MessageType.MESG06: "Distress message from {planet} in Sector {x} {y}, The food supply is extremely low and {casualties} troops have starved to death.",
        MessageType.MESG07: "Distress message from {planet} in Sector {x} {y}, The food supply is extremely low and {casualties} civilians have starved to death."
    }
    
    template = templates.get(message_type, "Unknown message type")
    return template.format(**data)

def format_status_message(message_type: int, data: Dict[str, Any]) -> str:
    """Format status message based on type"""
    templates = {
        MessageType.MESG08: "Message from {location} in Sector {x} {y}, The population has reached the maximum sustainable on this planet. Implementing birth control procedures. Population now {quantity}.",
        MessageType.MESG09: "Message from {location} in Sector {x} {y}, There are no more facilities for storing missiles, the missile production has been suspended at {quantity}.",
        MessageType.MESG10: "Message from {location} in Sector {x} {y}, There are no more facilities for storing torpedoes, the torpedo production has been suspended at {quantity}."
    }
    
    template = templates.get(message_type, "Unknown status message")
    return template.format(**data)


