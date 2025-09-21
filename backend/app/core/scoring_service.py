"""
Galactic Empire - Comprehensive Scoring and Ranking System

This module provides advanced scoring calculations, ranking systems, and
achievement tracking for competitive gameplay.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.core.database import get_db
from app.core.game_config import game_config, ConfigCategory
from app.models.user import User
from app.models.ship import Ship
from app.models.planet import Planet
from app.models.team import Team

logger = logging.getLogger(__name__)


class ScoreType(Enum):
    """Types of scores tracked"""
    KILL_SCORE = "kill_score"
    PLANET_SCORE = "planet_score"
    TEAM_SCORE = "team_score"
    NET_WORTH = "net_worth"
    COMBAT_RATING = "combat_rating"
    ECONOMIC_RATING = "economic_rating"
    STRATEGIC_RATING = "strategic_rating"
    OVERALL_RATING = "overall_rating"


class AchievementType(Enum):
    """Types of achievements"""
    COMBAT = "combat"
    ECONOMIC = "economic"
    STRATEGIC = "strategic"
    TEAMWORK = "teamwork"
    EXPLORATION = "exploration"
    SPECIAL = "special"


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of player scores"""
    kill_score: int = 0
    planet_score: int = 0
    team_score: int = 0
    net_worth: int = 0
    combat_rating: float = 0.0
    economic_rating: float = 0.0
    strategic_rating: float = 0.0
    overall_rating: float = 0.0
    
    def get_total_score(self) -> int:
        """Calculate total score"""
        return self.kill_score + self.planet_score + self.team_score + self.net_worth


@dataclass
class PlayerRanking:
    """Player ranking information"""
    user_id: int
    username: str
    rank: int
    score: int
    score_breakdown: ScoreBreakdown
    team_name: Optional[str] = None
    last_active: Optional[datetime] = None
    achievements: List[str] = field(default_factory=list)


@dataclass
class TeamRanking:
    """Team ranking information"""
    team_id: int
    team_name: str
    rank: int
    total_score: int
    member_count: int
    average_score: float
    coordination_bonus: float
    last_active: Optional[datetime] = None


@dataclass
class Achievement:
    """Achievement definition"""
    id: str
    name: str
    description: str
    achievement_type: AchievementType
    requirement: Dict[str, Any]
    reward_score: int
    icon: str = ""
    rarity: str = "common"  # common, rare, epic, legendary


