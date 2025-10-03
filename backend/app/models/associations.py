"""
Association tables for many-to-many relationships
"""

from sqlalchemy import Column, Integer, ForeignKey, Table, Boolean
from .base import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# Association table for planet items
planet_items = Table(
    'planet_items',
    Base.metadata,
    Column('planet_id', Integer, ForeignKey('planets.id'), primary_key=True),
    Column('item_id', Integer, ForeignKey('items.id'), primary_key=True),
    Column('quantity', Integer, default=0),
    Column('rate', Integer, default=0),  # rate of manufacture
    Column('sell_to_allies', Boolean, default=False),
    Column('reserve', Integer, default=0),
    Column('markup_to_allies', Integer, default=0),
    Column('sold_to_allies', Integer, default=0),
)
