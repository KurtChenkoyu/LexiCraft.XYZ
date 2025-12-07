#!/usr/bin/env python3
"""
Vocabulary Pipeline V2 - Main Enrichment Script

This script orchestrates the full vocabulary enrichment pipeline:
1. Load word list (3.5k → 12k words)
2. For each word:
   a. Get WordNet senses
   b. AI selects best senses
   c. Simplify definitions
   d. Get/validate Chinese translations
   e. Generate Taiwan-context examples
   f. Validate examples
   g. Mine relationships from WordNet
3. Compute hop data and connection values
4. Export to vocabulary.json

Usage:
    python scripts/enrich_vocabulary_v2.py --test --limit 10  # Test with 10 words
    python scripts/enrich_vocabulary_v2.py --limit 100        # Process 100 words
    python scripts/enrich_vocabulary_v2.py                    # Full run (12k words)
    python scripts/enrich_vocabulary_v2.py --resume           # Resume from checkpoint
    python scripts/enrich_vocabulary_v2.py --daemon           # Run as auto-restart daemon
"""

import os
import sys
import json
import time
import signal
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import nltk
from nltk.corpus import wordnet as wn

# Ensure WordNet is available
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet...")
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# Import our modules
from src.data_sources.cc_cedict import get_translations, get_best_translation
from src.data_sources.evp_cefr import get_cefr_level
from src.data_sources.spelling import normalize_spelling, is_british_spelling
from src.data_sources.chinese_translation import get_chinese_translation
from src.ai.sense_selector import select_senses, SelectedSense
from src.ai.simplifier import simplify_definition
from src.ai.translator import generate_translation
from src.ai.example_gen import generate_example
from src.ai.validator import validate_example, quick_validate_example
from src.pipeline.status import get_status_manager, PipelineState


@dataclass
class EnrichedSense:
    """A fully enriched word sense."""
    id: str
    word: str
    pos: str
    cefr: str
    tier: int
    definition_en: str
    definition_zh: str
    definition_zh_explanation: str  # NEW: explanation for understanding
    example_en: str
    example_zh_translation: str  # Renamed from example_zh
    example_zh_explanation: str  # NEW: explanation with connection pathways
    validated: bool
    translation_source: str  # NEW: 'omw', 'cc-cedict', 'ai'
    connections: Dict[str, List[str]]
    connection_counts: Dict[str, int]
    value: Dict[str, int]
    hop_1: Dict[str, Any]
    hop_2: Dict[str, Any]
    hop_3: Dict[str, Any]
    network_value: Dict[str, int]


