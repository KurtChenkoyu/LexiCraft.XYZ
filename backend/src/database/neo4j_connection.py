"""
Neo4j Connection Manager

Handles connection to Neo4j Aura instance and provides session management.
"""
from neo4j import GraphDatabase
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    """Manages Neo4j database connection and sessions."""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI (defaults to NEO4J_URI env var)
            user: Neo4j username (defaults to NEO4J_USER env var)
            password: Neo4j password (defaults to NEO4J_PASSWORD env var)
        """
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError(
                "Neo4j connection parameters missing. "
                "Provide uri/user/password or set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables."
            )
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
    
    def get_session(self):
        """Get a new Neo4j session."""
        return self.driver.session()
    
    def verify_connectivity(self) -> bool:
        """
        Verify that the connection to Neo4j is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 as test")
                value = result.single()["test"]
                return value == 1
        except Exception as e:
            print(f"Connection verification failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

