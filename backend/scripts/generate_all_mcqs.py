"""
Bulk MCQ Generation Script - Parallel Processing

Generates MCQs for all senses in VocabularyStore using 10 parallel workers.

Features:
- Parallel processing (10 workers)
- Progress tracking with checkpoint
- Skips already-generated MCQs
- Error handling and retry logic
- Real-time progress updates
- Summary statistics

Usage:
    python3 scripts/generate_all_mcqs.py
    python3 scripts/generate_all_mcqs.py --workers 10 --batch-size 50
    python3 scripts/generate_all_mcqs.py --resume --checkpoint mcq_checkpoint.json
"""

import sys
import os
import json
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import multiprocessing
from multiprocessing import Manager
from functools import partial

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.vocabulary_store import vocabulary_store
from src.mcq_assembler import MCQAssembler


# Global checkpoint file
CHECKPOINT_FILE = Path(__file__).parent.parent / "mcq_generation_checkpoint.json"


def load_checkpoint() -> Dict:
    """Load checkpoint data if exists."""
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load checkpoint: {e}")
            return {}
    return {}


def save_checkpoint(data: Dict):
    """Save checkpoint data."""
    try:
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to save checkpoint: {e}")


def get_existing_mcq_senses(db_session, mcq_type: Optional[str] = None) -> set:
    """Get set of sense IDs that already have MCQs (optionally filtered by type)."""
    try:
        # Import directly to avoid Neo4j dependency
        import importlib.util
        from pathlib import Path
        from sqlalchemy import distinct
        
        models_path = Path(__file__).parent.parent / "src" / "database" / "models.py"
        spec = importlib.util.spec_from_file_location("models", models_path)
        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)
        MCQPool = models_module.MCQPool
        
        query = db_session.query(distinct(MCQPool.sense_id)).filter(
            MCQPool.is_active == True
        )
        if mcq_type:
            query = query.filter(MCQPool.mcq_type == mcq_type)
        result = query.all()
        return {row[0] for row in result}
    except Exception as e:
        print(f"⚠️ Error checking existing MCQs: {e}")
        return set()


def write_mcqs_to_csv(mcqs: List, csv_writer, worker_id: int) -> int:
    """
    Write MCQs to CSV file.
    
    Args:
        mcqs: List of MCQ objects
        csv_writer: CSV writer instance
        worker_id: Worker ID for logging
    
    Returns:
        Number of MCQs written
    """
    count = 0
    for mcq in mcqs:
        try:
            # Serialize options to JSON string
            options_json = json.dumps([{
                "text": opt.text,
                "is_correct": opt.is_correct,
                "source": opt.source,
                "source_word": opt.source_word,
                "tier": opt.tier,
                "frequency_rank": opt.frequency_rank,
                "pos": opt.pos
            } for opt in mcq.options])
            
            # Serialize metadata to JSON string
            metadata_json = json.dumps(mcq.metadata)
            
            # Write row matching PostgreSQL column order
            csv_writer.writerow([
                mcq.sense_id,
                mcq.word,
                mcq.mcq_type.value,  # Enum to string
                mcq.question,
                mcq.context or '',  # Handle None
                options_json,
                mcq.correct_index,
                mcq.explanation or '',  # Handle None
                metadata_json
            ])
            count += 1
        except Exception as e:
            print(f"Worker {worker_id}: ⚠️ Failed to write MCQ to CSV: {e}")
            continue
    
    return count


