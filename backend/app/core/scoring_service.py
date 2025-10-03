"""
Galactic Empire - Scoring Service

This module implements the original scoring system with kill/planet/team scoring
formulas from the classic BBS game.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.game_config import game_config
from app.models.user import User
from app.models.ship import Ship, ShipClass
from app.models.planet import Planet
from app.models.team import Team

logger = logging.getLogger(__name__)


class ScoreType(Enum):
    """Types of scores"""
    KILL_SCORE = "kill_score"
    PLANET_SCORE = "planet_score"
    TEAM_SCORE = "team_score"
    TOTAL_SCORE = "total_score"


@dataclass
class ShipClassPoints:
    """Ship class point values from original game"""
    ship_class: str
    points: int
    description: str


@dataclass
class PlayerScore:
    """Player score breakdown"""
    user_id: int
    username: str
    kill_score: int
    planet_score: int
    team_score: int
    total_score: int
    rank: int
    last_updated: datetime


@dataclass
class TeamScore:
    """Team score breakdown"""
    team_id: int
    team_name: str
    total_score: int
    member_count: int
    average_score: float
    rank: int
    last_updated: datetime


class ScoringService:
    """Service for managing game scoring calculations"""
    
    def __init__(self):
        # Original ship class point values from GEREADME.DOC
        self.ship_class_points = {
            "Interceptor": 10,
            "Light Freighter": 25,
            "Heavy Freighter": 75,
            "Destroyer": 150,
            "Star Cruiser": 200,
            "Battle Cruiser": 250,
            "Frigate": 300,
            "Dreadnought": 500,
            "Freight Barge": 200,
            "Cybertron Scout": 75,
            "Cybertron Battle Cruiser": 200,
            "Flagship": 1000,  # Estimated based on progression
            "Scout": 15,       # Estimated
            "Fighter": 50,     # Estimated
            "Battleship": 400, # Estimated
            "Cyborg": 300,     # Estimated
            "Droid": 100       # Estimated
        }
        
        # Original team scoring formula: (A/B)+(C*B)
        # Where A = sum of individual scores, B = number of team members, C = team bonus
        self.team_bonus_base = 1000
        self.team_coordination_multiplier = 0.5
    
    def calculate_kill_score(self, user_id: int, db: Session) -> int:
        """Calculate kill score based on ships destroyed"""
        try:
            # Get user's kill history from database
            # This would need to be implemented in the database schema
            # For now, we'll use a placeholder calculation
            
            # In the original game, kill score was based on:
            # 1. Ship class points of destroyed ships
            # 2. Bonus percentage of killed player's score
            # 3. Score reduction for the killed player
            
            # Placeholder calculation - would need actual kill records
            kill_score = 0
            
            # TODO: Implement actual kill tracking in database
            # Example calculation:
            # for kill in user_kills:
            #     ship_points = self.ship_class_points.get(kill.ship_class, 10)
            #     bonus = kill.victim_score * 0.1  # 10% bonus
            #     kill_score += ship_points + bonus
            
            return kill_score
            
        except Exception as e:
            logger.error(f"Error calculating kill score for user {user_id}: {e}")
            return 0
    
    def calculate_planet_score(self, user_id: int, db: Session) -> int:
        """Calculate planet score based on controlled planets"""
        try:
            # Get user's planets
            planets = db.query(Planet).filter(Planet.owner_id == user_id).all()
            
            planet_score = 0
            
            for planet in planets:
                # Base score per planet
                base_score = game_config.get_config("planet_population_value", 10)
                
                # Population bonus
                population_bonus = planet.population * base_score
                
                # Production bonus
                production_bonus = planet.production_rate * game_config.get_config("planet_production_value", 5)
                
                # Environment bonus
                environment_bonus = (planet.environment_factor / 100.0) * 100
                
                # Resource bonus
                resource_bonus = (planet.resource_factor / 100.0) * 50
                
                # Strategic bonus for multiple planets
                strategic_bonus = game_config.get_config("planet_strategic_bonus", 0.2)
                if len(planets) > 1:
                    strategic_bonus *= (len(planets) - 1)
                
                planet_score += int(population_bonus + production_bonus + 
                                  environment_bonus + resource_bonus + strategic_bonus)
            
            return planet_score
            
        except Exception as e:
            logger.error(f"Error calculating planet score for user {user_id}: {e}")
            return 0
    
    def calculate_team_score(self, user_id: int, db: Session) -> int:
        """Calculate team score using original formula (A/B)+(C*B)"""
        try:
            # Get user's team
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.team_id:
                return 0
            
            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                return 0
            
            # Get all team members
            team_members = db.query(User).filter(User.team_id == team.id).all()
            if not team_members:
                return 0
            
            # Calculate individual scores for all team members
            total_individual_score = 0
            for member in team_members:
                member_kill_score = self.calculate_kill_score(member.id, db)
                member_planet_score = self.calculate_planet_score(member.id, db)
                total_individual_score += member_kill_score + member_planet_score
            
            # Apply original team scoring formula: (A/B)+(C*B)
            # A = sum of individual scores
            # B = number of team members
            # C = team bonus base
            A = total_individual_score
            B = len(team_members)
            C = self.team_bonus_base
            
            team_score = int((A / B) + (C * B))
            
            # Apply coordination bonus
            coordination_bonus = game_config.get_config("team_coordination_bonus", 0.5)
            team_score = int(team_score * (1.0 + coordination_bonus))
            
            return team_score
            
        except Exception as e:
            logger.error(f"Error calculating team score for user {user_id}: {e}")
            return 0
    
    def calculate_total_score(self, user_id: int, db: Session) -> int:
        """Calculate total player score"""
        try:
            kill_score = self.calculate_kill_score(user_id, db)
            planet_score = self.calculate_planet_score(user_id, db)
            team_score = self.calculate_team_score(user_id, db)
            
            total_score = kill_score + planet_score + team_score
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating total score for user {user_id}: {e}")
            return 0
    
    def get_player_rankings(self, db: Session, limit: int = 100) -> List[PlayerScore]:
        """Get player rankings by total score"""
        try:
            # Get all active users
            users = db.query(User).filter(User.is_active == True).all()
            
            player_scores = []
            
            for user in users:
                total_score = self.calculate_total_score(user.id, db)
                kill_score = self.calculate_kill_score(user.id, db)
                planet_score = self.calculate_planet_score(user.id, db)
                team_score = self.calculate_team_score(user.id, db)
                
                player_scores.append(PlayerScore(
                    user_id=user.id,
                    username=user.username,
                    kill_score=kill_score,
                    planet_score=planet_score,
                    team_score=team_score,
                    total_score=total_score,
                    rank=0,  # Will be set after sorting
                    last_updated=datetime.utcnow()
                ))
            
            # Sort by total score (descending)
            player_scores.sort(key=lambda x: x.total_score, reverse=True)
            
            # Assign ranks
            for i, player in enumerate(player_scores):
                player.rank = i + 1
            
            return player_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error getting player rankings: {e}")
            return []
    
    def get_team_rankings(self, db: Session, limit: int = 50) -> List[TeamScore]:
        """Get team rankings by total score"""
        try:
            # Get all active teams
            teams = db.query(Team).filter(Team.is_active == True).all()
            
            team_scores = []
            
            for team in teams:
                # Get team members
                team_members = db.query(User).filter(User.team_id == team.id).all()
                if not team_members:
                    continue
                
                # Calculate team score using first member (team score is same for all members)
                team_score = self.calculate_team_score(team_members[0].id, db)
                
                # Calculate average individual score
                total_individual_score = 0
                for member in team_members:
                    individual_score = (self.calculate_kill_score(member.id, db) + 
                                      self.calculate_planet_score(member.id, db))
                    total_individual_score += individual_score
                
                average_score = total_individual_score / len(team_members)
                
                team_scores.append(TeamScore(
                    team_id=team.id,
                    team_name=team.team_name,
                    total_score=team_score,
                    member_count=len(team_members),
                    average_score=average_score,
                    rank=0,  # Will be set after sorting
                    last_updated=datetime.utcnow()
                ))
            
            # Sort by total score (descending)
            team_scores.sort(key=lambda x: x.total_score, reverse=True)
            
            # Assign ranks
            for i, team in enumerate(team_scores):
                team.rank = i + 1
            
            return team_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error getting team rankings: {e}")
            return []
    
    def update_player_score(self, user_id: int, db: Session) -> PlayerScore:
        """Update and return player score"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            total_score = self.calculate_total_score(user_id, db)
            kill_score = self.calculate_kill_score(user_id, db)
            planet_score = self.calculate_planet_score(user_id, db)
            team_score = self.calculate_team_score(user_id, db)
            
            # Update user's score in database
            # This would need to be added to the User model
            # user.total_score = total_score
            # user.kill_score = kill_score
            # user.planet_score = planet_score
            # user.team_score = team_score
            # user.score_updated_at = datetime.utcnow()
            # db.commit()
            
            return PlayerScore(
                user_id=user_id,
                username=user.username,
                kill_score=kill_score,
                planet_score=planet_score,
                team_score=team_score,
                total_score=total_score,
                rank=0,  # Would need to calculate rank
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error updating player score for user {user_id}: {e}")
            raise
    
    def get_ship_class_points(self, ship_class: str) -> int:
        """Get point value for ship class"""
        return self.ship_class_points.get(ship_class, 10)
    
    def add_kill_record(self, killer_id: int, victim_id: int, ship_class: str, 
                       victim_score: int, db: Session) -> bool:
        """Add a kill record and update scores"""
        try:
            # This would need to be implemented in the database schema
            # For now, we'll just log the kill
            
            ship_points = self.get_ship_class_points(ship_class)
            bonus = int(victim_score * 0.1)  # 10% bonus from original game
            
            logger.info(f"Kill recorded: User {killer_id} destroyed {ship_class} "
                       f"belonging to user {victim_id}. Points: {ship_points}, Bonus: {bonus}")
            
            # TODO: Implement actual kill tracking
            # kill_record = KillRecord(
            #     killer_id=killer_id,
            #     victim_id=victim_id,
            #     ship_class=ship_class,
            #     points_awarded=ship_points,
            #     bonus_awarded=bonus,
            #     timestamp=datetime.utcnow()
            # )
            # db.add(kill_record)
            # db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding kill record: {e}")
            return False
    
    def recalculate_all_scores(self, db: Session) -> Dict[str, Any]:
        """Recalculate all player and team scores"""
        try:
            start_time = datetime.utcnow()
            
            # Get all active users
            users = db.query(User).filter(User.is_active == True).all()
            
            updated_count = 0
            for user in users:
                try:
                    self.update_player_score(user.id, db)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating score for user {user.id}: {e}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "success": True,
                "updated_players": updated_count,
                "total_players": len(users),
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }
            
            logger.info(f"Score recalculation completed: {updated_count}/{len(users)} players updated in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error recalculating scores: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global scoring service instance
scoring_service = ScoringService()


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance"""
    return scoring_service