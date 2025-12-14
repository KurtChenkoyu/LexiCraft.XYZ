#!/usr/bin/env python3
"""
Stage 3 Complete Dictionary Enrichment

Transforms vocabulary from "academic WordNet" to "production-ready dictionary" using:
1. Layer 1: Deep WordNet extraction (derivations, similar, attributes, etc.)
2. Layer 2: Free Dictionary API (common synonyms/antonyms)
3. Layer 3: Cascading collocations (NGSL → WordNet → Datamuse)

Usage:
    python3 enrich_stage3_complete.py --limit 100          # Test with 100 senses
    python3 enrich_stage3_complete.py                      # Full enrichment
    python3 enrich_stage3_complete.py --resume             # Resume from checkpoint
"""

import argparse
import json
import sys
import os
import threading
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from modules import (
    VocabularyLoader,
    DeepWordNetExtractor,
    FreeDictAPIClient,
    CollocationCascade,
    DataMerger
)


class Stage3Enricher:
    """Main orchestrator for Stage 3 enrichment."""
    
    def __init__(
        self,
        vocab_file: str,
        ngsl_phrase_file: str,
        checkpoint_file: str = 'stage3_checkpoint.json'
    ):
        """
        Initialize enricher.
        
        Args:
            vocab_file: Path to vocabulary.json
            ngsl_phrase_file: Path to NGSL phrases CSV
            checkpoint_file: Path to checkpoint file for resume capability
        """
        print("🚀 Initializing Stage 3 Enricher...")
        print(f"   Vocabulary: {vocab_file}")
        print(f"   NGSL: {ngsl_phrase_file}")
        
        # Initialize components
        self.vocab_loader = VocabularyLoader(vocab_file)
        self.wordnet_extractor = DeepWordNetExtractor(self.vocab_loader)
        self.free_dict_client = FreeDictAPIClient(self.vocab_loader)
        self.collocation_cascade = CollocationCascade(ngsl_phrase_file, {})
        self.merger = DataMerger()
        
        self.checkpoint_file = checkpoint_file
        self.processed_senses = set()
        
        # Thread-safe locks for parallel processing
        self.checkpoint_lock = threading.Lock()
        self.processed_lock = threading.Lock()
        
        print(f"✅ Initialized. Vocabulary has {len(self.vocab_loader.get_all_sense_ids())} senses")
    
    def load_checkpoint(self):
        """Load checkpoint if it exists."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                self.processed_senses = set(checkpoint.get('processed', []))
                print(f"📂 Loaded checkpoint: {len(self.processed_senses)} senses already processed")
    
    def save_checkpoint(self):
        """Save checkpoint (thread-safe)."""
        with self.checkpoint_lock:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'processed': list(self.processed_senses),
                    'timestamp': datetime.now().isoformat()
                }, f)
    
    def mark_processed(self, sense_id: str):
        """Mark sense as processed (thread-safe)."""
        with self.processed_lock:
            self.processed_senses.add(sense_id)
    
    def enrich_sense(self, sense_id: str) -> Dict:
        """
        Enrich a single sense with all three layers.
        
        Args:
            sense_id: The sense ID to enrich
        
        Returns:
            Enriched sense data
        """
        # Get base sense
        sense_data = self.vocab_loader.get_sense(sense_id)
        if not sense_data:
            print(f"⚠️  Sense not found: {sense_id}")
            return None
        
        word = sense_data.get('word', '')
        pos = sense_data.get('pos', '')
        
        # Layer 1: Deep WordNet
        wordnet_data = self.wordnet_extractor.extract_all(sense_id)
        
        # Fix broken references
        if 'connections' in sense_data:
            sense_data['connections'] = self.wordnet_extractor.fix_broken_references(
                sense_data['connections']
            )
        
        # Layer 2: Common Usage (Free Dict)
        common_data = self.free_dict_client.fetch(word)
        
        # Merge Free Dict with existing connections
        connections = sense_data.get('connections', {})
        connections = self.free_dict_client.merge_with_existing(
            connections,
            common_data,
            word
        )
        
        # Layer 3: Collocations (Cascade: NGSL → WordNet → Datamuse)
        collocations = self.collocation_cascade.get_collocations(word, pos)
        
        # Merge all three layers
        enriched = self.merger.merge_layers(
            sense_data,
            wordnet_data,
            connections,
            collocations
        )
        
        return enriched
    
    def enrich_all(self, limit: int = None, resume: bool = False, workers: int = 5):
        """
        Enrich all senses using parallel processing.
        
        Args:
            limit: Optional limit for testing (e.g., 100 senses)
            resume: Whether to resume from checkpoint
            workers: Number of parallel workers (default: 5)
        """
        # Load checkpoint if resuming
        if resume:
            self.load_checkpoint()
        
        # Get all sense IDs
        all_sense_ids = self.vocab_loader.get_all_sense_ids()
        
        # Filter out already processed if resuming
        if resume:
            all_sense_ids = [sid for sid in all_sense_ids if sid not in self.processed_senses]
        
        # Apply limit if specified
        if limit:
            all_sense_ids = all_sense_ids[:limit]
        
        print(f"\n📊 Enriching {len(all_sense_ids)} senses with {workers} workers...")
        print("=" * 60)
        
        # Use ThreadPoolExecutor for parallel processing
        checkpoint_counter = 0
        checkpoint_lock = threading.Lock()  # Lock for checkpoint counter
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_sense = {
                executor.submit(self.enrich_sense, sense_id): sense_id 
                for sense_id in all_sense_ids
            }
            
            # Process completed tasks with progress bar
            with tqdm(total=len(all_sense_ids), desc="Enriching") as pbar:
                for future in as_completed(future_to_sense):
                    sense_id = future_to_sense[future]
                    try:
                        enriched = future.result()
                        
                        if enriched:
                            # Update in vocabulary (vocab_loader already thread-safe for reads)
                            self.vocab_loader.update_sense(sense_id, enriched)
                            self.mark_processed(sense_id)
                            
                            with checkpoint_lock:
                                checkpoint_counter += 1
                                # Save checkpoint every 100 senses
                                if checkpoint_counter >= 100:
                                    self.save_checkpoint()
                                    checkpoint_counter = 0
                        
                        pbar.update(1)
                    
                    except Exception as e:
                        print(f"\n❌ Error processing {sense_id}: {e}")
                        pbar.update(1)
                        continue
        
        # Final checkpoint
        self.save_checkpoint()
        
        print("\n✅ Enrichment complete!")
        self._print_summary()
    
    def _print_summary(self):
        """Print enrichment summary."""
        print("\n" + "=" * 60)
        print("📈 ENRICHMENT SUMMARY")
        print("=" * 60)
        
        # WordNet stats
        wn_stats = self.wordnet_extractor.get_stats()
        print("\n🔷 Layer 1 (WordNet):")
        print(f"   Senses processed: {wn_stats['total_processed']}")
        print(f"   Derivations added: {wn_stats['derivations_added']}")
        print(f"   Morphological forms: {wn_stats['morphological_added']} (comparatives, conjugations, etc.)")
        print(f"   Similar relationships: {wn_stats['similar_added']}")
        print(f"   Attributes: {wn_stats['attributes_added']}")
        print(f"   Broken refs fixed: {wn_stats['broken_refs_fixed']}")
        
        # Free Dict stats
        fd_stats = self.free_dict_client.get_stats()
        print("\n🔷 Layer 2 (Free Dictionary API):")
        print(f"   API calls made: {fd_stats['total_requests']}")
        print(f"   Cache hits: {fd_stats['cache_hits']}")
        print(f"   Synonyms added: {fd_stats['synonyms_added']}")
        print(f"   Antonyms added: {fd_stats['antonyms_added']}")
        print(f"   API errors: {fd_stats['api_errors']}")
        
        # Collocation stats
        col_stats = self.collocation_cascade.get_stats()
        print("\n🔷 Layer 3 (Collocations - Cascade):")
        print(f"   Words processed: {col_stats['total_words']}")
        print(f"   NGSL coverage: {col_stats.get('ngsl_coverage', 'N/A')}")
        print(f"   WordNet coverage: {col_stats.get('wordnet_coverage', 'N/A')}")
        print(f"   Datamuse coverage: {col_stats.get('datamuse_coverage', 'N/A')}")
        print(f"   Total phrases:")
        print(f"     - From NGSL: {col_stats['phrases_from_ngsl']}")
        print(f"     - From WordNet: {col_stats['phrases_from_wordnet']}")
        print(f"     - From Datamuse: {col_stats['phrases_from_datamuse']}")
        
        # Merger stats
        merge_stats = self.merger.get_stats()
        print("\n🔷 Merger:")
        print(f"   Senses merged: {merge_stats['total_merged']}")
        print(f"   Connections added: {merge_stats['connections_added']}")
        print(f"   Collocations added: {merge_stats['collocations_added']}")
        
        print("\n" + "=" * 60)
    
    def save_output(self, output_file: str):
        """Save enriched vocabulary."""
        print(f"\n💾 Saving to {output_file}...")
        self.vocab_loader.save(output_file)
        print("✅ Saved!")
    
    def generate_report(self, report_file: str):
        """Generate validation report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'senses_processed': len(self.processed_senses),
            'layers': {
                'wordnet': self.wordnet_extractor.get_stats(),
                'free_dict': self.free_dict_client.get_stats(),
                'collocations': self.collocation_cascade.get_stats(),
                'merger': self.merger.get_stats()
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Report saved to {report_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Stage 3 Complete Dictionary Enrichment'
    )
    parser.add_argument(
        '--vocab',
        default='../data/vocabulary.json',
        help='Path to vocabulary.json'
    )
    parser.add_argument(
        '--ngsl',
        default='../data/source/ngsl_phrases.csv',
        help='Path to NGSL phrases CSV'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file (default: overwrites input)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of senses (for testing)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from checkpoint'
    )
    parser.add_argument(
        '--report',
        default='enrichment_report_stage3.json',
        help='Path for validation report'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    vocab_file = (script_dir / args.vocab).resolve()
    ngsl_file = (script_dir / args.ngsl).resolve()
    output_file = args.output or str(vocab_file)
    
    # Check files exist
    if not vocab_file.exists():
        print(f"❌ Vocabulary file not found: {vocab_file}")
        sys.exit(1)
    
    # Create enricher
    enricher = Stage3Enricher(
        vocab_file=str(vocab_file),
        ngsl_phrase_file=str(ngsl_file),
        checkpoint_file=str(script_dir / 'stage3_checkpoint.json')
    )
    
    # Run enrichment
    enricher.enrich_all(limit=args.limit, resume=args.resume, workers=args.workers)
    
    # Save output
    enricher.save_output(output_file)
    
    # Generate report
    enricher.generate_report(str(script_dir / args.report))
    
    print("\n🎉 Stage 3 enrichment complete!")


if __name__ == '__main__':
    main()