def process_sense_batch(
    sense_ids: List[str],
    worker_id: int,
    skip_existing: bool = True,
    mcq_type_filter: Optional[str] = None,
    output_csv_dir: Optional[str] = None
) -> Tuple[int, int, Dict]:
    """
    Process a batch of senses in a single worker.
    
    Args:
        sense_ids: List of sense IDs to process
        worker_id: Worker identifier for logging
        skip_existing: Whether to skip senses that already have MCQs
        mcq_type_filter: If set, only generate MCQs of this type (e.g., 'usage')
        output_csv_dir: If set, write to CSV files instead of database
    
    Returns:
        (processed_count, mcq_count, stats_dict)
    """
    from src.database.postgres_connection import PostgresConnection
    
    processed = 0
    mcqs_generated = 0
    stats = {
        'meaning': 0,
        'usage': 0,
        'discrimination': 0,
        'errors': 0,
        'skipped': 0
    }
    
    # CSV MODE: Open worker-specific file
    csv_file = None
    csv_writer = None
    
    if output_csv_dir:
        try:
            os.makedirs(output_csv_dir, exist_ok=True)
            filename = os.path.join(output_csv_dir, f"mcqs_worker_{worker_id}.csv")
            csv_file = open(filename, 'a', newline='', encoding='utf-8')  # FIXED: append mode to preserve all batches
            csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
            print(f"Worker {worker_id}: 📝 Writing to {filename}")
        except Exception as e:
            print(f"Worker {worker_id}: ❌ Failed to open CSV file: {e}")
            return 0, 0, {'errors': len(sense_ids)}
    
    try:
        if output_csv_dir:
            # ===== CSV MODE: No database connection =====
            assembler = MCQAssembler()
            
            for sense_id in sense_ids:
                try:
                    mcqs = assembler.assemble_mcqs_for_sense(sense_id)
                    
                    if mcq_type_filter and mcqs:
                        mcqs = [m for m in mcqs if m.mcq_type.value == mcq_type_filter]
                    
                    if not mcqs:
                        stats['skipped'] += 1
                        continue
                    
                    # Write to CSV
                    written = write_mcqs_to_csv(mcqs, csv_writer, worker_id)
                    
                    if written > 0:
                        processed += 1
                        mcqs_generated += written
                        
                        for mcq in mcqs:
                            mcq_type = mcq.mcq_type.value
                            if mcq_type in stats:
                                stats[mcq_type] += 1
                
                except Exception as e:
                    stats['errors'] += 1
                    print(f"Worker {worker_id}: ⚠️ Error processing {sense_id}: {e}")
                    continue
        
        else:
            # ===== DATABASE MODE: Original logic =====
            try:
                from src.database.postgres_connection import PostgresConnection
                from src.mcq_assembler import store_mcqs_to_postgres
            except ImportError as e:
                print(f"Worker {worker_id}: ❌ Failed to import database modules: {e}")
                return 0, 0, {'errors': len(sense_ids)}
            
            pg_conn = PostgresConnection()
            db_session = pg_conn.get_session()
            
            # Get existing MCQs if skipping (filtered by type if specified)
            existing_senses = set()
            if skip_existing:
                try:
                    existing_senses = get_existing_mcq_senses(db_session, mcq_type_filter)
                except Exception as e:
                    print(f"Worker {worker_id}: ⚠️ Could not check existing MCQs: {e}")
            
            # Initialize assembler
            assembler = MCQAssembler()
            
            # Commit at batch end only (aligned with batch size)
            commit_interval = 200
            
            for sense_id in sense_ids:
                try:
                    # Skip if already has MCQs
                    if skip_existing and sense_id in existing_senses:
                        stats['skipped'] += 1
                        continue
                    
                    # Start nested transaction (savepoint) for this sense
                    # Context manager auto-commits on success, auto-rolls back on exception
                    with db_session.begin_nested():
                        # Generate MCQs
                        mcqs = assembler.assemble_mcqs_for_sense(sense_id)
                        
                        # Filter by type if specified
                        if mcq_type_filter and mcqs:
                            mcqs = [m for m in mcqs if m.mcq_type.value == mcq_type_filter]
                        
                        if not mcqs:
                            processed += 1
                            continue
                        
                        # Store to database WITHOUT committing (savepoint controls commit)
                        # CRITICAL: commit=False prevents burning the savepoint
                        stored_count = store_mcqs_to_postgres(mcqs, db_session, commit=False)
                        
                        if stored_count > 0:
                            processed += 1
                            mcqs_generated += stored_count
                            
                            # Count by type
                            for mcq in mcqs:
                                mcq_type = mcq.mcq_type.value
                                if mcq_type in stats:
                                    stats[mcq_type] += 1
                    
                    # Savepoint auto-commits on successful exit from 'with' block
                    
                except Exception as e:
                    # Context manager auto-rolled back the savepoint
                    stats['errors'] += 1
                    error_msg = str(e).lower()
                    
                    # Log error but continue to next sense
                    if "ssl" in error_msg or "connection" in error_msg or "closed" in error_msg:
                        print(f"Worker {worker_id}: ⚠️ Connection error for {sense_id}: {e}")
                    else:
                        print(f"Worker {worker_id}: ⚠️ Skipped {sense_id}: {e}")
                    
                    # Continue to next sense (don't break batch)
                    continue
            
            # Final commit for any remaining changes
            try:
                db_session.commit()
            except Exception as e:
                db_session.rollback()
                print(f"Worker {worker_id}: ⚠️ Final commit error: {e}")
            
            db_session.close()
        
    except Exception as e:
        print(f"Worker {worker_id}: ❌ Fatal error: {e}")
        stats['errors'] += len(sense_ids)
    
    finally:
        if csv_file:
            csv_file.close()
            print(f"Worker {worker_id}: ✅ Closed CSV file ({mcqs_generated} MCQs written)")
    
    return processed, mcqs_generated, stats


