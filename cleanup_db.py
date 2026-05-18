import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env if exists (for local testing)
load_dotenv()

# Get DATABASE_URL from environment
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ ERROR: DATABASE_URL not found in environment variables.")
    exit(1)

# Handle Render's 'postgres://' prefix
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        print("🔄 Cleaning up database tables...")
        
        # Disable foreign key checks for truncation (PostgreSQL specific)
        conn.execute(text("TRUNCATE TABLE users, tasks, daily_scores RESTART IDENTITY CASCADE;"))
        conn.commit()
        
        print("✅ SUCCESS: All user accounts and data have been cleared.")
        print("🚀 You can now create a fresh account from the app.")

except Exception as e:
    print(f"❌ ERROR: Could not clean database: {e}")
