"""
Phase 4: Graph Injection (The Loader)
Loads the Master Vocabulary into Neo4j V6.1 Schema.

1. Loads master_vocab.csv
2. Creates (:Word) nodes in batches.
3. Sets properties: name, frequency_rank, moe_level.
"""

import pandas as pd
from pathlib import Path
import sys

from src.database.neo4j_connection import Neo4jConnection

# Constants
DATA_FILE = Path(__file__).parent.parent.parent / "data" / "processed" / "master_vocab.csv"
BATCH_SIZE = 1000

def load_vocabulary(conn: Neo4jConnection):
    print(f"Loading vocabulary from {DATA_FILE}...")
    if not DATA_FILE.exists():
        print(f"Error: File not found: {DATA_FILE}")
        return

    df = pd.read_csv(DATA_FILE)
    total_words = len(df)
    print(f"Found {total_words} words to load.")
    
    # Convert dataframe to list of dicts
    records = df.to_dict('records')
    
    # Batch process
    with conn.get_session() as session:
        for i in range(0, total_words, BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            print(f"Processing batch {i} - {min(i + BATCH_SIZE, total_words)}...")
            
            query = """
            UNWIND $batch AS row
            MERGE (w:Word {name: row.word})
            SET w.frequency_rank = row.unified_rank,
                w.moe_level = toInteger(row.moe_level),
                w.ngsl_rank = toInteger(row.ngsl_rank)
            """
            
            try:
                session.run(query, batch=batch)
            except Exception as e:
                print(f"Error processing batch: {e}")
                
    print("✅ Vocabulary Load Complete.")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            load_vocabulary(conn)
        else:
            print("Connection failed.")
    finally:
        conn.close()

