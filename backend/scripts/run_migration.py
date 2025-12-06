"""
Run database migration to create all tables.

Usage:
    python scripts/run_migration.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / '.env')

# Add parent directory to path
sys.path.insert(0, str(backend_dir))

from src.database.postgres_connection import PostgresConnection
from src.database.models import Base


def run_migration():
    """Run migration to create all tables."""
    print("=" * 60)
    print("Running Database Migration")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = PostgresConnection()
        print("✅ Connected to database")
        
        # Create all tables
        print("\nCreating tables...")
        Base.metadata.create_all(conn.engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        conn.close()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

