"""initial schema for ships planets sectors users

Revision ID: e671003de52c
Revises: 
Create Date: 2026-09-13 15:41:53.265875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e671003de52c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('cash', sa.Integer(), nullable=True),
        sa.Column('kills', sa.Integer(), nullable=True),
        sa.Column('planets_owned', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )

    # Create sectors table
    op.create_table(
        'sectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shard_id', sa.String(), nullable=False),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('wormhole_target_id', sa.Integer(), nullable=True),
        sa.Column('planet_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['wormhole_target_id'], ['sectors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create planets table
    op.create_table(
        'planets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('treasury', sa.Integer(), nullable=True),
        sa.Column('tax_rate', sa.Float(), nullable=True),
        sa.Column('production_rates', sa.JSON(), nullable=True),
        sa.Column('item_stocks', sa.JSON(), nullable=True),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.Column('is_safe_harbor', sa.Integer(), nullable=True),
        sa.Column('safe_harbor_rent', sa.Integer(), nullable=True),
        sa.Column('npc_defender_count', sa.Integer(), nullable=True),
        sa.Column('npc_defender_strength', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ships table
    op.create_table(
        'ships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('class_type', sa.String(), nullable=False),
        sa.Column('position_x', sa.Integer(), nullable=False),
        sa.Column('position_y', sa.Integer(), nullable=False),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('damage', sa.Float(), nullable=True),
        sa.Column('energy', sa.Float(), nullable=True),
        sa.Column('shields', sa.Float(), nullable=True),
        sa.Column('cargo', sa.JSON(), nullable=True),
        sa.Column('is_docked', sa.Integer(), nullable=True),
        sa.Column('docked_planet_id', sa.Integer(), nullable=True),
        sa.Column('insurance_active', sa.Integer(), nullable=True),
        sa.Column('insurance_expiry', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['docked_planet_id'], ['planets.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ships')
    op.drop_table('planets')
    op.drop_table('sectors')
    op.drop_table('users')
    op.drop_table('teams')
