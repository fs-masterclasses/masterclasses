"""Make Masterclass.max_attendees field nullable

Revision ID: b75eebbb2d5e
Revises: 668309119649
Create Date: 2020-05-05 16:34:55.267941

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b75eebbb2d5e'
down_revision = '668309119649'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('masterclass', 'max_attendees',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('masterclass', 'max_attendees',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
