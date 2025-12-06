"""
Parallel version of Level 2 content generation agent.
Processes multiple senses concurrently to speed up generation.

Usage:
    python3 -m src.agent_stage2_parallel --workers 5  # Use 5 parallel workers
    python3 -m src.agent_stage2_parallel --workers 10 --limit 100
"""

import os
import json
import argparse
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from src.database.neo4j_connection import Neo4jConnection
from src.models.learning_point import MultiLayerExamples, ExamplePair

# Import functions from agent_stage2
from src.agent_stage2 import (
    fetch_relationships,
    get_multilayer_examples,
    update_graph_stage2,
    load_checkpoint,
    save_checkpoint
)

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("⚠️ WARNING: GOOGLE_API_KEY not found. Agent will fail if run without --mock.")


# Thread-safe checkpoint saving
checkpoint_lock = threading.Lock()
processed_lock = threading.Lock()


def process_sense(
    record: Dict,
    conn: Neo4jConnection,
    mock: bool,
    checkpoint_file: str,
    processed_senses: set,
    stats: Dict
) -> Tuple[bool, str]:
    """
    Process a single sense. Thread-safe.
    
    Returns:
        (success: bool, sense_id: str)
    """
    word = record["word"]
    sense_id = record["sense_id"]
    definition_en = record.get("definition_en", "")
    definition_zh = record.get("definition_zh", "")
    
    part_of_speech = record.get("part_of_speech")
    existing_example_en = record.get("existing_example_en")
    existing_example_zh = record.get("existing_example_zh")
    usage_ratio = record.get("usage_ratio")
    frequency_rank = record.get("frequency_rank")
    moe_level = record.get("moe_level")
    cefr = record.get("cefr")
    is_moe_word = record.get("is_moe_word", False)
    phrases = record.get("phrases") or []
    
    try:
        # Fetch relationships (with definitions) - now uses sense-specific relationships
        relationships = fetch_relationships(conn, word, sense_id=sense_id)
        
        # Generate multi-layer examples with enhanced context
        examples = get_multilayer_examples(
            sense_id,
            word,
            definition_en,
            definition_zh,
            relationships,
            part_of_speech=part_of_speech,
            existing_example_en=existing_example_en,
            existing_example_zh=existing_example_zh,
            usage_ratio=usage_ratio,
            frequency_rank=frequency_rank,
            moe_level=moe_level,
            cefr=cefr,
            is_moe_word=is_moe_word,
            phrases=phrases,
            mock=mock
        )
        
        if examples:
            # Update graph
            update_graph_stage2(conn, examples)
            
            with processed_lock:
                processed_senses.add(sense_id)
                stats["success"] += 1
                stats["total_processed"] += 1
            
            return (True, sense_id)
        else:
            with processed_lock:
                stats["error"] += 1
            return (False, sense_id)
            
    except Exception as e:
        with processed_lock:
            stats["error"] += 1
        print(f"  ❌ Failed {sense_id}: {e}")
        return (False, sense_id)


