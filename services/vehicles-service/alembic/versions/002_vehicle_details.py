"""Additional vehicle details; Revision ID: 002_vehicle_details"""
from alembic import op
import sqlalchemy as sa
revision="002_vehicle_details";down_revision="525b7cab1097";branch_labels=None;depends_on=None
def upgrade():
    op.add_column("vehicles",sa.Column("vehicle_type",sa.String(32),nullable=False,server_default="car"))
    op.add_column("vehicles",sa.Column("fuel_type",sa.String(32)))
    op.add_column("vehicles",sa.Column("registration_date",sa.Date()))
    op.add_column("vehicles",sa.Column("nickname",sa.String(80)))
    op.add_column("vehicles",sa.Column("notes",sa.Text()))
def downgrade():
    for col in ("notes","nickname","registration_date","fuel_type","vehicle_type"):
        op.drop_column("vehicles",col)
