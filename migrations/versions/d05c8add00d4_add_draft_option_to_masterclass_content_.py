"""Add draft option to Masterclass Content model

Revision ID: d05c8add00d4
Revises: bcd3cfe07b70
Create Date: 2020-05-04 20:17:02.547891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd05c8add00d4'
down_revision = 'bcd3cfe07b70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('masterclass_content', sa.Column('draft', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('masterclass_content', 'draft')
    # ### end Alembic commands ###
