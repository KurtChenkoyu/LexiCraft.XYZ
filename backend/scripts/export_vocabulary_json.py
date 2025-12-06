"""
Export Vocabulary Data from Neo4j to JSON

This script exports all vocabulary data from Neo4j into a JSON file
that can be bundled with the frontend or loaded in-memory by the backend.

Usage:
    python backend/scripts/export_vocabulary_json.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection


def export_words(session) -> Dict[str, Dict[str, Any]]:
    """Export all Word nodes."""
    print("Exporting Words...")
    query = """
        MATCH (w:Word)
        RETURN w.name as name, 
               w.frequency_rank as frequency_rank,
               w.moe_level as moe_level,
               w.ngsl_rank as ngsl_rank
        ORDER BY w.frequency_rank
    """
    result = session.run(query)
    
    words = {}
    for record in result:
        word_name = record['name']
        words[word_name] = {
            'name': word_name,
            'frequency_rank': record.get('frequency_rank'),
            'moe_level': record.get('moe_level'),
            'ngsl_rank': record.get('ngsl_rank'),
            'senses': []  # Will be populated when exporting senses
        }
    
    print(f"  Exported {len(words)} words")
    return words


def export_senses(session, words: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Export all Sense nodes and link them to words."""
    print("Exporting Senses...")
    query = """
        MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
        RETURN 
            s.id as sense_id,
            w.name as word,
            COALESCE(s.definition_en, s.definition, '') as definition_en,
            s.definition as definition,
            COALESCE(s.definition_zh_translation, s.definition_zh, '') as definition_zh,
            COALESCE(s.definition_zh_explanation, '') as definition_zh_explanation,
            s.example_en as example_en,
            COALESCE(s.example_zh_translation, s.example_zh, '') as example_zh,
            COALESCE(s.example_zh_explanation, '') as example_zh_explanation,
            s.pos as pos,
            s.enriched as enriched,
            w.frequency_rank as frequency_rank
        ORDER BY w.frequency_rank, s.id
    """
    result = session.run(query)
    
    senses = {}
    for record in result:
        sense_id = record['sense_id']
        word_name = record['word']
        
        sense_data = {
            'id': sense_id,
            'word': word_name,
            'definition_en': record.get('definition_en') or '',
            'definition': record.get('definition') or '',
            'definition_zh': record.get('definition_zh') or '',
            'definition_zh_explanation': record.get('definition_zh_explanation') or '',
            'example_en': record.get('example_en') or '',
            'example_zh': record.get('example_zh') or '',
            'example_zh_explanation': record.get('example_zh_explanation') or '',
            'pos': record.get('pos'),
            'enriched': record.get('enriched', False),
            'frequency_rank': record.get('frequency_rank'),
        }
        
        senses[sense_id] = sense_data
        
        # Link sense to word
        if word_name in words:
            words[word_name]['senses'].append(sense_id)
    
    print(f"  Exported {len(senses)} senses")
    return senses


def export_relationships(session) -> Dict[str, Dict[str, List[str]]]:
    """Export all relationships between words."""
    print("Exporting Relationships...")
    
    # Export RELATED_TO relationships
    related_query = """
        MATCH (w1:Word)-[:RELATED_TO]->(w2:Word)
        MATCH (w1)-[:HAS_SENSE]->(s1:Sense)
        MATCH (w2)-[:HAS_SENSE]->(s2:Sense)
        RETURN DISTINCT s1.id as source_sense, s2.id as target_sense, 'RELATED_TO' as type
    """
    
    # Export OPPOSITE_TO relationships
    opposite_query = """
        MATCH (w1:Word)-[:OPPOSITE_TO]->(w2:Word)
        MATCH (w1)-[:HAS_SENSE]->(s1:Sense)
        MATCH (w2)-[:HAS_SENSE]->(s2:Sense)
        RETURN DISTINCT s1.id as source_sense, s2.id as target_sense, 'OPPOSITE_TO' as type
    """
    
    relationships = {}
    
    # Process RELATED_TO
    result = session.run(related_query)
    for record in result:
        source = record['source_sense']
        target = record['target_sense']
        if source not in relationships:
            relationships[source] = {'related': [], 'opposite': []}
        relationships[source]['related'].append(target)
    
    # Process OPPOSITE_TO
    result = session.run(opposite_query)
    for record in result:
        source = record['source_sense']
        target = record['target_sense']
        if source not in relationships:
            relationships[source] = {'related': [], 'opposite': []}
        relationships[source]['opposite'].append(target)
    
    print(f"  Exported relationships for {len(relationships)} senses")
    return relationships


def build_band_index(senses: Dict[str, Dict[str, Any]]) -> Dict[int, List[str]]:
    """Build frequency band index for fast lookups."""
    print("Building frequency band index...")
    
    bands = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
    band_index = {band: [] for band in bands}
    
    for sense_id, sense_data in senses.items():
        rank = sense_data.get('frequency_rank')
        if rank is None:
            continue
        
        # Find the appropriate band
        for band in bands:
            if rank <= band:
                band_index[band].append(sense_id)
                break
    
    # Also add a catch-all for ranks > 8000
    band_index[9999] = [
        sense_id for sense_id, sense_data in senses.items()
        if sense_data.get('frequency_rank', 0) > 8000
    ]
    
    print(f"  Indexed senses into {len(bands)} frequency bands")
    return band_index


def main():
    """Main export function."""
    print("=" * 60)
    print("Vocabulary Export Script")
    print("=" * 60)
    
    # Connect to Neo4j
    try:
        conn = Neo4jConnection()
        print("Connected to Neo4j")
    except Exception as e:
        print(f"ERROR: Failed to connect to Neo4j: {e}")
        print("Make sure NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD are set")
        return 1
    
    try:
        with conn.get_session() as session:
            # Export data
            words = export_words(session)
            senses = export_senses(session, words)
            relationships = export_relationships(session)
            band_index = build_band_index(senses)
            
            # Build final structure
            vocabulary_data = {
                'version': '1.0',
                'exportedAt': datetime.now().isoformat(),
                'words': words,
                'senses': senses,
                'relationships': relationships,
                'bandIndex': band_index,
            }
            
            # Determine output path
            script_dir = Path(__file__).parent
            backend_dir = script_dir.parent
            project_root = backend_dir.parent
            
            # Output to both backend/data and landing-page/data
            backend_output = backend_dir / 'data' / 'vocabulary.json'
            frontend_output = project_root / 'landing-page' / 'data' / 'vocabulary.json'
            
            # Create directories if needed
            backend_output.parent.mkdir(parents=True, exist_ok=True)
            frontend_output.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON files
            print("\nWriting JSON files...")
            with open(backend_output, 'w', encoding='utf-8') as f:
                json.dump(vocabulary_data, f, ensure_ascii=False, indent=2)
            print(f"  Backend: {backend_output}")
            
            with open(frontend_output, 'w', encoding='utf-8') as f:
                json.dump(vocabulary_data, f, ensure_ascii=False, indent=2)
            print(f"  Frontend: {frontend_output}")
            
            # Print statistics
            print("\n" + "=" * 60)
            print("Export Complete!")
            print("=" * 60)
            print(f"Words: {len(words)}")
            print(f"Senses: {len(senses)}")
            print(f"Relationships: {sum(len(r.get('related', []) + r.get('opposite', [])) for r in relationships.values())}")
            print(f"Frequency bands: {len(band_index)}")
            
            # Calculate file size
            file_size = backend_output.stat().st_size
            print(f"File size: {file_size / 1024 / 1024:.2f} MB")
            
    except Exception as e:
        print(f"\nERROR during export: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

