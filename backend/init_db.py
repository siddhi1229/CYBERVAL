import sys
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import get_settings
from app.database import Base, check_db_health, engine
from app import models  # noqa: F401


def init_db() -> None:
    settings = get_settings()
    raw_url = settings.sync_database_url

    # Safe display of database host/endpoint without password
    if "@" in raw_url:
        prefix, rest = raw_url.split("@", 1)
        proto = prefix.split("://", 1)[0] if "://" in prefix else "postgresql"
        safe_url = f"{proto}://***:***@{rest}"
    else:
        safe_url = raw_url

    print(f"Connecting to database at {safe_url}...")

    health = check_db_health()
    if not health.get("online"):
        print("\n[ERROR] Could not connect to the database:")
        print(f"  {health.get('error')}")
        print("\nChecklist for online / cloud databases:")
        print("  1. Verify DATABASE_URL in your .env file.")
        print("  2. Ensure your cloud database (Neon, Supabase, Render, AWS RDS) is active/online.")
        print("  3. For Neon or Supabase, ensure sslmode=require is in the connection string.")
        print("  4. Check if your database firewall or IP allowlist permits incoming connections.")
        sys.exit(1)

    print("Database connection verified successfully.")
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("CYBERVAL database schema created successfully!")


if __name__ == "__main__":
    init_db()