def run_stage2_agent_parallel(
    conn: Neo4jConnection,
    target_word: str = None,
    limit: Optional[int] = None,
    mock: bool = False,
    checkpoint_file: str = "level2_checkpoint.json",
    resume: bool = True,
    workers: int = 5
):
    """
    Run Content Level 2 generation agent with parallel processing.
    
    Args:
        conn: Neo4j connection
        target_word: Specific word to process (optional)
        limit: Maximum number of senses to process (None = all)
        mock: Use mock data instead of API
        checkpoint_file: Path to checkpoint file
        resume: Whether to resume from checkpoint
        workers: Number of parallel workers (default: 5)
    """
    print("🎯 Starting Content Level 2 Multi-Layer Example Generation Agent (Parallel)...")
    print(f"   Workers: {workers}")
    
    # Load checkpoint if resuming
    checkpoint = load_checkpoint(checkpoint_file) if resume else {"processed_senses": [], "total_processed": 0}
    processed_senses = set(checkpoint.get("processed_senses", []))
    total_processed = checkpoint.get("total_processed", 0)
    start_time = checkpoint.get("start_time") or time.time()
    
    if resume and processed_senses:
        print(f"📋 Resuming from checkpoint: {len(processed_senses)} senses already processed")
        print(f"   Total processed so far: {total_processed}")
    
    # Fetch all tasks
    with conn.get_session() as session:
        if target_word:
            result = session.run("""
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true 
                  AND (s.stage2_enriched IS NULL OR s.stage2_enriched = false)
                OPTIONAL MATCH (s)<-[:MAPS_TO_SENSE]-(p:Phrase)
                WITH w, s, collect(DISTINCT p.text) as phrases
                RETURN w.name as word, 
                       s.id as sense_id,
                       s.definition_en, 
                       s.definition_zh,
                       s.pos as part_of_speech,
                       s.example_en as existing_example_en,
                       s.example_zh as existing_example_zh,
                       s.usage_ratio as usage_ratio,
                       w.frequency_rank as frequency_rank,
                       w.moe_level as moe_level,
                       w.cefr as cefr,
                       w.is_moe_word as is_moe_word,
                       phrases
            """, word=target_word)
        else:
            query = """
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true 
                  AND (s.stage2_enriched IS NULL OR s.stage2_enriched = false)
                OPTIONAL MATCH (s)<-[:MAPS_TO_SENSE]-(p:Phrase)
                WITH w, s, collect(DISTINCT p.text) as phrases
                RETURN w.name as word, 
                       s.id as sense_id,
                       s.definition_en, 
                       s.definition_zh,
                       s.pos as part_of_speech,
                       s.example_en as existing_example_en,
                       s.example_zh as existing_example_zh,
                       s.usage_ratio as usage_ratio,
                       w.frequency_rank as frequency_rank,
                       w.moe_level as moe_level,
                       w.cefr as cefr,
                       w.is_moe_word as is_moe_word,
                       phrases
                ORDER BY w.frequency_rank ASC, s.usage_ratio DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            result = session.run(query)
        
        tasks = list(result)
    
    # Filter out already processed senses
    if resume and processed_senses:
        original_count = len(tasks)
        tasks = [t for t in tasks if t["sense_id"] not in processed_senses]
        skipped = original_count - len(tasks)
        if skipped > 0:
            print(f"⏭️  Skipping {skipped} already processed senses")
    
    total_tasks = len(tasks)
    print(f"\n📊 Processing {total_tasks} senses (total processed: {total_processed})")
    if limit is None:
        print(f"   (No limit - will process all remaining senses)")
    
    if not tasks:
        print("✅ No senses need Level 2 content generation.")
        return
    
    # Thread-safe stats
    stats = {
        "success": 0,
        "error": 0,
        "total_processed": total_processed
    }
    
    # Process in parallel
    completed = 0
    last_checkpoint_time = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_sense = {
            executor.submit(process_sense, record, conn, mock, checkpoint_file, processed_senses, stats): record["sense_id"]
            for record in tasks
        }
        
        # Process completed tasks
        for future in as_completed(future_to_sense):
            sense_id = future_to_sense[future]
            completed += 1
            
            try:
                success, _ = future.result()
                status = "✅" if success else "⚠️"
                print(f"[{completed}/{total_tasks} ({completed/total_tasks*100:.1f}%)] {status} {sense_id}")
            except Exception as e:
                print(f"[{completed}/{total_tasks}] ❌ {sense_id}: {e}")
            
            # Save checkpoint every 10 successes or every 30 seconds
            current_time = time.time()
            if (stats["total_processed"] % 10 == 0 and stats["total_processed"] > total_processed) or \
               (current_time - last_checkpoint_time > 30):
                with checkpoint_lock:
                    save_checkpoint(checkpoint_file, list(processed_senses), stats["total_processed"], start_time)
                    last_checkpoint_time = current_time
                    elapsed = current_time - start_time
                    rate = stats["total_processed"] / elapsed if elapsed > 0 else 0
                    remaining = total_tasks - completed
                    eta_seconds = remaining / (rate * workers) if rate > 0 else 0
                    print(f"  💾 Checkpoint saved. Rate: {rate*60:.1f} senses/min, ETA: {eta_seconds/60:.1f} min")
    
    # Final checkpoint save
    with checkpoint_lock:
        save_checkpoint(checkpoint_file, list(processed_senses), stats["total_processed"], start_time)
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ Batch Complete!")
    print(f"   Processed: {stats['success']} successful, {stats['error']} errors")
    print(f"   Total processed: {stats['total_processed']}")
    print(f"   Time elapsed: {elapsed/60:.1f} minutes")
    if stats['success'] > 0:
        print(f"   Average rate: {stats['success']/elapsed*60:.1f} senses/minute")
        print(f"   Speedup: ~{workers}x (with {workers} workers)")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Level 2: Multi-Layer Example Generation (Parallel)")
    parser.add_argument("--word", type=str, help="Target word to enrich")
    parser.add_argument("--limit", type=int, default=None, help="Batch size (None = all remaining)")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no API key)")
    parser.add_argument("--checkpoint", type=str, default="level2_checkpoint.json", help="Checkpoint file path")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from checkpoint")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers (default: 5)")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            run_stage2_agent_parallel(
                conn, 
                target_word=args.word, 
                limit=args.limit, 
                mock=args.mock,
                checkpoint_file=args.checkpoint,
                resume=not args.no_resume,
                workers=args.workers
            )
    finally:
        conn.close()


