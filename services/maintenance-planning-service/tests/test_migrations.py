import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


SERVICE_DIR = Path(__file__).resolve().parents[1]
EXPECTED_REVISION = "bfa900fd755e"


def test_fresh_database_can_be_initialized_with_alembic(tmp_path):
    database_path = tmp_path / "planning_migration_test.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=SERVICE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"Alembic falló.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "maintenance_rules" in tables
        assert "maintenance_tasks" in tables
        assert "alembic_version" in tables

        foreign_keys = inspector.get_foreign_keys("maintenance_tasks")
        assert any(
            fk["constrained_columns"] == ["rule_id"]
            and fk["referred_table"] == "maintenance_rules"
            and fk["referred_columns"] == ["id"]
            for fk in foreign_keys
        )

        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()

        assert revision == EXPECTED_REVISION

    finally:
        engine.dispose()