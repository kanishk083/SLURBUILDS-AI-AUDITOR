from alembic import context
from sqlalchemy import create_engine, pool
from backend.models import Base
from backend.config import settings

url = settings().database_url.replace("+asyncpg", "+psycopg")
engine = create_engine(url, poolclass=pool.NullPool)
with engine.connect() as connection:
    connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
    connection.commit()
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
