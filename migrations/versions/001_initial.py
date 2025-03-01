"""Initial database migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-03-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user table
    op.create_table(
        'user',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('api_key', sa.String(), nullable=True, unique=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create admin table
    op.create_table(
        'admin',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('can_manage_merchants', sa.Boolean(), nullable=False, default=True),
        sa.Column('can_verify_transactions', sa.Boolean(), nullable=False, default=True),
        sa.Column('can_export_reports', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create merchant table
    op.create_table(
        'merchant',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('business_name', sa.String(), nullable=False),
        sa.Column('business_type', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('callback_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('whitelist_ips', postgresql.JSONB(), nullable=True),
        sa.Column('bank_details', postgresql.JSONB(), nullable=True),
        sa.Column('upi_details', postgresql.JSONB(), nullable=True),
        sa.Column('min_deposit', sa.Integer(), nullable=False, default=500),
        sa.Column('max_deposit', sa.Integer(), nullable=False, default=300000),
        sa.Column('min_withdrawal', sa.Integer(), nullable=False, default=1000),
        sa.Column('max_withdrawal', sa.Integer(), nullable=False, default=1000000),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create payment table
    op.create_table(
        'payment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('merchant.id'), nullable=False),
        sa.Column('reference', sa.String(), nullable=False, index=True),
        sa.Column('trxn_hash_key', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('payment_type', sa.Enum('DEPOSIT', 'WITHDRAWAL', name='payment_type'), nullable=False),
        sa.Column('payment_method', sa.Enum('UPI', 'BANK_TRANSFER', name='payment_method'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, default='INR'),
        sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'DECLINED', 'EXPIRED', name='payment_status'), 
                 nullable=False, default='PENDING'),
        sa.Column('upi_id', sa.String(), nullable=True),
        sa.Column('qr_code_data', sa.Text(), nullable=True),
        sa.Column('bank_name', sa.String(), nullable=True),
        sa.Column('account_name', sa.String(), nullable=True),
        sa.Column('account_number', sa.String(), nullable=True),
        sa.Column('ifsc_code', sa.String(), nullable=True),
        sa.Column('utr_number', sa.String(), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('verification_method', sa.String(), nullable=True),
        sa.Column('user_data', postgresql.JSONB(), nullable=True),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(), nullable=True),
        sa.Column('callback_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes
    op.create_index('ix_payment_status', 'payment', ['status'])
    op.create_index('ix_payment_payment_type', 'payment', ['payment_type'])
    op.create_index('ix_payment_created_at', 'payment', ['created_at'])
    op.create_index('ix_payment_utr_number', 'payment', ['utr_number'])


def downgrade():
    op.drop_table('payment')
    op.drop_table('merchant')
    op.drop_table('admin')
    op.drop_table('user')
    
    # Drop enum types
    op.execute("DROP TYPE payment_type")
    op.execute("DROP TYPE payment_method")
    op.execute("DROP TYPE payment_status")