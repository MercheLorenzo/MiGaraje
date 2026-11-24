from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config,pool
from app.core.config import settings
from app.db.session import Base
from app.models.account import User,VehicleOwner
config=context.config
config.set_main_option("sqlalchemy.url",settings.database_url.replace("%","%%"))
target_metadata=Base.metadata

def offline():
    context.configure(url=settings.database_url,target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()

def online():
    engine=engine_from_config(config.get_section(config.config_ini_section),prefix="sqlalchemy.",poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata)
        with context.begin_transaction():context.run_migrations()
if context.is_offline_mode():offline()
else:online()