@dataclass
class EnrichmentStats:
    """Statistics for the enrichment run."""
    words_processed: int = 0
    senses_created: int = 0
    ai_calls: int = 0
    validation_passed: int = 0
    validation_failed: int = 0
    errors: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class VocabularyPipelineV2:
    """Main pipeline class for vocabulary enrichment."""
    
    # Cost estimation per API call (Gemini Flash)
    COST_PER_CALL_USD = 0.0001  # Rough estimate
    
    def __init__(
        self,
        test_mode: bool = False,
        limit: Optional[int] = None,
        resume: bool = False,
        daemon_mode: bool = False,
        workers: int = 10
    ):
        self.test_mode = test_mode
        self.limit = limit
        self.resume = resume
        self.daemon_mode = daemon_mode
        self.workers = workers
        self._shutdown_requested = False
        
        # Thread-safe locks
        self.checkpoint_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.data_lock = threading.Lock()
        
        # Paths
        self.backend_dir = Path(__file__).parent.parent
        self.data_dir = self.backend_dir / 'data'
        self.source_dir = self.data_dir / 'source'
        self.logs_dir = self.backend_dir / 'logs'
        
        # Output paths
        self.output_backend = self.data_dir / 'vocabulary.json'
        self.output_frontend = self.backend_dir.parent / 'landing-page' / 'data' / 'vocabulary.json'
        
        # Checkpoint for resume
        self.checkpoint_file = self.logs_dir / 'enrichment_checkpoint.json'
        
        # Create directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = EnrichmentStats()
        
        # Data storage
        self.enriched_senses: Dict[str, Dict] = {}
        self.all_relationships: Dict[str, Dict[str, List[str]]] = {}
        self.processed_words: Set[str] = set()
        
        # Status manager
        self.status_manager = get_status_manager()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load checkpoint if resuming
        if resume and self.checkpoint_file.exists():
            self._load_checkpoint()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n⚠️ Received signal {signum}, shutting down gracefully...")
        self._shutdown_requested = True
    
    def should_stop(self) -> bool:
        """Check if we should stop processing."""
        if self._shutdown_requested:
            return True
        if self.status_manager.should_stop():
            return True
        return False
    
    def _load_checkpoint(self):
        """Load progress from checkpoint file."""
        print("Loading checkpoint...")
        with open(self.checkpoint_file) as f:
            checkpoint = json.load(f)
        
        self.processed_words = set(checkpoint.get('processed_words', []))
        self.enriched_senses = checkpoint.get('enriched_senses', {})
        self.all_relationships = checkpoint.get('relationships', {})
        print(f"  Resuming from {len(self.processed_words)} processed words")
    
    def _save_checkpoint(self):
        """Save progress to checkpoint file (thread-safe)."""
        with self.checkpoint_lock:
            checkpoint = {
                'processed_words': list(self.processed_words),
                'enriched_senses': self.enriched_senses.copy(),
                'relationships': {k: v.copy() for k, v in self.all_relationships.items()},
                'stats': asdict(self.stats),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, ensure_ascii=False)
    
    def load_word_list(self) -> List[Dict]:
        """Load the master word list."""
        word_list_path = self.backend_dir.parent / 'data' / 'processed' / 'master_vocab.csv'
        
        if not word_list_path.exists():
            raise FileNotFoundError(f"Word list not found: {word_list_path}")
        
        words = []
        with open(word_list_path) as f:
            # Skip header
            header = f.readline().strip().split(',')
            
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    word = parts[0]
                    
                    # Skip if already processed (resume mode)
                    if word in self.processed_words:
                        continue
                    
                    # Normalize British spellings
                    american_word = normalize_spelling(word)
                    
                    words.append({
                        'word': american_word,
                        'original': word,
                        'frequency_rank': int(float(parts[1])),
                        'moe_level': int(parts[2]),
                        'ngsl_rank': int(parts[3]) if parts[3] else None
                    })
        
        print(f"Loaded {len(words)} words from master list")
        
        if self.limit:
            words = words[:self.limit]
            print(f"  Limited to {len(words)} words")
        
        return words
    
    def get_wordnet_senses(self, word: str) -> List[Dict]:
        """Get all WordNet senses for a word."""
        synsets = wn.synsets(word)
        
        senses = []
        for syn in synsets:
            senses.append({
                'id': syn.name(),
                'definition': syn.definition(),
                'pos': syn.pos(),
                'lemmas': [l.name().replace('_', ' ') for l in syn.lemmas()],
                'examples': syn.examples()
            })
        
        return senses
    
    def get_wordnet_relationships(self, sense_id: str) -> Dict[str, List[str]]:
        """Get relationships from WordNet for a sense."""
        try:
            synset = wn.synset(sense_id)
        except Exception:
            return {'related': [], 'opposite': []}
        
        related = set()
        opposite = set()
        
        # Get antonyms (opposites)
        for lemma in synset.lemmas():
            for ant in lemma.antonyms():
                opposite.add(ant.synset().name())
        
        # Get similar_tos (for adjectives)
        for sim in synset.similar_tos():
            related.add(sim.name())
        
        # Get also_sees
        for also in synset.also_sees():
            related.add(also.name())
        
        # Get hypernyms (more general)
        for hyper in synset.hypernyms():
            related.add(hyper.name())
        
        # Get hyponyms (more specific) - limit to prevent explosion
        for hypo in synset.hyponyms()[:5]:
            related.add(hypo.name())
        
        return {
            'related': list(related),
            'opposite': list(opposite)
        }
    
    def determine_tier(self, word_data: Dict) -> int:
        """Determine the block tier based on frequency and complexity."""
        freq_rank = word_data.get('frequency_rank', 5000)
        
        if freq_rank < 500:
            return 1  # Basic block
        elif freq_rank < 2000:
            return 2  # Multi-sense block
        elif freq_rank < 5000:
            return 2
        else:
            return 3
    
    def calculate_value(
        self, 
        connections: Dict[str, List[str]], 
        tier: int
    ) -> Dict[str, int]:
        """Calculate XP value based on connections."""
        # Base XP by tier
        TIER_BASE_XP = {1: 100, 2: 150, 3: 200, 4: 500}
        
        # Connection bonuses
        BONUS = {
            'related': 10,
            'opposite': 10,
            'phrases': 20,
            'idioms': 30,
            'morphological': 10
        }
        
        base_xp = TIER_BASE_XP.get(tier, 100)
        
        connection_bonus = 0
        for conn_type, bonus in BONUS.items():
            count = len(connections.get(conn_type, []))
            connection_bonus += count * bonus
        
        return {
            'base_xp': base_xp,
            'connection_bonus': connection_bonus,
            'total_xp': base_xp + connection_bonus
        }
    
    def enrich_word(self, word_data: Dict) -> List[Dict]:
        """
        Enrich a single word through the full pipeline.
        
        Returns list of enriched senses for this word.
        """
        word = word_data['word']
        frequency_rank = word_data.get('frequency_rank', 5000)
        
        # 1. Get WordNet senses
        wordnet_senses = self.get_wordnet_senses(word)
        
        if not wordnet_senses:
            return []
        
        # 2. Get CEFR level
        cefr = get_cefr_level(word, frequency_rank=frequency_rank)
        
        # 3. AI selects best senses
        max_senses = 2 if frequency_rank < 2000 else 1
        selected = select_senses(
            word=word,
            wordnet_senses=wordnet_senses,
            max_senses=max_senses,
            frequency_rank=frequency_rank,
            cefr=cefr
        )
        with self.stats_lock:
            self.stats.ai_calls += 1
        
        if not selected:
            return []
        
        enriched = []
        tier = self.determine_tier(word_data)
        
        for sense in selected:
            try:
                # 4. Simplify definition
                simple_def = simplify_definition(
                    word=word,
                    definition=sense.definition,
                    pos=sense.pos
                )
                with self.stats_lock:
                    self.stats.ai_calls += 1
                
                # 5. Get Chinese translation (uses OMW + CC-CEDICT + AI)
                translation_result = generate_translation(
                    word=word,
                    definition=simple_def,
                    sense_id=sense.sense_id,
                    pos=sense.pos
                )
                with self.stats_lock:
                    self.stats.ai_calls += 1
                
                # 6. Generate example (with balanced context)
                example_result = generate_example(
                    word=word,
                    definition=simple_def,
                    pos=sense.pos
                )
                with self.stats_lock:
                    self.stats.ai_calls += 1
                
                # 7. Validate example
                validation = validate_example(
                    word=word,
                    definition=simple_def,
                    example=example_result.example_en,
                    pos=sense.pos
                )
                with self.stats_lock:
                    self.stats.ai_calls += 1
                    if validation.passed:
                        self.stats.validation_passed += 1
                    else:
                        self.stats.validation_failed += 1
                
                # Regenerate if failed (one retry)
                if not validation.passed and not self.test_mode:
                    example_result = generate_example(word, simple_def, sense.pos)
                    with self.stats_lock:
                        self.stats.ai_calls += 1
                    validation = validate_example(word, simple_def, example_result.example_en, sense.pos)
                    with self.stats_lock:
                        self.stats.ai_calls += 1
                        if validation.passed:
                            self.stats.validation_passed += 1
                            self.stats.validation_failed -= 1
                
                # 8. Get relationships from WordNet
                relationships = self.get_wordnet_relationships(sense.sense_id)
                
                # Store relationships for hop computation later (thread-safe)
                with self.data_lock:
                    self.all_relationships[sense.sense_id] = relationships
                
                # Calculate connection counts
                connection_counts = {
                    'related': len(relationships.get('related', [])),
                    'opposite': len(relationships.get('opposite', [])),
                    'phrases': 0,  # TODO: Add phrase mining
                    'idioms': 0,   # TODO: Add idiom mining
                    'morphological': 0,
                    'total': len(relationships.get('related', [])) + len(relationships.get('opposite', []))
                }
                
                # Calculate value
                value = self.calculate_value(relationships, tier)
                
                enriched_sense = {
                    'id': sense.sense_id,
                    'word': word,
                    'pos': sense.pos,
                    'cefr': cefr,
                    'tier': tier,
                    'definition_en': simple_def,
                    'definition_zh': translation_result.translation,
                    'definition_zh_explanation': translation_result.explanation,
                    'translation_source': translation_result.source,
                    'example_en': example_result.example_en,
                    'example_zh_translation': example_result.example_zh_translation,
                    'example_zh_explanation': example_result.example_zh_explanation,
                    'example_context': example_result.context,
                    'validated': validation.passed,
                    'connections': {
                        'related': relationships.get('related', []),
                        'opposite': relationships.get('opposite', []),
                        'phrases': [],
                        'idioms': [],
                        'morphological': []
                    },
                    'connection_counts': connection_counts,
                    'value': value,
                    # Hop data computed after all senses are processed
                    'hop_1': {'senses': [], 'count': 0, 'unlock_next_at': 0},
                    'hop_2': {'senses': [], 'count': 0, 'unlock_next_at': 0},
                    'hop_3': {'count': 0},
                    'network_value': {'total_reachable': 0, 'potential_xp': 0}
                }
                
                enriched.append(enriched_sense)
                self.stats.senses_created += 1
                
            except Exception as e:
                print(f"    ⚠️ Error enriching sense {sense.sense_id}: {e}")
                self.stats.errors += 1
                continue
        
        return enriched
    
    def compute_hop_data(self):
        """Compute hop data for all senses after enrichment."""
        print("\nComputing hop data...")
        
        # Get all valid sense IDs
        valid_sense_ids = set(self.enriched_senses.keys())
        
        for sense_id, sense_data in tqdm(self.enriched_senses.items(), desc="Computing hops"):
            hop_data = self._compute_hops_for_sense(sense_id, valid_sense_ids)
            
            sense_data['hop_1'] = hop_data.get('hop_1', {'senses': [], 'count': 0, 'unlock_next_at': 0})
            sense_data['hop_2'] = hop_data.get('hop_2', {'senses': [], 'count': 0, 'unlock_next_at': 0})
            sense_data['hop_3'] = hop_data.get('hop_3', {'count': 0})
            sense_data['network_value'] = hop_data.get('network_value', {'total_reachable': 0, 'potential_xp': 0})
    
    def _compute_hops_for_sense(
        self, 
        sense_id: str, 
        valid_sense_ids: Set[str],
        max_hop: int = 3
    ) -> Dict[str, Any]:
        """Compute hop data for a single sense."""
        hop_data = {}
        seen = {sense_id}
        current_frontier = {sense_id}
        
        for hop in range(1, max_hop + 1):
            next_frontier = set()
            
            for node in current_frontier:
                connections = self.all_relationships.get(node, {})
                for conn_type in ['related', 'opposite']:
                    for neighbor in connections.get(conn_type, []):
                        if neighbor not in seen and neighbor in valid_sense_ids:
                            next_frontier.add(neighbor)
                            seen.add(neighbor)
            
            if hop <= 2:
                hop_data[f'hop_{hop}'] = {
                    'senses': list(next_frontier)[:50],  # Limit for size
                    'count': len(next_frontier),
                    'unlock_next_at': max(1, int(len(next_frontier) * 0.6))
                }
            else:
                hop_data[f'hop_{hop}'] = {
                    'count': len(next_frontier)
                }
            
            current_frontier = next_frontier
        
        # Network value
        total_reachable = len(seen) - 1
        hop_data['network_value'] = {
            'total_reachable': total_reachable,
            'potential_xp': total_reachable * 40
        }
        
        return hop_data
    
    def build_graph_data(self) -> Dict[str, List]:
        """Build graph data for visualization."""
        print("\nBuilding graph data...")
        
        nodes = []
        edges = []
        edge_set = set()  # To avoid duplicates
        
        for sense_id, sense_data in self.enriched_senses.items():
            # Add node
            nodes.append({
                'id': sense_id,
                'word': sense_data['word'],
                'pos': sense_data['pos'],
                'value': sense_data['value']['total_xp'],
                'tier': sense_data['tier'],
                'group': str((sense_data.get('frequency_rank', 5000) // 1000) * 1000)
            })
            
            # Add edges
            for related_id in sense_data['connections'].get('related', []):
                if related_id in self.enriched_senses:
                    edge_key = tuple(sorted([sense_id, related_id]))
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        edges.append({
                            'source': sense_id,
                            'target': related_id,
                            'type': 'related',
                            'weight': 1
                        })
            
            for opposite_id in sense_data['connections'].get('opposite', []):
                if opposite_id in self.enriched_senses:
                    edge_key = tuple(sorted([sense_id, opposite_id]))
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        edges.append({
                            'source': sense_id,
                            'target': opposite_id,
                            'type': 'opposite',
                            'weight': 1
                        })
        
        print(f"  Built {len(nodes)} nodes, {len(edges)} edges")
        
        return {'nodes': nodes, 'edges': edges}
    
    def build_output(self, words: List[Dict]) -> Dict[str, Any]:
        """Build the final output structure."""
        print("\nBuilding output structure...")
        
        # Build words dict
        words_dict = {}
        for word_data in words:
            word = word_data['word']
            # Find senses for this word
            sense_ids = [
                sid for sid, sdata in self.enriched_senses.items()
                if sdata['word'] == word
            ]
            
            words_dict[word] = {
                'name': word,
                'frequency_rank': word_data.get('frequency_rank'),
                'moe_level': word_data.get('moe_level'),
                'ngsl_rank': word_data.get('ngsl_rank'),
                'senses': sense_ids
            }
        
        # Build band index
        band_index = {str(band): [] for band in [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9999]}
        for sense_id, sense_data in self.enriched_senses.items():
            word = sense_data['word']
            if word in words_dict:
                freq = words_dict[word].get('frequency_rank', 9999)
                for band in [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]:
                    if freq <= band:
                        band_index[str(band)].append(sense_id)
                        break
                else:
                    band_index['9999'].append(sense_id)
        
        # Build graph data
        graph_data = self.build_graph_data()
        
        return {
            'version': '2.0',
            'exportedAt': datetime.now().isoformat(),
            'stats': {
                'words': len(words_dict),
                'senses': len(self.enriched_senses),
                'validated': self.stats.validation_passed,
                'errors': self.stats.errors
            },
            'words': words_dict,
            'senses': self.enriched_senses,
            'bandIndex': band_index,
            'graph_data': graph_data
        }
    
    def export(self, output_data: Dict):
        """Export vocabulary data to JSON files."""
        print("\nExporting vocabulary data...")
        
        # Ensure directories exist
        self.output_backend.parent.mkdir(parents=True, exist_ok=True)
        self.output_frontend.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to backend
        with open(self.output_backend, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"  Backend: {self.output_backend}")
        
        # Write to frontend
        with open(self.output_frontend, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"  Frontend: {self.output_frontend}")
        
        # Calculate file size
        size_mb = self.output_backend.stat().st_size / 1024 / 1024
        print(f"  File size: {size_mb:.2f} MB")
    
    def save_report(self):
        """Save enrichment report."""
        report_path = self.logs_dir / 'enrichment_report.json'
        
        report = {
            'stats': asdict(self.stats),
            'summary': {
                'words_processed': self.stats.words_processed,
                'senses_created': self.stats.senses_created,
                'validation_rate': (
                    self.stats.validation_passed / max(1, self.stats.validation_passed + self.stats.validation_failed)
                ),
                'error_rate': self.stats.errors / max(1, self.stats.senses_created + self.stats.errors)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved: {report_path}")
    
    def _process_word_worker(self, word_data: Dict) -> Tuple[bool, str, List[Dict]]:
        """
        Process a single word (thread-safe worker function).
        
        Returns:
            (success: bool, word: str, enriched_senses: List[Dict])
        """
        word = word_data['word']
        
        try:
            enriched = self.enrich_word(word_data)
            
            # Thread-safe data storage
            with self.data_lock:
                for sense in enriched:
                    self.enriched_senses[sense['id']] = sense
                self.processed_words.add(word)
            
            # Stats are already updated in enrich_word() with locks
            # Just update words_processed and senses_created here
            with self.stats_lock:
                self.stats.words_processed += 1
                self.stats.senses_created += len(enriched)
            
            return (True, word, enriched)
            
        except Exception as e:
            error_msg = str(e)
            with self.stats_lock:
                self.stats.errors += 1
            self.status_manager.record_error(f"{word}: {error_msg}")
            return (False, word, [])
    
    def _run_sequential(self, words: List[Dict]) -> bool:
        """Run pipeline sequentially (original behavior)."""
        stopped = False
        for i, word_data in enumerate(tqdm(words, desc="Enriching")):
            if self.should_stop():
                print("\n⏸️ Stop requested, saving progress...")
                stopped = True
                break
            
            success, word, enriched = self._process_word_worker(word_data)
            
            if not success:
                print(f"\n  ❌ Error processing '{word}'")
                status = self.status_manager.get_status()
                if status.consecutive_errors >= 10:
                    print("⚠️ Too many consecutive errors, pausing...")
                    self.status_manager.mark_paused()
                    self._save_checkpoint()
                    return False
                continue
            
            # Update status
            with self.stats_lock:
                estimated_cost = self.stats.ai_calls * self.COST_PER_CALL_USD
                self.status_manager.update_progress(
                    processed_words=self.stats.words_processed,
                    current_word=word,
                    total_senses=self.stats.senses_created,
                    validated_senses=self.stats.validation_passed,
                    failed_senses=self.stats.validation_failed,
                    ai_calls=self.stats.ai_calls,
                    estimated_cost_usd=estimated_cost
                )
            
            # Save checkpoint every 25 words
            if (i + 1) % 25 == 0:
                self._save_checkpoint()
            
            # Rate limiting (only in sequential mode)
            if not self.test_mode and (i + 1) % 10 == 0:
                time.sleep(0.5)
        
        return stopped
    
    def _run_parallel(self, words: List[Dict]) -> bool:
        """Run pipeline with parallel workers."""
        total_words = len(words)
        completed = 0
        last_checkpoint_time = time.time()
        last_status_update = time.time()
        last_progress_time = time.time()
        last_progress_count = 0
        
        print(f"🚀 Starting parallel processing with {self.workers} workers")
        print(f"📊 Total words to process: {total_words:,}")
        print(f"💾 Checkpoint will save every 25 words or 15 seconds")
        print(f"📈 Progress updates every 5 words\n")
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_word = {
                executor.submit(self._process_word_worker, word_data): word_data['word']
                for word_data in words
            }
            
            # Process completed tasks
            for future in as_completed(future_to_word):
                if self.should_stop():
                    print("\n⏸️ Stop requested, saving progress...")
                    # Cancel remaining tasks
                    for f in future_to_word:
                        f.cancel()
                    return True
                
                word = future_to_word[future]
                completed += 1
                current_time = time.time()
                
                try:
                    success, _, enriched = future.result()
                    status_icon = "✅" if success else "⚠️"
                    
                    # Progress update every 5 words (more frequent)
                    if completed % 5 == 0 or completed == total_words:
                        elapsed_since_last = current_time - last_progress_time
                        words_since_last = completed - last_progress_count
                        rate = (words_since_last / elapsed_since_last * 60) if elapsed_since_last > 0 else 0
                        
                        with self.stats_lock:
                            progress_pct = (self.stats.words_processed / total_words * 100) if total_words > 0 else 0
                            print(f"[{completed}/{total_words}] {status_icon} {word} | "
                                  f"Processed: {self.stats.words_processed:,} ({progress_pct:.1f}%) | "
                                  f"Rate: {rate:.1f} words/min | "
                                  f"Senses: {self.stats.senses_created:,}")
                        
                        last_progress_time = current_time
                        last_progress_count = completed
                    
                except Exception as e:
                    print(f"[{completed}/{total_words}] ❌ {word}: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Update status more frequently (every 3 seconds or every 25 words)
                if current_time - last_status_update > 3 or completed % 25 == 0:
                    with self.stats_lock:
                        estimated_cost = self.stats.ai_calls * self.COST_PER_CALL_USD
                        self.status_manager.update_progress(
                            processed_words=self.stats.words_processed,
                            current_word=word,
                            total_senses=self.stats.senses_created,
                            validated_senses=self.stats.validation_passed,
                            failed_senses=self.stats.validation_failed,
                            ai_calls=self.stats.ai_calls,
                            estimated_cost_usd=estimated_cost
                        )
                    last_status_update = current_time
                
                # Save checkpoint more frequently (every 25 words or every 15 seconds)
                if completed % 25 == 0 or (current_time - last_checkpoint_time > 15):
                    self._save_checkpoint()
                    last_checkpoint_time = current_time
                    
                    # Calculate ETA with better accuracy
                    with self.stats_lock:
                        if self.stats.start_time:
                            try:
                                start_dt = datetime.fromisoformat(self.stats.start_time)
                                elapsed = (datetime.now() - start_dt).total_seconds()
                            except:
                                elapsed = 1
                        else:
                            elapsed = 1
                        rate = self.stats.words_processed / elapsed if elapsed > 0 else 0
                        remaining = total_words - self.stats.words_processed
                        eta_minutes = (remaining / (rate * self.workers)) / 60 if rate > 0 else 0
                        eta_hours = eta_minutes / 60
                        current_cost = self.stats.ai_calls * self.COST_PER_CALL_USD
                        
                        print(f"  💾 Checkpoint saved | "
                              f"Rate: {rate*60:.1f} words/min | "
                              f"ETA: {eta_hours:.1f}h ({eta_minutes:.0f}min) | "
                              f"Cost: ${current_cost:.2f}")
                
                # Heartbeat check - detect if stuck
                if current_time - last_progress_time > 300:  # 5 minutes without progress
                    with self.stats_lock:
                        if self.stats.words_processed == last_progress_count:
                            print(f"\n⚠️ WARNING: No progress in 5 minutes!")
                            print(f"   Last processed: {last_progress_count} words")
                            print(f"   Current: {self.stats.words_processed} words")
                            print(f"   This may indicate workers are stuck. Consider restarting.")
                            last_progress_time = current_time  # Reset to avoid spam
                
                # Check for too many errors
                status = self.status_manager.get_status()
                if status.consecutive_errors >= 10:
                    print("⚠️ Too many consecutive errors, pausing...")
                    self.status_manager.mark_paused()
                    self._save_checkpoint()
                    return False
        
        return False
    
    def run(self) -> bool:
        """
        Run the full pipeline.
        
        Returns:
            True if completed successfully, False if stopped or failed
        """
        print("=" * 60)
        print("Vocabulary Pipeline V2")
        print("=" * 60)
        print(f"Mode: {'TEST' if self.test_mode else 'PRODUCTION'}")
        print(f"Limit: {self.limit or 'ALL'}")
        print(f"Resume: {self.resume}")
        print(f"Daemon: {self.daemon_mode}")
        print(f"Workers: {self.workers}")
        print()
        
        self.stats.start_time = datetime.now().isoformat()
        
        # Clear any pending stop request
        self.status_manager.clear_stop_request()
        
        # 1. Load word list
        words = self.load_word_list()
        
        if not words:
            print("No words to process!")
            return True
        
        # Start status tracking
        self.status_manager.start_run(total_words=len(words))
        
        # 2. Process each word (parallel or sequential)
        print(f"\nProcessing {len(words)} words...")
        if self.workers > 1:
            print(f"🚀 Using {self.workers} parallel workers")
            stopped = self._run_parallel(words)
        else:
            print("📝 Using sequential processing")
            stopped = self._run_sequential(words)
        
        # Save final checkpoint
        self._save_checkpoint()
        
        if stopped:
            self.status_manager.mark_stopped()
            print("Pipeline stopped by user request")
            return False
        
        # 3. Compute hop data
        self.compute_hop_data()
        
        # 4. Build output
        output_data = self.build_output(words)
        
        # 5. Export
        self.export(output_data)
        
        # 6. Save report
        self.stats.end_time = datetime.now().isoformat()
        self.save_report()
        
        # Mark completed
        self.status_manager.mark_completed()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Pipeline Complete!")
        print("=" * 60)
        print(f"Words processed: {self.stats.words_processed}")
        print(f"Senses created: {self.stats.senses_created}")
        print(f"Validation passed: {self.stats.validation_passed}")
        print(f"Validation failed: {self.stats.validation_failed}")
        print(f"Errors: {self.stats.errors}")
        print(f"AI calls: {self.stats.ai_calls}")
        print(f"Estimated cost: ${self.stats.ai_calls * self.COST_PER_CALL_USD:.2f} USD")
        
        return True


def run_daemon(test_mode: bool = False, limit: Optional[int] = None, workers: int = 10):
    """
    Run the pipeline in daemon mode with auto-restart.
    
    Will automatically resume and retry on failures.
    """
    print("=" * 60)
    print("🔄 DAEMON MODE - Auto-restart enabled")
    print("=" * 60)
    
    max_retries = 10
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        print(f"\n📍 Attempt {attempt + 1}/{max_retries}")
        
        try:
            pipeline = VocabularyPipelineV2(
                test_mode=test_mode,
                limit=limit,
                resume=True,  # Always resume in daemon mode
                daemon_mode=True,
                workers=workers
            )
            
            success = pipeline.run()
            
            if success:
                print("\n✅ Pipeline completed successfully!")
                return True
            
            # Check if it was a user-requested stop
            status = pipeline.status_manager.get_status()
            if status.state == PipelineState.STOPPED.value:
                print("\n⏹️ Pipeline stopped by user request")
                return False
            
            # Otherwise, retry after delay
            print(f"\n⚠️ Pipeline paused/failed, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached, giving up.")
                return False
    
    print("❌ Pipeline failed after max retries")
    return False


def main():
    parser = argparse.ArgumentParser(description='Vocabulary Pipeline V2')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no retries)')
    parser.add_argument('--limit', type=int, help='Limit number of words to process')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode with auto-restart')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers (default: 10)')
    parser.add_argument('--status', action='store_true', help='Show current pipeline status')
    parser.add_argument('--stop', action='store_true', help='Request pipeline to stop')
    args = parser.parse_args()
    
    status_manager = get_status_manager()
    
    # Handle status command
    if args.status:
        status = status_manager.get_status()
        print(json.dumps(status.to_dict(), indent=2))
        return
    
    # Handle stop command
    if args.stop:
        status_manager.request_stop()
        print("Stop requested. Pipeline will stop after current word.")
        return
    
    # Check if already running
    if status_manager.is_running():
        print("⚠️ Pipeline is already running!")
        print("Use --status to check progress or --stop to request stop")
        return
    
    # Run in daemon mode or normal mode
    if args.daemon:
        run_daemon(test_mode=args.test, limit=args.limit, workers=args.workers)
    else:
        pipeline = VocabularyPipelineV2(
            test_mode=args.test,
            limit=args.limit,
            resume=args.resume,
            workers=args.workers
        )
        pipeline.run()


if __name__ == '__main__':
    main()

