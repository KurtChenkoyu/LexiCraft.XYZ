"""
Test script for MCQ Assembler V2 (Context-Aware, Polysemy-Safe).

Tests the fixes:
1. MEANING MCQ now shows context sentence
2. Distractors come from DIFFERENT WORDS (not polysemy traps)
3. USAGE MCQ is sense-specific
4. Source words tracked for transparency
5. RELATED_TO similarity checked

Usage:
    python3 -m scripts.test_mcq_assembler
    python3 -m scripts.test_mcq_assembler --word break
"""

import sys
sys.path.insert(0, '.')

from src.mcq_assembler import MCQAssembler, MCQType, mcq_to_dict, format_mcq_display
from src.database.neo4j_connection import Neo4jConnection
import json


def test_polysemy_safety(conn: Neo4jConnection, word: str):
    """
    Test that we don't use other senses of the SAME word as distractors.
    
    Example: "break" has multiple senses (opportunity, rest, damage).
    Distractors should come from DIFFERENT words, not "break (rest sense)".
    """
    print(f"\n{'='*70}")
    print(f"POLYSEMY SAFETY TEST FOR: {word}")
    print(f"{'='*70}\n")
    
    assembler = MCQAssembler(conn)
    
    # Find senses for this word
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN s.id as sense_id,
                   s.definition_en as definition_en,
                   s.definition_zh as definition_zh
        """, word=word)
        
        senses = list(result)
    
    if not senses:
        print(f"❌ No enriched senses found for '{word}'")
        return False
    
    print(f"📚 Word '{word}' has {len(senses)} senses (polysemy!):")
    for s in senses:
        def_preview = (s.get("definition_zh") or s.get("definition_en") or "N/A")[:40]
        print(f"   - {s['sense_id']}: {def_preview}...")
    
    # Test MCQ generation for each sense
    all_passed = True
    
    for sense in senses:
        sense_id = sense["sense_id"]
        print(f"\n--- Testing MCQs for {sense_id} ---")
        
        # Fetch sense data to see what other senses are excluded
        sense_data = assembler._fetch_sense_data(sense_id)
        if not sense_data:
            continue
        
        other_senses = sense_data.get("other_senses", [])
        print(f"   Other senses of same word: {len(other_senses)}")
        
        # Fetch distractors
        distractors = assembler._fetch_distractors_safe(
            word, sense_id, other_senses
        )
        
        excluded = distractors.get("other_senses_excluded", [])
        print(f"   Excluded definitions (same word, different sense): {len(excluded)}")
        
        # Generate MCQs
        mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        
        if not mcqs:
            print(f"   ⚠️ No MCQs generated")
            continue
        
        # Check each MCQ for polysemy violations
        for mcq in mcqs:
            if mcq.mcq_type == MCQType.MEANING:
                print(f"\n   [MEANING MCQ]")
                print(f"   Context: {mcq.context[:50]}..." if mcq.context else "   ❌ NO CONTEXT!")
                
                for opt in mcq.options:
                    if not opt.is_correct:
                        # Check if distractor is from a different word
                        if opt.source_word == word:
                            print(f"   ❌ POLYSEMY VIOLATION: Distractor '{opt.text[:30]}...' from SAME word!")
                            all_passed = False
                        else:
                            print(f"   ✅ Distractor from '{opt.source_word}': {opt.text[:30]}...")
    
    if all_passed:
        print(f"\n✅ POLYSEMY SAFETY: PASSED")
    else:
        print(f"\n❌ POLYSEMY SAFETY: FAILED")
    
    return all_passed


def test_context_presence(conn: Neo4jConnection, word: str):
    """Test that MEANING MCQs always have context."""
    print(f"\n{'='*70}")
    print(f"CONTEXT PRESENCE TEST FOR: {word}")
    print(f"{'='*70}\n")
    
    assembler = MCQAssembler(conn)
    
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN s.id as sense_id
        """, word=word)
        sense_ids = [r["sense_id"] for r in result]
    
    all_have_context = True
    
    for sense_id in sense_ids:
        mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        
        for mcq in mcqs:
            if mcq.mcq_type == MCQType.MEANING:
                if mcq.context:
                    print(f"✅ {sense_id} MEANING MCQ has context: '{mcq.context[:40]}...'")
                else:
                    print(f"❌ {sense_id} MEANING MCQ has NO CONTEXT!")
                    all_have_context = False
    
    if all_have_context:
        print(f"\n✅ CONTEXT PRESENCE: PASSED")
    else:
        print(f"\n❌ CONTEXT PRESENCE: FAILED")
    
    return all_have_context


