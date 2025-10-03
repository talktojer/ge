"""
Database models for Galactic Empire
"""

from .base import Base
from .associations import user_roles, role_permissions, planet_items
from .role import Role, Permission, UserPermission, APIKey
from .user import User, UserAccount, UserToken, UserSession
from .ship import Ship, ShipClass, ShipType
from .planet import Planet, Sector, PlanetItem
from .team import Team
from .mail import Mail, MailStatus
from .item import Item, ItemType
from .mine import Mine
from .beacon import Beacon
from .wormhole import Wormhole, WormholeTable
from .config import (
    GameConfig, ConfigHistory, ConfigVersion, BalanceAdjustment,
    PlayerScore, PlayerAchievement, TeamScore, GameStatistics, BalanceReport
)

__all__ = [
    "Base",
    "user_roles",
    "role_permissions",
    "planet_items",
    "Role",
    "Permission",
    "UserPermission",
    "APIKey",
    "User",
    "UserAccount",
    "UserToken",
    "UserSession", 
    "Ship",
    "ShipClass",
    "ShipType",
    "Planet",
    "Sector",
    "PlanetItem",
    "Team",
    "Mail",
    "MailStatus",
    "Item",
    "ItemType",
    "Mine",
    "Beacon",
    "Wormhole",
    "WormholeTable",
    "GameConfig",
    "ConfigHistory",
    "ConfigVersion",
    "BalanceAdjustment",
    "PlayerScore",
    "PlayerAchievement",
    "TeamScore",
    "GameStatistics",
    "BalanceReport",
]
