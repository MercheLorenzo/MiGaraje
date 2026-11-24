"""Additional maintenance costs and parts; Revision ID: 002_maintenance_details"""
from alembic import op
import sqlalchemy as sa
revision="002_maintenance_details";down_revision="6025108d0968";branch_labels=None;depends_on=None
def upgrade():
    op.add_column("maintenances",sa.Column("workshop",sa.String(120)))
    op.add_column("maintenances",sa.Column("parts_cost",sa.Numeric(10,2)))
    op.add_column("maintenances",sa.Column("labor_cost",sa.Numeric(10,2)))
    op.add_column("maintenances",sa.Column("part_brand",sa.String(120)))
    op.add_column("maintenances",sa.Column("part_model",sa.String(120)))
    op.add_column("maintenances",sa.Column("notes",sa.Text()))
def downgrade():
    for col in ("notes","part_model","part_brand","labor_cost","parts_cost","workshop"):
        op.drop_column("maintenances",col)
