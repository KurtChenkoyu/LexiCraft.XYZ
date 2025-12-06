"""
Phase 5: Performance Engineering
Schema Optimization & Vector Embeddings Generation

1. Unique constraints on Word.name, Sense.id
2. Indexes on frequency_rank, moe_level
3. Vector embeddings for Word and Sense nodes
4. Vector indexes for similarity search
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from tqdm import tqdm

# Allow running from backend/ directly
# sys.path.append(str(Path(__file__).parent.parent)) 

from src.database.neo4j_connection import Neo4jConnection

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY is required. Set it in .env file.")

genai.configure(api_key=API_KEY)

# Embedding model
EMBEDDING_MODEL = "models/text-embedding-004"
BATCH_SIZE = 100  # Process 100 nodes at a time
EMBEDDING_DIMENSIONS = 768  # text-embedding-004 produces 768-dimensional vectors


def optimize_schema(conn: Neo4jConnection):
    """Apply schema optimizations: constraints and indexes."""
    print("Applying V6.1 Schema Optimizations...")
    
    with conn.get_session() as session:
        # 1. Constraints
        # Word name must be unique
        print("Creating constraint: word_name_unique")
        session.run("""
            CREATE CONSTRAINT word_name_unique IF NOT EXISTS
            FOR (w:Word) REQUIRE w.name IS UNIQUE
        """)
        
        # Sense ID must be unique
        print("Creating constraint: sense_id_unique")
        session.run("""
            CREATE CONSTRAINT sense_id_unique IF NOT EXISTS
            FOR (s:Sense) REQUIRE s.id IS UNIQUE
        """)
        
        # 2. Indexes
        # Frequency Rank (Critical for sorting)
        print("Creating index: word_freq_idx")
        session.run("""
            CREATE INDEX word_freq_idx IF NOT EXISTS
            FOR (w:Word) ON (w.frequency_rank)
        """)
        
        # MOE Level (For filtering)
        print("Creating index: word_moe_idx")
        session.run("""
            CREATE INDEX word_moe_idx IF NOT EXISTS
            FOR (w:Word) ON (w.moe_level)
        """)
        
    print("✅ Schema Optimization Complete.")


def create_vector_indexes(conn: Neo4jConnection):
    """Create vector indexes for Word and Sense embeddings."""
    print("Creating Vector Indexes...")
    
    with conn.get_session() as session:
        # Vector index for Word embeddings
        print("Creating vector index: word_embedding_idx")
        try:
            session.run("""
                CREATE VECTOR INDEX word_embedding_idx IF NOT EXISTS
                FOR (w:Word) ON w.embedding
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 768,
                        `vector.similarity_function`: 'cosine'
                    }
                }
            """)
        except Exception as e:
            # Neo4j version might not support vector indexes yet
            print(f"⚠️  Warning: Could not create Word vector index: {e}")
            print("   (This is okay - vector indexes are optional for now)")
        
        # Vector index for Sense embeddings
        print("Creating vector index: sense_embedding_idx")
        try:
            session.run("""
                CREATE VECTOR INDEX sense_embedding_idx IF NOT EXISTS
                FOR (s:Sense) ON s.embedding
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 768,
                        `vector.similarity_function`: 'cosine'
                    }
                }
            """)
        except Exception as e:
            # Neo4j version might not support vector indexes yet
            print(f"⚠️  Warning: Could not create Sense vector index: {e}")
            print("   (This is okay - vector indexes are optional for now)")
    
    print("✅ Vector Index Creation Complete.")


def fetch_words_without_embeddings(conn: Neo4jConnection, batch_size: int) -> List[Dict[str, Any]]:
    """
    Fetch a batch of Word nodes that don't have embeddings.
    
    Returns:
        List of dicts with 'name' and 'id' (internal Neo4j ID) for each word
    """
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word)
            WHERE w.embedding IS NULL
            RETURN id(w) as node_id, w.name as name
            LIMIT $batch_size
        """, batch_size=batch_size)
        
        return [{"node_id": record["node_id"], "name": record["name"]} 
                for record in result]


