import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / '.env')

# Add parent directory to path
sys.path.insert(0, str(backend_dir))

from src.database.postgres_connection import PostgresConnection

def apply_sql_migration(migration_file):
    print(f"Applying migration: {migration_file}")
    conn = PostgresConnection()
    session = conn.get_session()
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
            # Split by semicolon to run statements separately if needed, 
            # but execute(text(sql)) might handle it if it's simple.
            # For safety with multi-statement, let's try executing the whole block.
            session.execute(text(sql))
            session.commit()
            print("✅ Migration applied successfully!")
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        session.close()
        conn.close()

if __name__ == "__main__":
    migration_path = backend_dir / "migrations" / "003_survey_questions.sql"
    if migration_path.exists():
        apply_sql_migration(migration_path)
    else:
        print(f"Migration file not found: {migration_path}")

