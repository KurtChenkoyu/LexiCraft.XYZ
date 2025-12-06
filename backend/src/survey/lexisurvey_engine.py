"""
LexiSurvey Engine V2: Probability-Based Vocabulary Assessment

Based on research into established vocabulary assessment methodologies:
- Nation's Vocabulary Levels Test (VLT)
- Computerized Adaptive Testing (CAT) with IRT
- TestYourVocab methodology
- IVST (Intelligent Vocabulary Size Test)

Key differences from V1:
1. NO fixed phases - adaptive confidence-based stopping
2. Frequency BAND sampling instead of binary search
3. Volume = extrapolation from band performance (research-validated formula)
4. Reach = highest band where accuracy > 50%
5. Continues until CONFIDENT, not until fixed question count

Algorithm:
1. Sample words across frequency bands
2. Track accuracy per band
3. Estimate vocabulary = Σ(band_accuracy × band_size)
4. Stop when confidence threshold reached

V3 Changes:
- Support VocabularyStore as optional fallback (in-memory JSON)
- Neo4j still primary for survey (more complex queries)
"""

import random
import math
import logging
from typing import Optional, List, Dict, Any, Tuple, Union

# Neo4j connection (primary for survey)
from src.database.neo4j_connection import Neo4jConnection

# VocabularyStore (optional fallback)
try:
    from src.services.vocabulary_store import vocabulary_store, VocabularyStore
    VOCABULARY_STORE_AVAILABLE = True
except ImportError:
    VOCABULARY_STORE_AVAILABLE = False
    vocabulary_store = None

logger = logging.getLogger(__name__)

from src.survey.models import (
    SurveyState,
    QuestionPayload,
    QuestionOption,
    AnswerSubmission,
    SurveyResult,
    TriMetricReport,
)
from src.survey.schema_adapter import SchemaAdapter


