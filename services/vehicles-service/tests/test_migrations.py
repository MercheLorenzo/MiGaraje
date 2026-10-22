import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


SERVICE_DIR = Path(__file__).resolve().parents[1]


def test_fresh_database_can_be_initialized_with_alembic(tmp_path):
    database_path = tmp_path / "vehicles_migration_test.db"
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

        assert "vehicles" in tables
        assert "alembic_version" in tables

        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()

        assert revision == "525b7cab1097"
    finally:
        engine.dispose()
