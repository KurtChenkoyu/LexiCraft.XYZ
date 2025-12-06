"""
Schema Adapter for LexiSurvey Engine (V7.1)

Maps abstract :Block concept to concrete :Word implementation.
Implements the Schema Adapter Pattern to allow the Engine to work with
the current Neo4j schema without requiring database migration.

Key Decision: :Word nodes are defined as a concrete subclass of the abstract :Block concept.
- Conceptual Model: :Block is the abstract concept (semantic territory blocks)
- Implementation: :Word is the concrete Neo4j node label (Core Blocks)
- Strategy: Use Schema Adapter Pattern to alias :Block → :Word in all queries
- No Migration: Database schema remains unchanged. All mapping happens in Python/Cypher query layer.

Based on LexiSurvey_V7.1_MasterSpec.md and LEXISURVEY_ENGINE_INTEGRATION.md
"""

from typing import Dict, Any, List


class SchemaAdapter:
    """
    Schema Adapter Pattern: Maps abstract :Block concept to concrete :Word implementation.
    
    The Engine uses abstract concepts:
    - :Block (abstract) → :Word (concrete implementation)
    - global_rank (abstract) → frequency_rank (concrete property)
    
    This adapter ensures all queries and results are properly mapped between
    the Engine's expected format and the current database schema.
    """
    
    @staticmethod
    def adapt_block_query(query: str) -> str:
        """
        Adapts abstract :Block queries to concrete :Word schema.
        
        Replaces:
        - :Block → :Word
        - global_rank → frequency_rank
        
        Args:
            query: Cypher query string using abstract :Block and global_rank
            
        Returns:
            Adapted query string using concrete :Word and frequency_rank
            
        Example:
            Input:  "MATCH (b:Block) WHERE b.global_rank >= $min_r"
            Output: "MATCH (b:Word) WHERE b.frequency_rank >= $min_r"
        """
        # Replace :Block with :Word
        adapted_query = query.replace(":Block", ":Word")
        
        # Replace global_rank with frequency_rank
        adapted_query = adapted_query.replace("global_rank", "frequency_rank")
        
        return adapted_query
    
    @staticmethod
    def adapt_result(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps database response back to Engine's expected format.
        
        Converts:
        - frequency_rank → global_rank (if present)
        
        Preserves all other fields as-is.
        
        Args:
            record: Dictionary from Neo4j query result (may contain frequency_rank)
            
        Returns:
            Dictionary with global_rank (if frequency_rank was present)
            
        Example:
            Input:  {"word": "establish", "frequency_rank": 3500, "name": "establish"}
            Output: {"word": "establish", "global_rank": 3500, "frequency_rank": 3500, "name": "establish"}
            
        Note:
            Both frequency_rank and global_rank are kept in the result to maintain
            compatibility with both the Engine (expects global_rank) and any code
            that might reference frequency_rank directly.
        """
        adapted_record = record.copy()
        
        # Map frequency_rank to global_rank if present
        if "frequency_rank" in adapted_record:
            adapted_record["global_rank"] = adapted_record["frequency_rank"]
        
        return adapted_record
    
    @staticmethod
    def adapt_results(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adapts a list of database records to Engine's expected format.
        
        Convenience method for adapting multiple records at once.
        
        Args:
            records: List of dictionaries from Neo4j query results
            
        Returns:
            List of adapted dictionaries with global_rank mapped
        """
        return [SchemaAdapter.adapt_result(record) for record in records]

