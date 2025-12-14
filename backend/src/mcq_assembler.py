"""
MCQ Assembler V3: Context-Aware, Polysemy-Safe MCQs

Philosophy:
- Explanation Engine = HELPER (never tested directly)
- MCQ = Simple verification (do you know THIS specific meaning?)
- "Help, not confuse" - supportive, not cruel

V3 Changes:
- Now uses VocabularyStore (in-memory JSON) instead of Neo4j
- Falls back to Neo4j if VocabularyStore not available
- All distractor data comes from embedded connections

MCQ Types:
1. MEANING: "In this sentence, what does X mean?" (with context!)
2. USAGE: "Which sentence shows X meaning [specific sense]?"
3. DISCRIMINATION: "X vs Y - which word fits?" (different words)

Usage:
    python3 -m src.mcq_assembler --word bank --sense bank.n.01
    python3 -m src.mcq_assembler --limit 10
"""

import json
import random
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

# Import VocabularyStore (primary data source in V3)
from src.services.vocabulary_store import vocabulary_store, VocabularyStore

# Neo4j is optional (fallback)
try:
    from src.database.neo4j_connection import Neo4jConnection
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    Neo4jConnection = None


class MCQType(Enum):
    """Types of MCQs we generate - each serves a clear purpose."""
    MEANING = "meaning"           # "In this sentence, what does X mean?"
    USAGE = "usage"               # "Which sentence shows X meaning [sense]?"
    DISCRIMINATION = "discrimination"  # "X vs Y - which word fits?"


@dataclass
class MCQOption:
    """A single MCQ option with full traceability."""
    text: str
    is_correct: bool
    source: str           # "target", "confused", "opposite", "orthographic", "similar", "band_sample"
    source_word: str = "" # The word this definition came from (for transparency)
    tier: int = 5         # 0=correct, 1=confused(best), 2=opposite, 3=orthographic, 4=similar, 5=band_sample(fallback)
    frequency_rank: Optional[int] = None  # Word frequency rank for difficulty matching
    pos: Optional[str] = None  # Part of speech for validation


@dataclass
class MCQ:
    """A complete MCQ ready for verification."""
    sense_id: str
    word: str
    mcq_type: MCQType
    question: str
    context: str              # The example sentence providing context
    options: List[MCQOption]
    correct_index: int
    explanation: str          # Shows AFTER answering (helps learning)
    metadata: Dict = field(default_factory=dict)


