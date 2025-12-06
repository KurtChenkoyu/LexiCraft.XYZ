"""
Verification Script: Layer Completeness Check

Verifies that all layers are generated where appropriate:
- Layer 1 has 2-3 examples (required)
- Layers 2-4 have examples if relationships exist
- Missing layers flagged for manual review

Note: This checks Content Level 2 (previously referred to as "Stage 2")
"""

import json
from src.database.neo4j_connection import Neo4jConnection


def verify_layer_completeness(conn: Neo4jConnection):
    """Verify that all layers are complete where appropriate."""
    print("=" * 60)
    print("CONTENT LEVEL 2: LAYER COMPLETENESS CHECK")
    print("=" * 60)
    
    with conn.get_session() as session:
        # Get all Level 2 content generated senses with their examples
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.stage2_enriched = true
            RETURN w.name as word, s.id as sense_id,
                   s.examples_contextual as contextual,
                   s.examples_opposite as opposite,
                   s.examples_similar as similar,
                   s.examples_confused as confused
        """)
        
        records = list(result)
        if not records:
            print("❌ No Level 2 content generated senses found.")
            return
        
        print(f"Checking {len(records)} enriched senses...\n")
        
        stats = {
            "total": len(records),
            "layer1_complete": 0,
            "layer1_incomplete": 0,
            "layer2_with_rels": 0,
            "layer2_without_examples": 0,
            "layer3_with_rels": 0,
            "layer3_without_examples": 0,
            "layer4_with_rels": 0,
            "layer4_without_examples": 0,
            "missing_layers": []
        }
        
        for record in records:
            word = record["word"]
            sense_id = record["sense_id"]
            # Parse JSON strings if they exist
            contextual_raw = record.get("contextual") or "[]"
            opposite_raw = record.get("opposite") or "[]"
            similar_raw = record.get("similar") or "[]"
            confused_raw = record.get("confused") or "[]"
            
            contextual = json.loads(contextual_raw) if isinstance(contextual_raw, str) else (contextual_raw or [])
            opposite = json.loads(opposite_raw) if isinstance(opposite_raw, str) else (opposite_raw or [])
            similar = json.loads(similar_raw) if isinstance(similar_raw, str) else (similar_raw or [])
            confused = json.loads(confused_raw) if isinstance(confused_raw, str) else (confused_raw or [])
            
            # Check Layer 1 (required)
            if 2 <= len(contextual) <= 3:
                stats["layer1_complete"] += 1
            else:
                stats["layer1_incomplete"] += 1
                stats["missing_layers"].append({
                    "sense_id": sense_id,
                    "word": word,
                    "issue": f"Layer 1 has {len(contextual)} examples (expected 2-3)"
                })
            
            # Check if relationships exist
            rel_result = session.run("""
                MATCH (w:Word {name: $word})
                OPTIONAL MATCH (w)-[:OPPOSITE_TO]->(opp:Word)
                OPTIONAL MATCH (w)-[:RELATED_TO]->(sim:Word)
                OPTIONAL MATCH (w)-[:CONFUSED_WITH]->(conf:Word)
                RETURN count(DISTINCT opp) as opp_count,
                       count(DISTINCT sim) as sim_count,
                       count(DISTINCT conf) as conf_count
            """, word=word)
            
            rel_data = rel_result.single()
            has_opposites = (rel_data["opp_count"] or 0) > 0
            has_similar = (rel_data["sim_count"] or 0) > 0
            has_confused = (rel_data["conf_count"] or 0) > 0
            
            # Check Layer 2
            if has_opposites:
                stats["layer2_with_rels"] += 1
                if len(opposite) == 0:
                    stats["layer2_without_examples"] += 1
                    stats["missing_layers"].append({
                        "sense_id": sense_id,
                        "word": word,
                        "issue": "Layer 2: Has OPPOSITE_TO relationships but no examples"
                    })
            
            # Check Layer 3
            if has_similar:
                stats["layer3_with_rels"] += 1
                if len(similar) == 0:
                    stats["layer3_without_examples"] += 1
                    stats["missing_layers"].append({
                        "sense_id": sense_id,
                        "word": word,
                        "issue": "Layer 3: Has RELATED_TO relationships but no examples"
                    })
            
            # Check Layer 4
            if has_confused:
                stats["layer4_with_rels"] += 1
                if len(confused) == 0:
                    stats["layer4_without_examples"] += 1
                    stats["missing_layers"].append({
                        "sense_id": sense_id,
                        "word": word,
                        "issue": "Layer 4: Has CONFUSED_WITH relationships but no examples"
                    })
        
        # Report statistics
        print("📊 Completeness Statistics:")
        print(f"  Total senses checked: {stats['total']}")
        print(f"\n  Layer 1 (Contextual):")
        print(f"    ✅ Complete (2-3 examples): {stats['layer1_complete']} ({stats['layer1_complete']/stats['total']*100:.1f}%)")
        print(f"    ⚠️  Incomplete: {stats['layer1_incomplete']} ({stats['layer1_incomplete']/stats['total']*100:.1f}%)")
        
        print(f"\n  Layer 2 (Opposites):")
        print(f"    Words with OPPOSITE_TO relationships: {stats['layer2_with_rels']}")
        if stats['layer2_with_rels'] > 0:
            print(f"    ⚠️  Missing examples: {stats['layer2_without_examples']} ({stats['layer2_without_examples']/stats['layer2_with_rels']*100:.1f}%)")
        
        print(f"\n  Layer 3 (Similar):")
        print(f"    Words with RELATED_TO relationships: {stats['layer3_with_rels']}")
        if stats['layer3_with_rels'] > 0:
            print(f"    ⚠️  Missing examples: {stats['layer3_without_examples']} ({stats['layer3_without_examples']/stats['layer3_with_rels']*100:.1f}%)")
        
        print(f"\n  Layer 4 (Confused):")
        print(f"    Words with CONFUSED_WITH relationships: {stats['layer4_with_rels']}")
        if stats['layer4_with_rels'] > 0:
            print(f"    ⚠️  Missing examples: {stats['layer4_without_examples']} ({stats['layer4_without_examples']/stats['layer4_with_rels']*100:.1f}%)")
        
        # Show missing layers
        if stats["missing_layers"]:
            print(f"\n⚠️  Missing Layers Found: {len(stats['missing_layers'])}")
            print("\nFirst 10 issues:")
            for i, issue in enumerate(stats["missing_layers"][:10], 1):
                print(f"  {i}. {issue['word']} ({issue['sense_id']}): {issue['issue']}")
            
            if len(stats["missing_layers"]) > 10:
                print(f"\n... and {len(stats['missing_layers']) - 10} more issues")
        else:
            print("\n✅ All layers complete where appropriate!")


if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_layer_completeness(conn)
    finally:
        conn.close()