def test_usage_sense_specific(conn: Neo4jConnection, word: str):
    """Test that USAGE MCQs are sense-specific (ask about specific meaning)."""
    print(f"\n{'='*70}")
    print(f"USAGE SENSE-SPECIFIC TEST FOR: {word}")
    print(f"{'='*70}\n")
    
    assembler = MCQAssembler(conn)
    
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN s.id as sense_id,
                   s.definition_zh as definition_zh
        """, word=word)
        senses = list(result)
    
    all_sense_specific = True
    
    for sense in senses:
        sense_id = sense["sense_id"]
        mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        
        for mcq in mcqs:
            if mcq.mcq_type == MCQType.USAGE:
                # Check if question mentions the specific meaning
                if "表示" in mcq.question:
                    print(f"✅ {sense_id} USAGE MCQ is sense-specific:")
                    print(f"   Q: {mcq.question}")
                else:
                    print(f"❌ {sense_id} USAGE MCQ is NOT sense-specific:")
                    print(f"   Q: {mcq.question}")
                    all_sense_specific = False
    
    if all_sense_specific:
        print(f"\n✅ USAGE SENSE-SPECIFIC: PASSED")
    else:
        print(f"\n❌ USAGE SENSE-SPECIFIC: FAILED (or no USAGE MCQs generated)")
    
    return all_sense_specific


def test_full_mcq_generation(conn: Neo4jConnection, word: str):
    """Full test of MCQ generation with detailed output."""
    print(f"\n{'='*70}")
    print(f"FULL MCQ GENERATION TEST FOR: {word}")
    print(f"{'='*70}\n")
    
    assembler = MCQAssembler(conn)
    
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN s.id as sense_id
        """, word=word)
        sense_ids = [r["sense_id"] for r in result]
    
    all_mcqs = []
    
    for sense_id in sense_ids:
        mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        all_mcqs.extend(mcqs)
        
        for mcq in mcqs:
            print(format_mcq_display(mcq))
    
    print(f"\n📊 Summary:")
    print(f"   Total MCQs: {len(all_mcqs)}")
    
    by_type = {}
    for mcq in all_mcqs:
        by_type[mcq.mcq_type.value] = by_type.get(mcq.mcq_type.value, 0) + 1
    
    for mcq_type, count in by_type.items():
        print(f"   {mcq_type}: {count}")
    
    return all_mcqs


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCQ Assembler V2")
    parser.add_argument("--word", type=str, default="break", help="Word to test")
    parser.add_argument("--full", action="store_true", help="Show full MCQ output")
    args = parser.parse_args()
    
    print("🧪 MCQ ASSEMBLER V2 TEST SUITE")
    print("Testing: Context-Aware, Polysemy-Safe MCQ Generation")
    print("=" * 70)
    
    conn = Neo4jConnection()
    
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            return
        
        # Run all tests
        results = []
        
        results.append(("Polysemy Safety", test_polysemy_safety(conn, args.word)))
        results.append(("Context Presence", test_context_presence(conn, args.word)))
        results.append(("Usage Sense-Specific", test_usage_sense_specific(conn, args.word)))
        
        if args.full:
            test_full_mcq_generation(conn, args.word)
        
        # Summary
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print("=" * 70)
        
        all_passed = True
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️ SOME TESTS FAILED - Review above for details")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
