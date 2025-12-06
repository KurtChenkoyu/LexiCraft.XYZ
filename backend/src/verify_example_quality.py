"""
Verification Script: Example Quality Check

Verifies naturalness and clarity of examples:
- Examples are natural and modern (not awkward/outdated)
- Examples clearly illustrate the target sense
- Layer 2 examples show appropriate contrast
- Layer 3 examples show meaningful differences
- Layer 4 examples actually clarify confusion
"""

import json
from src.database.neo4j_connection import Neo4jConnection


def check_example_naturalness(example_text: str) -> list:
    """Basic heuristics for example naturalness."""
    issues = []
    
    # Check for outdated phrases
    outdated_phrases = ["thou", "hath", "doth", "art", "shalt"]
    if any(phrase in example_text.lower() for phrase in outdated_phrases):
        issues.append("Contains outdated language")
    
    # Check for awkward constructions
    awkward_patterns = ["the the ", "a a ", "is is ", "was was "]
    if any(pattern in example_text.lower() for pattern in awkward_patterns):
        issues.append("Contains awkward repetition")
    
    # Check length (too short or too long)
    words = example_text.split()
    if len(words) < 3:
        issues.append("Too short (less than 3 words)")
    elif len(words) > 30:
        issues.append("Too long (more than 30 words)")
    
    return issues


def verify_example_quality(conn: Neo4jConnection):
    """Verify quality of examples across all layers."""
    print("=" * 60)
    print("STAGE 2: EXAMPLE QUALITY CHECK")
    print("=" * 60)
    
    with conn.get_session() as session:
        # Get Stage 2 enriched senses
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.stage2_enriched = true
            RETURN w.name as word, s.id as sense_id,
                   s.definition_en as definition,
                   s.examples_contextual as contextual,
                   s.examples_opposite as opposite,
                   s.examples_similar as similar,
                   s.examples_confused as confused
            LIMIT 20
        """)
        
        records = list(result)
        if not records:
            print("❌ No Stage 2 enriched senses found.")
            return
        
        print(f"Checking quality of examples for {len(records)} senses...\n")
        
        quality_issues = []
        stats = {
            "total_examples": 0,
            "naturalness_issues": 0,
            "clarity_issues": 0,
            "contrast_issues": 0,
            "difference_issues": 0,
            "clarification_issues": 0
        }
        
        for record in records:
            word = record["word"]
            sense_id = record["sense_id"]
            definition = record.get("definition", "")
            # Parse JSON strings if they exist
            contextual_raw = record.get("contextual") or "[]"
            opposite_raw = record.get("opposite") or "[]"
            similar_raw = record.get("similar") or "[]"
            confused_raw = record.get("confused") or "[]"
            
            contextual = json.loads(contextual_raw) if isinstance(contextual_raw, str) else (contextual_raw or [])
            opposite = json.loads(opposite_raw) if isinstance(opposite_raw, str) else (opposite_raw or [])
            similar = json.loads(similar_raw) if isinstance(similar_raw, str) else (similar_raw or [])
            confused = json.loads(confused_raw) if isinstance(confused_raw, str) else (confused_raw or [])
            
            # Check Layer 1 (Contextual)
            for ex in contextual:
                stats["total_examples"] += 1
                example_text = ex.get("example_en", "")
                
                # Naturalness check
                naturalness_issues = check_example_naturalness(example_text)
                if naturalness_issues:
                    stats["naturalness_issues"] += 1
                    quality_issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "contextual",
                        "issue": f"Naturalness: {', '.join(naturalness_issues)}",
                        "example": example_text[:100]
                    })
                
                # Clarity check (word should appear in example)
                if word.lower() not in example_text.lower():
                    stats["clarity_issues"] += 1
                    quality_issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "contextual",
                        "issue": "Clarity: Target word not found in example",
                        "example": example_text[:100]
                    })
            
            # Check Layer 2 (Opposites) - should show contrast
            for ex in opposite:
                stats["total_examples"] += 1
                example_text = ex.get("example_en", "")
                rel_word = ex.get("relationship_word", "")
                
                # Check if both words appear (showing contrast)
                if rel_word and rel_word.lower() not in example_text.lower():
                    stats["contrast_issues"] += 1
                    quality_issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "opposite",
                        "issue": f"Contrast: Relationship word '{rel_word}' not in example",
                        "example": example_text[:100]
                    })
            
            # Check Layer 3 (Similar) - should show difference
            for ex in similar:
                stats["total_examples"] += 1
                example_text = ex.get("example_en", "")
                rel_word = ex.get("relationship_word", "")
                
                # Check if synonym appears
                if rel_word and rel_word.lower() not in example_text.lower():
                    stats["difference_issues"] += 1
                    quality_issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "similar",
                        "issue": f"Difference: Relationship word '{rel_word}' not in example",
                        "example": example_text[:100]
                    })
            
            # Check Layer 4 (Confused) - should clarify
            for ex in confused:
                stats["total_examples"] += 1
                example_text = ex.get("example_en", "")
                rel_word = ex.get("relationship_word", "")
                
                # Check if confused word appears
                if rel_word and rel_word.lower() not in example_text.lower():
                    stats["clarification_issues"] += 1
                    quality_issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "confused",
                        "issue": f"Clarification: Relationship word '{rel_word}' not in example",
                        "example": example_text[:100]
                    })
        
        # Report results
        print(f"📊 Quality Statistics:")
        print(f"  Total examples checked: {stats['total_examples']}")
        print(f"  Naturalness issues: {stats['naturalness_issues']} ({stats['naturalness_issues']/max(stats['total_examples'],1)*100:.1f}%)")
        print(f"  Clarity issues: {stats['clarity_issues']} ({stats['clarity_issues']/max(stats['total_examples'],1)*100:.1f}%)")
        print(f"  Contrast issues (Layer 2): {stats['contrast_issues']}")
        print(f"  Difference issues (Layer 3): {stats['difference_issues']}")
        print(f"  Clarification issues (Layer 4): {stats['clarification_issues']}")
        
        if quality_issues:
            print(f"\n⚠️  Quality Issues Found: {len(quality_issues)}")
            print("\nFirst 10 issues:")
            for i, issue in enumerate(quality_issues[:10], 1):
                print(f"\n{i}. {issue['word']} ({issue['sense_id']}) - Layer: {issue['layer']}")
                print(f"   Issue: {issue['issue']}")
                print(f"   Example: {issue['example']}")
            
            if len(quality_issues) > 10:
                print(f"\n... and {len(quality_issues) - 10} more issues")
        else:
            print("\n✅ All examples pass quality checks!")


if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_example_quality(conn)
    finally:
        conn.close()

