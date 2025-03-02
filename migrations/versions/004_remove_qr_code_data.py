"""remove qr_code_data

Revision ID: 004
Revises: 003
Create Date: 2024-03-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Drop qr_code_data column from payment table
    op.drop_column('payment', 'qr_code_data')


def downgrade():
    # Add back qr_code_data column
    op.add_column('payment', sa.Column('qr_code_data', sa.Text(), nullable=True)) 