"""
Galactic Empire - Game Configuration Management System

This module provides centralized configuration management for all game balance
parameters, allowing real-time adjustment without server restart.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.base import Base

logger = logging.getLogger(__name__)


class ConfigCategory(Enum):
    """Configuration categories for organization"""
    SHIP_BALANCE = "ship_balance"
    COMBAT_BALANCE = "combat_balance"
    ECONOMIC_SYSTEM = "economic_system"
    SCORING_SYSTEM = "scoring_system"
    GAME_MECHANICS = "game_mechanics"
    ADMIN_SETTINGS = "admin_settings"


class ConfigType(Enum):
    """Configuration value types"""
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    JSON = "json"


@dataclass
class ConfigParameter:
    """Represents a single configuration parameter"""
    key: str
    value: Union[int, float, bool, str, Dict[str, Any]]
    config_type: ConfigType
    category: ConfigCategory
    description: str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    default_value: Union[int, float, bool, str, Dict[str, Any]] = None
    requires_restart: bool = False
    validation_func: Optional[callable] = None


class GameConfiguration:
    """Centralized game configuration management"""
    
    def __init__(self):
        self._config: Dict[str, ConfigParameter] = {}
        self._config_history: List[Dict[str, Any]] = []
        self._initialize_default_config()
    
    def _initialize_default_config(self):
        """Initialize all default configuration parameters"""
        
        # Ship Balance Configuration
        ship_configs = [
            # Energy System
            ConfigParameter("energy_max", 65000, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Maximum energy capacity", min_value=10000, max_value=100000),
            ConfigParameter("energy_recharge_rate", 1, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Energy recharge per tick", min_value=1, max_value=50),
            ConfigParameter("energy_minimum", 5000, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Minimum energy for auto-load", min_value=1000, max_value=20000),
            
            # Movement System
            ConfigParameter("rotation_energy_cost", 30, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Energy cost for rotation", min_value=10, max_value=100),
            ConfigParameter("rotation_amount", 20, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Degrees of rotation per tick", min_value=5, max_value=45),
            ConfigParameter("acceleration_energy_cost", 120, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Energy cost for acceleration", min_value=50, max_value=500),
            ConfigParameter("movement_energy_min", 3000, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Minimum energy for movement", min_value=1000, max_value=10000),
            ConfigParameter("movement_energy_cost", 10, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Energy cost per movement unit", min_value=1, max_value=50),
            
            # Shield System
            ConfigParameter("shield_min_power", 200, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Minimum shield power requirement", min_value=100, max_value=1000),
            ConfigParameter("shield_energy_cost", 100, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Shield energy cost per tick", min_value=50, max_value=500),
            ConfigParameter("shield_hit_energy_drain", 1000, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Energy drained when shields hit", min_value=500, max_value=5000),
            ConfigParameter("shield_max_charge", 10, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Maximum shield charge level", min_value=5, max_value=20),
            ConfigParameter("shield_min_charge", 5, ConfigType.INTEGER, ConfigCategory.SHIP_BALANCE,
                          "Minimum effective shield charge", min_value=1, max_value=10),
        ]
        
        # Combat Balance Configuration
        combat_configs = [
            # Phaser System
            ConfigParameter("phaser_reload_rate", 10, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Phaser reload rate per tick", min_value=1, max_value=50),
            ConfigParameter("phaser_min_fire", 60, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Minimum energy to fire phaser", min_value=20, max_value=200),
            ConfigParameter("phaser_energy_cost", 57, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Energy cost for phaser charging", min_value=20, max_value=200),
            ConfigParameter("phaser_min_energy", 500, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Minimum energy to fire phaser", min_value=100, max_value=2000),
            ConfigParameter("phaser_bias", 2, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Phaser spread bias for better aim", min_value=0, max_value=10),
            
            # Hyper-Phaser System
            ConfigParameter("hyper_phaser_min_fire", 6000, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Minimum flux energy for hyper-phaser", min_value=2000, max_value=20000),
            ConfigParameter("hyper_phaser_energy_cost", 5000, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Energy cost for hyper-phaser fire", min_value=1000, max_value=15000),
            ConfigParameter("hyper_phaser_beam_width", 5, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Hyper-phaser beam width", min_value=1, max_value=20),
            
            # Weapon Damage Factors
            ConfigParameter("torpedo_damage_factor", 1.5, ConfigType.FLOAT, ConfigCategory.COMBAT_BALANCE,
                          "Torpedo damage multiplier", min_value=0.5, max_value=5.0),
            ConfigParameter("torpedo_max_damage", 100, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Maximum torpedo damage", min_value=25, max_value=500),
            ConfigParameter("missile_damage_factor", 1.5, ConfigType.FLOAT, ConfigCategory.COMBAT_BALANCE,
                          "Missile damage multiplier", min_value=0.5, max_value=5.0),
            ConfigParameter("missile_max_damage", 100, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Maximum missile damage", min_value=25, max_value=500),
            ConfigParameter("ion_cannon_max_damage", 100, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Maximum ion cannon damage", min_value=25, max_value=500),
            ConfigParameter("mine_max_damage", 100, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Maximum mine damage", min_value=25, max_value=500),
            
            # Combat Mechanics
            ConfigParameter("critical_hit_chance", 0.10, ConfigType.FLOAT, ConfigCategory.COMBAT_BALANCE,
                          "Base critical hit chance", min_value=0.01, max_value=0.50),
            ConfigParameter("repair_rate", 0.05, ConfigType.FLOAT, ConfigCategory.COMBAT_BALANCE,
                          "Ship repair rate per tick", min_value=0.01, max_value=0.50),
            ConfigParameter("jammer_time", 10, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Jammer effectiveness duration", min_value=1, max_value=60),
            ConfigParameter("decoy_time", 15, ConfigType.INTEGER, ConfigCategory.COMBAT_BALANCE,
                          "Decoy lifetime in ticks", min_value=5, max_value=60),
            ConfigParameter("too_close_distance", 15000.0, ConfigType.FLOAT, ConfigCategory.COMBAT_BALANCE,
                          "Minimum safe distance between ships", min_value=5000.0, max_value=50000.0),
        ]
        
        # Economic System Configuration
        economic_configs = [
            # Starting Resources
            ConfigParameter("start_cash", 1000000, ConfigType.INTEGER, ConfigCategory.ECONOMIC_SYSTEM,
                          "Starting cash for new players", min_value=100000, max_value=10000000),
            ConfigParameter("start_energy", 50000, ConfigType.INTEGER, ConfigCategory.ECONOMIC_SYSTEM,
                          "Starting energy for new players", min_value=10000, max_value=100000),
            
            # Production Rates
            ConfigParameter("item_production_base_rate", 1.0, ConfigType.FLOAT, ConfigCategory.ECONOMIC_SYSTEM,
                          "Base item production rate", min_value=0.1, max_value=10.0),
            ConfigParameter("planet_population_growth_rate", 0.02, ConfigType.FLOAT, ConfigCategory.ECONOMIC_SYSTEM,
                          "Planet population growth rate", min_value=0.001, max_value=0.1),
            ConfigParameter("planet_tax_rate", 0.05, ConfigType.FLOAT, ConfigCategory.ECONOMIC_SYSTEM,
                          "Planet tax collection rate", min_value=0.01, max_value=0.25),
            
            # Trading
            ConfigParameter("trade_markup_min", 0.10, ConfigType.FLOAT, ConfigCategory.ECONOMIC_SYSTEM,
                          "Minimum trade markup", min_value=0.01, max_value=1.0),
            ConfigParameter("trade_markup_max", 0.50, ConfigType.FLOAT, ConfigCategory.ECONOMIC_SYSTEM,
                          "Maximum trade markup", min_value=0.10, max_value=2.0),
            ConfigParameter("reserve_factor", 0.20, ConfigType.FLOAT, ConfigCategory.ECONOMIC_SYSTEM,
                          "Planet reserve factor for trading", min_value=0.05, max_value=0.80),
        ]
        
        # Scoring System Configuration
        scoring_configs = [
            # Kill Scoring
            ConfigParameter("kill_score_base", 100, ConfigType.INTEGER, ConfigCategory.SCORING_SYSTEM,
                          "Base kill score", min_value=10, max_value=1000),
            ConfigParameter("ship_class_multipliers", {
                "Interceptor": 1.0, "Scout": 1.2, "Fighter": 1.5, "Destroyer": 2.0,
                "Cruiser": 2.5, "Battleship": 3.0, "Dreadnought": 4.0, "Flagship": 5.0,
                "Cyborg": 3.5, "Droid": 2.0
            }, ConfigType.JSON, ConfigCategory.SCORING_SYSTEM, "Ship class kill multipliers"),
            
            # Planet Scoring
            ConfigParameter("planet_population_value", 10, ConfigType.INTEGER, ConfigCategory.SCORING_SYSTEM,
                          "Score per planet population unit", min_value=1, max_value=100),
            ConfigParameter("planet_production_value", 5, ConfigType.INTEGER, ConfigCategory.SCORING_SYSTEM,
                          "Score per planet production unit", min_value=1, max_value=50),
            ConfigParameter("planet_strategic_bonus", 0.2, ConfigType.FLOAT, ConfigCategory.SCORING_SYSTEM,
                          "Strategic planet bonus multiplier", min_value=0.0, max_value=1.0),
            
            # Team Scoring
            ConfigParameter("team_bonus_base", 1000, ConfigType.INTEGER, ConfigCategory.SCORING_SYSTEM,
                          "Base team bonus score", min_value=100, max_value=10000),
            ConfigParameter("team_coordination_bonus", 0.5, ConfigType.FLOAT, ConfigCategory.SCORING_SYSTEM,
                          "Team coordination bonus multiplier", min_value=0.0, max_value=2.0),
        ]
        
        # Game Mechanics Configuration
        mechanics_configs = [
            # Galaxy Settings
            ConfigParameter("galaxy_width", 30, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Galaxy width in sectors", min_value=10, max_value=100),
            ConfigParameter("galaxy_height", 15, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Galaxy height in sectors", min_value=5, max_value=50),
            ConfigParameter("max_planets_per_sector", 9, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Maximum planets per sector", min_value=3, max_value=20),
            ConfigParameter("max_planets_per_player", 9, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Maximum planets per player", min_value=1, max_value=20),
            
            # Wormhole Settings
            ConfigParameter("wormhole_generation_odds", 5, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Wormhole generation odds (1 in X)", min_value=1, max_value=100),
            ConfigParameter("wormhole_stability_base", 0.8, ConfigType.FLOAT, ConfigCategory.GAME_MECHANICS,
                          "Base wormhole stability", min_value=0.1, max_value=1.0),
            
            # Beacon Settings
            ConfigParameter("beacon_max_messages", 100, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Maximum beacon messages", min_value=10, max_value=1000),
            ConfigParameter("beacon_message_size", 75, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Maximum beacon message size", min_value=25, max_value=200),
            
            # Mine Settings
            ConfigParameter("mine_max_count", 20, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Maximum mines in game", min_value=5, max_value=200),
            ConfigParameter("mine_detection_range", 10000, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Mine detection range", min_value=1000, max_value=50000),
            
            # Mail System
            ConfigParameter("mail_retention_days", 7, ConfigType.INTEGER, ConfigCategory.GAME_MECHANICS,
                          "Mail retention period in days", min_value=1, max_value=30),
        ]
        
        # Admin Settings Configuration
        admin_configs = [
            ConfigParameter("game_speed", 1.0, ConfigType.FLOAT, ConfigCategory.ADMIN_SETTINGS,
                          "Game speed multiplier", min_value=0.1, max_value=10.0),
            ConfigParameter("tick_interval", 30, ConfigType.INTEGER, ConfigCategory.ADMIN_SETTINGS,
                          "Game tick interval in seconds", min_value=5, max_value=300),
            ConfigParameter("maintenance_mode", False, ConfigType.BOOLEAN, ConfigCategory.ADMIN_SETTINGS,
                          "Maintenance mode flag", requires_restart=True),
            ConfigParameter("debug_mode", False, ConfigType.BOOLEAN, ConfigCategory.ADMIN_SETTINGS,
                          "Debug mode flag", requires_restart=True),
            ConfigParameter("max_players", 100, ConfigType.INTEGER, ConfigCategory.ADMIN_SETTINGS,
                          "Maximum concurrent players", min_value=10, max_value=1000),
        ]
        
        # Combine all configurations
        all_configs = (ship_configs + combat_configs + economic_configs + 
                      scoring_configs + mechanics_configs + admin_configs)
        
        for config in all_configs:
            self._config[config.key] = config
            if config.default_value is None:
                config.default_value = config.value
    
    def get_config(self, key: str) -> Any:
        """Get configuration value by key"""
        if key not in self._config:
            raise ValueError(f"Configuration key '{key}' not found")
        return self._config[key].value
    
    def set_config(self, key: str, value: Any, admin_user: str = "system") -> bool:
        """Set configuration value with validation and history tracking"""
        if key not in self._config:
            raise ValueError(f"Configuration key '{key}' not found")
        
        config = self._config[key]
        
        # Validate value type and range
        if not self._validate_config_value(config, value):
            return False
        
        # Store old value for history
        old_value = config.value
        
        # Update configuration
        config.value = value
        
        # Log configuration change
        self._log_config_change(key, old_value, value, admin_user)
        
        logger.info(f"Configuration updated: {key} = {value} (by {admin_user})")
        return True
    
    def _validate_config_value(self, config: ConfigParameter, value: Any) -> bool:
        """Validate configuration value"""
        # Type validation
        if config.config_type == ConfigType.INTEGER:
            if not isinstance(value, int):
                return False
        elif config.config_type == ConfigType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
        elif config.config_type == ConfigType.BOOLEAN:
            if not isinstance(value, bool):
                return False
        elif config.config_type == ConfigType.STRING:
            if not isinstance(value, str):
                return False
        elif config.config_type == ConfigType.JSON:
            if not isinstance(value, (dict, list)):
                return False
        
        # Range validation
        if config.min_value is not None:
            if isinstance(value, (int, float)) and value < config.min_value:
                return False
        if config.max_value is not None:
            if isinstance(value, (int, float)) and value > config.max_value:
                return False
        
        # Custom validation
        if config.validation_func and not config.validation_func(value):
            return False
        
        return True
    
    def _log_config_change(self, key: str, old_value: Any, new_value: Any, admin_user: str):
        """Log configuration change to history"""
        change_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "admin_user": admin_user
        }
        self._config_history.append(change_record)
        
        # Keep only last 1000 changes
        if len(self._config_history) > 1000:
            self._config_history = self._config_history[-1000:]
    
    def get_config_by_category(self, category: ConfigCategory) -> Dict[str, ConfigParameter]:
        """Get all configurations in a category"""
        return {k: v for k, v in self._config.items() if v.category == category}
    
    def get_all_configs(self) -> Dict[str, ConfigParameter]:
        """Get all configurations"""
        return self._config.copy()
    
    def get_config_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        return self._config_history[-limit:]
    
    def reset_to_default(self, key: str, admin_user: str = "system") -> bool:
        """Reset configuration to default value"""
        if key not in self._config:
            return False
        
        config = self._config[key]
        if config.default_value is None:
            return False
        
        return self.set_config(key, config.default_value, admin_user)
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration as JSON-serializable dict"""
        return {
            key: {
                "value": config.value,
                "type": config.config_type.value,
                "category": config.category.value,
                "description": config.description,
                "min_value": config.min_value,
                "max_value": config.max_value,
                "default_value": config.default_value,
                "requires_restart": config.requires_restart
            }
            for key, config in self._config.items()
        }
    
    def import_config(self, config_data: Dict[str, Any], admin_user: str = "system") -> List[str]:
        """Import configuration from JSON-serializable dict"""
        errors = []
        success_count = 0
        
        for key, config_info in config_data.items():
            try:
                if key in self._config:
                    # Update existing configuration
                    if self.set_config(key, config_info["value"], admin_user):
                        success_count += 1
                    else:
                        errors.append(f"Failed to set {key}: validation failed")
                else:
                    errors.append(f"Unknown configuration key: {key}")
            except Exception as e:
                errors.append(f"Error setting {key}: {str(e)}")
        
        logger.info(f"Configuration import completed: {success_count} successful, {len(errors)} errors")
        return errors


# Global configuration instance
game_config = GameConfiguration()


def get_game_config() -> GameConfiguration:
    """Get the global game configuration instance"""
    return game_config


def get_config_value(key: str) -> Any:
    """Convenience function to get configuration value"""
    return game_config.get_config(key)


def set_config_value(key: str, value: Any, admin_user: str = "system") -> bool:
    """Convenience function to set configuration value"""
    return game_config.set_config(key, value, admin_user)