class MCQAssembler:
    """
    Assembles fair, context-aware MCQs using VocabularyStore (or Neo4j fallback).
    
    Core Principles:
    1. Always provide CONTEXT (example sentence)
    2. Distractors from DIFFERENT WORDS (not polysemy traps)
    3. Test THIS specific sense, not "any meaning of the word"
    """
    
    # Constants for distractor validation
    FREQUENCY_BAND_TOLERANCE = 2000  # Max rank difference for valid distractor
    
    def __init__(self, vocab_store: VocabularyStore = None, conn=None):
        """
        Initialize MCQ Assembler.
        
        Args:
            vocab_store: VocabularyStore instance (preferred, uses JSON)
            conn: Neo4jConnection (fallback)
        """
        self.vocab = vocab_store or vocabulary_store
        self.conn = conn
        self._use_neo4j = False
        
        # Check if VocabularyStore is loaded
        if not self.vocab.is_loaded:
            if HAS_NEO4J and self.conn:
                print("⚠️ VocabularyStore not loaded, using Neo4j fallback")
                self._use_neo4j = True
            else:
                print("⚠️ VocabularyStore not loaded and no Neo4j connection")
    
    def assemble_mcqs_for_sense(self, sense_id: str) -> List[MCQ]:
        """
        Generate MCQ pool for a single sense.
        
        Returns 8-15 MCQs (enhanced for efficacy):
        - 5-8x MEANING (one per contextual example)
        - 1-3x USAGE (if 8+ examples exist, different correct answers)
        - 2-3x DISCRIMINATION (one per confused word relationship)
        """
        mcqs = []
        
        # Fetch sense data including other senses of same word (for polysemy awareness)
        sense_data = self._fetch_sense_data(sense_id)
        if not sense_data:
            print(f"⚠️ Sense {sense_id} not found or not enriched")
            return []
        
        word = sense_data["word"]
        target_pos = sense_data.get("pos")
        target_rank = sense_data.get("frequency_rank")
        
        # Fetch distractors from DIFFERENT WORDS only (with POS and frequency validation)
        distractors = self._fetch_distractors_safe(
            word, 
            sense_id, 
            sense_data.get("other_senses", []),
            target_pos=target_pos,
            target_rank=target_rank
        )
        
        # Check if sense is too similar to other senses of same word
        is_too_similar = self._is_sense_too_similar_to_others(sense_data, threshold=0.75)
        
        # 1. MEANING MCQs - Skip if too similar to other senses
        if not is_too_similar:
            all_examples = []
            if sense_data.get("examples_contextual"):
                all_examples.extend(sense_data["examples_contextual"])
            elif sense_data.get("example_en"):
                # Fallback to single example_en if no contextual examples
                all_examples.append({
                    "example_en": sense_data["example_en"],
                    "example_zh": sense_data.get("example_zh", "")
                })
            
            for i, example in enumerate(all_examples[:20]):  # Limit to 20 MEANING MCQs (primary senses get 15-20)
                meaning_mcq = self._create_meaning_mcq(sense_data, distractors, example_override=example, example_index=i)
                if meaning_mcq:
                    mcqs.append(meaning_mcq)
        
        # 2. USAGE MCQs - Generate multiple with different correct answers (up to 3)
        if self._has_enough_usage_options(sense_data, distractors):
            examples_contextual = sense_data.get("examples_contextual", [])
            num_usage_mcqs = min(3, len(examples_contextual))
            for correct_idx in range(num_usage_mcqs):
                usage_mcq = self._create_usage_mcq(sense_data, distractors, correct_example_index=correct_idx)
                if usage_mcq:
                    mcqs.append(usage_mcq)
        
        # 3. DISCRIMINATION MCQs - Generate one per confused word (up to 3)
        confused_words = distractors.get("confused", [])
        for i, confused_word_data in enumerate(confused_words[:3]):  # Limit to 3 DISCRIMINATION MCQs
            discrimination_mcq = self._create_discrimination_mcq(
                sense_data, distractors, confused_word_override=confused_word_data, confused_index=i
            )
            if discrimination_mcq:
                mcqs.append(discrimination_mcq)
        
        return mcqs
    
    def _fetch_sense_data(self, sense_id: str) -> Optional[Dict]:
        """
        Fetch sense data AND other senses of the same word (for polysemy awareness).
        Uses VocabularyStore primarily, with Neo4j fallback.
        """
        if self._use_neo4j and self.conn:
            return self._fetch_sense_data_neo4j(sense_id)
        
        # Use VocabularyStore (V3 format)
        sense = self.vocab.get_sense(sense_id)
        if not sense:
            return None
        
        # Build sense_data in expected format
        data = {
            "word": sense.get("word", ""),
            "frequency_rank": sense.get("frequency_rank"),
            "pos": sense.get("pos"),
            "sense_id": sense_id,
            "definition_en": sense.get("definition_en", ""),
            "definition_zh": sense.get("definition_zh", ""),
            "example_en": sense.get("example_en", ""),
            "example_zh": sense.get("example_zh_translation", sense.get("example_zh", "")),
            "examples_contextual": sense.get("examples_contextual", []),  # Use Level 2 enriched examples
            "examples_opposite": sense.get("examples_opposite", []),
            "examples_similar": sense.get("examples_similar", []),
            "examples_confused": sense.get("examples_confused", []),
            "enriched": True,
            "stage2_enriched": sense.get("stage2_version", 0) > 0
        }
        
        # Fallback: Build examples_contextual from example_en if no Level 2 data
        if not data["examples_contextual"] and data["example_en"]:
            data["examples_contextual"] = [{
                "example_en": data["example_en"],
                "example_zh": data["example_zh"]
            }]
        
        # Get other senses of the same word (embedded in V3 format)
        other_sense_ids = self.vocab.get_other_senses_of_word(sense_id)
        data["other_senses"] = []
        for other_id in other_sense_ids:
            other_sense = self.vocab.get_sense(other_id)
            if other_sense and other_sense.get("definition_zh"):
                data["other_senses"].append({
                    "sense_id": other_id,
                    "definition_zh": other_sense.get("definition_zh", ""),
                    "definition_en": other_sense.get("definition_en", "")
                })
        
        return data
    
    def _is_sense_too_similar_to_others(self, sense_data: Dict, threshold: float = 0.75) -> bool:
        """
        Check if this sense is too similar to other senses of the same word.
        
        If definitions are too similar, generating MEANING MCQs becomes a trick question
        rather than a learning tool. Skip MEANING MCQs for such senses.
        
        Uses string similarity (SequenceMatcher) since embeddings are not available
        in vocabulary.json. Threshold of 0.75 means 75% character-level similarity.
        
        Args:
            sense_data: Current sense data with 'other_senses' list
            threshold: Similarity threshold (0.75 = 75% similar)
        
        Returns:
            True if too similar to other senses, False otherwise
        """
        current_def_zh = sense_data.get("definition_zh", "")
        if not current_def_zh:
            return False
        
        other_senses = sense_data.get("other_senses", [])
        if not other_senses:
            return False  # No other senses to compare
        
        for other_sense in other_senses:
            other_def_zh = other_sense.get("definition_zh", "")
            if not other_def_zh:
                continue
            
            # Check similarity using SequenceMatcher (string similarity)
            similarity = SequenceMatcher(None, current_def_zh, other_def_zh).ratio()
            if similarity >= threshold:
                return True  # Too similar!
        
        return False
    
    def _fetch_sense_data_neo4j(self, sense_id: str) -> Optional[Dict]:
        """Fetch sense data from Neo4j (fallback)."""
        if not self.conn:
            return None
        
        with self.conn.get_session() as session:
            # Main sense data
            result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense {id: $sense_id})
                RETURN w.name as word,
                       w.frequency_rank as frequency_rank,
                       s.pos as pos,
                       s.id as sense_id,
                       s.definition_en as definition_en,
                       s.definition_zh as definition_zh,
                       s.example_en as example_en,
                       s.example_zh as example_zh,
                       s.examples_contextual as examples_contextual,
                       s.examples_opposite as examples_opposite,
                       s.examples_similar as examples_similar,
                       s.examples_confused as examples_confused,
                       s.enriched as enriched,
                       s.stage2_enriched as stage2_enriched
            """, sense_id=sense_id)
            
            record = result.single()
            if not record:
                return None
            
            data = dict(record)
            word = data["word"]
            
            # Parse JSON strings for examples
            for key in ["examples_contextual", "examples_opposite", "examples_similar", "examples_confused"]:
                if data.get(key):
                    try:
                        data[key] = json.loads(data[key]) if isinstance(data[key], str) else data[key]
                    except json.JSONDecodeError:
                        data[key] = []
                else:
                    data[key] = []
            
            # Fetch OTHER senses of the same word (for polysemy awareness)
            other_result = session.run("""
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                WHERE s.id <> $sense_id AND s.definition_zh IS NOT NULL
                RETURN s.id as sense_id, 
                       s.definition_zh as definition_zh,
                       s.definition_en as definition_en
            """, word=word, sense_id=sense_id)
            
            data["other_senses"] = [
                {
                    "sense_id": r["sense_id"],
                    "definition_zh": r.get("definition_zh", ""),
                    "definition_en": r.get("definition_en", "")
                }
                for r in other_result
            ]
            
            return data
    
    def _validate_distractor(
        self,
        distractor: Dict,
        target_pos: str,
        target_rank: int,
        strict_pos: bool = True
    ) -> bool:
        """
        Validate a distractor candidate.
        
        Checks:
        1. POS match (if strict_pos=True)
        2. Frequency band proximity (within ±2000 rank)
        """
        # POS validation (if we have POS data)
        if strict_pos and distractor.get("pos") and target_pos:
            # Normalize POS tags (n, v, a, r, s)
            distractor_pos = distractor["pos"].lower()[:1] if distractor.get("pos") else ""
            target_pos_norm = target_pos.lower()[:1] if target_pos else ""
            
            # Allow adjective variants (a, s)
            if target_pos_norm in ("a", "s"):
                if distractor_pos not in ("a", "s"):
                    return False
            elif distractor_pos != target_pos_norm:
                return False
        
        # Frequency band validation (if we have rank data)
        distractor_rank = distractor.get("frequency_rank")
        if distractor_rank is not None and target_rank is not None:
            if abs(distractor_rank - target_rank) > self.FREQUENCY_BAND_TOLERANCE:
                return False
        
        return True
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _get_orthographic_candidates(
        self,
        word: str,
        target_pos: str,
        target_rank: int,
        exclude_words: Set[str],
        max_distance: int = 2,
        limit: int = 4
    ) -> List[Dict]:
        """
        Find words with small edit distance (1-2) that could cause spelling confusion.
        Uses VocabularyStore for candidate search.
        """
        candidates = []
        word_lower = word.lower()
        word_len = len(word)
        
        # Get senses in similar frequency band from VocabularyStore
        min_rank = max(1, (target_rank or 5000) - self.FREQUENCY_BAND_TOLERANCE)
        max_rank = (target_rank or 5000) + self.FREQUENCY_BAND_TOLERANCE
        
        # Get candidate senses from VocabularyStore
        candidate_senses = self.vocab.get_senses_by_rank_range(
            min_rank=min_rank,
            max_rank=max_rank,
            exclude_words=exclude_words,
            limit=500  # Get a pool to search through
        )
        
        seen_words = set(exclude_words)
        seen_words.add(word_lower)
        
        for sense in candidate_senses:
            candidate_word = sense.get("word", "")
            candidate_lower = candidate_word.lower()
            
            # Skip if already used or wrong length
            if candidate_lower in seen_words:
                continue
            if abs(len(candidate_word) - word_len) > 2:
                continue
            
            # Calculate edit distance
            distance = self._levenshtein_distance(word_lower, candidate_lower)
            
            if distance <= max_distance and distance > 0:
                candidate = {
                    "word": candidate_word,
                    "definition_zh": sense.get("definition_zh", ""),
                    "definition_en": sense.get("definition_en", ""),
                    "sense_id": sense.get("id", ""),
                    "pos": sense.get("pos"),
                    "frequency_rank": sense.get("frequency_rank"),
                    "edit_distance": distance
                }
                
                # Validate POS and frequency (relaxed for orthographic)
                if self._validate_distractor(candidate, target_pos, target_rank, strict_pos=False):
                    candidates.append(candidate)
                    seen_words.add(candidate_lower)
                    
                    if len(candidates) >= limit:
                        break
        
        # Sort by edit distance (closer = better distractor)
        candidates.sort(key=lambda x: x.get("edit_distance", 999))
        return candidates[:limit]
    
    def _get_band_sample_candidates(
        self,
        word: str,
        target_pos: str,
        target_rank: int,
        exclude_words: Set[str],
        limit: int = 6
    ) -> List[Dict]:
        """
        Get random words from the same frequency band as fallback distractors.
        Uses VocabularyStore for efficient band sampling.
        """
        candidates = []
        word_lower = word.lower()
        
        # Use tighter band for band sampling (±500)
        band_tolerance = 500
        min_rank = max(1, (target_rank or 5000) - band_tolerance)
        max_rank = (target_rank or 5000) + band_tolerance
        
        # Get candidate senses from VocabularyStore
        candidate_senses = self.vocab.get_senses_by_rank_range(
            min_rank=min_rank,
            max_rank=max_rank,
            pos=target_pos,
            exclude_words=exclude_words,
            limit=limit * 3
        )
        
        seen_words = set(exclude_words)
        seen_words.add(word_lower)
        seen_definitions = set()
        
        # Shuffle for randomness
        random.shuffle(candidate_senses)
        
        for sense in candidate_senses:
            candidate_word = sense.get("word", "")
            candidate_lower = candidate_word.lower()
            definition_zh = sense.get("definition_zh", "")
            
            # Skip if already used or definition already seen
            if candidate_lower in seen_words:
                continue
            if definition_zh in seen_definitions:
                continue
            
            candidate = {
                "word": candidate_word,
                "definition_zh": definition_zh,
                "definition_en": sense.get("definition_en", ""),
                "sense_id": sense.get("id", ""),
                "pos": sense.get("pos"),
                "frequency_rank": sense.get("frequency_rank")
            }
            
            candidates.append(candidate)
            seen_words.add(candidate_lower)
            seen_definitions.add(definition_zh)
            
            if len(candidates) >= limit:
                break
        
        return candidates
    
    def _fetch_distractors_safe(
        self, 
        word: str, 
        target_sense_id: str,
        other_senses: List[Dict],
        target_pos: str = None,
        target_rank: int = None
    ) -> Dict[str, List[Dict]]:
        """
        Fetch distractors from DIFFERENT WORDS only.
        Uses VocabularyStore for embedded connections.
        
        CRITICAL: Excludes definitions from:
        1. Other senses of the SAME word (polysemy trap!)
        2. Definitions too similar to the correct answer
        3. Words with mismatched POS (optional)
        4. Words outside frequency band (±2000 rank)
        """
        distractors = {
            "confused": [],
            "opposite": [],
            "similar": [],
            "other_senses_excluded": []  # Track what we excluded
        }
        
        # Collect definitions from other senses of SAME word (to exclude)
        same_word_definitions = set()
        for sense in other_senses:
            if sense.get("definition_zh"):
                same_word_definitions.add(sense["definition_zh"])
            if sense.get("definition_en"):
                same_word_definitions.add(sense["definition_en"])
        
        distractors["other_senses_excluded"] = list(same_word_definitions)
        
        # Get connections from VocabularyStore (embedded in V3)
        sense = self.vocab.get_sense(target_sense_id)
        if sense:
            connections = sense.get("connections", {})
            
            # CONFUSED_WITH (Tier 1)
            for conf in self.vocab.get_confused_senses(target_sense_id):
                def_zh = conf.get("definition_zh", "")
                if def_zh not in same_word_definitions:
                    candidate = {
                        "word": conf.get("word", ""),
                        "reason": conf.get("reason", "Unknown"),
                        "definition_zh": def_zh,
                        "definition_en": conf.get("definition_en", ""),
                        "sense_id": conf.get("sense_id", ""),
                        "pos": conf.get("pos"),
                        "frequency_rank": conf.get("frequency_rank")
                    }
                    if self._validate_distractor(candidate, target_pos, target_rank, strict_pos=False):
                        distractors["confused"].append(candidate)
            
            # OPPOSITE_TO (Tier 2)
            for opp in self.vocab.get_opposite_senses(target_sense_id):
                def_zh = opp.get("definition_zh", "")
                if def_zh not in same_word_definitions:
                    candidate = {
                        "word": opp.get("word", ""),
                        "definition_zh": def_zh,
                        "definition_en": opp.get("definition_en", ""),
                        "sense_id": opp.get("sense_id", ""),
                        "pos": opp.get("pos"),
                        "frequency_rank": opp.get("frequency_rank")
                    }
                    if self._validate_distractor(candidate, target_pos, target_rank, strict_pos=True):
                        distractors["opposite"].append(candidate)
            
            # RELATED_TO (Tier 4)
            for rel in self.vocab.get_related_senses(target_sense_id):
                def_zh = rel.get("definition_zh", "")
                if def_zh not in same_word_definitions:
                    candidate = {
                        "word": rel.get("word", ""),
                        "definition_zh": def_zh,
                        "definition_en": rel.get("definition_en", ""),
                        "sense_id": rel.get("sense_id", ""),
                        "pos": rel.get("pos"),
                        "frequency_rank": rel.get("frequency_rank")
                    }
                    if self._validate_distractor(candidate, target_pos, target_rank, strict_pos=True):
                        distractors["similar"].append(candidate)
        
        return distractors
    
    def _fill_distractor_pool(
        self,
        sense_data: Dict,
        distractors: Dict,
        correct_def: str,
        target_count: int = 20
    ) -> List[MCQOption]:
        """
        Fill 15-20 distractor slots using waterfall priority.
        
        Enhanced for multiple MCQs per sense - generates larger pool to allow
        different subsets for each MCQ, preventing pattern memorization.
        
        Tier allocation (in priority order):
        1-5: CONFUSED_WITH (semantic - highest pedagogical value)
        6-10: OPPOSITE_TO (semantic - meaning boundaries)
        11-15: Orthographic (Levenshtein <= 2 - visual confusion)
        16-20: RELATED_TO (semantic - use carefully, may be too similar)
        Tier 5 (BAND_SAMPLE): Max 10 (50% cap) - frequency-matched fallback
        """
        pool = []
        seen_definitions = {correct_def}
        seen_words = {sense_data["word"].lower()}
        
        target_pos = sense_data.get("pos")
        target_rank = sense_data.get("frequency_rank")
        word = sense_data["word"]
        
        def add_option(candidate: Dict, source: str, tier: int) -> bool:
            """Helper to add option if not duplicate."""
            def_zh = candidate.get("definition_zh", "")
            if not def_zh or def_zh in seen_definitions:
                return False
            
            word_lower = candidate.get("word", "").lower()
            if word_lower in seen_words:
                return False
            
            pool.append(MCQOption(
                text=def_zh,
                is_correct=False,
                source=source,
                source_word=candidate.get("word", ""),
                tier=tier,
                frequency_rank=candidate.get("frequency_rank"),
                pos=candidate.get("pos")
            ))
            seen_definitions.add(def_zh)
            seen_words.add(word_lower)
            return True
        
        # Tier 1: CONFUSED_WITH (up to 5) - highest value
        for conf in distractors.get("confused", [])[:5]:
            if len(pool) >= target_count:
                break
            add_option(conf, source="confused", tier=1)
        
        # Tier 2: OPPOSITE_TO (up to 5) - meaning boundaries
        for opp in distractors.get("opposite", [])[:5]:
            if len(pool) >= target_count:
                break
            add_option(opp, source="opposite", tier=2)
        
        # Tier 3: Orthographic (up to 5) - visual confusion
        if len(pool) < target_count:
            ortho_candidates = self._get_orthographic_candidates(
                word=word,
                target_pos=target_pos,
                target_rank=target_rank,
                exclude_words=seen_words,
                max_distance=2,
                limit=5
            )
            for ortho in ortho_candidates:
                if len(pool) >= target_count:
                    break
                add_option(ortho, source="orthographic", tier=3)
        
        # Tier 4: RELATED_TO (up to 5) - use carefully
        for sim in distractors.get("similar", [])[:5]:
            if len(pool) >= target_count:
                break
            add_option(sim, source="similar", tier=4)
        
        # Tier 5: Band Sample (fill remaining up to target) - camouflage fallback
        # STRICT CAP: Cannot exceed 50% of target (max 10)
        TIER_5_LIMIT = 10  # 50% of 20
        tier_5_count = 0
        
        if len(pool) < target_count:
            remaining = target_count - len(pool)
            # Don't exceed Tier 5 limit
            remaining = min(remaining, TIER_5_LIMIT - tier_5_count)
            
            if remaining > 0:
                band_candidates = self._get_band_sample_candidates(
                    word=word,
                    target_pos=target_pos,
                    target_rank=target_rank,
                    exclude_words=seen_words,
                    limit=remaining + 5  # Get extras in case some are duplicates
                )
                for bs in band_candidates:
                    if len(pool) >= target_count:
                        break
                    if tier_5_count >= TIER_5_LIMIT:
                        break
                    if add_option(bs, source="band_sample", tier=5):
                        tier_5_count += 1
        
        return pool[:target_count]
    
    def _select_distractor_subset(
        self,
        full_pool: List[MCQOption],
        subset_size: int = 15,
        seed: int = 0,
        prefer_high_tiers: bool = True
    ) -> List[MCQOption]:
        """
        Select a subset of distractors from the full pool for a single MCQ.
        
        Uses deterministic selection based on seed to ensure reproducibility
        while allowing different subsets for different MCQs of the same sense.
        
        Stores up to 15 distractors (expanded from 8) to maximize runtime variety.
        The API layer (select_options_from_pool) randomly picks 5 from this pool,
        creating the "Last War" dynamic feel where repeated attempts feel fresh.
        
        Args:
            full_pool: Full pool of distractors (up to 20)
            subset_size: Number of distractors to select (default 15, up from 8)
            seed: Seed for selection (use example_index or confused_index)
            prefer_high_tiers: If True, prioritize tier 1-2 distractors
        """
        if len(full_pool) <= subset_size:
            return full_pool
        
        # Group by tier
        tier_groups = {}
        for opt in full_pool:
            tier = opt.tier
            if tier not in tier_groups:
                tier_groups[tier] = []
            tier_groups[tier].append(opt)
        
        selected = []
        
        if prefer_high_tiers:
            # Select at least some from each tier (if available)
            # Tier 1 (confused): take 2
            # Tier 2 (opposite): take 2
            # Tier 3 (orthographic): take 1
            # Tier 4 (similar): take 1
            # Tier 5 (band_sample): fill remaining
            
            tier_quotas = {1: 2, 2: 2, 3: 1, 4: 1, 5: 2}
            
            for tier in sorted(tier_groups.keys()):
                quota = tier_quotas.get(tier, 1)
                available = tier_groups[tier]
                
                # Use seed to rotate which items we pick
                if len(available) > quota:
                    start_idx = seed % len(available)
                    rotated = available[start_idx:] + available[:start_idx]
                    selected.extend(rotated[:quota])
                else:
                    selected.extend(available)
                
                if len(selected) >= subset_size:
                    break
        else:
            # Random selection with seed
            rng = random.Random(seed)
            selected = rng.sample(full_pool, min(subset_size, len(full_pool)))
        
        # If we still need more, add from remaining pool
        if len(selected) < subset_size:
            remaining = [opt for opt in full_pool if opt not in selected]
            rng = random.Random(seed + 1000)
            rng.shuffle(remaining)
            selected.extend(remaining[:subset_size - len(selected)])
        
        return selected[:subset_size]
    
    def _create_meaning_mcq(
        self, 
        sense_data: Dict, 
        distractors: Dict,
        example_override: Optional[Dict] = None,
        example_index: int = 0
    ) -> Optional[MCQ]:
        """
        Create MEANING MCQ with CONTEXT.
        
        Generates 8 distractors using waterfall strategy.
        
        Args:
            sense_data: Sense data including definitions and examples
            distractors: Distractor candidates from various sources
            example_override: Optional specific example to use (for generating multiple MCQs)
            example_index: Index of this example (for unique MCQ identification)
        """
        word = sense_data["word"]
        sense_id = sense_data["sense_id"]
        correct_def = sense_data.get("definition_zh") or sense_data.get("definition_en")
        target_pos = sense_data.get("pos")
        target_rank = sense_data.get("frequency_rank")
        
        if not correct_def:
            return None
        
        # Get context sentence - use override if provided, otherwise fallback
        context_sentence = ""
        if example_override and example_override.get("example_en"):
            context_sentence = example_override["example_en"]
        else:
            examples_contextual = sense_data.get("examples_contextual", [])
            if examples_contextual and examples_contextual[0].get("example_en"):
                context_sentence = examples_contextual[0]["example_en"]
            elif sense_data.get("example_en"):
                context_sentence = sense_data["example_en"]
        
        if not context_sentence:
            return None
        
        # Build options: 1 correct + 8 distractors from waterfall strategy
        options = [
            MCQOption(
                text=correct_def, 
                is_correct=True, 
                source="target",
                source_word=word,
                tier=0,
                frequency_rank=target_rank,
                pos=target_pos
            )
        ]
        
        # Use waterfall strategy to fill large distractor pool (15-20)
        full_distractor_pool = self._fill_distractor_pool(
            sense_data=sense_data,
            distractors=distractors,
            correct_def=correct_def,
            target_count=20
        )
        
        # Select a unique subset for this specific MCQ (based on example_index)
        # Store 15 distractors (up from 8) to maximize runtime variety at API layer
        # API's select_options_from_pool() will randomly pick 5 from this larger pool
        distractor_pool = self._select_distractor_subset(
            full_pool=full_distractor_pool,
            subset_size=15,
            seed=example_index,
            prefer_high_tiers=True
        )
        
        # Require minimum 4 distractors
        if len(distractor_pool) < 4:
            return None
        
        options.extend(distractor_pool)
        random.shuffle(options)
        
        correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
        
        question = f'在這個句子中，"{word}" 是什麼意思？'
        
        explanation = f'正確答案是「{correct_def}」。'
        explanation += f'\n在句子「{context_sentence}」中，"{word}" 表示「{correct_def}」。'
        
        # Track distractor tier distribution
        tier_distribution = {}
        for opt in distractor_pool:
            tier_distribution[opt.source] = tier_distribution.get(opt.source, 0) + 1
        
        return MCQ(
            sense_id=sense_id,
            word=word,
            mcq_type=MCQType.MEANING,
            question=question,
            context=context_sentence,
            options=options,
            correct_index=correct_index,
            explanation=explanation,
            metadata={
                "distractor_sources": [
                    {"source": opt.source, "word": opt.source_word, "tier": opt.tier} 
                    for opt in options if not opt.is_correct
                ],
                "tier_distribution": tier_distribution,
                "total_distractors": len(distractor_pool),
                "full_pool_size": len(full_distractor_pool),  # Track total available distractors
                "example_index": example_index  # Track which example this MCQ uses
            }
        )
    
    def _has_enough_usage_options(self, sense_data: Dict, distractors: Dict) -> bool:
        """Check if we have enough different sentences for USAGE MCQ."""
        count = 0
        
        if sense_data.get("examples_contextual"):
            count += len(sense_data["examples_contextual"])
        
        for ex_list in [sense_data.get("examples_confused", []), 
                        sense_data.get("examples_opposite", []),
                        sense_data.get("examples_similar", [])]:
            if ex_list:
                count += len(ex_list)
        
        return count >= 4
    
    def _create_usage_mcq(
        self, 
        sense_data: Dict, 
        distractors: Dict,
        correct_example_index: int = 0
    ) -> Optional[MCQ]:
        """
        Create USAGE MCQ that's SENSE-SPECIFIC.
        
        Args:
            sense_data: Sense data including definitions and examples
            distractors: Distractor candidates from various sources
            correct_example_index: Which contextual example to use as correct answer
        """
        word = sense_data["word"]
        sense_id = sense_data["sense_id"]
        correct_def = sense_data.get("definition_zh") or sense_data.get("definition_en")
        examples_contextual = sense_data.get("examples_contextual", [])
        
        if not examples_contextual or not correct_def:
            return None
        
        # Use the specified example index as correct answer
        if correct_example_index >= len(examples_contextual):
            return None
            
        correct_example = examples_contextual[correct_example_index]
        correct_sentence = correct_example.get("example_en", "")
        
        if not correct_sentence:
            return None
        
        # GUARDRAIL: Only generate USAGE MCQs for polysemous words
        other_sense_data = sense_data.get("other_senses", [])
        if len(other_sense_data) == 0:
            return None  # Cannot ask "which sense?" if word has only one sense
        
        options = [
            MCQOption(
                text=correct_sentence, 
                is_correct=True, 
                source="target",
                source_word=word
            )
        ]
        
        # Build distractors from OTHER SENSES of the SAME WORD
        distractor_sentences = []
        
        for other_sense_dict in other_sense_data[:3]:  # Max 3 other senses
            # Extract sense_id from dict (format: {"sense_id": "...", "definition_zh": "...", "definition_en": "..."})
            other_sense_id = other_sense_dict.get("sense_id") if isinstance(other_sense_dict, dict) else other_sense_dict
            if not other_sense_id:
                continue
            
            other_sense = self.vocab.get_sense(other_sense_id)
            if not other_sense:
                continue
            
            # Get examples from this other sense
            other_examples = other_sense.get("examples_contextual", [])
            if not other_examples and other_sense.get("example_en"):
                other_examples = [{"example_en": other_sense["example_en"]}]
            
            # Add one example from this sense (must contain the word)
            for ex in other_examples[:1]:
                sentence = ex.get("example_en", "")
                if sentence and word.lower() in sentence.lower() and sentence != correct_sentence:
                    distractor_sentences.append(MCQOption(
                        text=sentence,
                        is_correct=False,
                        source="other_sense",
                        source_word=word,  # Same word, different sense!
                        tier=5  # Mark as Tier 5
                    ))
                    break
        
        # Deduplicate
        seen = {correct_sentence}
        unique_distractors = []
        for opt in distractor_sentences:
            if opt.text not in seen:
                seen.add(opt.text)
                unique_distractors.append(opt)
        
        # Require at least one non-target distractor (other sense)
        if len(unique_distractors) < 1:
            return None  # Not enough polysemy for meaningful USAGE MCQ
        
        # Use up to 3 other-sense examples as distractors
        options.extend(unique_distractors[:3])
        random.shuffle(options)
        
        correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
        
        def_display = correct_def[:20] + "..." if len(correct_def) > 20 else correct_def
        question = f'哪一個句子中的 "{word}" 表示「{def_display}」？'
        
        explanation = f'正確答案是：「{correct_sentence}」'
        explanation += f'\n這個句子中的 "{word}" 表示「{correct_def}」。'
        
        return MCQ(
            sense_id=sense_id,
            word=word,
            mcq_type=MCQType.USAGE,
            question=question,
            context="",
            options=options,
            correct_index=correct_index,
            explanation=explanation,
            metadata={
                "target_definition": correct_def,
                "correct_example_index": correct_example_index  # Track which example is correct
            }
        )
    
    def _create_discrimination_mcq(
        self, 
        sense_data: Dict, 
        distractors: Dict,
        confused_word_override: Optional[Dict] = None,
        confused_index: int = 0
    ) -> Optional[MCQ]:
        """
        Create DISCRIMINATION MCQ between DIFFERENT WORDS.
        
        Args:
            sense_data: Sense data including definitions and examples
            distractors: Distractor candidates from various sources
            confused_word_override: Optional specific confused word to use (for generating multiple MCQs)
            confused_index: Index of this confused word (for unique MCQ identification)
        """
        word = sense_data["word"]
        sense_id = sense_data["sense_id"]
        confused = distractors.get("confused", [])
        
        if not confused and not confused_word_override:
            return None
        
        # Use override if provided, otherwise use first confused word
        confused_word_data = confused_word_override if confused_word_override else confused[0]
        confused_word = confused_word_data["word"]
        
        if confused_word == word:
            return None
        
        confusion_reason = confused_word_data.get("reason", "")
        
        # Try to find a context sentence that contains the target word
        examples_contextual = sense_data.get("examples_contextual", [])
        context_sentence = ""
        
        # Try each contextual example to find one that contains the word
        for ex in examples_contextual:
            sentence = ex.get("example_en", "")
            if sentence and word.lower() in sentence.lower():
                context_sentence = sentence
                break
        
        # Fallback to example_en
        if not context_sentence and sense_data.get("example_en"):
            if word.lower() in sense_data["example_en"].lower():
                context_sentence = sense_data["example_en"]
        
        if not context_sentence or word.lower() not in context_sentence.lower():
            return None
        
        # Get both definitions for bilingual format
        definition_en = sense_data.get("definition_en", "")
        definition_zh = sense_data.get("definition_zh", "")
        
        if not definition_en or not definition_zh:
            return None  # Need both for bilingual format
        
        # Clean definitions (remove trailing punctuation)
        clean_def_en = definition_en.rstrip('.。')
        clean_def_zh = definition_zh.rstrip('.。')
        
        # Create bilingual replacement: English / Chinese
        bilingual_def = f"{clean_def_en} / {clean_def_zh}"
        
        # If too long (>80 chars), truncate English part
        MAX_DEF_LENGTH = 80
        if len(bilingual_def) > MAX_DEF_LENGTH:
            remaining = MAX_DEF_LENGTH - len(clean_def_zh) - 6  # Account for " / ..."
            if remaining > 20:
                clean_def_en = clean_def_en[:remaining] + "..."
                bilingual_def = f"{clean_def_en} / {clean_def_zh}"
            else:
                # Just use Chinese if truncation too aggressive
                bilingual_def = clean_def_zh
        
        # Replace word with bilingual definition
        replacement_sentence = context_sentence
        replaced = False
        for variant in [word, word.capitalize(), word.upper(), word.lower()]:
            if variant in replacement_sentence:
                replacement_sentence = replacement_sentence.replace(
                    variant, 
                    f"**({bilingual_def})**",
                    1  # Replace only first occurrence
                )
                replaced = True
                break
        
        if not replaced:
            return None
        
        options = [
            MCQOption(text=word, is_correct=True, source="target", source_word=word)
        ]
        
        # Add the primary confused word first
        added_words = {word.lower()}
        if confused_word.lower() not in added_words:
            options.append(MCQOption(
                text=confused_word,
                is_correct=False,
                source="confused",
                source_word=confused_word
            ))
            added_words.add(confused_word.lower())
        
        # Add other confused words as additional distractors
        for conf in confused:
            if conf["word"].lower() not in added_words and len(options) < 4:
                options.append(MCQOption(
                    text=conf["word"],
                    is_correct=False,
                    source="confused",
                    source_word=conf["word"]
                ))
                added_words.add(conf["word"].lower())
        
        while len(options) < 4:
            options.append(MCQOption(
                text="以上皆非",
                is_correct=False,
                source="none_of_above",
                source_word=""
            ))
        
        random.shuffle(options)
        correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
        
        question = '根據句子中的定義，選擇正確的詞：'
        
        explanation = f'正確答案是 "{word}"。'
        if confusion_reason:
            explanation += f'\n"{word}" 和 "{confused_word}" 容易混淆（{confusion_reason}）。'
        
        return MCQ(
            sense_id=sense_id,
            word=word,
            mcq_type=MCQType.DISCRIMINATION,
            question=question,
            context=replacement_sentence,
            options=options,
            correct_index=correct_index,
            explanation=explanation,
            metadata={
                "confused_with": confused_word,
                "confusion_reason": confusion_reason,
                "original_sentence": context_sentence,
                "confused_index": confused_index  # Track which confused word this MCQ tests
            }
        )
    
    def assemble_mcqs_batch(self, limit: int = 10) -> List[MCQ]:
        """Generate MCQs for multiple senses using VocabularyStore."""
        all_mcqs = []
        
        # Get sense IDs from VocabularyStore
        senses = list(self.vocab._senses.values())[:limit]
        sense_ids = [s.get("id") for s in senses if s.get("definition_zh")]
        
        print(f"🎯 Generating MCQs for {len(sense_ids)} senses...")
        
        for sense_id in sense_ids:
            mcqs = self.assemble_mcqs_for_sense(sense_id)
            all_mcqs.extend(mcqs)
            
            if mcqs:
                print(f"  ✅ {sense_id}: {len(mcqs)} MCQs")
            else:
                print(f"  ⚠️ {sense_id}: No MCQs generated")
        
        return all_mcqs


def mcq_to_dict(mcq: MCQ) -> Dict:
    """Convert MCQ to JSON-serializable dict."""
    return {
        "sense_id": mcq.sense_id,
        "word": mcq.word,
        "type": mcq.mcq_type.value,
        "question": mcq.question,
        "context": mcq.context,
        "options": [
            {
                "text": opt.text, 
                "is_correct": opt.is_correct, 
                "source": opt.source,
                "source_word": opt.source_word,
                "tier": opt.tier,
                "frequency_rank": opt.frequency_rank,
                "pos": opt.pos
            } 
            for opt in mcq.options
        ],
        "correct_index": mcq.correct_index,
        "explanation": mcq.explanation,
        "metadata": mcq.metadata
    }


def format_mcq_display(mcq: MCQ) -> str:
    """Format MCQ for display/debugging."""
    lines = [
        f"\n[{mcq.mcq_type.value.upper()}] Word: {mcq.word} ({mcq.sense_id})",
        f"Q: {mcq.question}"
    ]
    
    if mcq.context:
        lines.append(f"📖 Context: \"{mcq.context}\"")
    
    lines.append("Options:")
    for i, opt in enumerate(mcq.options):
        marker = "✅" if opt.is_correct else "  "
        source_info = f" [{opt.source}: {opt.source_word}]" if opt.source_word else f" [{opt.source}]"
        lines.append(f"  {marker} {chr(65+i)}) {opt.text}{source_info if not opt.is_correct else ''}")
    
    lines.append(f"💡 {mcq.explanation[:100]}...")
    
    return "\n".join(lines)


def store_mcqs_to_postgres(mcqs: List[MCQ], db_session, max_retries: int = 3, commit: bool = True) -> int:
    """
    Store generated MCQs to PostgreSQL with retry logic and session recovery.
    
    Args:
        mcqs: List of MCQ objects to store
        db_session: Database session
        max_retries: Maximum retry attempts for connection errors
        commit: Whether to commit the session after storing (default True)
    
    Returns:
        Number of MCQs successfully stored
    """
    from src.database.postgres_crud import mcq_stats
    import psycopg2
    from sqlalchemy.exc import OperationalError, DisconnectionError
    
    stored_count = 0
    
    for mcq in mcqs:
        retry_count = 0
        stored = False
        
        while retry_count < max_retries and not stored:
            try:
                # Check if session is in a bad state and recover
                try:
                    from sqlalchemy import text
                    db_session.execute(text("SELECT 1"))
                except (OperationalError, DisconnectionError) as e:
                    # Session is in bad state, rollback and continue
                    db_session.rollback()
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        continue
                    else:
                        raise
                
                options = [
                    {
                        "text": opt.text,
                        "is_correct": opt.is_correct,
                        "source": opt.source,
                        "source_word": opt.source_word,
                        "tier": opt.tier,
                        "frequency_rank": opt.frequency_rank,
                        "pos": opt.pos
                    }
                    for opt in mcq.options
                ]
                
                mcq_stats.create_mcq(
                    session=db_session,
                    sense_id=mcq.sense_id,
                    word=mcq.word,
                    mcq_type=mcq.mcq_type.value,
                    question=mcq.question,
                    options=options,
                    correct_index=mcq.correct_index,
                    context=mcq.context,
                    explanation=mcq.explanation,
                    metadata=mcq.metadata,
                    commit=False  # Batch commit at end
                )
                stored_count += 1
                stored = True
                
            except (OperationalError, DisconnectionError, psycopg2.OperationalError) as e:
                # SSL or connection error - rollback and retry
                error_msg = str(e).lower()
                if "ssl" in error_msg or "connection" in error_msg or "closed" in error_msg:
                    db_session.rollback()
                    retry_count += 1
                    if retry_count < max_retries:
                        continue
                    else:
                        print(f"⚠️ Failed to store MCQ for {mcq.sense_id} after {max_retries} retries: {e}")
                        break
                else:
                    # Other operational error - don't retry
                    db_session.rollback()
                    print(f"⚠️ Failed to store MCQ for {mcq.sense_id}: {e}")
                    break
                    
            except Exception as e:
                # Other errors - rollback and skip
                db_session.rollback()
                print(f"⚠️ Failed to store MCQ for {mcq.sense_id}: {e}")
                break
    
    # Commit all successful inserts in one batch (if commit=True)
    if commit:
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            print(f"⚠️ Failed to commit MCQs: {e}")
            raise e  # Re-raise to alert caller
    
    return stored_count


def run_mcq_assembler(word: str = None, sense_id: str = None, limit: int = 10, store: bool = False):
    """
    Main entry point for MCQ assembly.
    Uses VocabularyStore by default (no Neo4j required).
    """
    db_session = None
    
    try:
        # Check if VocabularyStore is loaded
        if not vocabulary_store.is_loaded:
            print("❌ VocabularyStore not loaded. Run enrich_vocabulary_v2.py first.")
            return
        
        print(f"✅ Using VocabularyStore V{vocabulary_store.version}")
        
        # Get PostgreSQL session if storing
        if store:
            from src.database.postgres_connection import PostgresConnection
            pg_conn = PostgresConnection()
            db_session = pg_conn.get_session()
        
        assembler = MCQAssembler()
        
        if sense_id:
            print(f"🎯 Generating MCQs for sense: {sense_id}")
            mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        elif word:
            sense_ids = vocabulary_store.get_sense_ids_for_word(word)
            mcqs = []
            for sid in sense_ids:
                mcqs.extend(assembler.assemble_mcqs_for_sense(sid))
        else:
            mcqs = assembler.assemble_mcqs_batch(limit=limit)
        
        # Print results
        print(f"\n{'='*70}")
        print(f"📊 MCQ GENERATION RESULTS (V3 - VocabularyStore)")
        print(f"{'='*70}")
        print(f"Total MCQs generated: {len(mcqs)}")
        
        by_type = {}
        for mcq in mcqs:
            by_type[mcq.mcq_type.value] = by_type.get(mcq.mcq_type.value, 0) + 1
        
        for mcq_type, count in by_type.items():
            print(f"  {mcq_type}: {count}")
        
        # Store to PostgreSQL if requested
        if store and mcqs and db_session:
            print(f"\n💾 Storing MCQs to PostgreSQL...")
            stored = store_mcqs_to_postgres(mcqs, db_session)
            print(f"✅ Stored {stored}/{len(mcqs)} MCQs to PostgreSQL")
        
        # Show sample MCQs
        if mcqs:
            print(f"\n{'='*70}")
            print(f"📝 SAMPLE MCQs")
            print(f"{'='*70}")
            
            for mcq in mcqs[:5]:
                print(format_mcq_display(mcq))
        
        return mcqs
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCQ Assembler V3 - VocabularyStore Based")
    parser.add_argument("--word", type=str, help="Target word")
    parser.add_argument("--sense", type=str, help="Target sense ID")
    parser.add_argument("--limit", type=int, default=10, help="Batch size")
    parser.add_argument("--store", action="store_true", help="Store MCQs to PostgreSQL")
    args = parser.parse_args()
    
    run_mcq_assembler(word=args.word, sense_id=args.sense, limit=args.limit, store=args.store)
