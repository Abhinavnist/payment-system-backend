"""Add report analytics table

Revision ID: 002_add_report_analytics
Revises: 001_initial
Create Date: 2024-03-01 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_report_analytics'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Create report_analytics table
    op.create_table(
        'report_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_transactions', sa.Integer(), default=0),
        sa.Column('successful_transactions', sa.Integer(), default=0),
        sa.Column('failed_transactions', sa.Integer(), default=0),
        sa.Column('pending_transactions', sa.Integer(), default=0),
        sa.Column('total_amount', sa.Integer(), default=0),
        sa.Column('successful_amount', sa.Integer(), default=0),
        sa.Column('failed_amount', sa.Integer(), default=0),
        sa.Column('pending_amount', sa.Integer(), default=0),
        sa.Column('deposit_count', sa.Integer(), default=0),
        sa.Column('withdrawal_count', sa.Integer(), default=0),
        sa.Column('deposit_amount', sa.Integer(), default=0),
        sa.Column('withdrawal_amount', sa.Integer(), default=0),
        sa.Column('payment_method_stats', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('success_rate', sa.Integer(), default=0),
        sa.Column('avg_processing_time', sa.Integer(), default=0),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('is_final', sa.Boolean(), default=False),
        sa.Column('generated_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchant.id'], ),
    )
    op.create_index(
        'ix_report_analytics_merchant_id', 
        'report_analytics', 
        ['merchant_id']
    )
    op.create_index(
        'ix_report_analytics_period_start_end', 
        'report_analytics', 
        ['period_start', 'period_end']
    )


def downgrade():
    op.drop_index('ix_report_analytics_period_start_end')
    op.drop_index('ix_report_analytics_merchant_id')
    op.drop_table('report_analytics') 