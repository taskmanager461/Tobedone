from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import get_settings

settings = get_settings()
DATABASE_URL = settings.pg_url

# Log database type (safely)
if DATABASE_URL.startswith("sqlite"):
    print("Using SQLite database")
else:
    print(f"Using PostgreSQL database at {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'unknown'}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
except Exception as e:
    print(f"Error creating engine: {e}")
    # Fallback to sqlite if engine creation fails
    engine = create_engine("sqlite:///./fallback.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "tasks" in table_names:
            task_columns = {col["name"] for col in inspector.get_columns("tasks")}
            if "goal_id" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN goal_id INTEGER"))
            if "xp_awarded" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN xp_awarded BOOLEAN NOT NULL DEFAULT 0"))

        if "goals" in table_names:
            goal_columns = {col["name"] for col in inspector.get_columns("goals")}
            if "xp_awarded" not in goal_columns:
                connection.execute(text("ALTER TABLE goals ADD COLUMN xp_awarded BOOLEAN NOT NULL DEFAULT 0"))

        if "users" in table_names:
            user_columns = {col["name"] for col in inspector.get_columns("users")}
            if "supabase_id" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN supabase_id VARCHAR(64)"))
            if "total_xp" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN total_xp INTEGER NOT NULL DEFAULT 0"))
            if "level" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN level INTEGER NOT NULL DEFAULT 1"))
            if "trust_score" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN trust_score FLOAT NOT NULL DEFAULT 0"))
