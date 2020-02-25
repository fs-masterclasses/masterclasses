"""Passwords can be null before registration

Revision ID: 0ebeb48ca191
Revises: c5ad5402448d
Create Date: 2020-02-08 16:32:53.532818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ebeb48ca191'
down_revision = 'c5ad5402448d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('draft', sa.Boolean(), nullable=True))
    op.alter_column('user', 'password_hash',
               existing_type=sa.VARCHAR(length=128),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'password_hash',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)
    op.drop_column('user', 'draft')
    # ### end Alembic commands ###