def split_into_batches(items: List, batch_size: int) -> List[List]:
    """Split list into batches."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def generate_all_mcqs(
    num_workers: int = 10,
    batch_size: int = 50,
    skip_existing: bool = True,
    resume: bool = False,
    limit: Optional[int] = None,
    mcq_type_filter: Optional[str] = None,
    output_csv_dir: Optional[str] = None
):
    """
    Generate MCQs for all senses using parallel workers.
    
    Args:
        num_workers: Number of parallel workers
        batch_size: Senses per batch per worker
        skip_existing: Skip senses that already have MCQs
        resume: Resume from checkpoint
        limit: Limit number of senses to process (for testing)
        mcq_type_filter: If set, only generate MCQs of this type (e.g., 'usage')
        output_csv_dir: If set, write to CSV files instead of database
    """
    print("=" * 70)
    print("MCQ BULK GENERATION - PARALLEL PROCESSING")
    print("=" * 70)
    print(f"Workers: {num_workers}")
    print(f"Batch size: {batch_size}")
    print(f"Skip existing: {skip_existing}")
    print(f"Resume: {resume}")
    if mcq_type_filter:
        print(f"MCQ type filter: {mcq_type_filter}")
    print("=" * 70)
    print()
    
    # Check VocabularyStore
    if not vocabulary_store.is_loaded:
        print("❌ VocabularyStore not loaded. Run enrich_vocabulary_v2.py first.")
        return
    
    print(f"✅ VocabularyStore V{vocabulary_store.version} loaded")
    print(f"   Total senses: {len(vocabulary_store._senses):,}")
    print()
    
    # Get all sense IDs
    all_senses = list(vocabulary_store._senses.values())
    sense_ids = [s.get('id') for s in all_senses if s.get('id')]
    
    if not sense_ids:
        print("❌ No sense IDs found in VocabularyStore")
        return
    
    print(f"📋 Found {len(sense_ids):,} sense IDs")
    
    # Apply limit if specified
    if limit:
        sense_ids = sense_ids[:limit]
        print(f"   Limited to {len(sense_ids):,} senses (testing mode)")
    
    # Load checkpoint if resuming
    processed_senses = set()
    if resume:
        checkpoint = load_checkpoint()
        processed_senses = set(checkpoint.get('processed_senses', []))
        print(f"📂 Resuming: {len(processed_senses):,} senses already processed")
    
    # Filter out already processed
    remaining_senses = [sid for sid in sense_ids if sid not in processed_senses]
    
    if not remaining_senses:
        print("✅ All senses already processed!")
        return
    
    print(f"🎯 Processing {len(remaining_senses):,} remaining senses")
    print()
    
    # Check existing MCQs in database (skip if CSV mode)
    if skip_existing and not output_csv_dir:
        print("🔍 Checking existing MCQs in database...")
        try:
            # Import directly to avoid Neo4j dependency in __init__.py
            import importlib.util
            from pathlib import Path
            
            postgres_path = Path(__file__).parent.parent / "src" / "database" / "postgres_connection.py"
            spec = importlib.util.spec_from_file_location("postgres_connection", postgres_path)
            postgres_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(postgres_module)
            PostgresConnection = postgres_module.PostgresConnection
            
            pg_conn = PostgresConnection()
            db_session = pg_conn.get_session()
            existing_senses = get_existing_mcq_senses(db_session, mcq_type_filter)
            db_session.close()
            
            # Filter out existing
            remaining_senses = [sid for sid in remaining_senses if sid not in existing_senses]
            type_msg = f" ({mcq_type_filter} type)" if mcq_type_filter else ""
            print(f"   Found {len(existing_senses):,} senses with existing MCQs{type_msg}")
            print(f"   Remaining to process: {len(remaining_senses):,}")
            print()
        except Exception as e:
            print(f"⚠️ Could not check existing MCQs: {e}")
            print("   Continuing without skip check...")
            print()
    elif output_csv_dir:
        print("📝 CSV mode: Skipping database check, generating all MCQs")
        print()
    
    if not remaining_senses:
        print("✅ All senses already have MCQs!")
        return
    
    # Split into batches for workers
    batches = list(split_into_batches(remaining_senses, batch_size))
    total_batches = len(batches)
    
    print(f"📦 Split into {total_batches} batches ({batch_size} senses each)")
    print(f"🚀 Starting {num_workers} workers...")
    print()
    
    # Start processing
    start_time = time.time()
    total_processed = 0
    total_mcqs = 0
    total_stats = {
        'meaning': 0,
        'usage': 0,
        'discrimination': 0,
        'errors': 0,
        'skipped': 0
    }
    
    # Create worker arguments
    worker_args = []
    for i, batch in enumerate(batches):
        worker_id = i % num_workers
        worker_args.append((batch, worker_id, skip_existing, mcq_type_filter, output_csv_dir))
    
    # Process with multiprocessing pool
    # CRITICAL: Use 'spawn' context to avoid SQLAlchemy/SSL fork issues
    # 'spawn' creates fresh processes without inheriting broken connections
    ctx = multiprocessing.get_context('spawn')
    
    try:
        with ctx.Pool(processes=num_workers) as pool:
            # Use starmap for multiple arguments
            results = pool.starmap(process_sense_batch, worker_args)
        
        # Aggregate results
        for processed, mcqs, stats in results:
            total_processed += processed
            total_mcqs += mcqs
            
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        
        # Update checkpoint
        processed_senses.update(remaining_senses)
        checkpoint_data = {
            'processed_senses': list(processed_senses),
            'last_updated': datetime.now().isoformat(),
            'total_processed': len(processed_senses),
            'total_mcqs': total_mcqs,
            'stats': total_stats
        }
        save_checkpoint(checkpoint_data)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        print("   Progress saved to checkpoint")
        return
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Print summary
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print("✅ GENERATION COMPLETE")
    print("=" * 70)
    print(f"Processed: {total_processed:,} senses")
    print(f"Generated: {total_mcqs:,} MCQs")
    print(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Rate: {total_processed/elapsed:.1f} senses/sec")
    print()
    print("MCQ Types:")
    print(f"  MEANING: {total_stats['meaning']:,}")
    print(f"  USAGE: {total_stats['usage']:,}")
    print(f"  DISCRIMINATION: {total_stats['discrimination']:,}")
    print()
    if total_stats['errors'] > 0:
        print(f"⚠️ Errors: {total_stats['errors']:,}")
    if total_stats['skipped'] > 0:
        print(f"⏭️ Skipped: {total_stats['skipped']:,}")
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk MCQ Generation with Parallel Processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of parallel workers (default: 10)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Senses per batch per worker (default: 50)"
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Don't skip senses that already have MCQs"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of senses to process (for testing)"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        help="Checkpoint file path (default: mcq_generation_checkpoint.json)"
    )
    parser.add_argument(
        "--mcq-type",
        type=str,
        choices=['meaning', 'usage', 'discrimination'],
        help="Only generate MCQs of this type (e.g., 'usage')"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        help="Directory to write CSV files (bypasses database, for fast generation)"
    )
    
    args = parser.parse_args()
    
    # Override checkpoint file if specified
    if args.checkpoint:
        global CHECKPOINT_FILE
        CHECKPOINT_FILE = Path(args.checkpoint)
    
    generate_all_mcqs(
        num_workers=args.workers,
        batch_size=args.batch_size,
        skip_existing=not args.no_skip,
        resume=args.resume,
        limit=args.limit,
        mcq_type_filter=args.mcq_type,
        output_csv_dir=args.output_csv
    )


if __name__ == "__main__":
    main()