def fetch_senses_without_embeddings(conn: Neo4jConnection, batch_size: int) -> List[Dict[str, Any]]:
    """
    Fetch a batch of Sense nodes that don't have embeddings.
    
    Returns:
        List of dicts with 'id', 'node_id', and 'definition_zh' for each sense
    """
    with conn.get_session() as session:
        result = session.run("""
            MATCH (s:Sense)
            WHERE s.embedding IS NULL AND s.definition_zh IS NOT NULL
            RETURN id(s) as node_id, s.id as sense_id, s.definition_zh as definition_zh
            LIMIT $batch_size
        """, batch_size=batch_size)
        
        return [{
            "node_id": record["node_id"],
            "sense_id": record["sense_id"],
            "definition_zh": record["definition_zh"]
        } for record in result]


def count_nodes_without_embeddings(conn: Neo4jConnection, node_type: str) -> int:
    """Count nodes without embeddings."""
    with conn.get_session() as session:
        if node_type == "Word":
            result = session.run("""
                MATCH (w:Word)
                WHERE w.embedding IS NULL
                RETURN count(w) as count
            """)
        else:  # Sense
            result = session.run("""
                MATCH (s:Sense)
                WHERE s.embedding IS NULL AND s.definition_zh IS NOT NULL
                RETURN count(s) as count
            """)
        
        record = result.single()
        return record["count"] if record else 0


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using Gemini API.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each is a list of 768 floats)
    """
    if not texts:
        return []
    
    try:
        # Use embed_content with batch processing
        # When content is an iterable (list), API returns {"embedding": [[...], [...], ...]}
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=texts,  # Pass list directly - API handles batching
            task_type="RETRIEVAL_DOCUMENT"  # Use RETRIEVAL_DOCUMENT for storing embeddings
        )
        
        # Extract embeddings from result
        # For batch input, result is {"embedding": [[...], [...], ...]}
        if isinstance(result, dict) and "embedding" in result:
            embeddings = result["embedding"]
            # BatchEmbeddingDict returns list[list[float]]
            if isinstance(embeddings, list):
                # Verify we got the right number of embeddings
                if len(embeddings) != len(texts):
                    raise ValueError(
                        f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                    )
                # Verify each embedding is a list of floats
                for i, emb in enumerate(embeddings):
                    if not isinstance(emb, list):
                        raise ValueError(
                            f"Embedding {i} is not a list: {type(emb)}"
                        )
                    if len(emb) != EMBEDDING_DIMENSIONS:
                        print(f"⚠️  Warning: Embedding {i} has {len(emb)} dimensions, expected {EMBEDDING_DIMENSIONS}")
                return embeddings
            return []
        
        raise ValueError(f"Unexpected result format from embed_content: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise


def update_word_embeddings(conn: Neo4jConnection, words: List[Dict[str, Any]], embeddings: List[List[float]]):
    """
    Update Word nodes with their embeddings.
    
    Args:
        conn: Neo4j connection
        words: List of word dicts with 'node_id' and 'name'
        embeddings: List of embedding vectors (768 floats each)
    """
    if len(words) != len(embeddings):
        raise ValueError(f"Mismatch: {len(words)} words but {len(embeddings)} embeddings")
    
    with conn.get_session() as session:
        # Prepare data for batch update
        data = [
            {"node_id": word["node_id"], "embedding": embedding}
            for word, embedding in zip(words, embeddings)
        ]
        
        # Batch update using UNWIND
        session.run("""
            UNWIND $data AS row
            MATCH (w:Word)
            WHERE id(w) = row.node_id
            SET w.embedding = row.embedding
        """, data=data)


def update_sense_embeddings(conn: Neo4jConnection, senses: List[Dict[str, Any]], embeddings: List[List[float]]):
    """
    Update Sense nodes with their embeddings.
    
    Args:
        conn: Neo4j connection
        senses: List of sense dicts with 'node_id', 'sense_id', 'definition_zh'
        embeddings: List of embedding vectors (768 floats each)
    """
    if len(senses) != len(embeddings):
        raise ValueError(f"Mismatch: {len(senses)} senses but {len(embeddings)} embeddings")
    
    with conn.get_session() as session:
        # Prepare data for batch update
        data = [
            {"node_id": sense["node_id"], "embedding": embedding}
            for sense, embedding in zip(senses, embeddings)
        ]
        
        # Batch update using UNWIND
        session.run("""
            UNWIND $data AS row
            MATCH (s:Sense)
            WHERE id(s) = row.node_id
            SET s.embedding = row.embedding
        """, data=data)


def generate_word_embeddings(conn: Neo4jConnection):
    """Generate and store embeddings for all Word nodes without embeddings."""
    print("\n" + "="*60)
    print("Generating Word Embeddings")
    print("="*60)
    
    total_count = count_nodes_without_embeddings(conn, "Word")
    print(f"Found {total_count} Word nodes without embeddings.")
    
    if total_count == 0:
        print("✅ All Word nodes already have embeddings.")
        return
    
    processed = 0
    
    with tqdm(total=total_count, desc="Processing Words", unit="words") as pbar:
        while True:
            # Fetch batch
            words = fetch_words_without_embeddings(conn, BATCH_SIZE)
            
            if not words:
                break
            
            # Extract text to embed (word names)
            texts = [word["name"] for word in words]
            
            # Generate embeddings
            try:
                embeddings = generate_embeddings_batch(texts)
                
                # Update Neo4j
                update_word_embeddings(conn, words, embeddings)
                
                processed += len(words)
                pbar.update(len(words))
                
            except Exception as e:
                print(f"\n❌ Error processing batch: {e}")
                print(f"   Failed on words: {[w['name'] for w in words]}")
                # Continue with next batch
                continue
    
    print(f"\n✅ Word Embeddings Complete. Processed {processed} words.")


def generate_sense_embeddings(conn: Neo4jConnection):
    """Generate and store embeddings for all Sense nodes without embeddings."""
    print("\n" + "="*60)
    print("Generating Sense Embeddings")
    print("="*60)
    
    total_count = count_nodes_without_embeddings(conn, "Sense")
    print(f"Found {total_count} Sense nodes without embeddings.")
    
    if total_count == 0:
        print("✅ All Sense nodes already have embeddings.")
        return
    
    processed = 0
    
    with tqdm(total=total_count, desc="Processing Senses", unit="senses") as pbar:
        while True:
            # Fetch batch
            senses = fetch_senses_without_embeddings(conn, BATCH_SIZE)
            
            if not senses:
                break
            
            # Extract text to embed (Traditional Chinese definitions)
            texts = [sense["definition_zh"] for sense in senses]
            
            # Generate embeddings
            try:
                embeddings = generate_embeddings_batch(texts)
                
                # Update Neo4j
                update_sense_embeddings(conn, senses, embeddings)
                
                processed += len(senses)
                pbar.update(len(senses))
                
            except Exception as e:
                print(f"\n❌ Error processing batch: {e}")
                print(f"   Failed on senses: {[s['sense_id'] for s in senses]}")
                # Continue with next batch
                continue
    
    print(f"\n✅ Sense Embeddings Complete. Processed {processed} senses.")


def main():
    """Main execution function."""
    print("="*60)
    print("Phase 5: Performance Engineering & Vector Embeddings")
    print("="*60)
    
    conn = Neo4jConnection()
    
    try:
        if not conn.verify_connectivity():
            print("❌ Connection to Neo4j failed.")
            return
        
        # Step 1: Schema optimizations
            optimize_schema(conn)
        
        # Step 2: Generate Word embeddings
        generate_word_embeddings(conn)
        
        # Step 3: Generate Sense embeddings
        generate_sense_embeddings(conn)
        
        # Step 4: Create vector indexes (optional, may fail on older Neo4j versions)
        create_vector_indexes(conn)
        
        print("\n" + "="*60)
        print("✅ All Optimizations Complete!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
