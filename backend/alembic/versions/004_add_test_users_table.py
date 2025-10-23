"""Add test users table

Revision ID: 004_add_test_users
Revises: 003_add_usage_logs
Create Date: 2025-01-23 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_test_users'
down_revision = '003_add_usage_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_users table
    op.create_table('test_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('age_group', sa.String(length=20), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('recruitment_channel', sa.Enum('online_community', 'online_ad', 'partnership', 'offline', 'referral', 'other', name='recruitmentchannel'), nullable=False),
        sa.Column('recruitment_details', sa.String(length=200), nullable=True),
        sa.Column('status', sa.Enum('invited', 'confirmed', 'in_progress', 'completed', 'rewarded', 'cancelled', name='participationstatus'), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rewarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feedback_count', sa.Integer(), nullable=True),
        sa.Column('average_rating', sa.Integer(), nullable=True),
        sa.Column('reward_type', sa.String(length=50), nullable=True),
        sa.Column('reward_amount', sa.Integer(), nullable=True),
        sa.Column('reward_sent', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='mlops'
    )
    
    # Create indexes
    op.create_index(op.f('ix_mlops_test_users_id'), 'test_users', ['id'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_test_users_email'), 'test_users', ['email'], unique=True, schema='mlops')
    op.create_index(op.f('ix_mlops_test_users_status'), 'test_users', ['status'], unique=False, schema='mlops')


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_mlops_test_users_status'), table_name='test_users', schema='mlops')
    op.drop_index(op.f('ix_mlops_test_users_email'), table_name='test_users', schema='mlops')
    op.drop_index(op.f('ix_mlops_test_users_id'), table_name='test_users', schema='mlops')
    
    # Drop table
    op.drop_table('test_users', schema='mlops')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS mlops.recruitmentchannel')
    op.execute('DROP TYPE IF EXISTS mlops.participationstatus')
