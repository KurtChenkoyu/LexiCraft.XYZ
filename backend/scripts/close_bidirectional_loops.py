#!/usr/bin/env python3
"""
Pass 2: Close Bidirectional Loops

If word A lists B as a synonym, ensure B lists A as a synonym.
This creates a "full loop" for better learning and graph connectivity.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List

INPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_comprehensive.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_comprehensive.json"

def load_vocabulary():
    """Load the Gemini-enriched vocabulary"""
    with open(INPUT_FILE, 'r') as f:
        return json.load(f)

def close_loops(vocabulary: Dict) -> Dict:
    """
    Create bidirectional connections.
    
    IMPORTANT: This only closes existing loops - it does NOT create new connections.
    It only adds reverse links for connections that already exist.
    """
    senses = vocabulary['senses']
    
    # Build reverse indexes
    synonym_links = defaultdict(lambda: {'sense_ids': set(), 'display_words': set()})
    antonym_links = defaultdict(lambda: {'sense_ids': set(), 'display_words': set()})
    similar_links = defaultdict(lambda: {'sense_ids': set(), 'display_words': set()})
    
    print("🔍 Phase 1: Building reverse indexes...")
    processed = 0
    
    # Pass 1: Collect all connections
    for sense_id, sense_data in senses.items():
        connections = sense_data.get('connections', {})
        
        # Synonyms
        if 'synonyms' in connections and connections['synonyms']:
            syn_data = connections['synonyms']
            # Handle both dict and list formats
            if isinstance(syn_data, dict) and syn_data and 'sense_ids' in syn_data and syn_data['sense_ids']:
                for target_id in syn_data['sense_ids']:
                    # Only process if target exists in vocabulary (no new connections)
                    if target_id in senses:
                        # Target should link back to this sense (closing existing loop)
                        synonym_links[target_id]['sense_ids'].add(sense_id)
                        synonym_links[target_id]['display_words'].add(sense_data.get('word', ''))
            
            # Also add current sense's display words to its own entry
            if syn_data and 'display_words' in syn_data and syn_data['display_words']:
                for word in syn_data['display_words']:
                    synonym_links[sense_id]['display_words'].add(word)
        
        # Antonyms
        if 'antonyms' in connections and connections['antonyms']:
            ant_data = connections['antonyms']
            # Handle both dict and list formats
            if isinstance(ant_data, dict) and ant_data and 'sense_ids' in ant_data and ant_data['sense_ids']:
                for target_id in ant_data['sense_ids']:
                    if target_id in senses:
                        antonym_links[target_id]['sense_ids'].add(sense_id)
                        antonym_links[target_id]['display_words'].add(sense_data.get('word', ''))
            
            if ant_data and 'display_words' in ant_data and ant_data['display_words']:
                for word in ant_data['display_words']:
                    antonym_links[sense_id]['display_words'].add(word)
        
        # Similar words
        if 'similar_words' in connections and connections['similar_words']:
            sim_data = connections['similar_words']
            # Handle both dict and list formats
            if isinstance(sim_data, dict) and sim_data and 'sense_ids' in sim_data and sim_data['sense_ids']:
                for target_id in sim_data['sense_ids']:
                    if target_id in senses:
                        similar_links[target_id]['sense_ids'].add(sense_id)
                        similar_links[target_id]['display_words'].add(sense_data.get('word', ''))
            
            if sim_data and 'display_words' in sim_data and sim_data['display_words']:
                for word in sim_data['display_words']:
                    similar_links[sense_id]['display_words'].add(word)
        
        processed += 1
        if processed % 1000 == 0:
            print(f"  Processed {processed}/{len(senses)} senses...")
    
    print(f"✅ Built indexes for {len(senses)} senses")
    
    # Pass 2: Merge bidirectional links
    print("\n🔗 Phase 2: Closing loops...")
    updated = 0
    
    for sense_id, sense_data in senses.items():
        if 'connections' not in sense_data:
            sense_data['connections'] = {}
        
        connections = sense_data['connections']
        changed = False
        
        # Merge synonyms
        if sense_id in synonym_links:
            if 'synonyms' not in connections or not connections['synonyms']:
                connections['synonyms'] = {'sense_ids': [], 'display_words': []}
            
            # Handle both dict and list formats
            syn_conn = connections['synonyms']
            if isinstance(syn_conn, list):
                # Convert list to dict format
                connections['synonyms'] = {'sense_ids': syn_conn, 'display_words': []}
                syn_conn = connections['synonyms']
            
            # Merge sense_ids
            existing_syn_ids = set(syn_conn.get('sense_ids', []) or [])
            new_syn_ids = synonym_links[sense_id]['sense_ids']
            merged_syn_ids = existing_syn_ids | new_syn_ids
            
            # Merge display_words
            existing_syn_words = set(syn_conn.get('display_words', []) or [])
            new_syn_words = synonym_links[sense_id]['display_words']
            merged_syn_words = existing_syn_words | new_syn_words
            
            # Remove the word itself from its own synonyms
            current_word = sense_data.get('word', '')
            merged_syn_words.discard(current_word)
            merged_syn_words.discard(current_word.lower())
            
            if len(merged_syn_ids) > len(existing_syn_ids) or len(merged_syn_words) > len(existing_syn_words):
                # Filter out None values before sorting
                connections['synonyms']['sense_ids'] = sorted([x for x in merged_syn_ids if x])
                connections['synonyms']['display_words'] = sorted([x for x in merged_syn_words if x])
                changed = True
        
        # Merge antonyms
        if sense_id in antonym_links:
            if 'antonyms' not in connections or not connections['antonyms']:
                connections['antonyms'] = {'sense_ids': [], 'display_words': []}
            
            # Handle both dict and list formats
            ant_conn = connections['antonyms']
            if isinstance(ant_conn, list):
                connections['antonyms'] = {'sense_ids': ant_conn, 'display_words': []}
                ant_conn = connections['antonyms']
            
            existing_ant_ids = set(ant_conn.get('sense_ids', []) or [])
            new_ant_ids = antonym_links[sense_id]['sense_ids']
            merged_ant_ids = existing_ant_ids | new_ant_ids
            
            existing_ant_words = set(ant_conn.get('display_words', []) or [])
            new_ant_words = antonym_links[sense_id]['display_words']
            merged_ant_words = existing_ant_words | new_ant_words
            
            # Remove the word itself
            current_word = sense_data.get('word', '')
            merged_ant_words.discard(current_word)
            merged_ant_words.discard(current_word.lower())
            
            if len(merged_ant_ids) > len(existing_ant_ids) or len(merged_ant_words) > len(existing_ant_words):
                # Filter out None values before sorting
                connections['antonyms']['sense_ids'] = sorted([x for x in merged_ant_ids if x])
                connections['antonyms']['display_words'] = sorted([x for x in merged_ant_words if x])
                changed = True
        
        # Merge similar words
        if sense_id in similar_links:
            if 'similar_words' not in connections or not connections['similar_words']:
                connections['similar_words'] = {'sense_ids': [], 'display_words': []}
            
            # Handle both dict and list formats
            sim_conn = connections['similar_words']
            if isinstance(sim_conn, list):
                connections['similar_words'] = {'sense_ids': sim_conn, 'display_words': []}
                sim_conn = connections['similar_words']
            
            existing_sim_ids = set(sim_conn.get('sense_ids', []) or [])
            new_sim_ids = similar_links[sense_id]['sense_ids']
            merged_sim_ids = existing_sim_ids | new_sim_ids
            
            existing_sim_words = set(sim_conn.get('display_words', []) or [])
            new_sim_words = similar_links[sense_id]['display_words']
            merged_sim_words = existing_sim_words | new_sim_words
            
            # Remove the word itself
            current_word = sense_data.get('word', '')
            merged_sim_words.discard(current_word)
            merged_sim_words.discard(current_word.lower())
            
            if len(merged_sim_ids) > len(existing_sim_ids) or len(merged_sim_words) > len(existing_sim_words):
                # Filter out None values before sorting
                connections['similar_words']['sense_ids'] = sorted([x for x in merged_sim_ids if x])
                connections['similar_words']['display_words'] = sorted([x for x in merged_sim_words if x])
                changed = True
        
        if changed:
            updated += 1
        
        if updated > 0 and updated % 500 == 0:
            print(f"  Updated {updated} senses...")
    
    print(f"✅ Updated {updated} senses with bidirectional links")
    
    return vocabulary

def main():
    print("="*60)
    print("🔄 Pass 2: Closing Bidirectional Loops")
    print("="*60)
    
    # Load vocabulary
    print(f"\n📖 Loading {INPUT_FILE}...")
    vocabulary = load_vocabulary()
    print(f"✅ Loaded {len(vocabulary['senses'])} senses")
    
    # Close loops
    vocabulary = close_loops(vocabulary)
    
    # Save output
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(vocabulary, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("✅ Pass 2 Complete!")
    print("="*60)
    print(f"📁 Output: {OUTPUT_FILE}")
    print("\n🎯 Ready for validation and deployment!")

if __name__ == '__main__':
    main()

