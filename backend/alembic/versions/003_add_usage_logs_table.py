"""Add usage logs table

Revision ID: 003_add_usage_logs
Revises: 002_add_feedback
Create Date: 2025-01-23 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_usage_logs'
down_revision = '002_add_feedback'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create usage_logs table
    op.create_table('usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('client_ip', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('is_error', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('request_size', sa.Integer(), nullable=True),
        sa.Column('response_size', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='mlops'
    )
    
    # Create indexes
    op.create_index(op.f('ix_mlops_usage_logs_id'), 'usage_logs', ['id'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_usage_logs_endpoint'), 'usage_logs', ['endpoint'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_usage_logs_status_code'), 'usage_logs', ['status_code'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_usage_logs_is_error'), 'usage_logs', ['is_error'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_usage_logs_created_at'), 'usage_logs', ['created_at'], unique=False, schema='mlops')


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_mlops_usage_logs_created_at'), table_name='usage_logs', schema='mlops')
    op.drop_index(op.f('ix_mlops_usage_logs_is_error'), table_name='usage_logs', schema='mlops')
    op.drop_index(op.f('ix_mlops_usage_logs_status_code'), table_name='usage_logs', schema='mlops')
    op.drop_index(op.f('ix_mlops_usage_logs_endpoint'), table_name='usage_logs', schema='mlops')
    op.drop_index(op.f('ix_mlops_usage_logs_id'), table_name='usage_logs', schema='mlops')
    
    # Drop table
    op.drop_table('usage_logs', schema='mlops')
