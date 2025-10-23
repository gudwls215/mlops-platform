"""Add feedback table

Revision ID: 002_add_feedback
Revises: 001_initial_migration
Create Date: 2025-01-23 15:45:44.004025

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_feedback'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feedbacks table
    op.create_table('feedbacks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('user_name', sa.String(length=100), nullable=True),
        sa.Column('user_email', sa.String(length=200), nullable=True),
        sa.Column('user_age_group', sa.String(length=20), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('related_resume_id', sa.Integer(), nullable=True),
        sa.Column('related_job_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='mlops'
    )
    
    # Create indexes
    op.create_index(op.f('ix_mlops_feedbacks_id'), 'feedbacks', ['id'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_feedbacks_feedback_type'), 'feedbacks', ['feedback_type'], unique=False, schema='mlops')
    op.create_index(op.f('ix_mlops_feedbacks_created_at'), 'feedbacks', ['created_at'], unique=False, schema='mlops')


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_mlops_feedbacks_created_at'), table_name='feedbacks', schema='mlops')
    op.drop_index(op.f('ix_mlops_feedbacks_feedback_type'), table_name='feedbacks', schema='mlops')
    op.drop_index(op.f('ix_mlops_feedbacks_id'), table_name='feedbacks', schema='mlops')
    
    # Drop table
    op.drop_table('feedbacks', schema='mlops')
