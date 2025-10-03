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
class ScoreBreakdown:
    """Detailed score breakdown for a player"""
    kill_score: int
    planet_score: int
    team_score: int
    net_worth: int
    combat_rating: float
    economic_rating: float
    strategic_rating: float
    overall_rating: float
    
    def get_total_score(self) -> int:
        """Calculate total score from components"""
        return self.kill_score + self.planet_score + self.team_score


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
class PlayerRanking:
    """Player ranking with detailed breakdown"""
    user_id: int
    username: str
    rank: int
    score: int
    score_breakdown: ScoreBreakdown
    team_name: Optional[str] = None
    last_active: Optional[datetime] = None
    achievements: List[str] = None
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []


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


@dataclass
class TeamRanking:
    """Team ranking with detailed breakdown"""
    team_id: int
    team_name: str
    rank: int
    total_score: int
    member_count: int
    average_score: float
    coordination_bonus: float
    last_active: Optional[datetime] = None


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
    
    def get_player_rankings(self, db: Session, limit: int = 100) -> List[PlayerRanking]:
        """Get player rankings by total score"""
        try:
            # Get all active users
            users = db.query(User).filter(User.is_active == True).all()
            
            player_rankings = []
            
            for user in users:
                total_score = self.calculate_total_score(user.id, db)
                kill_score = self.calculate_kill_score(user.id, db)
                planet_score = self.calculate_planet_score(user.id, db)
                team_score = self.calculate_team_score(user.id, db)
                
                # Calculate additional metrics for detailed breakdown
                net_worth = self._calculate_net_worth(user.id, db)
                combat_rating = self._calculate_combat_rating(user.id, db)
                economic_rating = self._calculate_economic_rating(user.id, db)
                strategic_rating = self._calculate_strategic_rating(user.id, db)
                overall_rating = self._calculate_overall_rating(combat_rating, economic_rating, strategic_rating)
                
                score_breakdown = ScoreBreakdown(
                    kill_score=kill_score,
                    planet_score=planet_score,
                    team_score=team_score,
                    net_worth=net_worth,
                    combat_rating=combat_rating,
                    economic_rating=economic_rating,
                    strategic_rating=strategic_rating,
                    overall_rating=overall_rating
                )
                
                # Get team name if user is in a team
                team_name = None
                if user.team_id:
                    team = db.query(Team).filter(Team.id == user.team_id).first()
                    if team:
                        team_name = team.team_name
                
                # Get achievements
                achievements = self._get_user_achievements(user.id, db)
                
                player_rankings.append(PlayerRanking(
                    user_id=user.id,
                    username=user.username,
                    rank=0,  # Will be set after sorting
                    score=total_score,
                    score_breakdown=score_breakdown,
                    team_name=team_name,
                    last_active=user.last_login,
                    achievements=achievements
                ))
            
            # Sort by total score (descending)
            player_rankings.sort(key=lambda x: x.score, reverse=True)
            
            # Assign ranks
            for i, player in enumerate(player_rankings):
                player.rank = i + 1
            
            return player_rankings[:limit]
            
        except Exception as e:
            logger.error(f"Error getting player rankings: {e}")
            return []
    
    def get_team_rankings(self, db: Session, limit: int = 50) -> List[TeamRanking]:
        """Get team rankings by total score"""
        try:
            # Get all active teams
            teams = db.query(Team).filter(Team.is_active == True).all()
            
            team_rankings = []
            
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
                
                # Calculate coordination bonus
                coordination_bonus = self._calculate_team_coordination_bonus(team.id, db)
                
                # Get team's last activity
                last_active = max([member.last_login for member in team_members if member.last_login], default=None)
                
                team_rankings.append(TeamRanking(
                    team_id=team.id,
                    team_name=team.team_name,
                    rank=0,  # Will be set after sorting
                    total_score=team_score,
                    member_count=len(team_members),
                    average_score=average_score,
                    coordination_bonus=coordination_bonus,
                    last_active=last_active
                ))
            
            # Sort by total score (descending)
            team_rankings.sort(key=lambda x: x.total_score, reverse=True)
            
            # Assign ranks
            for i, team in enumerate(team_rankings):
                team.rank = i + 1
            
            return team_rankings[:limit]
            
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
    
    def _calculate_net_worth(self, user_id: int, db: Session) -> int:
        """Calculate player's net worth based on ships and planets"""
        try:
            # Get user's ships
            ships = db.query(Ship).filter(Ship.owner_id == user_id).all()
            ship_value = sum(self.get_ship_class_points(ship.ship_class) for ship in ships)
            
            # Get user's planets
            planets = db.query(Planet).filter(Planet.owner_id == user_id).all()
            planet_value = sum(planet.population * 10 + planet.production_rate * 5 for planet in planets)
            
            return ship_value + planet_value
        except Exception as e:
            logger.error(f"Error calculating net worth for user {user_id}: {e}")
            return 0
    
    def _calculate_combat_rating(self, user_id: int, db: Session) -> float:
        """Calculate combat rating based on kill score and ship power"""
        try:
            kill_score = self.calculate_kill_score(user_id, db)
            ships = db.query(Ship).filter(Ship.owner_id == user_id).all()
            
            # Base combat rating from kill score
            combat_rating = kill_score * 0.1
            
            # Add ship power bonus
            for ship in ships:
                ship_power = self.get_ship_class_points(ship.ship_class)
                combat_rating += ship_power * 0.05
            
            return min(combat_rating, 1000.0)  # Cap at 1000
        except Exception as e:
            logger.error(f"Error calculating combat rating for user {user_id}: {e}")
            return 0.0
    
    def _calculate_economic_rating(self, user_id: int, db: Session) -> float:
        """Calculate economic rating based on planet control and production"""
        try:
            planets = db.query(Planet).filter(Planet.owner_id == user_id).all()
            
            economic_rating = 0.0
            for planet in planets:
                # Population contributes to economic rating
                economic_rating += planet.population * 0.1
                # Production rate contributes
                economic_rating += planet.production_rate * 0.2
                # Resource factor contributes
                economic_rating += (planet.resource_factor / 100.0) * 10
            
            return min(economic_rating, 1000.0)  # Cap at 1000
        except Exception as e:
            logger.error(f"Error calculating economic rating for user {user_id}: {e}")
            return 0.0
    
    def _calculate_strategic_rating(self, user_id: int, db: Session) -> float:
        """Calculate strategic rating based on team coordination and positioning"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.team_id:
                return 0.0
            
            # Base strategic rating from team score
            team_score = self.calculate_team_score(user_id, db)
            strategic_rating = team_score * 0.05
            
            # Add bonus for multiple planets (strategic spread)
            planets = db.query(Planet).filter(Planet.owner_id == user_id).all()
            if len(planets) > 1:
                strategic_rating += (len(planets) - 1) * 50
            
            return min(strategic_rating, 1000.0)  # Cap at 1000
        except Exception as e:
            logger.error(f"Error calculating strategic rating for user {user_id}: {e}")
            return 0.0
    
    def _calculate_overall_rating(self, combat_rating: float, economic_rating: float, strategic_rating: float) -> float:
        """Calculate overall rating from component ratings"""
        try:
            # Weighted average of component ratings
            overall = (combat_rating * 0.4 + economic_rating * 0.3 + strategic_rating * 0.3)
            return min(overall, 1000.0)  # Cap at 1000
        except Exception as e:
            logger.error(f"Error calculating overall rating: {e}")
            return 0.0
    
    def _calculate_team_coordination_bonus(self, team_id: int, db: Session) -> float:
        """Calculate team coordination bonus"""
        try:
            team_members = db.query(User).filter(User.team_id == team_id).all()
            if len(team_members) < 2:
                return 0.0
            
            # Base coordination bonus increases with team size
            base_bonus = len(team_members) * 0.1
            
            # Check for coordinated activities (simplified)
            # In a real implementation, this would check for joint operations
            coordination_bonus = base_bonus + 0.2
            
            return min(coordination_bonus, 1.0)  # Cap at 100%
        except Exception as e:
            logger.error(f"Error calculating team coordination bonus for team {team_id}: {e}")
            return 0.0
    
    def _get_user_achievements(self, user_id: int, db: Session) -> List[str]:
        """Get user achievements (placeholder implementation)"""
        try:
            achievements = []
            
            # Check for various achievements
            kill_score = self.calculate_kill_score(user_id, db)
            planet_score = self.calculate_planet_score(user_id, db)
            net_worth = self._calculate_net_worth(user_id, db)
            
            if kill_score >= 1000:
                achievements.append("Combat Veteran")
            if kill_score >= 5000:
                achievements.append("Warrior Elite")
            if planet_score >= 500:
                achievements.append("Planetary Governor")
            if planet_score >= 2000:
                achievements.append("Galactic Emperor")
            if net_worth >= 10000:
                achievements.append("Wealthy Merchant")
            if net_worth >= 50000:
                achievements.append("Galactic Tycoon")
            
            return achievements
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return []
    
    def get_player_score_breakdown(self, user_id: int, db: Session) -> ScoreBreakdown:
        """Get detailed score breakdown for a specific player"""
        try:
            kill_score = self.calculate_kill_score(user_id, db)
            planet_score = self.calculate_planet_score(user_id, db)
            team_score = self.calculate_team_score(user_id, db)
            net_worth = self._calculate_net_worth(user_id, db)
            combat_rating = self._calculate_combat_rating(user_id, db)
            economic_rating = self._calculate_economic_rating(user_id, db)
            strategic_rating = self._calculate_strategic_rating(user_id, db)
            overall_rating = self._calculate_overall_rating(combat_rating, economic_rating, strategic_rating)
            
            return ScoreBreakdown(
                kill_score=kill_score,
                planet_score=planet_score,
                team_score=team_score,
                net_worth=net_worth,
                combat_rating=combat_rating,
                economic_rating=economic_rating,
                strategic_rating=strategic_rating,
                overall_rating=overall_rating
            )
        except Exception as e:
            logger.error(f"Error getting score breakdown for user {user_id}: {e}")
            return ScoreBreakdown(0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0)
    
    def check_achievements(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Check and return user achievements"""
        try:
            achievements = self._get_user_achievements(user_id, db)
            
            # Convert to expected format
            result = []
            for i, achievement in enumerate(achievements):
                result.append({
                    "id": i + 1,
                    "name": achievement,
                    "description": f"Achievement: {achievement}",
                    "achievement_type": "general",
                    "reward_score": 100,
                    "icon": "🏆",
                    "rarity": "common"
                })
            
            return result
        except Exception as e:
            logger.error(f"Error checking achievements for user {user_id}: {e}")
            return []
    
    def clear_cache(self):
        """Clear scoring service cache (placeholder)"""
        # In a real implementation, this would clear any cached calculations
        pass


# Global scoring service instance
scoring_service = ScoringService()


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance"""
    return scoring_service