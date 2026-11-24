"""Añadir rol de autorización a cuentas existentes (todos siguen siendo usuarios)."""
from alembic import op
import sqlalchemy as sa

revision = "002_admin_role"
down_revision = "001_accounts"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("role", sa.String(16), server_default="user", nullable=False))


def downgrade():
    op.drop_column("users", "role")