class LexiSurveyEngine:
    """
    LexiSurvey Engine: Probability-Based Adaptive Vocabulary Assessment (V2)
    
    This is the production engine implementing research-validated vocabulary assessment.
    Previously known as V2, now the main engine replacing the binary search approach.
    
    Core principles from research:
    1. Vocabulary knowledge follows a PROBABILITY CURVE, not a sharp boundary
    2. Test words across FREQUENCY BANDS, estimate from band performance
    3. Continue until CONFIDENCE threshold reached, not fixed questions
    4. Use information-gain to select next band to test
    
    Volume formula (from Nation's VLT):
        Volume = Σ (band_accuracy × band_size)
        
    Example: If user gets 90% at 1K, 70% at 2K, 40% at 3K, 10% at 4K:
        Volume = 0.9×1000 + 0.7×1000 + 0.4×1000 + 0.1×1000 = 2100 words
    """
    
    # Frequency bands (each represents ~1000 words)
    FREQUENCY_BANDS = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
    BAND_SIZE = 1000  # Each band represents ~1000 words
    
    # Stopping criteria (based on CAT research)
    MIN_QUESTIONS = 10       # Minimum before considering early stop
    MAX_QUESTIONS = 35       # Safety limit (research shows 30-60 is typical)
    CONFIDENCE_THRESHOLD = 0.80  # Stop when this confident (SE < 0.20)
    
    # Band selection parameters
    MIN_SAMPLES_PER_BAND = 2   # Need at least 2 samples for reliable estimate
    TARGET_SAMPLES_PER_BAND = 4  # Ideal samples per band
    
    # Discriminator threshold (for trap validation)
    SIMILARITY_THRESHOLD = 0.6  # Reject traps with similarity > 0.6
    
    # Duplicate prevention
    RECENT_WORDS_WINDOW = 20  # Exclude recent words
    
    def __init__(self, conn: Optional[Neo4jConnection] = None, use_vocabulary_store: bool = False):
        """
        Initialize the V2 engine.
        
        Args:
            conn: Neo4j connection (primary data source for survey)
            use_vocabulary_store: If True and Neo4j unavailable, use VocabularyStore
        """
        self.conn = conn
        self.adapter = SchemaAdapter()
        self.use_vocabulary_store = use_vocabulary_store and VOCABULARY_STORE_AVAILABLE
        
        if not conn and not self.use_vocabulary_store:
            raise ValueError(
                "Either Neo4j connection or VocabularyStore must be available"
            )
    
    def process_step(
        self,
        state: SurveyState,
        previous_answer: Optional[AnswerSubmission] = None,
        question_details: Optional[Dict[str, Any]] = None
    ) -> SurveyResult:
        """
        Process one step of the adaptive vocabulary survey.
        
        Steps:
        1. Initialize band tracking if needed
        2. Grade previous answer and update band performance
        3. Calculate current confidence and vocabulary estimate
        4. Check if should stop (confidence reached OR max questions)
        5. Select next band using information gain heuristic
        6. Generate question from that band
        
        Args:
            state: Current survey state
            previous_answer: Answer to previous question (None for first question)
            question_details: Details about the answered question
            
        Returns:
            SurveyResult with status="continue" and next question,
            or status="complete" with final metrics
        """
        # Step 1: Initialize band tracking if not present
        if state.band_performance is None:
            state.band_performance = {
                band: {"tested": 0, "correct": 0} 
                for band in self.FREQUENCY_BANDS
            }
        
        # Step 2: Grade previous answer
        if previous_answer:
            self._grade_answer(state, previous_answer, question_details)
        
        # Step 3: Calculate confidence and estimate
        confidence = self._calculate_confidence(state)
        state.confidence = confidence
        state.estimated_vocab = self._estimate_vocabulary_size(state)
        
        # Step 4: Check if should stop
        if self._should_complete_survey(state, confidence):
            metrics = self._calculate_final_metrics(state)
            methodology = self._generate_methodology_explanation(state)
            return SurveyResult(
                status="complete",
                session_id=state.session_id,
                metrics=metrics,
                detailed_history=state.history,
                methodology=methodology,
                debug_info={
                    "confidence": round(confidence, 3),
                    "question_count": len(state.history),
                    "estimated_vocab": state.estimated_vocab,
                    "stopping_reason": self._get_stopping_reason(state, confidence),
                    "band_performance": {
                        str(band): {
                            "tested": bp["tested"],
                            "correct": bp["correct"],
                            "accuracy": round(bp["correct"] / bp["tested"], 2) if bp["tested"] > 0 else 0
                        }
                        for band, bp in state.band_performance.items()
                        if bp["tested"] > 0
                    }
                }
            )
        
        # Step 5: Select next band to test
        target_band = self._select_next_band(state)
        
        # Step 6: Generate question from that band
        payload = self._generate_question_from_band(target_band, state)
        
        return SurveyResult(
            status="continue",
            session_id=state.session_id,
            payload=payload,
            debug_info={
                "confidence": round(confidence, 3),
                "question_count": len(state.history) + 1,
                "target_band": target_band,
                "estimated_vocab": state.estimated_vocab,
            }
        )
    
    # =========================================================================
    # ANSWER GRADING
    # =========================================================================
    
    def _grade_answer(
        self, 
        state: SurveyState, 
        answer: AnswerSubmission, 
        question_details: Optional[Dict[str, Any]] = None
    ):
        """
        Grade answer and update band performance.
        
        Updates:
        - Band performance counters
        - History with full details
        - Bounds (for reference, not primary metric)
        """
        # Extract rank from question_id
        try:
            rank = int(answer.question_id.split("_")[1])
        except (ValueError, IndexError):
            rank = state.current_rank
        
        # Determine correctness using stateless hack
        is_correct = self._evaluate_answer_correctness(answer)
        
        # Find which band this word belongs to
        word_band = self._rank_to_band(rank)
        
        # Update band performance
        if word_band in state.band_performance:
            state.band_performance[word_band]["tested"] += 1
            if is_correct:
                state.band_performance[word_band]["correct"] += 1
        
        # Extract question details
        word = question_details.get("word") if question_details else None
        all_options = question_details.get("options", []) if question_details else []
        correct_option_ids = [
            opt.get("id") for opt in all_options 
            if opt.get("is_correct") or opt.get("type") == "target"
        ] if all_options else []
        
        # Add to history with full details
        history_entry = {
            "rank": rank,
            "correct": is_correct,
            "time_taken": answer.time_taken,
            "word": word,
            "question_id": answer.question_id,
            "band": word_band,
            "question_number": len(state.history) + 1,
            "selected_option_ids": answer.selected_option_ids,
            "correct_option_ids": correct_option_ids,
            "all_options": all_options
        }
        state.history.append(history_entry)
        
        # Update bounds (for reference)
        if is_correct:
            state.low_bound = max(state.low_bound, rank)
        else:
            state.high_bound = min(state.high_bound, rank)
    
    def _evaluate_answer_correctness(self, answer: AnswerSubmission) -> bool:
        """
        Evaluate if the user's answer is correct using the stateless hack.
        
        Stateless hack: If option_id contains "target", it's a correct option.
        
        Rules:
        - Must select at least one target option
        - Must NOT select any non-target options (traps, fillers)
        - Selecting "unknown" is always wrong
        """
        # If user selected "unknown", it's wrong
        if any("unknown" in opt_id.lower() for opt_id in answer.selected_option_ids):
            return False
        
        # Check for target selection
        has_target = any("target" in opt_id.lower() for opt_id in answer.selected_option_ids)
        
        # Check for non-target selection (traps, fillers)
        has_non_target = any(
            "trap" in opt_id.lower() or 
            "filler" in opt_id.lower() or
            ("target" not in opt_id.lower() and "unknown" not in opt_id.lower())
            for opt_id in answer.selected_option_ids
        )
        
        return has_target and not has_non_target
    
    def _rank_to_band(self, rank: int) -> int:
        """Map a word rank to its frequency band."""
        for band in self.FREQUENCY_BANDS:
            if rank <= band:
                return band
        return self.FREQUENCY_BANDS[-1]
    
    # =========================================================================
    # CONFIDENCE & VOCABULARY ESTIMATION
    # =========================================================================
    
    def _calculate_confidence(self, state: SurveyState) -> float:
        """
        Calculate confidence in vocabulary estimate.
        
        Based on CAT/IRT research, confidence depends on:
        - Number of questions answered (more = better)
        - Number of bands with adequate samples
        - Consistency of responses (monotonicity)
        - Stability of estimate over recent questions
        
        Returns value 0.0-1.0 where >0.80 is "confident enough to stop"
        """
        n_questions = len(state.history)
        
        if n_questions == 0:
            return 0.0
        
        # Factor 1: Question count (more = better, saturates at ~30)
        question_factor = min(n_questions / 30, 1.0)
        
        # Factor 2: Band coverage (how many bands have enough samples)
        bands_with_samples = sum(
            1 for bp in state.band_performance.values() 
            if bp["tested"] >= self.MIN_SAMPLES_PER_BAND
        )
        coverage_factor = bands_with_samples / len(self.FREQUENCY_BANDS)
        
        # Factor 3: Monotonicity (consistent response pattern)
        monotonicity = self._calculate_monotonicity(state.history)
        
        # Factor 4: Estimate stability (check if estimate is converging)
        stability_factor = self._calculate_stability(state)
        
        # Weighted combination (based on CAT literature)
        confidence = (
            0.25 * question_factor +
            0.30 * coverage_factor +
            0.25 * monotonicity +
            0.20 * stability_factor
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_monotonicity(self, history: List[Dict]) -> float:
        """
        Calculate how monotonic (consistent) the response pattern is.
        
        A consistent learner shows:
        - High accuracy at low ranks
        - Low accuracy at high ranks
        - Smooth transition between
        
        "Wrong then correct" pairs indicate gaps/inconsistency.
        """
        if len(history) < 2:
            return 0.5
        
        sorted_history = sorted(history, key=lambda h: h["rank"])
        consistent_pairs = 0
        total_pairs = len(sorted_history) - 1
        
        for i in range(total_pairs):
            lower_correct = sorted_history[i].get("correct", False)
            higher_correct = sorted_history[i + 1].get("correct", False)
            
            # Only "wrong then correct" is inconsistent (gap in knowledge)
            if not lower_correct and higher_correct:
                pass  # Inconsistent - don't count
            else:
                consistent_pairs += 1
        
        return consistent_pairs / total_pairs if total_pairs > 0 else 0.5
    
    def _calculate_stability(self, state: SurveyState) -> float:
        """
        Calculate stability of vocabulary estimate.
        
        If estimates are converging (not jumping around), we're more confident.
        """
        if len(state.history) < 5:
            return 0.3  # Not enough data
        
        # Calculate estimates at different points
        # (This is simplified - full implementation would track estimate history)
        current_estimate = state.estimated_vocab
        
        # Check if we have boundary convergence
        bounds_range = abs(state.high_bound - state.low_bound)
        if bounds_range < 2000:
            return 0.9
        elif bounds_range < 4000:
            return 0.6
        else:
            return 0.3
    
    def _estimate_vocabulary_size(self, state: SurveyState) -> int:
        """
        Estimate total vocabulary size from band performance.
        
        Formula (from Nation's VLT and TestYourVocab):
            Volume = Σ (band_accuracy × band_size)
        
        Example:
            Band 1K: 90% accuracy → 900 words
            Band 2K: 70% accuracy → 700 words  
            Band 3K: 40% accuracy → 400 words
            Band 4K: 10% accuracy → 100 words
            Total: 2100 words
        
        For untested bands, we interpolate based on neighbors.
        """
        total = 0
        prev_accuracy = 1.0  # Assume 100% for very common words
        
        for band in self.FREQUENCY_BANDS:
            bp = state.band_performance.get(band, {"tested": 0, "correct": 0})
            
            if bp["tested"] > 0:
                accuracy = bp["correct"] / bp["tested"]
            else:
                # Interpolate: assume gradual decline from previous band
                accuracy = max(0, prev_accuracy - 0.15)
            
            # Each band represents BAND_SIZE words
            band_contribution = accuracy * self.BAND_SIZE
            total += band_contribution
            
            prev_accuracy = accuracy
        
        return int(total)
    
    # =========================================================================
    # STOPPING CRITERIA
    # =========================================================================
    
    def _should_complete_survey(self, state: SurveyState, confidence: float) -> bool:
        """
        Determine if survey should complete.
        
        Based on CAT research, stop when:
        1. Confidence threshold reached AND minimum questions answered
        2. Maximum questions reached
        3. All bands adequately sampled AND enough questions
        """
        n_questions = len(state.history)
        
        # Must have minimum questions
        if n_questions < self.MIN_QUESTIONS:
            return False
        
        # Stop at maximum
        if n_questions >= self.MAX_QUESTIONS:
            return True
        
        # Stop if confident enough
        if confidence >= self.CONFIDENCE_THRESHOLD:
            return True
        
        # Stop if all bands have enough samples
        all_bands_sampled = all(
            bp["tested"] >= self.MIN_SAMPLES_PER_BAND 
            for bp in state.band_performance.values()
        )
        if all_bands_sampled and n_questions >= 16:
            return True
        
        return False
    
    def _get_stopping_reason(self, state: SurveyState, confidence: float) -> str:
        """Determine why the survey stopped."""
        n = len(state.history)
        
        if n >= self.MAX_QUESTIONS:
            return f"Maximum questions reached ({self.MAX_QUESTIONS})"
        elif confidence >= self.CONFIDENCE_THRESHOLD:
            return f"Confidence threshold reached ({confidence:.0%} >= {self.CONFIDENCE_THRESHOLD:.0%})"
        else:
            return "Adequate band coverage achieved"
    
    # =========================================================================
    # BAND SELECTION (Information Gain)
    # =========================================================================
    
    def _select_next_band(self, state: SurveyState) -> int:
        """
        Select next frequency band to test using information gain heuristic.
        
        Priority (based on CAT research):
        1. Bands near the estimated boundary (high information gain)
        2. Bands with too few samples (reduce uncertainty)
        3. Avoid over-sampling any single band
        """
        # Calculate current estimate to find boundary area
        current_estimate = state.estimated_vocab
        estimated_boundary_band = self._rank_to_band(current_estimate)
        
        # Score each band
        band_scores = {}
        for band in self.FREQUENCY_BANDS:
            bp = state.band_performance.get(band, {"tested": 0, "correct": 0})
            tested = bp["tested"]
            
            # Priority 1: Bands needing more samples
            if tested < self.MIN_SAMPLES_PER_BAND:
                sample_need_score = 1.0
            elif tested < self.TARGET_SAMPLES_PER_BAND:
                sample_need_score = 0.6
            else:
                sample_need_score = 0.2
            
            # Priority 2: Bands near estimated boundary (high information gain)
            distance_from_boundary = abs(band - estimated_boundary_band)
            proximity_score = max(0, 1.0 - distance_from_boundary / 4000)
            
            # Priority 3: Avoid over-sampling
            over_sample_penalty = min(tested / 8, 0.4)
            
            # Combine scores
            total_score = (
                0.35 * sample_need_score +
                0.45 * proximity_score -
                0.20 * over_sample_penalty
            )
            
            # Boost extreme bands slightly (help detect edge cases)
            if band <= 1000 or band >= 7000:
                total_score += 0.05
            
            band_scores[band] = max(0.01, total_score)  # Ensure positive
        
        # Select band using weighted random (allows exploration)
        sorted_bands = sorted(band_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Pick from top 3 to add variety
        top_bands = sorted_bands[:3]
        weights = [score for _, score in top_bands]
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        selected_band = random.choices([b for b, _ in top_bands], weights=weights)[0]
        return selected_band
    
    # =========================================================================
    # QUESTION GENERATION
    # =========================================================================
    
    def _generate_question_from_band(self, target_band: int, state: SurveyState) -> QuestionPayload:
        """
        Generate a question from the specified frequency band.
        
        Steps:
        1. Calculate rank range for the band
        2. Pick random rank within band
        3. Fetch word at that rank
        4. Generate options (targets, traps, fillers, unknown)
        """
        # Calculate rank range for this band
        band_idx = self.FREQUENCY_BANDS.index(target_band)
        min_rank = self.FREQUENCY_BANDS[band_idx - 1] + 1 if band_idx > 0 else 51
        max_rank = target_band
        
        # Pick random rank within band (avoid edges slightly)
        margin = min(50, (max_rank - min_rank) // 4)
        target_rank = random.randint(min_rank + margin, max_rank - margin // 2)
        
        # Generate full question payload
        return self._generate_question_payload(target_rank, state)
    
    def _generate_question_payload(self, rank: int, state: SurveyState) -> QuestionPayload:
        """
        Generate a complete question payload for a word near the target rank.
        
        Uses SchemaAdapter to query Neo4j and creates:
        - 1-5 target definitions (correct answers)
        - 0-3 trap definitions (from confused words)
        - Filler definitions
        - "Unknown" option
        """
        with self.conn.get_session() as session:
            # Get recently used words to avoid repetition
            recently_used_words = [
                h.get("word", "").lower() 
                for h in state.history[-self.RECENT_WORDS_WINDOW:]
                if h.get("word")
            ]
            
            # Fetch target word at this rank
            word, actual_rank, target_embedding = self._fetch_target_word(
                session, rank, recently_used_words
            )
            
            # Generate options
            options, option_metadata = self._generate_options(
                session, word, actual_rank, target_embedding
            )
            
            # Create question payload
            question_id = f"q_{actual_rank}_{random.randint(10000, 99999)}"
            
            payload = QuestionPayload(
                question_id=question_id,
                word=word,
                rank=actual_rank,
                options=options,
                time_limit=12
            )
            
            # Store metadata for later
            payload._option_metadata = option_metadata
            state.current_rank = actual_rank
            
            return payload
    
    def _fetch_target_word(
        self, 
        session, 
        rank: int, 
        excluded_words: List[str]
    ) -> Tuple[str, int, Optional[List[float]]]:
        """
        Fetch a target word near the specified rank.
        
        Filters:
        - Word length >= 3
        - Not a stop word (rank > 50)
        - Not recently used
        - Has Chinese definition
        """
        search_radius = 50
        max_attempts = 3
        word = None
        actual_rank = rank
        embedding = None
        
        for attempt in range(max_attempts):
            if excluded_words:
                query = """
                    MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                    WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                    AND size(b.name) >= 3
                    AND b.frequency_rank > 50
                    AND NOT toLower(b.name) IN $excluded_words
                    AND s.definition_zh IS NOT NULL
                    WITH b, rand() as r 
                    ORDER BY r 
                    LIMIT 1
                    RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                """
                params = {
                    "min_r": max(51, rank - search_radius),
                    "max_r": min(8000, rank + search_radius),
                    "excluded_words": [w.lower() for w in excluded_words if w]
                }
            else:
                query = """
                    MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                    WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                    AND size(b.name) >= 3
                    AND b.frequency_rank > 50
                    AND s.definition_zh IS NOT NULL
                    WITH b, rand() as r 
                    ORDER BY r 
                    LIMIT 1
                    RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                """
                params = {
                    "min_r": max(51, rank - search_radius),
                    "max_r": min(8000, rank + search_radius)
                }
            
            result = session.run(query, **params)
            row = result.single()
            
            if row:
                word = row["word"]
                actual_rank = int(row["rank"])
                embedding = row["embedding"]
                break
            else:
                search_radius *= 2  # Expand search
        
        # Fallback if no word found
        if not word:
            word = "example"
            actual_rank = rank
            embedding = None
            logger.warning(f"No word found for rank {rank}, using fallback")
        
        return word, actual_rank, embedding
    
    def _generate_options(
        self,
        session,
        target_word: str,
        rank: int,
        target_embedding: Optional[List[float]] = None
    ) -> Tuple[List[QuestionOption], Dict]:
        """
        Generate 6 options for the question.
        
        Options include:
        - 1-5 Target definitions (correct answers from target word's senses)
        - 0-3 Trap definitions (from CONFUSED_WITH relationships)
        - Fillers (random definitions from nearby ranks)
        - 1 "Unknown" option
        """
        options = []
        target_metadata = {}
        
        # Step 1: Fetch target definitions
        target_query = """
            MATCH (t:Word {name: $target_word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.definition_zh IS NOT NULL
            WITH s, 
                 CASE WHEN s.id STARTS WITH toLower($target_word) THEN 10.0 ELSE 0.1 END as sense_match_bonus,
                 COALESCE(s.usage_ratio, 1.0) as base_weight
            RETURN s.id as sense_id,
                   s.definition_zh as text, 
                   s.definition_en as definition_en,
                   s.example_zh as example_zh,
                   s.example_en as example_en,
                   (base_weight + sense_match_bonus) as weight
            ORDER BY weight DESC
            LIMIT 5
        """
        
        target_results = session.run(target_query, target_word=target_word)
        target_definitions = []
        for record in target_results:
            text = record.get("text")
            if text:
                target_definitions.append({
                    "text": text,
                    "sense_id": record.get("sense_id"),
                    "definition_en": record.get("definition_en"),
                    "example_zh": record.get("example_zh"),
                    "example_en": record.get("example_en"),
                    "weight": record.get("weight", 1.0)
                })
        
        # Deduplicate target definitions by text before adding
        seen_texts = set()
        unique_targets = []
        for target_def in target_definitions:
            text = target_def["text"]
            if text not in seen_texts:
                seen_texts.add(text)
                unique_targets.append(target_def)
        
        # Add target options (limit to 3 unique targets)
        num_targets = min(len(unique_targets), 3)
        if num_targets == 0:
            unique_targets.append({"text": "此單字尚未有中文定義", "sense_id": None})
            num_targets = 1
        
        for i in range(num_targets):
            target_def = unique_targets[i]
            target_def = target_definitions[i]
            option_id = f"target_{target_word}_{i}"
            options.append(QuestionOption(
                id=option_id,
                text=target_def["text"],
                type="target",
                is_correct=True
            ))
            # Store metadata for API layer to attach to options
            metadata = {}
            if target_def.get("sense_id"):
                metadata["sense_id"] = target_def["sense_id"]
                metadata["is_primary_sense"] = target_def["sense_id"].startswith(target_word.lower())
            if target_def.get("definition_en"):
                metadata["definition_en"] = target_def["definition_en"]
            if target_def.get("example_zh"):
                metadata["example_zh"] = target_def["example_zh"]
            if target_def.get("example_en"):
                metadata["example_en"] = target_def["example_en"]
            target_metadata[option_id] = metadata
        
        # Step 2: Fetch trap definitions
        trap_definitions = self._fetch_traps(session, target_word, target_embedding)
        
        num_traps = min(len(trap_definitions), 2)  # Max 2 traps
        for i in range(num_traps):
            if len(options) >= 5:
                break
            trap_def = trap_definitions[i]
            option_id = f"trap_{trap_def.get('word_id', i)}"
            options.append(QuestionOption(
                id=option_id,
                text=trap_def["text"],
                type="trap",
                is_correct=False
            ))
            # Store metadata for API layer to attach
            metadata = {}
            if trap_def.get("sense_id"):
                metadata["sense_id"] = trap_def["sense_id"]
            if trap_def.get("definition_en"):
                metadata["definition_en"] = trap_def["definition_en"]
            if trap_def.get("example_zh"):
                metadata["example_zh"] = trap_def["example_zh"]
            if trap_def.get("example_en"):
                metadata["example_en"] = trap_def["example_en"]
            if trap_def.get("word_name"):
                metadata["word_name"] = trap_def["word_name"]
            target_metadata[option_id] = metadata
        
        # Step 3: Fetch filler definitions
        filler_definitions = self._fetch_fillers(session, target_word, rank)
        
        # Add enough fillers to reach 5 options (before unknown)
        filler_idx = 0
        while len(options) < 5 and filler_idx < len(filler_definitions):
            filler_def = filler_definitions[filler_idx]
            if not any(opt.text == filler_def["text"] for opt in options):
                option_id = f"filler_{filler_idx}"
                options.append(QuestionOption(
                    id=option_id,
                    text=filler_def["text"],
                    type="filler",
                    is_correct=False
                ))
                # Store metadata for API layer to attach
                metadata = {}
                if filler_def.get("sense_id"):
                    metadata["sense_id"] = filler_def["sense_id"]
                if filler_def.get("definition_en"):
                    metadata["definition_en"] = filler_def["definition_en"]
                if filler_def.get("example_zh"):
                    metadata["example_zh"] = filler_def["example_zh"]
                if filler_def.get("example_en"):
                    metadata["example_en"] = filler_def["example_en"]
                if filler_def.get("word_name"):
                    metadata["word_name"] = filler_def["word_name"]
                target_metadata[option_id] = metadata
            filler_idx += 1
        
        # Pad with placeholder fillers if needed
        while len(options) < 5:
            options.append(QuestionOption(
                id=f"filler_pad_{len(options)}",
                text="其他選項",
                type="filler",
                is_correct=False
            ))
        
        # Step 4: Add "Unknown" option
        options.append(QuestionOption(
            id="unknown_option",
            text="我不知道",
            type="unknown",
            is_correct=False
        ))
        
        # Shuffle options (except keep unknown last)
        unknown_option = options.pop()
        random.shuffle(options)
        options.append(unknown_option)
        
        return options, target_metadata
    
    def _fetch_traps(
        self, 
        session, 
        target_word: str, 
        target_embedding: Optional[List[float]]
    ) -> List[Dict]:
        """Fetch trap definitions from CONFUSED_WITH relationships."""
        trap_query = """
            MATCH (t:Word {name: $target_word})-[:CONFUSED_WITH]->(trap:Word)
            MATCH (trap)-[:HAS_SENSE]->(ts:Sense)
            WHERE ts.definition_zh IS NOT NULL
            RETURN trap.word_id as word_id,
                   trap.name as word_name,
                   ts.definition_zh as text,
                   ts.id as sense_id,
                   ts.definition_en as definition_en,
                   ts.example_zh as example_zh,
                   ts.example_en as example_en,
                   trap.embedding as embedding
            ORDER BY ts.usage_ratio DESC
            LIMIT 5
        """
        
        results = session.run(trap_query, target_word=target_word)
        traps = []
        
        for record in results:
            text = record.get("text")
            if text:
                # Validate trap using embedding similarity if available
                trap_embedding = record.get("embedding")
                if self._validate_trap(target_embedding, trap_embedding):
                    traps.append({
                        "text": text,
                        "word_id": record.get("word_id", "unknown"),
                        "word_name": record.get("word_name"),
                        "sense_id": record.get("sense_id"),
                        "definition_en": record.get("definition_en"),
                        "example_zh": record.get("example_zh"),
                        "example_en": record.get("example_en")
                    })
        
        return traps[:3]  # Max 3 traps
    
    def _validate_trap(
        self, 
        target_embedding: Optional[List[float]], 
        trap_embedding: Optional[List[float]]
    ) -> bool:
        """Validate trap using cosine similarity."""
        if not target_embedding or not trap_embedding:
            return True  # Accept if no embeddings
        
        try:
            # Convert if needed
            if not isinstance(target_embedding, list):
                target_embedding = list(target_embedding)
            if not isinstance(trap_embedding, list):
                trap_embedding = list(trap_embedding)
            
            similarity = self._cosine_similarity(target_embedding, trap_embedding)
            return similarity < self.SIMILARITY_THRESHOLD
        except Exception:
            return True
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(v1) != len(v2):
            return 0.3
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(a * a for a in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _fetch_fillers(self, session, target_word: str, rank: int) -> List[Dict]:
        """Fetch filler definitions from nearby ranks."""
        filler_query = """
            MATCH (f:Word)-[:HAS_SENSE]->(fs:Sense)
            WHERE f.frequency_rank >= $min_r AND f.frequency_rank <= $max_r
            AND NOT f.name = $target_word
            AND size(f.name) >= 3
            AND f.frequency_rank > 50
            AND fs.definition_zh IS NOT NULL
            WITH f, fs, rand() as r
            ORDER BY r
            LIMIT 6
            RETURN f.word_id as word_id,
                   f.name as word_name,
                   fs.definition_zh as text,
                   fs.id as sense_id,
                   fs.definition_en as definition_en,
                   fs.example_zh as example_zh,
                   fs.example_en as example_en
        """
        
        results = session.run(
            filler_query,
            min_r=max(51, rank - 200),
            max_r=min(8000, rank + 200),
            target_word=target_word
        )
        
        fillers = []
        for record in results:
            text = record.get("text")
            if text:
                fillers.append({
                    "text": text,
                    "word_id": record.get("word_id", "unknown"),
                    "word_name": record.get("word_name"),
                    "sense_id": record.get("sense_id"),
                    "definition_en": record.get("definition_en"),
                    "example_zh": record.get("example_zh"),
                    "example_en": record.get("example_en")
                })
        
        return fillers
    
    # =========================================================================
    # FINAL METRICS CALCULATION
    # =========================================================================
    
    def _calculate_final_metrics(self, state: SurveyState) -> TriMetricReport:
        """
        Calculate final Tri-Metric Report using research-validated formulas.
        
        Volume: Extrapolated vocabulary size from band performance
        Reach: Highest band where accuracy > 50%
        Density: Monotonicity of response pattern
        """
        # VOLUME: Band-based extrapolation (Nation's VLT formula)
        volume = self._estimate_vocabulary_size(state)
        
        # REACH: Highest band with >50% accuracy
        reach = self._calculate_reach(state)
        
        # DENSITY: Monotonicity (consistency of knowledge)
        density = self._calculate_density(state)
        
        # Clamp values
        volume = max(0, min(8000, volume))
        reach = max(0, min(8000, reach))
        density = max(0.0, min(1.0, density))
        
        return TriMetricReport(
            volume=volume,
            reach=reach,
            density=density
        )
    
    def _calculate_reach(self, state: SurveyState) -> int:
        """
        Calculate reach: highest frequency band where accuracy > 50%.
        
        This represents the vocabulary "horizon" - the furthest point
        where the user still demonstrates knowledge.
        """
        threshold = 0.50
        
        # Check bands from highest to lowest
        for band in reversed(self.FREQUENCY_BANDS):
            bp = state.band_performance.get(band, {"tested": 0, "correct": 0})
            if bp["tested"] >= self.MIN_SAMPLES_PER_BAND:
                accuracy = bp["correct"] / bp["tested"]
                if accuracy >= threshold:
                    return band
        
        # Fallback: any band with >threshold accuracy
        for band in reversed(self.FREQUENCY_BANDS):
            bp = state.band_performance.get(band, {"tested": 0, "correct": 0})
            if bp["tested"] > 0:
                accuracy = bp["correct"] / bp["tested"]
                if accuracy >= threshold:
                    return band
        
        # Last resort: return lowest tested band
        for band in self.FREQUENCY_BANDS:
            if state.band_performance.get(band, {}).get("tested", 0) > 0:
                return band
        
        return self.FREQUENCY_BANDS[0]
    
    def _calculate_density(self, state: SurveyState) -> float:
        """
        Calculate density: consistency of vocabulary knowledge.
        
        Uses monotonicity with edge case handling.
        High density = consistent knowledge (few gaps)
        Low density = inconsistent (gaps in knowledge)
        """
        if len(state.history) == 0:
            return 0.0
        
        correct_count = sum(1 for h in state.history if h.get("correct", False))
        
        if correct_count == 0:
            return 0.0
        elif correct_count == len(state.history):
            return 1.0
        else:
            return self._calculate_monotonicity(state.history)
    
    def _generate_methodology_explanation(self, state: SurveyState) -> Dict[str, Any]:
        """Generate explanation of the adaptive methodology used."""
        return {
            "algorithm": "Adaptive Frequency Band Sampling (V2)",
            "approach": "Probability-based vocabulary estimation",
            "description": (
                "This assessment samples words across frequency bands and estimates "
                "vocabulary size using the formula: Volume = Σ(band_accuracy × 1000). "
                "Testing continues until confidence threshold is reached."
            ),
            "total_questions": len(state.history),
            "bands_sampled": {
                str(band): {
                    "tested": bp["tested"],
                    "correct": bp["correct"],
                    "accuracy": f"{bp['correct']/bp['tested']*100:.0f}%" if bp["tested"] > 0 else "N/A"
                }
                for band, bp in state.band_performance.items()
                if bp["tested"] > 0
            },
            "stopping_reason": self._get_stopping_reason(state, state.confidence),
            "formula": "Volume = Σ (band_accuracy × 1000) for each frequency band",
            "research_basis": [
                "Nation's Vocabulary Levels Test (VLT)",
                "Computerized Adaptive Testing (CAT)",
                "TestYourVocab methodology"
            ]
        }
