"""Create notifications and preferences. Revision ID: 001_notifications"""
from alembic import op
import sqlalchemy as sa
revision="001_notifications";down_revision=None;branch_labels=None;depends_on=None
def upgrade():
    op.create_table("notification_preferences",sa.Column("user_id",sa.Integer(),primary_key=True),sa.Column("email_enabled",sa.Boolean(),nullable=False),sa.Column("reminder_offsets",sa.String(100),nullable=False),sa.Column("test_sent_at",sa.DateTime(timezone=True)))
    op.create_table("notifications",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),nullable=False),sa.Column("task_id",sa.Integer(),nullable=False),sa.Column("vehicle_id",sa.Integer(),nullable=False),sa.Column("dedupe_key",sa.String(160),nullable=False),sa.Column("title",sa.String(160),nullable=False),sa.Column("body",sa.Text(),nullable=False),sa.Column("level",sa.String(20),nullable=False),sa.Column("is_read",sa.Boolean(),nullable=False),sa.Column("email_status",sa.String(32),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("dedupe_key"))
    op.create_index("ix_notifications_user_id","notifications",["user_id"])
def downgrade():
    op.drop_index("ix_notifications_user_id",table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("notification_preferences")