class ScoringService:
    """Service for calculating scores, rankings, and achievements"""
    
    def __init__(self):
        self._achievements: Dict[str, Achievement] = {}
        self._score_cache: Dict[int, ScoreBreakdown] = {}
        self._ranking_cache: Dict[str, List[Any]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._initialize_achievements()
    
    def _initialize_achievements(self):
        """Initialize all available achievements"""
        achievements = [
            # Combat Achievements
            Achievement(
                id="first_kill",
                name="First Blood",
                description="Score your first kill",
                achievement_type=AchievementType.COMBAT,
                requirement={"kills": 1},
                reward_score=100,
                icon="⚔️",
                rarity="common"
            ),
            Achievement(
                id="ace_pilot",
                name="Ace Pilot",
                description="Achieve 10 kills",
                achievement_type=AchievementType.COMBAT,
                requirement={"kills": 10},
                reward_score=500,
                icon="🏆",
                rarity="rare"
            ),
            Achievement(
                id="destroyer",
                name="Destroyer",
                description="Achieve 50 kills",
                achievement_type=AchievementType.COMBAT,
                requirement={"kills": 50},
                reward_score=2000,
                icon="💀",
                rarity="epic"
            ),
            Achievement(
                id="legendary_warrior",
                name="Legendary Warrior",
                description="Achieve 100 kills",
                achievement_type=AchievementType.COMBAT,
                requirement={"kills": 100},
                reward_score=5000,
                icon="👑",
                rarity="legendary"
            ),
            
            # Economic Achievements
            Achievement(
                id="merchant",
                name="Merchant",
                description="Accumulate 1M credits",
                achievement_type=AchievementType.ECONOMIC,
                requirement={"credits": 1000000},
                reward_score=200,
                icon="💰",
                rarity="common"
            ),
            Achievement(
                id="tycoon",
                name="Tycoon",
                description="Accumulate 10M credits",
                achievement_type=AchievementType.ECONOMIC,
                requirement={"credits": 10000000},
                reward_score=1000,
                icon="💎",
                rarity="rare"
            ),
            Achievement(
                id="empire_builder",
                name="Empire Builder",
                description="Control 5 planets",
                achievement_type=AchievementType.ECONOMIC,
                requirement={"planets_controlled": 5},
                reward_score=1500,
                icon="🏰",
                rarity="epic"
            ),
            
            # Strategic Achievements
            Achievement(
                id="explorer",
                name="Explorer",
                description="Visit 20 different sectors",
                achievement_type=AchievementType.STRATEGIC,
                requirement={"sectors_visited": 20},
                reward_score=300,
                icon="🗺️",
                rarity="rare"
            ),
            Achievement(
                id="diplomat",
                name="Diplomat",
                description="Send 100 diplomatic messages",
                achievement_type=AchievementType.STRATEGIC,
                requirement={"diplomatic_messages": 100},
                reward_score=400,
                icon="🤝",
                rarity="rare"
            ),
            
            # Teamwork Achievements
            Achievement(
                id="team_player",
                name="Team Player",
                description="Join a team",
                achievement_type=AchievementType.TEAMWORK,
                requirement={"team_member": True},
                reward_score=100,
                icon="👥",
                rarity="common"
            ),
            Achievement(
                id="coordinator",
                name="Coordinator",
                description="Lead team to victory",
                achievement_type=AchievementType.TEAMWORK,
                requirement={"team_victories": 1},
                reward_score=800,
                icon="🎯",
                rarity="epic"
            ),
            
            # Special Achievements
            Achievement(
                id="survivor",
                name="Survivor",
                description="Survive 10 battles",
                achievement_type=AchievementType.SPECIAL,
                requirement={"battles_survived": 10},
                reward_score=300,
                icon="🛡️",
                rarity="rare"
            ),
            Achievement(
                id="perfectionist",
                name="Perfectionist",
                description="Win 10 battles without taking damage",
                achievement_type=AchievementType.SPECIAL,
                requirement={"perfect_victories": 10},
                reward_score=1500,
                icon="✨",
                rarity="legendary"
            ),
        ]
        
        for achievement in achievements:
            self._achievements[achievement.id] = achievement
    
    def calculate_kill_score(self, kills: List[Dict[str, Any]]) -> int:
        """Calculate kill score based on ship classes destroyed"""
        base_score = game_config.get_config("kill_score_base")
        ship_multipliers = game_config.get_config("ship_class_multipliers")
        
        total_score = 0
        for kill in kills:
            ship_class = kill.get("ship_class", "Fighter")
            multiplier = ship_multipliers.get(ship_class, 1.0)
            
            # Additional bonuses
            bonus = 1.0
            if kill.get("critical_hit", False):
                bonus += 0.5  # 50% bonus for critical hits
            if kill.get("outnumbered", False):
                bonus += 0.3  # 30% bonus for outnumbered victories
            if kill.get("first_strike", False):
                bonus += 0.2  # 20% bonus for first strike
            
            kill_score = int(base_score * multiplier * bonus)
            total_score += kill_score
        
        return total_score
    
    def calculate_planet_score(self, planets: List[Dict[str, Any]]) -> int:
        """Calculate planet score based on planet value"""
        population_value = game_config.get_config("planet_population_value")
        production_value = game_config.get_config("planet_production_value")
        strategic_bonus = game_config.get_config("planet_strategic_bonus")
        
        total_score = 0
        for planet in planets:
            # Base planet score
            population_score = planet.get("population", 0) * population_value
            production_score = planet.get("total_production", 0) * production_value
            
            # Strategic bonus
            strategic_value = 1.0
            if planet.get("strategic_location", False):
                strategic_value += strategic_bonus
            if planet.get("high_resources", False):
                strategic_value += strategic_bonus * 0.5
            
            planet_score = int((population_score + production_score) * strategic_value)
            total_score += planet_score
        
        return total_score
    
    def calculate_team_score(self, team_stats: Dict[str, Any]) -> int:
        """Calculate team score based on team performance"""
        base_bonus = game_config.get_config("team_bonus_base")
        coordination_bonus = game_config.get_config("team_coordination_bonus")
        
        # Base team score
        team_score = base_bonus
        
        # Member count bonus
        member_count = team_stats.get("member_count", 1)
        if member_count >= 5:
            team_score += int(base_bonus * 0.5)  # 50% bonus for large teams
        
        # Coordination bonus
        coordinated_actions = team_stats.get("coordinated_actions", 0)
        if coordinated_actions > 10:
            team_score += int(base_bonus * coordination_bonus)
        
        # Victory bonus
        victories = team_stats.get("victories", 0)
        team_score += victories * 500
        
        return team_score
    
    def calculate_net_worth(self, assets: Dict[str, Any]) -> int:
        """Calculate net worth from all assets"""
        net_worth = 0
        
        # Ship values
        ships = assets.get("ships", [])
        for ship in ships:
            ship_value = self._calculate_ship_value(ship)
            net_worth += ship_value
        
        # Planet values
        planets = assets.get("planets", [])
        for planet in planets:
            planet_value = self._calculate_planet_value(planet)
            net_worth += planet_value
        
        # Credits
        net_worth += assets.get("credits", 0)
        
        # Items and resources
        items = assets.get("items", {})
        for item_type, quantity in items.items():
            item_value = self._calculate_item_value(item_type, quantity)
            net_worth += item_value
        
        return net_worth
    
    def _calculate_ship_value(self, ship: Dict[str, Any]) -> int:
        """Calculate ship value based on class and condition"""
        ship_class = ship.get("ship_class", "Fighter")
        condition = ship.get("condition", 1.0)
        
        # Base ship values
        ship_values = {
            "Interceptor": 100000,
            "Scout": 80000,
            "Fighter": 150000,
            "Destroyer": 300000,
            "Cruiser": 500000,
            "Battleship": 800000,
            "Dreadnought": 1200000,
            "Flagship": 2000000,
            "Cyborg": 400000,
            "Droid": 200000
        }
        
        base_value = ship_values.get(ship_class, 150000)
        return int(base_value * condition)
    
    def _calculate_planet_value(self, planet: Dict[str, Any]) -> int:
        """Calculate planet value based on resources and development"""
        population = planet.get("population", 0)
        resources = planet.get("total_resources", 0)
        development = planet.get("development_level", 1.0)
        
        # Base value calculation
        base_value = population * 1000 + resources * 100
        return int(base_value * development)
    
    def _calculate_item_value(self, item_type: str, quantity: int) -> int:
        """Calculate item value based on type and quantity"""
        # Base item values (per unit)
        item_values = {
            "energy": 10,
            "fuel": 25,
            "weapons": 100,
            "shields": 150,
            "cargo": 50,
            "technology": 200,
            "food": 15,
            "medicine": 75,
            "luxury": 300,
            "military": 250,
            "construction": 40,
            "research": 500,
            "communication": 120,
            "transport": 80
        }
        
        unit_value = item_values.get(item_type, 50)
        return quantity * unit_value
    
    def calculate_ratings(self, player_stats: Dict[str, Any]) -> Tuple[float, float, float, float]:
        """Calculate combat, economic, strategic, and overall ratings"""
        # Combat rating
        combat_rating = self._calculate_combat_rating(player_stats)
        
        # Economic rating
        economic_rating = self._calculate_economic_rating(player_stats)
        
        # Strategic rating
        strategic_rating = self._calculate_strategic_rating(player_stats)
        
        # Overall rating (weighted average)
        overall_rating = (
            combat_rating * 0.4 +
            economic_rating * 0.3 +
            strategic_rating * 0.3
        )
        
        return combat_rating, economic_rating, strategic_rating, overall_rating
    
    def _calculate_combat_rating(self, player_stats: Dict[str, Any]) -> float:
        """Calculate combat rating based on performance"""
        kills = player_stats.get("kills", 0)
        deaths = player_stats.get("deaths", 1)  # Avoid division by zero
        battles = player_stats.get("battles", 0)
        damage_dealt = player_stats.get("damage_dealt", 0)
        damage_taken = player_stats.get("damage_taken", 1)
        
        # Kill/death ratio
        kd_ratio = kills / deaths
        
        # Battle participation
        participation_rate = battles / max(player_stats.get("days_active", 1), 1)
        
        # Damage efficiency
        damage_ratio = damage_dealt / damage_taken
        
        # Calculate rating (0-10 scale)
        rating = (kd_ratio * 0.4 + participation_rate * 0.3 + damage_ratio * 0.3) * 2
        return min(rating, 10.0)
    
    def _calculate_economic_rating(self, player_stats: Dict[str, Any]) -> float:
        """Calculate economic rating based on wealth and production"""
        net_worth = player_stats.get("net_worth", 0)
        planets_controlled = player_stats.get("planets_controlled", 0)
        trade_volume = player_stats.get("trade_volume", 0)
        production_output = player_stats.get("production_output", 0)
        
        # Wealth factor
        wealth_factor = min(net_worth / 10000000, 1.0)  # Normalize to 10M
        
        # Production factor
        production_factor = min(production_output / 1000000, 1.0)  # Normalize to 1M
        
        # Trade factor
        trade_factor = min(trade_volume / 5000000, 1.0)  # Normalize to 5M
        
        # Calculate rating (0-10 scale)
        rating = (wealth_factor * 0.4 + production_factor * 0.4 + trade_factor * 0.2) * 10
        return min(rating, 10.0)
    
    def _calculate_strategic_rating(self, player_stats: Dict[str, Any]) -> float:
        """Calculate strategic rating based on planning and execution"""
        sectors_controlled = player_stats.get("sectors_controlled", 0)
        diplomatic_actions = player_stats.get("diplomatic_actions", 0)
        strategic_victories = player_stats.get("strategic_victories", 0)
        exploration_bonus = player_stats.get("sectors_explored", 0)
        
        # Control factor
        control_factor = min(sectors_controlled / 10, 1.0)  # Normalize to 10 sectors
        
        # Diplomatic factor
        diplomatic_factor = min(diplomatic_actions / 50, 1.0)  # Normalize to 50 actions
        
        # Victory factor
        victory_factor = min(strategic_victories / 5, 1.0)  # Normalize to 5 victories
        
        # Exploration factor
        exploration_factor = min(exploration_bonus / 20, 1.0)  # Normalize to 20 sectors
        
        # Calculate rating (0-10 scale)
        rating = (control_factor * 0.3 + diplomatic_factor * 0.2 + 
                 victory_factor * 0.3 + exploration_factor * 0.2) * 10
        return min(rating, 10.0)
    
    def get_player_score_breakdown(self, user_id: int, db: Session) -> ScoreBreakdown:
        """Get detailed score breakdown for a player"""
        # Check cache first
        if user_id in self._score_cache:
            return self._score_cache[user_id]
        
        # Get player data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return ScoreBreakdown()
        
        # Get player statistics
        player_stats = self._get_player_statistics(user_id, db)
        
        # Calculate scores
        kill_score = self.calculate_kill_score(player_stats.get("kills", []))
        planet_score = self.calculate_planet_score(player_stats.get("planets", []))
        team_score = self.calculate_team_score(player_stats.get("team_stats", {}))
        net_worth = self.calculate_net_worth(player_stats.get("assets", {}))
        
        # Calculate ratings
        combat_rating, economic_rating, strategic_rating, overall_rating = \
            self.calculate_ratings(player_stats)
        
        breakdown = ScoreBreakdown(
            kill_score=kill_score,
            planet_score=planet_score,
            team_score=team_score,
            net_worth=net_worth,
            combat_rating=combat_rating,
            economic_rating=economic_rating,
            strategic_rating=strategic_rating,
            overall_rating=overall_rating
        )
        
        # Cache result
        self._score_cache[user_id] = breakdown
        return breakdown
    
    def _get_player_statistics(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive player statistics"""
        # This would be implemented with actual database queries
        # For now, return mock data structure
        return {
            "kills": [],
            "planets": [],
            "team_stats": {},
            "assets": {},
            "days_active": 1,
            "battles": 0,
            "deaths": 0,
            "damage_dealt": 0,
            "damage_taken": 0,
            "planets_controlled": 0,
            "trade_volume": 0,
            "production_output": 0,
            "sectors_controlled": 0,
            "diplomatic_actions": 0,
            "strategic_victories": 0,
            "sectors_explored": 0
        }
    
    def get_player_rankings(self, db: Session, limit: int = 100) -> List[PlayerRanking]:
        """Get player rankings"""
        cache_key = f"player_rankings_{limit}"
        
        # Check cache
        if (cache_key in self._ranking_cache and 
            self._cache_timestamp and 
            datetime.utcnow() - self._cache_timestamp < timedelta(minutes=5)):
            return self._ranking_cache[cache_key]
        
        rankings = []
        
        # Get all users with their scores
        users = db.query(User).all()
        
        for user in users:
            score_breakdown = self.get_player_score_breakdown(user.id, db)
            total_score = score_breakdown.get_total_score()
            
            # Get team information
            team_name = None
            if hasattr(user, 'team') and user.team:
                team_name = user.team.team_name
            
            ranking = PlayerRanking(
                user_id=user.id,
                username=user.username,
                rank=0,  # Will be set after sorting
                score=total_score,
                score_breakdown=score_breakdown,
                team_name=team_name,
                last_active=user.updated_at
            )
            rankings.append(ranking)
        
        # Sort by total score
        rankings.sort(key=lambda x: x.score, reverse=True)
        
        # Assign ranks
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1
        
        # Cache results
        self._ranking_cache[cache_key] = rankings
        self._cache_timestamp = datetime.utcnow()
        
        return rankings[:limit]
    
    def get_team_rankings(self, db: Session, limit: int = 50) -> List[TeamRanking]:
        """Get team rankings"""
        cache_key = f"team_rankings_{limit}"
        
        # Check cache
        if (cache_key in self._ranking_cache and 
            self._cache_timestamp and 
            datetime.utcnow() - self._cache_timestamp < timedelta(minutes=5)):
            return self._ranking_cache[cache_key]
        
        rankings = []
        
        # Get all teams with their scores
        teams = db.query(Team).all()
        
        for team in teams:
            # Calculate team score
            team_stats = self._get_team_statistics(team.id, db)
            total_score = self.calculate_team_score(team_stats)
            
            # Calculate coordination bonus
            coordination_bonus = self._calculate_coordination_bonus(team.id, db)
            
            ranking = TeamRanking(
                team_id=team.id,
                team_name=team.team_name,
                rank=0,  # Will be set after sorting
                total_score=total_score,
                member_count=len(team.members) if hasattr(team, 'members') else 0,
                average_score=total_score / max(len(team.members), 1) if hasattr(team, 'members') else 0,
                coordination_bonus=coordination_bonus,
                last_active=team.updated_at
            )
            rankings.append(ranking)
        
        # Sort by total score
        rankings.sort(key=lambda x: x.total_score, reverse=True)
        
        # Assign ranks
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1
        
        # Cache results
        self._ranking_cache[cache_key] = rankings
        self._cache_timestamp = datetime.utcnow()
        
        return rankings[:limit]
    
    def _get_team_statistics(self, team_id: int, db: Session) -> Dict[str, Any]:
        """Get team statistics"""
        # This would be implemented with actual database queries
        return {
            "member_count": 0,
            "coordinated_actions": 0,
            "victories": 0
        }
    
    def _calculate_coordination_bonus(self, team_id: int, db: Session) -> float:
        """Calculate team coordination bonus"""
        # This would analyze team activities and coordination
        return 1.0
    
    def check_achievements(self, user_id: int, db: Session) -> List[Achievement]:
        """Check which achievements a player has earned"""
        player_stats = self._get_player_statistics(user_id, db)
        earned_achievements = []
        
        for achievement in self._achievements.values():
            if self._check_achievement_requirement(achievement, player_stats):
                earned_achievements.append(achievement)
        
        return earned_achievements
    
    def _check_achievement_requirement(self, achievement: Achievement, 
                                     player_stats: Dict[str, Any]) -> bool:
        """Check if player meets achievement requirement"""
        requirement = achievement.requirement
        
        for key, required_value in requirement.items():
            player_value = player_stats.get(key, 0)
            if player_value < required_value:
                return False
        
        return True
    
    def clear_cache(self):
        """Clear all cached data"""
        self._score_cache.clear()
        self._ranking_cache.clear()
        self._cache_timestamp = None
        logger.info("Scoring service cache cleared")


# Global scoring service instance
scoring_service = ScoringService()


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance"""
    return scoring_service
