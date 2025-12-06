"""
Phase 0: Data Preparation
Unified Frequency Ranking Strategy (V6.1)

1. Loads Real Phase 1 Data (combined_word_list_phase1.csv).
2. Calculates Unified Rank:
   - Base = Corpus Rank (proxy for NGSL)
   - Multiplier = 0.8x if 'Taiwan' in sources (MOE Boost)
3. Exports master_vocab.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os

# Constants
DATA_DIR = Path(__file__).parent.parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "processed"
REAL_DATA_PATH = Path(__file__).parent.parent.parent / "scripts" / "combined_word_list_phase1.csv"

def ensure_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_unified_rank(row):
    """
    The V6.1 Logic:
    Base = NGSL Rank (or 50,000 if missing)
    Multiplier = 0.8 if MOE Level 1-4 (Taiwan Boost)
    """
    # Use corpus_rank as proxy for NGSL rank
    base_rank = row['corpus_rank'] if pd.notna(row['corpus_rank']) else 50000
    
    # If 'Taiwan' is in sources, treat as Level 1-4 (Boosted)
    multiplier = 1.0
    if isinstance(row['sources'], str) and "Taiwan" in row['sources']:
        multiplier = 0.8
            
    return base_rank * multiplier

def run_pipeline():
    ensure_directories()
    
    print(f"Loading real data from {REAL_DATA_PATH}...")
    if not REAL_DATA_PATH.exists():
        print(f"❌ Error: Phase 1 data not found at {REAL_DATA_PATH}")
        return

    df = pd.read_csv(REAL_DATA_PATH)
    
    # Normalize columns for V6.1 schema
    # We need: word, ngsl_rank, moe_level
    
    # 1. NGSL Rank -> corpus_rank
    df['ngsl_rank'] = df['corpus_rank']
    
    # 2. MOE Level -> 1 if Taiwan source, else 6 (placeholder)
    df['moe_level'] = df['sources'].apply(lambda x: 1 if isinstance(x, str) and "Taiwan" in x else 6)
    
    # Calculate Unified Rank
    print("Calculating Unified Rank...")
    df['unified_rank'] = df.apply(calculate_unified_rank, axis=1)
    
    # Sort by Priority (Lower unified_rank = Higher Priority)
    df = df.sort_values('unified_rank')
    
    # Clean up types
    df['moe_level'] = df['moe_level'].fillna(6).astype(int)
    df['ngsl_rank'] = df['ngsl_rank'].fillna(50000).astype(int)
    
    # Select final columns
    df_master = df[['word', 'unified_rank', 'moe_level', 'ngsl_rank']]
    
    # Save
    output_path = OUTPUT_DIR / "master_vocab.csv"
    df_master.to_csv(output_path, index=False)
    
    print(f"✅ Master Vocabulary Generated: {len(df_master)} words")
    print(f"Saved to: {output_path}")
    
    # Show sample
    print("\nSample High Priority Words:")
    print(df_master.head(5))

if __name__ == "__main__":
    run_pipeline()
