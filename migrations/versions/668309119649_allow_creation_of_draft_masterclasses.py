"""Allow creation of draft masterclasses

Revision ID: 668309119649
Revises: bcd3cfe07b70
Create Date: 2020-05-04 20:28:18.243511

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '668309119649'
down_revision = 'bcd3cfe07b70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('masterclass', sa.Column('draft', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('masterclass', 'draft')
    # ### end Alembic commands ###