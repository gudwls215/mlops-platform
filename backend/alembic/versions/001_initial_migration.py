"""Initial migration with all models

Revision ID: 001_initial_migration
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in mlops schema"""
    
    # Create mlops schema if it doesn't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS mlops")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        schema='mlops'
    )
    
    # Create index on email
    op.create_index('ix_mlops_users_email', 'users', ['email'], unique=True, schema='mlops')
    
    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('education', sa.Text(), nullable=True),
        sa.Column('certifications', sa.Text(), nullable=True),
        sa.Column('career_summary', sa.Text(), nullable=True),
        sa.Column('generated_by_ai', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['mlops.users.id'], ondelete='CASCADE'),
        schema='mlops'
    )
    
    # Create indexes for resumes
    op.create_index('ix_mlops_resumes_user_id', 'resumes', ['user_id'], schema='mlops')
    op.create_index('ix_mlops_resumes_title', 'resumes', ['title'], schema='mlops')
    
    # Create job_postings table
    op.create_table(
        'job_postings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('company', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=False),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('employment_type', sa.String(50), nullable=True),
        sa.Column('experience_level', sa.String(50), nullable=True),
        sa.Column('skills_required', sa.Text(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='mlops'
    )
    
    # Create indexes for job_postings
    op.create_index('ix_mlops_job_postings_title', 'job_postings', ['title'], schema='mlops')
    op.create_index('ix_mlops_job_postings_company', 'job_postings', ['company'], schema='mlops')
    op.create_index('ix_mlops_job_postings_location', 'job_postings', ['location'], schema='mlops')
    
    # Create cover_letters table
    op.create_table(
        'cover_letters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_posting_id', sa.Integer(), nullable=True),
        sa.Column('resume_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('generated_by_ai', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['mlops.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_posting_id'], ['mlops.job_postings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resume_id'], ['mlops.resumes.id'], ondelete='SET NULL'),
        schema='mlops'
    )
    
    # Create indexes for cover_letters
    op.create_index('ix_mlops_cover_letters_user_id', 'cover_letters', ['user_id'], schema='mlops')
    op.create_index('ix_mlops_cover_letters_job_posting_id', 'cover_letters', ['job_posting_id'], schema='mlops')
    
    # Create prediction_logs table
    op.create_table(
        'prediction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=True),
        sa.Column('job_posting_id', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('prediction_score', sa.Float(), nullable=False),
        sa.Column('prediction_result', sa.JSON(), nullable=True),
        sa.Column('input_features', sa.JSON(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['mlops.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['mlops.resumes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_posting_id'], ['mlops.job_postings.id'], ondelete='SET NULL'),
        schema='mlops'
    )
    
    # Create indexes for prediction_logs
    op.create_index('ix_mlops_prediction_logs_user_id', 'prediction_logs', ['user_id'], schema='mlops')
    op.create_index('ix_mlops_prediction_logs_model_name', 'prediction_logs', ['model_name'], schema='mlops')
    op.create_index('ix_mlops_prediction_logs_created_at', 'prediction_logs', ['created_at'], schema='mlops')
    
    # Create job_applications table (새로운 테이블)
    op.create_table(
        'job_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_posting_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('cover_letter_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='applied'),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['mlops.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_posting_id'], ['mlops.job_postings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['mlops.resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cover_letter_id'], ['mlops.cover_letters.id'], ondelete='SET NULL'),
        schema='mlops'
    )
    
    # Create indexes for job_applications
    op.create_index('ix_mlops_job_applications_user_id', 'job_applications', ['user_id'], schema='mlops')
    op.create_index('ix_mlops_job_applications_status', 'job_applications', ['status'], schema='mlops')
    op.create_index('ix_mlops_job_applications_applied_at', 'job_applications', ['applied_at'], schema='mlops')


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('job_applications', schema='mlops')
    op.drop_table('prediction_logs', schema='mlops')
    op.drop_table('cover_letters', schema='mlops')
    op.drop_table('job_postings', schema='mlops')
    op.drop_table('resumes', schema='mlops')
    op.drop_table('users', schema='mlops')
    
    # Drop schema if empty
    op.execute("DROP SCHEMA IF EXISTS mlops")