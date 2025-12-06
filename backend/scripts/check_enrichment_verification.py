#!/usr/bin/env python3
"""
Comprehensive Enrichment and Verification Status Check
Checks if all words are enriched and verified.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection

def check_enrichment_verification_status(conn: Neo4jConnection):
    """Check comprehensive enrichment and verification status."""
    
    print("=" * 80)
    print("COMPREHENSIVE ENRICHMENT & VERIFICATION STATUS")
    print("=" * 80)
    print()
    
    with conn.get_session() as session:
        # 1. Total counts
        print("📊 OVERALL STATISTICS")
        print("-" * 80)
        
        total_words_result = session.run("""
            MATCH (w:Word)
            RETURN count(w) as total_words
        """).single()
        total_words = total_words_result['total_words']
        print(f"Total Words: {total_words:,}")
        
        total_senses_result = session.run("""
            MATCH (s:Sense)
            RETURN count(s) as total_senses
        """).single()
        total_senses = total_senses_result['total_senses']
        print(f"Total Senses: {total_senses:,}")
        print()
        
        # 2. Enrichment Status
        print("🔍 ENRICHMENT STATUS")
        print("-" * 80)
        
        # Enriched senses
        enriched_senses_result = session.run("""
            MATCH (s:Sense)
            WHERE s.enriched = true
            RETURN count(s) as enriched_senses
        """).single()
        enriched_senses = enriched_senses_result['enriched_senses']
        enriched_percentage = (enriched_senses / total_senses * 100) if total_senses > 0 else 0
        print(f"Enriched Senses: {enriched_senses:,} / {total_senses:,} ({enriched_percentage:.1f}%)")
        
        # Unenriched senses
        unenriched_senses = total_senses - enriched_senses
        unenriched_percentage = (unenriched_senses / total_senses * 100) if total_senses > 0 else 0
        print(f"Unenriched Senses: {unenriched_senses:,} / {total_senses:,} ({unenriched_percentage:.1f}%)")
        print()
        
        # Words with at least one enriched sense
        words_with_enriched_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN count(DISTINCT w) as words_with_enriched
        """).single()
        words_with_enriched = words_with_enriched_result['words_with_enriched']
        words_with_enriched_percentage = (words_with_enriched / total_words * 100) if total_words > 0 else 0
        print(f"Words with at least one enriched sense: {words_with_enriched:,} / {total_words:,} ({words_with_enriched_percentage:.1f}%)")
        
        # Words that are fully enriched (all senses enriched)
        fully_enriched_words_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WITH w, 
                 count(s) as total_senses,
                 sum(CASE WHEN s.enriched = true THEN 1 ELSE 0 END) as enriched_count
            WHERE total_senses > 0 AND enriched_count = total_senses
            RETURN count(w) as fully_enriched_words
        """).single()
        fully_enriched_words = fully_enriched_words_result['fully_enriched_words']
        fully_enriched_percentage = (fully_enriched_words / total_words * 100) if total_words > 0 else 0
        print(f"Words fully enriched (all senses): {fully_enriched_words:,} / {total_words:,} ({fully_enriched_percentage:.1f}%)")
        print()
        
        # 3. Verification Status
        print("✅ VERIFICATION STATUS")
        print("-" * 80)
        
        # Total questions
        total_questions_result = session.run("""
            MATCH (q:Question)
            RETURN count(q) as total_questions
        """).single()
        total_questions = total_questions_result['total_questions']
        print(f"Total Questions: {total_questions:,}")
        
        # Enriched senses with verification questions
        verified_senses_result = session.run("""
            MATCH (s:Sense)-[:VERIFIED_BY]->(q:Question)
            WHERE s.enriched = true
            RETURN count(DISTINCT s) as verified_senses
        """).single()
        verified_senses = verified_senses_result['verified_senses']
        verified_percentage = (verified_senses / enriched_senses * 100) if enriched_senses > 0 else 0
        print(f"Enriched Senses with Questions: {verified_senses:,} / {enriched_senses:,} ({verified_percentage:.1f}%)")
        
        # Enriched senses without verification
        unverified_enriched = enriched_senses - verified_senses
        unverified_percentage = (unverified_enriched / enriched_senses * 100) if enriched_senses > 0 else 0
        print(f"Enriched Senses without Questions: {unverified_enriched:,} / {enriched_senses:,} ({unverified_percentage:.1f}%)")
        print()
        
        # Words with at least one verified sense
        words_with_verified_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)-[:VERIFIED_BY]->(q:Question)
            WHERE s.enriched = true
            RETURN count(DISTINCT w) as words_with_verified
        """).single()
        words_with_verified = words_with_verified_result['words_with_verified']
        words_with_verified_percentage = (words_with_verified / total_words * 100) if total_words > 0 else 0
        print(f"Words with at least one verified sense: {words_with_verified:,} / {total_words:,} ({words_with_verified_percentage:.1f}%)")
        
        # Words that are fully verified (all enriched senses have questions)
        fully_verified_words_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            WITH w,
                 count(s) as enriched_senses,
                 sum(CASE WHEN EXISTS((s)-[:VERIFIED_BY]->(:Question)) THEN 1 ELSE 0 END) as verified_count
            WHERE enriched_senses > 0 AND verified_count = enriched_senses
            RETURN count(w) as fully_verified_words
        """).single()
        fully_verified_words = fully_verified_words_result['fully_verified_words']
        fully_verified_percentage = (fully_verified_words / total_words * 100) if total_words > 0 else 0
        print(f"Words fully verified (all enriched senses have questions): {fully_verified_words:,} / {total_words:,} ({fully_verified_percentage:.1f}%)")
        print()
        
        # 4. Summary
        print("=" * 80)
        print("📋 SUMMARY")
        print("=" * 80)
        
        all_enriched = (enriched_senses == total_senses)
        all_verified = (verified_senses == enriched_senses) if enriched_senses > 0 else False
        
        if all_enriched and all_verified:
            print("✅ ALL WORDS ARE ENRICHED AND VERIFIED!")
        elif all_enriched:
            print("🟡 ALL SENSES ARE ENRICHED, but some are missing verification questions.")
        elif all_verified:
            print("🟡 ALL ENRICHED SENSES ARE VERIFIED, but some senses are not yet enriched.")
        else:
            print("🟠 INCOMPLETE: Some senses are not enriched, and some enriched senses are not verified.")
        
        print()
        print(f"Enrichment Progress: {enriched_senses:,}/{total_senses:,} senses ({enriched_percentage:.1f}%)")
        print(f"Verification Progress: {verified_senses:,}/{enriched_senses:,} enriched senses ({verified_percentage:.1f}%)")
        print()
        
        # 5. Sample of unenriched senses
        if unenriched_senses > 0:
            print("📝 SAMPLE OF UNENRICHED SENSES")
            print("-" * 80)
            unenriched_sample_result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched IS NULL OR s.enriched = false
                RETURN w.name as word, w.frequency_rank as rank, s.id as sense_id
                ORDER BY w.frequency_rank
                LIMIT 10
            """)
            records = list(unenriched_sample_result)
            for i, record in enumerate(records, 1):
                print(f"  {i}. {record['word']} (rank {record['rank']}) - {record['sense_id']}")
            if unenriched_senses > 10:
                print(f"  ... and {unenriched_senses - 10:,} more")
            print()
        
        # 6. Sample of enriched but unverified senses
        if unverified_enriched > 0:
            print("📝 SAMPLE OF ENRICHED BUT UNVERIFIED SENSES")
            print("-" * 80)
            unverified_sample_result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true
                  AND NOT EXISTS((s)-[:VERIFIED_BY]->(:Question))
                RETURN w.name as word, w.frequency_rank as rank, s.id as sense_id
                ORDER BY w.frequency_rank
                LIMIT 10
            """)
            records = list(unverified_sample_result)
            for i, record in enumerate(records, 1):
                print(f"  {i}. {record['word']} (rank {record['rank']}) - {record['sense_id']}")
            if unverified_enriched > 10:
                print(f"  ... and {unverified_enriched - 10:,} more")
            print()

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            check_enrichment_verification_status(conn)
        else:
            print("❌ Failed to connect to Neo4j database.")
            sys.exit(1)
    finally:
        conn.close()


