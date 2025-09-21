"""Add ship types and ship classes tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_ship_types_and_classes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create ship_types table
    op.create_table('ship_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type_name', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ship_types_id'), 'ship_types', ['id'], unique=False)
    op.create_index(op.f('ix_ship_types_type_name'), 'ship_types', ['type_name'], unique=True)
    
    # Create ship_classes table
    op.create_table('ship_classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_number', sa.Integer(), nullable=False),
        sa.Column('typename', sa.String(length=50), nullable=False),
        sa.Column('shipname', sa.String(length=50), nullable=False),
        sa.Column('ship_type_id', sa.Integer(), nullable=False),
        sa.Column('max_shields', sa.Integer(), nullable=True, default=0),
        sa.Column('max_phasers', sa.Integer(), nullable=True, default=0),
        sa.Column('max_torpedoes', sa.Integer(), nullable=True, default=0),
        sa.Column('max_missiles', sa.Integer(), nullable=True, default=0),
        sa.Column('has_decoy', sa.Boolean(), nullable=True, default=False),
        sa.Column('has_jammer', sa.Boolean(), nullable=True, default=False),
        sa.Column('has_zipper', sa.Boolean(), nullable=True, default=False),
        sa.Column('has_mine', sa.Boolean(), nullable=True, default=False),
        sa.Column('has_attack_planet', sa.Boolean(), nullable=True, default=False),
        sa.Column('has_cloaking', sa.Boolean(), nullable=True, default=False),
        sa.Column('max_acceleration', sa.Integer(), nullable=True, default=0),
        sa.Column('max_warp', sa.Integer(), nullable=True, default=0),
        sa.Column('max_tons', sa.BigInteger(), nullable=True, default=0),
        sa.Column('max_price', sa.BigInteger(), nullable=True, default=0),
        sa.Column('max_points', sa.Integer(), nullable=True, default=0),
        sa.Column('scan_range', sa.Integer(), nullable=True, default=0),
        sa.Column('cybs_can_attack', sa.Boolean(), nullable=True, default=True),
        sa.Column('number_to_attack', sa.Integer(), nullable=True, default=0),
        sa.Column('lowest_to_attack', sa.Integer(), nullable=True, default=1),
        sa.Column('no_claim', sa.Boolean(), nullable=True, default=False),
        sa.Column('total_to_create', sa.Integer(), nullable=True, default=0),
        sa.Column('tough_factor', sa.Integer(), nullable=True, default=0),
        sa.Column('damage_factor', sa.Integer(), nullable=True, default=90),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('help_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ship_type_id'], ['ship_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ship_classes_id'), 'ship_classes', ['id'], unique=False)
    op.create_index(op.f('ix_ship_classes_class_number'), 'ship_classes', ['class_number'], unique=False)
    
    # Add foreign key constraint to ships table
    op.add_column('ships', sa.Column('ship_class_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key('fk_ships_ship_class_id', 'ships', 'ship_classes', ['ship_class_id'], ['id'])


def downgrade():
    # Remove foreign key constraint from ships table
    op.drop_constraint('fk_ships_ship_class_id', 'ships', type_='foreignkey')
    op.drop_column('ships', 'ship_class_id')
    
    # Drop ship_classes table
    op.drop_index(op.f('ix_ship_classes_class_number'), table_name='ship_classes')
    op.drop_index(op.f('ix_ship_classes_id'), table_name='ship_classes')
    op.drop_table('ship_classes')
    
    # Drop ship_types table
    op.drop_index(op.f('ix_ship_types_type_name'), table_name='ship_types')
    op.drop_index(op.f('ix_ship_types_id'), table_name='ship_types')
    op.drop_table('ship_types')


