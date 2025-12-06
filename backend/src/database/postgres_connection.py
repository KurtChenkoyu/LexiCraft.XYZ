"""
PostgreSQL Connection Manager (Supabase)

Handles connection to Supabase PostgreSQL instance and provides session management.
Optimized for Supabase Transaction mode pooler (port 6543).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Optional, Generator
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Global engine singleton - reuse across requests
_engine = None
_SessionLocal = None


def _get_engine():
    """Get or create the global engine singleton."""
    global _engine, _SessionLocal
    
    if _engine is None:
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            raise ValueError(
                "PostgreSQL connection string missing. "
                "Set DATABASE_URL environment variable."
            )
        
        # Create engine for Transaction Pooler (port 6543)
        # Use NullPool - Supabase handles connection pooling
        _engine = create_engine(
            connection_string,
            poolclass=NullPool,  # Essential for Transaction mode
            connect_args={
                "sslmode": "require",
                "connect_timeout": 30,
            },
            echo=False
        )
        
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
            expire_on_commit=False  # Prevent lazy loading issues after commit
        )
    
    return _engine, _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Ensures proper cleanup and rollback on errors.
    
    Usage:
        with get_db_session() as db:
            db.query(...)
    """
    _, SessionLocal = _get_engine()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class PostgresConnection:
    """Manages PostgreSQL database connection and sessions."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize PostgreSQL connection.
        
        Args:
            connection_string: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        
        if not self.connection_string:
            raise ValueError(
                "PostgreSQL connection string missing. "
                "Provide connection_string or set DATABASE_URL environment variable."
            )
        
        # Use global engine if using default connection string
        if self.connection_string == os.getenv("DATABASE_URL"):
            self.engine, self.SessionLocal = _get_engine()
        else:
            # Custom connection string - create new engine
            self.engine = create_engine(
                self.connection_string,
                poolclass=NullPool,
                connect_args={
                    "sslmode": "require",
                    "connect_timeout": 30,
                },
                echo=False
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False
            )
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def verify_connectivity(self) -> bool:
        """
        Verify that the connection to PostgreSQL is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                value = result.scalar()
                return value == 1
        except Exception as e:
            print(f"Connection verification failed: {e}")
            return False
    
    def close(self):
        """Close the database engine."""
        # Don't dispose global engine
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

