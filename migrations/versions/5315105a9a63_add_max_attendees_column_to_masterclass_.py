"""Add max_attendees column to masterclass table

Revision ID: 5315105a9a63
Revises: 8ef412805e7c
Create Date: 2020-01-13 22:03:46.854543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5315105a9a63'
down_revision = '8ef412805e7c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('masterclass', sa.Column('max_attendees', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('masterclass', 'max_attendees')
    # ### end Alembic commands ###
