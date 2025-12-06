#!/usr/bin/env python3
"""
Test Script for MCQ Adaptive Selection System

Tests the complete flow:
1. MCQ Generation (from Neo4j enriched content)
2. MCQ Storage (to PostgreSQL)
3. Ability Estimation (from history/FSRS)
4. Adaptive Selection (matching difficulty to ability)
5. Answer Processing (recording attempts, updating stats)
6. Quality Reporting (viewing stats and flagged MCQs)

Usage:
    python scripts/test_mcq_adaptive.py --all
    python scripts/test_mcq_adaptive.py --generate --store
    python scripts/test_mcq_adaptive.py --select --user-id <uuid>
    python scripts/test_mcq_adaptive.py --quality-report
"""

import sys
import uuid
import argparse
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_mcq_generation():
    """Test MCQ generation from Neo4j."""
    print("\n" + "="*70)
    print("📝 TEST: MCQ Generation from Neo4j")
    print("="*70)
    
    from src.database.neo4j_connection import Neo4jConnection
    from src.mcq_assembler import MCQAssembler, format_mcq_display
    
    conn = Neo4jConnection()
    
    if not conn.verify_connectivity():
        print("❌ Failed to connect to Neo4j")
        return None
    
    assembler = MCQAssembler(conn)
    
    # Test with a few enriched senses
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.stage2_enriched = true
            RETURN s.id as sense_id, w.name as word
            LIMIT 5
        """)
        senses = [(r["sense_id"], r["word"]) for r in result]
    
    if not senses:
        print("⚠️ No enriched senses found. Run Stage 2 enrichment first.")
        conn.close()
        return None
    
    all_mcqs = []
    for sense_id, word in senses:
        print(f"\n🎯 Generating MCQs for: {word} ({sense_id})")
        mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        
        if mcqs:
            print(f"   Generated {len(mcqs)} MCQs:")
            for mcq in mcqs:
                print(f"   - {mcq.mcq_type.value}: {mcq.question[:50]}...")
            all_mcqs.extend(mcqs)
        else:
            print("   No MCQs generated (insufficient distractors)")
    
    conn.close()
    
    print(f"\n✅ Total MCQs generated: {len(all_mcqs)}")
    
    # Show sample with full formatting
    if all_mcqs:
        print("\n📖 Sample MCQ:")
        print(format_mcq_display(all_mcqs[0]))
    
    return all_mcqs


def test_mcq_storage(mcqs=None):
    """Test storing MCQs to PostgreSQL."""
    print("\n" + "="*70)
    print("💾 TEST: MCQ Storage to PostgreSQL")
    print("="*70)
    
    from src.database.postgres_connection import PostgresConnection
    from src.database.postgres_crud import mcq_stats
    
    # Generate MCQs if not provided
    if mcqs is None:
        mcqs = test_mcq_generation()
        if not mcqs:
            print("⚠️ No MCQs to store")
            return False
    
    pg_conn = PostgresConnection()
    db = pg_conn.get_session()
    
    try:
        stored_count = 0
        for mcq in mcqs:
            options = [
                {
                    "text": opt.text,
                    "is_correct": opt.is_correct,
                    "source": opt.source,
                    "source_word": opt.source_word
                }
                for opt in mcq.options
            ]
            
            stored_mcq = mcq_stats.create_mcq(
                session=db,
                sense_id=mcq.sense_id,
                word=mcq.word,
                mcq_type=mcq.mcq_type.value,
                question=mcq.question,
                options=options,
                correct_index=mcq.correct_index,
                context=mcq.context,
                explanation=mcq.explanation,
                metadata=mcq.metadata
            )
            stored_count += 1
            print(f"   ✅ Stored: {mcq.word} ({mcq.mcq_type.value}) -> ID: {stored_mcq.id}")
        
        print(f"\n✅ Stored {stored_count}/{len(mcqs)} MCQs to PostgreSQL")
        return True
        
    except Exception as e:
        print(f"❌ Error storing MCQs: {e}")
        db.rollback()
        return False


def test_adaptive_selection(user_id: str = None):
    """Test adaptive MCQ selection."""
    print("\n" + "="*70)
    print("🎯 TEST: Adaptive MCQ Selection")
    print("="*70)
    
    from src.database.postgres_connection import PostgresConnection
    from src.mcq_adaptive import MCQAdaptiveService, AbilitySource
    
    pg_conn = PostgresConnection()
    db = pg_conn.get_session()
    service = MCQAdaptiveService(db)
    
    # Use provided user_id or generate test one
    if user_id:
        test_user_id = uuid.UUID(user_id)
    else:
        test_user_id = uuid.uuid4()
        print(f"   Using test user ID: {test_user_id}")
    
    # Get a sense with MCQs
    from src.database.models import MCQPool
    sample_mcq = db.query(MCQPool).filter(MCQPool.is_active == True).first()
    
    if not sample_mcq:
        print("⚠️ No MCQs in database. Run --generate --store first.")
        return False
    
    sense_id = sample_mcq.sense_id
    print(f"\n📖 Testing with sense: {sense_id} (word: {sample_mcq.word})")
    
    # Test ability estimation
    print("\n1️⃣ Ability Estimation:")
    ability = service.estimate_ability(test_user_id, sense_id)
    print(f"   Ability: {ability.ability:.3f}")
    print(f"   Confidence: {ability.confidence:.3f}")
    print(f"   Source: {ability.source.value}")
    print(f"   Data points: {ability.data_points}")
    
    # Test MCQ selection
    print("\n2️⃣ Adaptive MCQ Selection:")
    selection = service.get_mcq_for_verification(test_user_id, sense_id)
    
    if selection:
        print(f"   Selected MCQ: {selection.mcq.mcq_type}")
        print(f"   Question: {selection.mcq.question[:60]}...")
        print(f"   User ability: {selection.user_ability:.3f}")
        print(f"   MCQ difficulty: {selection.mcq_difficulty or 'Not calculated yet'}")
        print(f"   Selection reason: {selection.selection_reason}")
        return selection
    else:
        print("   ⚠️ No suitable MCQ found")
        return None


def test_answer_processing(user_id: str = None):
    """Test answer processing and stats update."""
    print("\n" + "="*70)
    print("✏️ TEST: Answer Processing")
    print("="*70)
    
    from src.database.postgres_connection import PostgresConnection
    from src.mcq_adaptive import MCQAdaptiveService
    
    pg_conn = PostgresConnection()
    db = pg_conn.get_session()
    service = MCQAdaptiveService(db)
    
    # Get an MCQ to test with
    selection = test_adaptive_selection(user_id)
    if not selection:
        print("⚠️ No MCQ selected for testing")
        return False
    
    # Use provided user_id or generate test one
    if user_id:
        test_user_id = uuid.UUID(user_id)
    else:
        test_user_id = uuid.uuid4()
    
    mcq = selection.mcq
    
    print("\n3️⃣ Processing Answer:")
    print(f"   MCQ ID: {mcq.id}")
    print(f"   Correct answer index: {mcq.correct_index}")
    
    # Simulate correct answer
    print("\n   📝 Simulating CORRECT answer...")
    result = service.process_answer(
        user_id=test_user_id,
        mcq_id=mcq.id,
        selected_index=mcq.correct_index,  # Correct answer
        response_time_ms=3500,
        context='test'
    )
    
    print(f"   Is correct: {result.is_correct}")
    print(f"   Ability before: {result.ability_before:.3f}")
    print(f"   Ability after: {result.ability_after:.3f}")
    print(f"   MCQ difficulty: {result.mcq_difficulty or 'N/A'}")
    print(f"   Feedback: {result.feedback}")
    
    # Simulate wrong answer
    wrong_index = (mcq.correct_index + 1) % len(mcq.options)
    print(f"\n   📝 Simulating WRONG answer (index {wrong_index})...")
    
    result2 = service.process_answer(
        user_id=test_user_id,
        mcq_id=mcq.id,
        selected_index=wrong_index,  # Wrong answer
        response_time_ms=8000,
        context='test'
    )
    
    print(f"   Is correct: {result2.is_correct}")
    print(f"   Ability before: {result2.ability_before:.3f}")
    print(f"   Ability after: {result2.ability_after:.3f}")
    print(f"   Feedback: {result2.feedback}")
    
    print("\n✅ Answer processing completed successfully")
    return True


def test_quality_reporting():
    """Test quality reporting."""
    print("\n" + "="*70)
    print("📊 TEST: Quality Reporting")
    print("="*70)
    
    from src.database.postgres_connection import PostgresConnection
    from src.mcq_adaptive import MCQAdaptiveService
    
    pg_conn = PostgresConnection()
    db = pg_conn.get_session()
    service = MCQAdaptiveService(db)
    
    # Get quality report
    print("\n1️⃣ Quality Summary:")
    report = service.get_quality_report()
    
    print(f"   Total MCQs: {report['total_mcqs']}")
    print(f"   Active MCQs: {report['active_mcqs']}")
    print(f"   Needs Review: {report['needs_review']}")
    print(f"   Total Attempts: {report['total_attempts']}")
    
    print("\n   Quality Distribution:")
    for level, count in report['quality_distribution'].items():
        print(f"   - {level.capitalize()}: {count}")
    
    if report['avg_quality_score']:
        print(f"\n   Average Quality Score: {report['avg_quality_score']:.3f}")
    
    # Get MCQs needing attention
    print("\n2️⃣ MCQs Needing Attention:")
    issues = service.get_mcqs_needing_attention(limit=5)
    
    if issues:
        for item in issues:
            print(f"\n   ⚠️ {item['word']} ({item['mcq_type']})")
            print(f"      Issue: {item['issue']}")
            print(f"      Reason: {item['reason']}")
    else:
        print("   ✅ No MCQs need attention")
    
    print("\n✅ Quality reporting completed")
    return report


def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "="*70)
    print("🚀 RUNNING ALL MCQ ADAPTIVE SELECTION TESTS")
    print("="*70)
    
    results = {}
    
    # Test 1: MCQ Generation
    mcqs = test_mcq_generation()
    results['generation'] = len(mcqs) if mcqs else 0
    
    if mcqs:
        # Test 2: MCQ Storage
        results['storage'] = test_mcq_storage(mcqs)
        
        # Test 3: Adaptive Selection
        selection = test_adaptive_selection()
        results['selection'] = selection is not None
        
        # Test 4: Answer Processing
        results['processing'] = test_answer_processing()
        
        # Test 5: Quality Reporting
        report = test_quality_reporting()
        results['reporting'] = report is not None
    else:
        print("\n⚠️ Skipping remaining tests due to no MCQs generated")
        results['storage'] = False
        results['selection'] = False
        results['processing'] = False
        results['reporting'] = False
    
    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)
    
    print(f"   MCQ Generation: {'✅' if results['generation'] > 0 else '❌'} ({results['generation']} MCQs)")
    print(f"   MCQ Storage: {'✅' if results['storage'] else '❌'}")
    print(f"   Adaptive Selection: {'✅' if results['selection'] else '❌'}")
    print(f"   Answer Processing: {'✅' if results['processing'] else '❌'}")
    print(f"   Quality Reporting: {'✅' if results['reporting'] else '❌'}")
    
    all_passed = all([
        results['generation'] > 0,
        results['storage'],
        results['selection'],
        results['processing'],
        results['reporting']
    ])
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED - Check output above for details")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Test MCQ Adaptive Selection System")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--generate", action="store_true", help="Test MCQ generation")
    parser.add_argument("--store", action="store_true", help="Store generated MCQs")
    parser.add_argument("--select", action="store_true", help="Test adaptive selection")
    parser.add_argument("--process", action="store_true", help="Test answer processing")
    parser.add_argument("--quality-report", action="store_true", help="Show quality report")
    parser.add_argument("--user-id", type=str, help="User ID for testing")
    
    args = parser.parse_args()
    
    if args.all:
        run_all_tests()
    elif args.generate:
        mcqs = test_mcq_generation()
        if args.store and mcqs:
            test_mcq_storage(mcqs)
    elif args.select:
        test_adaptive_selection(args.user_id)
    elif args.process:
        test_answer_processing(args.user_id)
    elif args.quality_report:
        test_quality_reporting()
    else:
        parser.print_help()
        print("\n💡 Tip: Run --all to test the complete system")


if __name__ == "__main__":
    main()

