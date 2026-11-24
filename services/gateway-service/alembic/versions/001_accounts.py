"""Create users and vehicle ownership. Revision ID: 001_accounts"""
from alembic import op
import sqlalchemy as sa
revision="001_accounts"
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("users",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("email",sa.String(254),nullable=False),sa.Column("full_name",sa.String(120),nullable=False),sa.Column("password_hash",sa.String(512),nullable=False),sa.Column("token_version",sa.Integer(),nullable=False,server_default="0"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("email"))
    op.create_index("ix_users_email","users",["email"])
    op.create_table("vehicle_owners",sa.Column("vehicle_id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False))
    op.create_index("ix_vehicle_owners_user_id","vehicle_owners",["user_id"])
def downgrade():
    op.drop_table("vehicle_owners")
    op.drop_index("ix_users_email",table_name="users")
    op.drop_table("users")
