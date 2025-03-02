"""add payment link fields

Revision ID: 003_add_payment_link_fields
Revises: 002_add_report_analytics
Create Date: 2024-03-01 16:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_payment_link_fields'
down_revision = '002_add_report_analytics'
branch_labels = None
depends_on = None


def upgrade():
    # Create PaymentLink table first
    op.create_table(
        'paymentlink',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchant.id'], ),
    )

    # Add new columns to Payment table
    op.add_column('payment', sa.Column('payment_link_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('payment', sa.Column('customer_email', sa.String(), nullable=True))
    op.add_column('payment', sa.Column('customer_phone', sa.String(), nullable=True))
    op.add_column('payment', sa.Column('customer_name', sa.String(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(None, 'payment', 'paymentlink', ['payment_link_id'], ['id'])


def downgrade():
    # Remove foreign key constraint first
    op.drop_constraint(None, 'payment', type_='foreignkey')
    
    # Remove columns from Payment table
    op.drop_column('payment', 'customer_name')
    op.drop_column('payment', 'customer_phone')
    op.drop_column('payment', 'customer_email')
    op.drop_column('payment', 'payment_link_id')
    
    # Drop PaymentLink table
    op.drop_table('paymentlink') 