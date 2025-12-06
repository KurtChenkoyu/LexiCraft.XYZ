"""
LexiSurvey Engine: Production Implementation (V7.1)

Implements the ValuationEngine logic from the Master Spec, adapted for production architecture:
- Uses SchemaAdapter to map abstract :Block → concrete :Word schema
- Uses Pydantic models for type safety
- Implements 3-Phase Funnel Algorithm for vocabulary assessment:
  - Phase 1 (Q1-Q5): Coarse sweep (±1500 steps)
  - Phase 2 (Q6-Q12): Fine tuning (±200 steps)
  - Phase 3 (Q13-Q15): Verification (±100 steps)
- Generates Tri-Metric Report: Volume, Reach, Density
- Uses stateless hack for answer grading (check if option_id contains "target")
- Validates traps using cosine similarity (Discriminator Logic: similarity < 0.6)
"""

import random
import math
import logging
from typing import Optional, List, Dict, Any, Tuple
from src.database.neo4j_connection import Neo4jConnection

logger = logging.getLogger(__name__)
from src.survey.models import (
    SurveyState,
    QuestionPayload,
    QuestionOption,
    AnswerSubmission,
    SurveyResult,
    TriMetricReport,
    QuestionHistory,
)
from src.survey.schema_adapter import SchemaAdapter


class LexiSurveyEngine:
    """
    LexiSurvey Engine: The Core Survey Controller (Production Implementation)
    
    Implements the ValuationEngine logic from the Master Spec, adapted for production:
    - Uses SchemaAdapter to map abstract :Block → concrete :Word schema
    - Uses Pydantic models for type safety
    - Implements 3-phase funnel algorithm (Coarse Sweep / Fine Tuning / Verification)
    - Generates Tri-Metric Report (Volume, Reach, Density)
    - Uses stateless hack for answer grading (check if option_id contains "target")
    - Validates traps using cosine similarity (Discriminator Logic)
    """
    
    # Phase configuration
    PHASE_1_QUESTIONS = 5  # Q1-Q5: Coarse sweep
    PHASE_2_QUESTIONS = 7  # Q6-Q12: Fine tuning
    PHASE_3_QUESTIONS = 3  # Q13-Q15: Verification
    MAX_QUESTIONS = 20  # Safety limit
    
    # Step sizes for each phase
    PHASE_1_STEP = 1500  # Aggressive binary search
    PHASE_2_STEP = 200   # Oscillating search
    PHASE_3_STEP = 100   # Verification
    
    # Survey completion thresholds
    MIN_QUESTIONS = 15
    CONFIDENCE_THRESHOLD = 0.85  # High confidence to complete early
    
    # Discriminator threshold (for trap validation)
    SIMILARITY_THRESHOLD = 0.6  # Reject traps with similarity > 0.6
    
    # Duplicate prevention
    RECENT_WORDS_WINDOW = 15  # Exclude last 15 words to prevent duplicates (increased for high-rank clusters)
    
    def __init__(self, conn: Neo4jConnection):
        """
        Initialize the LexiSurveyEngine.
        
        Args:
            conn: Neo4j connection instance
        """
        self.conn = conn
        self.adapter = SchemaAdapter()
    
    def process_step(
        self,
        state: SurveyState,
        previous_answer: Optional[AnswerSubmission] = None,
        question_details: Optional[Dict[str, Any]] = None
    ) -> SurveyResult:
        """
        CORE CONTROLLER: Process one step of the survey.
        
        Steps:
        1. Grade previous answer (if provided) and update history
        2. Check if survey is complete (generate Tri-Metric Report)
        3. Calculate next rank (Adaptive Frequency Sweep)
        4. Fetch question data (Neo4j with SchemaAdapter)
        
        Args:
            state: Current survey state
            previous_answer: Previous answer submission (None for first question)
            question_details: Detailed info about the answered question (retrieved from DB)
            
        Returns:
            SurveyResult with either:
            - status="continue" + payload (next question)
            - status="complete" + metrics (final report)
        """
        # Step 1: Grade previous answer and update history
        if previous_answer:
            self._grade_answer(state, previous_answer, question_details)
        
        # Step 2: Check if survey is complete
        question_count = len(state.history)
        if self._should_complete_survey(state, question_count):
            metrics = self._calculate_final_metrics(state)
            methodology = self._generate_methodology_explanation(state)
            return SurveyResult(
                status="complete",
                session_id=state.session_id,
                metrics=metrics,
                detailed_history=state.history,
                methodology=methodology,
                debug_info={
                    "phase": state.phase,
                    "confidence": state.confidence,
                    "question_count": question_count,
                }
            )
        
        # Step 3: Calculate next rank
        next_rank = self._calculate_next_rank(state, question_count)
        state.current_rank = next_rank
        
        # Step 4: Update phase based on question count
        state.phase = self._determine_phase(question_count)
        
        # Step 5: Generate question payload
        payload = self._generate_question_payload(next_rank, state.phase, state)
        
        # Step 6: Update confidence
        state.confidence = self._calculate_confidence(state)
        
        return SurveyResult(
            status="continue",
            session_id=state.session_id,
            payload=payload,
            debug_info={
                "current_confidence": state.confidence,
                "phase": state.phase,
                "question_count": question_count + 1,
            }
        )
    
    def _grade_answer(
        self, 
        state: SurveyState, 
        answer: AnswerSubmission, 
        question_details: Optional[Dict[str, Any]] = None
    ):
        """
        Grade the user's answer and update survey state.
        
        Args:
            state: Survey state to update
            answer: User's answer submission
            question_details: Optional detailed info about the question
        """
        # Extract question info from question_id (format: "q_{rank}")
        try:
            rank = int(answer.question_id.split("_")[1])
        except (ValueError, IndexError):
            rank = state.current_rank
        
        # Determine if answer is correct
        is_correct = self._evaluate_answer_correctness(answer)
        
        # Extract correct option IDs if details available
        correct_option_ids = []
        all_options_data = None
        word = None
        question_number = None
        phase_val = state.phase
        
        if question_details:
            word = question_details.get("word")
            phase_val = question_details.get("phase", state.phase)
            question_number = question_details.get("question_number")
            all_options = question_details.get("options", [])
            all_options_data = all_options
            
            # Find correct options
            correct_option_ids = [
                opt.get("id") for opt in all_options 
                if opt.get("is_correct") or opt.get("type") == "target"
            ]
        
        # Add to history with full details
        # Use .dict() if constructing QuestionHistory object, or just dict if appending to list
        # Since state.history is List[Dict], we append a dict
        history_entry = {
            "rank": rank,
            "correct": is_correct,
            "time_taken": answer.time_taken,
            "word": word,
            "question_id": answer.question_id,
            "phase": phase_val,
            "question_number": question_number if question_number else len(state.history) + 1,
            "selected_option_ids": answer.selected_option_ids,
            "correct_option_ids": correct_option_ids,
            "all_options": all_options_data
        }
        
        state.history.append(history_entry)
        
        # Update bounds based on answer
        if is_correct:
            state.low_bound = max(state.low_bound, rank)
        else:
            state.high_bound = min(state.high_bound, rank)
        
        # Check for pivot trigger (massive rank jump in Phase 1)
        if state.phase == 1 and len(state.history) >= 2:
            prev_rank = state.history[-2]["rank"]
            if abs(rank - prev_rank) > 1500:
                state.pivot_triggered = True
    
    def _evaluate_answer_correctness(self, answer: AnswerSubmission) -> bool:
        """
        Evaluate if the user's answer is correct using the stateless hack.
        
        The stateless hack: If any selected option_id contains "target", the answer is correct.
        This works because we always prefix target options with "target_" in the option IDs.
        
        For multi-select questions:
        - User must select ALL target options (those with "target" in the ID)
        - User must NOT select any non-target options (traps, fillers, unknown)
        
        Args:
            answer: Answer submission with selected_option_ids
            
        Returns:
            True if answer is correct, False otherwise
        """
        # If user selected "unknown", it's definitely wrong
        if any("unknown" in opt_id.lower() for opt_id in answer.selected_option_ids):
            return False
        
        # Stateless hack: Check if user selected any target options
        has_target = any("target" in opt_id.lower() for opt_id in answer.selected_option_ids)
        
        # Check if user selected any non-target options (traps, fillers)
        has_non_target = any(
            "trap" in opt_id.lower() or 
            "filler" in opt_id.lower() or
            ("target" not in opt_id.lower() and "unknown" not in opt_id.lower())
            for opt_id in answer.selected_option_ids
        )
        
        # Answer is correct if:
        # 1. User selected at least one target option
        # 2. User did NOT select any non-target options
        return has_target and not has_non_target
    
    def _should_complete_survey(self, state: SurveyState, question_count: int) -> bool:
        """
        Determine if the survey should be completed.
        
        Completion conditions:
        1. Minimum questions answered (15)
        2. High confidence reached (0.85)
        3. Maximum questions reached (20)
        4. Bounds converged (high_bound - low_bound < 200)
        
        Args:
            state: Current survey state
            question_count: Number of questions answered
            
        Returns:
            True if survey should complete, False otherwise
        """
        # Must have minimum questions
        if question_count < self.MIN_QUESTIONS:
            return False
        
        # Check maximum questions
        if question_count >= self.MAX_QUESTIONS:
            return True
        
        # Check confidence threshold
        if state.confidence >= self.CONFIDENCE_THRESHOLD:
            return True
        
        # Check bounds convergence
        if (state.high_bound - state.low_bound) < 200:
            return True
        
        return False
    
    def _calculate_next_rank(self, state: SurveyState, question_count: int) -> int:
        """
        Calculate the next rank to test using adaptive binary search.
        
        Phase 1 (Q1-Q5): ±1500 steps
        Phase 2 (Q6-Q12): ±200 steps
        Phase 3 (Q13-Q15): ±100 steps
        
        Args:
            state: Current survey state
            question_count: Number of questions answered
            
        Returns:
            Next rank to test
        """
        phase = self._determine_phase(question_count)
        
        if phase == 1:
            # Coarse sweep: aggressive binary search
            step_size = self.PHASE_1_STEP
        elif phase == 2:
            # Fine tuning: oscillating search
            step_size = self.PHASE_2_STEP
        else:
            # Verification: small steps
            step_size = self.PHASE_3_STEP
        
        # Binary search: test midpoint
        mid = (state.low_bound + state.high_bound) // 2
        
        # Add some randomness to avoid always testing exact midpoint
        # Oscillate around the midpoint in Phase 2
        if phase == 2 and len(state.history) > 0:
            # Oscillate: alternate between above and below midpoint
            last_rank = state.history[-1]["rank"]
            if last_rank < mid:
                # Last was below, try above
                next_rank = min(mid + step_size, state.high_bound)
            else:
                # Last was above, try below
                next_rank = max(mid - step_size, state.low_bound)
        else:
            # Phase 1 and 3: use midpoint with small random variation
            variation = random.randint(-step_size // 4, step_size // 4)
            next_rank = mid + variation
        
        # Clamp to valid range
        next_rank = max(1, min(8000, next_rank))
        next_rank = max(state.low_bound, min(state.high_bound, next_rank))
        
        return next_rank
    
    def _determine_phase(self, question_count: int) -> int:
        """
        Determine the current phase based on question count.
        
        Args:
            question_count: Number of questions answered
            
        Returns:
            Phase number (1, 2, or 3)
        """
        if question_count < self.PHASE_1_QUESTIONS:
            return 1
        elif question_count < (self.PHASE_1_QUESTIONS + self.PHASE_2_QUESTIONS):
            return 2
        else:
            return 3
    
    def _generate_question_payload(self, rank: int, phase: int, state: SurveyState) -> QuestionPayload:
        """
        Generate a question payload for the given rank.
        
        Uses SchemaAdapter to transform queries from :Block → :Word.
        Fetches target word, generates 6 options (targets, traps, fillers, unknown).
        
        Args:
            rank: Frequency rank to test
            phase: Current phase (for question difficulty adjustment)
            state: Survey state (to exclude recently used words)
            
        Returns:
            QuestionPayload with word, rank, and 6 options
        """
        with self.conn.get_session() as session:
            # Get recently used words to avoid repetition
            # Use larger window and normalize to lowercase for case-insensitive matching
            # For high-rank words (7000+), use even larger window since words are more clustered
            window_size = self.RECENT_WORDS_WINDOW * 2 if rank >= 7000 else self.RECENT_WORDS_WINDOW
            recently_used_words = [
                h.get("word").lower() if h.get("word") else None
                for h in state.history[-window_size:] 
                if h.get("word")
            ]
            # Also get ALL used words for duplicate detection logging
            all_used_words = [
                h.get("word").lower() if h.get("word") else None
                for h in state.history
                if h.get("word")
            ]
            
            # Step 1: Fetch target word at this rank
            # UPDATED: Adds filters to ignore short words and stop words (Noise Filter)
            # Filter 1: No tiny words (< 3 letters)
            # Filter 2: No stop words (Rank < 50)
            # Filter 3: Exclude recently used words
            # Filter 4: Only words that HAVE Chinese definitions (NEW - prevents placeholder issues)
            # Normalize excluded words for case-insensitive matching in query
            excluded_words_normalized = [w.lower() for w in recently_used_words if w] if recently_used_words else []
            
            if excluded_words_normalized:
                query_anchor = """
                    MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                    WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                    AND size(b.name) >= 3        // Filter 1: No tiny words
                    AND b.frequency_rank > 50    // Filter 2: No stop words
                    AND NOT toLower(b.name) IN $excluded_words  // Filter 3: Exclude recently used (case-insensitive)
                    AND s.definition_zh IS NOT NULL    // Filter 4: Must have Chinese definition
                    WITH b, rand() as r 
                    ORDER BY r 
                    LIMIT 1
                    RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                """
            else:
                query_anchor = """
                    MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                    WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                    AND size(b.name) >= 3        // Filter 1: No tiny words
                    AND b.frequency_rank > 50    // Filter 2: No stop words
                    AND s.definition_zh IS NOT NULL    // Filter 4: Must have Chinese definition
                    WITH b, rand() as r 
                    ORDER BY r 
                    LIMIT 1
                    RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                """
            
            # Search range expands if we are deep in the graph to ensure we find *something*
            # Start with a reasonable radius, expand if needed
            search_radius = 20 if phase > 1 else 100
            max_attempts = 3
            word = None
            actual_rank = rank
            target_embedding = None
            # Keep excluded words throughout - DO NOT clear them when expanding search
            current_excluded_words = excluded_words_normalized.copy() if excluded_words_normalized else []
            
            for attempt in range(max_attempts):
                # Rebuild query if exclusion list changed
                if current_excluded_words:
                    current_query = """
                        MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                        WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                        AND size(b.name) >= 3
                        AND b.frequency_rank > 50
                        AND NOT toLower(b.name) IN $excluded_words  // Case-insensitive exclusion
                        AND s.definition_zh IS NOT NULL    // Must have Chinese definition
                        WITH b, rand() as r 
                        ORDER BY r 
                        LIMIT 1
                        RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                    """
                else:
                    current_query = """
                        MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                        WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                        AND size(b.name) >= 3
                        AND b.frequency_rank > 50
                        AND s.definition_zh IS NOT NULL    // Must have Chinese definition
                        WITH b, rand() as r 
                        ORDER BY r 
                        LIMIT 1
                        RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                    """
                
                # Execute with rank range
                params = {
                    "min_r": max(1, rank - search_radius),
                    "max_r": min(8000, rank + search_radius)
                }
                if current_excluded_words:
                    params["excluded_words"] = current_excluded_words
                
                result = session.run(current_query, **params)
                
                row = result.single()
                
                if row:
                    word = row["word"]
                    # Convert rank to int (Neo4j may return float)
                    actual_rank = int(row["rank"])
                    target_embedding = row["embedding"]
                    
                    # LOG DUPLICATE DETECTION
                    word_lower = word.lower() if word else None
                    if word_lower and word_lower in all_used_words:
                        # Find when it was used
                        first_occurrence = next((i for i, w in enumerate(all_used_words) if w == word_lower), -1)
                        logger.warning(
                            f"⚠️ DUPLICATE DETECTED: Word '{word}' (rank {actual_rank}) "
                            f"was already used at question {first_occurrence + 1}. "
                            f"Current question: {len(state.history) + 1}. "
                            f"Recent words: {recently_used_words[-5:]}"
                        )
                    break
                else:
                    # If no word found, expand search radius
                    # IMPORTANT: Keep excluded words - don't clear them!
                    if attempt < max_attempts - 1:
                        search_radius = int(search_radius * 2)  # Double the radius
                        # DO NOT clear excluded words - this was causing duplicates!
                        # Excluded words should persist throughout all attempts
            
            if not word:
                # Fallback if sparse data (shouldn't happen with full DB)
                # Try one more time with wider range, but STILL respect exclusions
                fallback_params = {
                    "min_r": max(1, rank - 500),
                    "max_r": min(8000, rank + 500)
                }
                if current_excluded_words:
                    fallback_query = """
                        MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                        WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                        AND size(b.name) >= 3
                        AND b.frequency_rank > 50
                        AND NOT toLower(b.name) IN $excluded_words  // Still respect exclusions
                        AND s.definition_zh IS NOT NULL    // Must have Chinese definition
                        WITH b, rand() as r 
                        ORDER BY r 
                        LIMIT 1
                        RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                    """
                    fallback_params["excluded_words"] = current_excluded_words
                else:
                    fallback_query = """
                        MATCH (b:Word)-[:HAS_SENSE]->(s:Sense)
                        WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                        AND size(b.name) >= 3
                        AND b.frequency_rank > 50
                        AND s.definition_zh IS NOT NULL    // Must have Chinese definition
                        WITH b, rand() as r 
                        ORDER BY r 
                        LIMIT 1
                        RETURN b.name as word, b.embedding as embedding, b.frequency_rank as rank
                    """
                
                result = session.run(fallback_query, **fallback_params)
                row = result.single()
                if row:
                    word = row["word"]
                    actual_rank = int(row["rank"])
                    target_embedding = row["embedding"]
                    
                    # LOG DUPLICATE DETECTION (fallback case)
                    word_lower = word.lower() if word else None
                    if word_lower and word_lower in all_used_words:
                        first_occurrence = next((i for i, w in enumerate(all_used_words) if w == word_lower), -1)
                        logger.warning(
                            f"⚠️ DUPLICATE DETECTED (fallback): Word '{word}' (rank {actual_rank}) "
                            f"was already used at question {first_occurrence + 1}. "
                            f"Current question: {len(state.history) + 1}. "
                            f"Recent words: {recently_used_words[-5:]}"
                        )
                else:
                    # Ultimate fallback
                    word = "Estimate"
                    actual_rank = 2000
                    target_embedding = None
            
            # Step 2: Generate options (pass embedding for discriminator logic)
            options, option_metadata = self._generate_options(session, word, actual_rank, target_embedding)
            
            # Step 3: Create question payload
            question_id = f"q_{actual_rank}_{random.randint(10000,99999)}"
            
            # Attach metadata to options for storage (as extra fields in dict)
            # This will be included when we serialize to JSON
            payload = QuestionPayload(
                question_id=question_id,
                word=word,
                rank=actual_rank,
                options=options,
                time_limit=12
            )
            
            # Store metadata on payload object for API layer to access
            payload._option_metadata = option_metadata
            
            return payload
    
    def _generate_options(
        self,
        session,
        target_word: str,
        rank: int,
        target_embedding: Optional[List[float]] = None
    ) -> List[QuestionOption]:
        """
        Generate 6 options for the question.
        
        Options include:
        - 1-5 Target definitions (correct answers from target word's senses)
        - 0-3 Trap definitions (from CONFUSED_WITH relationships)
        - 2 Fillers (random definitions from nearby ranks)
        - 1 "Unknown" option
        
        Args:
            session: Neo4j session
            target_word: Target word
            rank: Frequency rank
            
        Returns:
            List of 6 QuestionOption objects
        """
        options = []
        option_id_counter = 0
        
        # Step 1: Fetch target definitions (correct answers)
        # STRONGLY prefer senses where sense_id matches word name (primary senses)
        # This ensures we get the correct definitions, not shared/wrong senses
        # Also fetch sense metadata for context/usage display
        target_query = """
            MATCH (t:Word {name: $target_word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.definition_zh IS NOT NULL
            // STRONGLY prioritize senses where sense_id starts with the word (primary senses)
            // This filters out incorrectly shared senses (e.g., brave using weather.v.01)
            WITH s, 
                 CASE 
                   WHEN s.id STARTS WITH toLower($target_word) THEN 10.0  // Strong bonus for matching
                   ELSE 0.1  // Very low priority for non-matching
                 END as sense_match_bonus,
                 COALESCE(s.usage_ratio, 1.0) as base_weight
            RETURN s.id as sense_id,
                   s.definition_zh as text, 
                   s.definition_en as definition_en,
                   s.example_en as example_en,
                   s.example_zh as example_zh,
                   s.usage_ratio as usage_ratio,
                   (base_weight + sense_match_bonus) as weight,
                   'target' as type
            ORDER BY weight DESC
            LIMIT 5
        """
        
        # Adapt query (though this one doesn't use :Block, it's good practice)
        adapted_target_query = self.adapter.adapt_block_query(target_query)
        target_results = session.run(adapted_target_query, target_word=target_word)
        
        target_definitions = []
        for record in target_results:
            text = record.get("text")
            if text:  # Only add if definition exists
                target_definitions.append({
                    "text": text,
                    "weight": record.get("weight", 1.0),
                    "type": "target",
                    "sense_id": record.get("sense_id"),
                    "definition_en": record.get("definition_en"),
                    "example_en": record.get("example_en"),
                    "example_zh": record.get("example_zh"),
                    "usage_ratio": record.get("usage_ratio")
                })
        
        # Add target options (1-5, but at least 1)
        num_targets = min(len(target_definitions), 5)
        if num_targets == 0:
            # Fallback: Try to find a definition from a related word or use English definition
            # First, try to get English definition and translate it
            fallback_query = """
                MATCH (t:Word {name: $target_word})-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_en IS NOT NULL
                RETURN s.definition_en as text_en
                LIMIT 1
            """
            fallback_result = session.run(fallback_query, target_word=target_word).single()
            if fallback_result and fallback_result.get("text_en"):
                # Use English definition as last resort (better than placeholder)
                target_definitions.append({
                    "text": fallback_result.get("text_en"),  # Use English if Chinese not available
                    "weight": 1.0,
                    "type": "target"
                })
                num_targets = 1
            else:
                # If no definition at all, this word shouldn't be in the survey
                # But we'll add a generic message instead of confusing placeholder
                target_definitions.append({
                    "text": "此單字尚未有中文定義",  # "This word does not have a Chinese definition yet"
                    "weight": 1.0,
                    "type": "target"
                })
                num_targets = 1
        
        # Store metadata mapping for later attachment
        target_metadata = {}
        for i in range(num_targets):
            target_def = target_definitions[i]
            option_id = f"target_{target_word}_{i}"
            options.append(QuestionOption(
                id=option_id,  # Use "target_" prefix for stateless hack
                text=target_def["text"],
                type="target",
                is_correct=True
            ))
            # Store metadata for detailed reporting (will be included in all_options)
            target_metadata[option_id] = {
                "sense_id": target_def.get("sense_id"),
                "definition_en": target_def.get("definition_en"),
                "example_en": target_def.get("example_en"),
                "example_zh": target_def.get("example_zh"),
                "usage_ratio": target_def.get("usage_ratio"),
                "is_primary_sense": target_def.get("sense_id", "").startswith(target_word.lower()) if target_def.get("sense_id") else None
            }
            option_id_counter += 1
        
        # Step 2: Fetch trap definitions (from CONFUSED_WITH relationships)
        # Use the passed-in target_embedding, or fetch it if not provided
        if target_embedding is None:
            target_node_query = """
                MATCH (t:Word {name: $target_word})
                RETURN t, t.embedding as target_embedding
                LIMIT 1
            """
            target_node_result = session.run(target_node_query, target_word=target_word).single()
            target_node = dict(target_node_result["t"]) if target_node_result and target_node_result.get("t") else None
            target_embedding = target_node_result.get("target_embedding") if target_node_result else None
        else:
            # Still need target_node for rank comparison fallback
            target_node_query = """
                MATCH (t:Word {name: $target_word})
                RETURN t
                LIMIT 1
            """
            target_node_result = session.run(target_node_query, target_word=target_word).single()
            target_node = dict(target_node_result["t"]) if target_node_result and target_node_result.get("t") else None
        
        trap_query = """
            MATCH (t:Word {name: $target_word})-[:CONFUSED_WITH]->(trap:Word)
            MATCH (trap)-[:HAS_SENSE]->(ts:Sense)
            WHERE ts.definition_zh IS NOT NULL
            RETURN trap, ts.definition_zh as text, trap.embedding as trap_embedding, 'trap' as type
            LIMIT 5
        """
        
        trap_results = session.run(trap_query, target_word=target_word)
        trap_definitions = []
        for record in trap_results:
            text = record.get("text")
            trap_node_raw = record.get("trap")
            trap_embedding = record.get("trap_embedding")
            
            if text and trap_node_raw:
                # Convert Neo4j Node to dictionary
                trap_node = dict(trap_node_raw)
                
                # Validate trap using cosine similarity (Discriminator Logic)
                if self._validate_trap(target_node, target_embedding, trap_node, trap_embedding):
                    trap_definitions.append({
                        "text": text,
                        "type": "trap",
                        "trap_node": trap_node,
                        "trap_embedding": trap_embedding
                    })
                    if len(trap_definitions) >= 3:  # Max 3 traps
                        break
        
        # Fallback: If no validated traps, try RELATED_TO relationships
        if len(trap_definitions) < 2:
            related_query = """
                MATCH (t:Word {name: $target_word})-[:RELATED_TO]->(trap:Word)
                MATCH (trap)-[:HAS_SENSE]->(ts:Sense)
                WHERE ts.definition_zh IS NOT NULL
                RETURN trap, ts.definition_zh as text, trap.embedding as trap_embedding, 'trap' as type
                LIMIT 5
            """
            related_results = session.run(related_query, target_word=target_word)
            for record in related_results:
                text = record.get("text")
                trap_node_raw = record.get("trap")
                trap_embedding = record.get("trap_embedding")
                
                if text and trap_node_raw:
                    # Convert Neo4j Node to dictionary
                    trap_node = dict(trap_node_raw)
                    
                    # Check if we already have this trap
                    if any(td.get("trap_node", {}).get("word_id") == trap_node.get("word_id") 
                           for td in trap_definitions):
                        continue
                    
                    # Validate trap using cosine similarity
                    if self._validate_trap(target_node, target_embedding, trap_node, trap_embedding):
                        trap_definitions.append({
                            "text": text,
                            "type": "trap",
                            "trap_node": trap_node,
                            "trap_embedding": trap_embedding
                        })
                        if len(trap_definitions) >= 3:
                            break
        
        # Add trap options (up to 3, but ensure we have 6 total options)
        num_traps = min(len(trap_definitions), 3)
        for i in range(num_traps):
            if option_id_counter >= 5:  # Reserve last slot for "unknown"
                break
            trap_word_id = trap_definitions[i].get("trap_node", {}).get("word_id", f"trap_{i}")
            options.append(QuestionOption(
                id=f"trap_{trap_word_id}",  # Use "trap_" prefix
                text=trap_definitions[i]["text"],
                type="trap",
                is_correct=False
            ))
            option_id_counter += 1
        
        # Step 3: Fetch filler definitions (semantically filtered for plausible distractors)
        # IMPROVED: Use semantic similarity to find plausible but distinct distractors
        # Fillers should be somewhat related (similarity 0.3-0.6) to be plausible, but not too similar (which would be traps)
        trap_word_ids = [td.get("trap_node", {}).get("word_id") for td in trap_definitions if td.get("trap_node", {}).get("word_id")]
        excluded_words = [target_word] + [td.get("trap_node", {}).get("name") for td in trap_definitions if td.get("trap_node", {}).get("name")]
        
        # We need enough fillers to make 6 total options
        # Current: len(target_definitions) targets + len(trap_definitions) traps + 1 unknown = X
        # Need: 6 - X fillers (but get a few extra to filter by similarity)
        needed_fillers = max(2, 6 - len(target_definitions) - len(trap_definitions) - 1)
        
        # Try to find semantically plausible fillers first
        filler_definitions = []
        search_radius = 50
        max_radius = 500
        max_attempts = 3
        
        # If we have target embedding, use semantic similarity filtering
        use_semantic_filtering = target_embedding is not None
        
        for attempt in range(max_attempts):
            if use_semantic_filtering:
                # Query with embedding fetch for similarity calculation
                filler_query = """
                    MATCH (f:Word)-[:HAS_SENSE]->(fs:Sense)
                    WHERE f.frequency_rank >= $min_r AND f.frequency_rank <= $max_r
                    AND NOT f.name IN $excluded_words
                    AND size(f.name) >= 3
                    AND f.frequency_rank > 50
                    AND fs.definition_zh IS NOT NULL
                    AND f.embedding IS NOT NULL
                    WITH f, fs, f.embedding as filler_embedding, rand() as r
                    ORDER BY r
                    LIMIT $limit
                    RETURN f.word_id as word_id, fs.definition_zh as text, 'filler' as type, filler_embedding as embedding
                """
            else:
                # Fallback: random selection if no embedding available
                filler_query = """
                    MATCH (f:Word)-[:HAS_SENSE]->(fs:Sense)
                    WHERE f.frequency_rank >= $min_r AND f.frequency_rank <= $max_r
                    AND NOT f.name IN $excluded_words
                    AND size(f.name) >= 3
                    AND f.frequency_rank > 50
                    AND fs.definition_zh IS NOT NULL
                    WITH f, fs, rand() as r
                    ORDER BY r
                    LIMIT $limit
                    RETURN f.word_id as word_id, fs.definition_zh as text, 'filler' as type, null as embedding
                """
            
            # Get more candidates when using semantic filtering (need to filter by similarity)
            candidate_limit = (needed_fillers * 3) if use_semantic_filtering else (needed_fillers + 2)
            filler_results = session.run(
                filler_query,
                min_r=max(1, rank - search_radius),
                max_r=min(8000, rank + search_radius),
                excluded_words=excluded_words,
                limit=candidate_limit
            )
            
            for record in filler_results:
                text = record.get("text")
                word_id = record.get("word_id")
                filler_embedding = record.get("embedding")
                
                if text and len(filler_definitions) < needed_fillers + 2:
                    # Avoid duplicates by text
                    if any(fd.get("text") == text for fd in filler_definitions):
                        continue
                    
                    # If using semantic filtering, check similarity
                    if use_semantic_filtering and filler_embedding:
                        try:
                            # Convert to list if needed
                            if not isinstance(filler_embedding, list):
                                filler_embedding = list(filler_embedding)
                            
                            similarity = self._cosine_similarity(target_embedding, filler_embedding)
                            
                            # Good filler: similarity between 0.2-0.7 (plausible but distinct)
                            # Too similar (>0.7) would be a trap, too different (<0.2) is obviously wrong
                            # But if we don't have enough fillers yet, accept wider range (0.05-0.85)
                            # For high-rank words, similarity might be naturally lower, so be more lenient
                            min_similarity = 0.2 if len(filler_definitions) >= needed_fillers else 0.05
                            max_similarity = 0.7 if len(filler_definitions) >= needed_fillers else 0.85
                            
                            # Also accept if similarity is very low but positive (better than completely random)
                            if min_similarity <= similarity <= max_similarity or (similarity > 0.0 and len(filler_definitions) < needed_fillers / 2):
                                filler_definitions.append({
                                    "text": text,
                                    "type": "filler",
                                    "word_id": word_id
                                })
                        except Exception:
                            # If similarity calculation fails, include it anyway (fallback)
                            filler_definitions.append({
                                "text": text,
                                "type": "filler",
                                "word_id": word_id
                            })
                    else:
                        # No semantic filtering, just add it
                        filler_definitions.append({
                            "text": text,
                            "type": "filler",
                            "word_id": word_id
                        })
            
            # If we found enough fillers, break
            if len(filler_definitions) >= needed_fillers:
                break
            
            # Expand search radius for next attempt
            if attempt < max_attempts - 1:
                search_radius = min(search_radius * 2, max_radius)
                # If we've expanded significantly, relax or disable semantic filtering
                if search_radius > 200:
                    use_semantic_filtering = False
                elif search_radius > 100 and len(filler_definitions) < needed_fillers:
                    # Relax similarity range if we're having trouble finding fillers
                    # This helps with high-rank words where semantic similarity might be lower
                    pass  # The similarity range already relaxes dynamically above
        
        # Add filler options (enough to make 6 total, but at least 2)
        num_fillers = min(len(filler_definitions), needed_fillers)
        for i in range(num_fillers):
            if option_id_counter >= 5:  # Reserve last slot for "unknown"
                break
            filler_word_id = filler_definitions[i].get("word_id", f"filler_{i}")
            options.append(QuestionOption(
                id=f"filler_{filler_word_id}",  # Use "filler_" prefix
                text=filler_definitions[i]["text"],
                type="filler",
                is_correct=False
            ))
            option_id_counter += 1
        
        # Step 4: Add "Unknown" option (always last)
        options.append(QuestionOption(
            id="unknown_option",
            text="我不知道",
            type="unknown",
            is_correct=False
        ))
        
        # Ensure we have exactly 6 options (pad with fillers if needed)
        # If we still don't have enough fillers, try one more time without semantic filtering
        if len(options) < 6 and use_semantic_filtering:
            # Last resort: get random fillers without semantic filtering
            last_resort_query = """
                MATCH (f:Word)-[:HAS_SENSE]->(fs:Sense)
                WHERE f.frequency_rank >= $min_r AND f.frequency_rank <= $max_r
                AND NOT f.name IN $excluded_words
                AND size(f.name) >= 3
                AND f.frequency_rank > 50
                AND fs.definition_zh IS NOT NULL
                WITH f, fs, rand() as r
                ORDER BY r
                LIMIT $limit
                RETURN f.word_id as word_id, fs.definition_zh as text, 'filler' as type
            """
            last_resort_results = session.run(
                last_resort_query,
                min_r=max(1, rank - 500),
                max_r=min(8000, rank + 500),
                excluded_words=excluded_words,
                limit=6 - len(options)
            )
            for record in last_resort_results:
                text = record.get("text")
                word_id = record.get("word_id")
                if text and len(options) < 6:
                    if not any(opt.text == text for opt in options):
                        options.insert(-1, QuestionOption(  # Insert before "unknown"
                            id=f"filler_{word_id}",
                            text=text,
                            type="filler",
                            is_correct=False
                        ))
        
        # Final fallback: pad with placeholders only if absolutely necessary
        while len(options) < 6:
            options.insert(-1, QuestionOption(  # Insert before "unknown"
                id=f"filler_pad_{len(options) - 1}",
                text="其他選項",
                type="filler",
                is_correct=False
            ))
        
        # Shuffle options (except keep "unknown" last)
        # Note: We keep the original IDs (target_*, trap_*, filler_*) for stateless hack
        unknown_option = options.pop()
        random.shuffle(options)
        options.append(unknown_option)
        
        # Return options and metadata for detailed reporting
        return options, target_metadata
    
    def _validate_trap(
        self,
        target_node: Optional[Dict[str, Any]],
        target_embedding: Optional[List[float]],
        trap_node: Dict[str, Any],
        trap_embedding: Optional[List[float]]
    ) -> bool:
        """
        Validate a trap word using cosine similarity on embeddings (Discriminator Logic).
        
        A good trap should be similar enough to be confusing, but not too similar.
        Rule: Only accept traps where CosineSimilarity(Target, Trap) < 0.6.
        
        If embeddings are missing/null, fallback to accepting the trap
        (or checking rank difference as a secondary check).
        
        Args:
            target_node: Target word node dictionary
            target_embedding: Target word embedding vector (list of floats)
            trap_node: Trap word node dictionary
            trap_embedding: Trap word embedding vector (list of floats)
            
        Returns:
            True if trap is valid (similarity < 0.6), False otherwise
        """
        # If embeddings exist, use cosine similarity
        if target_embedding and trap_embedding:
            try:
                # Convert to lists if needed (Neo4j might return as array)
                if not isinstance(target_embedding, list):
                    target_embedding = list(target_embedding)
                if not isinstance(trap_embedding, list):
                    trap_embedding = list(trap_embedding)
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(target_embedding, trap_embedding)
                
                # Discriminator rule: Only accept traps where similarity < 0.6
                # This ensures the definitions are distinct enough to be a fair trap
                if similarity >= self.SIMILARITY_THRESHOLD:
                    return False  # Too similar, reject trap
                
                # Good trap: similarity is between 0.0 and 0.6
                return True
            except Exception as e:
                # If similarity calculation fails, fallback to rank check
                pass
        
        # Fallback: Check rank difference if embeddings are missing
        # Accept trap if rank is within reasonable range (not too close, not too far)
        if target_node and trap_node:
            target_rank = target_node.get("frequency_rank") or target_node.get("rank", 0)
            trap_rank = trap_node.get("frequency_rank") or trap_node.get("rank", 0)
            
            if target_rank > 0 and trap_rank > 0:
                rank_diff = abs(target_rank - trap_rank)
                # Accept if rank is within reasonable range (100-2000)
                # This ensures traps are from similar vocabulary levels
                return 100 <= rank_diff <= 2000
        
        # If we can't validate, accept the trap (better to have a trap than no trap)
        return True
    
    def _calculate_confidence(self, state: SurveyState) -> float:
        """
        Calculate current confidence level based on survey progress.
        
        Confidence increases with:
        - More questions answered
        - Consistent answers
        - Converged bounds
        
        Args:
            state: Current survey state
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if len(state.history) == 0:
            return 0.0
        
        # Base confidence from question count
        question_factor = min(len(state.history) / self.MIN_QUESTIONS, 1.0)
        
        # Consistency factor (ratio of correct answers)
        correct_count = sum(1 for h in state.history if h.get("correct", False))
        consistency_factor = correct_count / len(state.history) if len(state.history) > 0 else 0.0
        
        # Convergence factor (how narrow the bounds are)
        range_size = state.high_bound - state.low_bound
        convergence_factor = 1.0 - min(range_size / 8000.0, 1.0)
        
        # Weighted combination
        confidence = (
            0.3 * question_factor +
            0.4 * consistency_factor +
            0.3 * convergence_factor
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_final_metrics(self, state: SurveyState) -> TriMetricReport:
        """
        Calculate the final Tri-Metric Report.
        
        Metrics:
        - Volume (Est. Reserves): Area under probability curve
        - Reach (Horizon): Highest rank where reliability > 50%
        - Density (Solidity): Consistency within owned zone
        
        Args:
            state: Final survey state
            
        Returns:
            TriMetricReport with volume, reach, and density
        """
        if len(state.history) == 0:
            return TriMetricReport(volume=0, reach=0, density=0.0)
        
        # Calculate Volume (Est. Reserves)
        # Area under probability curve: sum of confidence-weighted word counts
        volume = 0
        for i, hist in enumerate(state.history):
            rank = hist["rank"]
            correct = hist.get("correct", False)
            
            # Weight by correctness and position in survey
            weight = 1.0 if correct else 0.3
            position_weight = 1.0 - (i / len(state.history)) * 0.2  # Slight decay
            
            volume += int(rank * weight * position_weight)
        
        # Normalize: divide by average to get estimated word count
        if len(state.history) > 0:
            volume = volume // len(state.history)
        
        # Calculate Reach (Horizon)
        # Highest rank where reliability > 50%
        # Find the highest rank with correct answer
        correct_ranks = [h["rank"] for h in state.history if h.get("correct", False)]
        if correct_ranks:
            max_correct_rank = max(correct_ranks)  # Store original for density calculation
            reach = max_correct_rank
        else:
            # If no correct answers, use low_bound
            max_correct_rank = state.low_bound
            reach = state.low_bound
        
        # Apply reliability threshold: if last few answers were wrong, reduce reach
        if len(state.history) >= 3:
            recent_correct = sum(1 for h in state.history[-3:] if h.get("correct", False))
            if recent_correct < 2:
                # Recent performance poor, reduce reach
                reach = int(reach * 0.8)
        
        # Calculate Density (Solidity)
        # Density measures how consistently the user knows words within their vocabulary range
        # 
        # APPROACH: Use MONOTONICITY with EDGE CASE HANDLING
        # - Monotonicity: proportion of consistent pairs (no "wrong → correct" reversals)
        # - Edge cases: all wrong = 0, all correct = 1
        #
        # Why monotonicity works:
        # - Consistent user: correct below boundary, wrong above → few reversals → high monotonicity
        # - Inconsistent user: gaps below boundary → more "wrong → correct" reversals → lower monotonicity
        
        if len(state.history) == 0:
            density = 0.0
        else:
            correct_count = sum(1 for h in state.history if h.get("correct", False))
            
            # Edge cases
            if correct_count == 0:
                density = 0.0  # No knowledge at all
            elif correct_count == len(state.history):
                density = 1.0  # Perfect knowledge
            elif len(state.history) < 2:
                # Single question, not an edge case
                density = 1.0 if state.history[0].get("correct", False) else 0.0
            else:
                # Normal case: calculate monotonicity
                sorted_history = sorted(state.history, key=lambda h: h["rank"])
                
                consistent_pairs = 0
                total_pairs = len(sorted_history) - 1
                
                for i in range(total_pairs):
                    lower_correct = sorted_history[i].get("correct", False)
                    higher_correct = sorted_history[i + 1].get("correct", False)
                    
                    # A pair is inconsistent only if: lower is WRONG but higher is CORRECT
                    # This indicates a "gap" in knowledge followed by a "lucky guess"
                    if not lower_correct and higher_correct:
                        # Inconsistent: missed an easier word but got a harder one
                        pass  # Don't increment
                    else:
                        # Consistent: either both correct, both wrong, or expected transition
                        consistent_pairs += 1
                
                density = consistent_pairs / total_pairs if total_pairs > 0 else 0.5
        
        # Clamp values
        volume = max(0, min(8000, volume))
        reach = max(0, min(8000, reach))
        density = max(0.0, min(1.0, density))
        
        return TriMetricReport(
            volume=volume,
            reach=reach,
            density=density
        )
    
    def _generate_methodology_explanation(self, state: SurveyState) -> Dict[str, Any]:
        """
        Generate explanation of how the survey was conducted.
        
        Returns:
            Dictionary with methodology details
        """
        total_questions = len(state.history)
        phase_1_count = sum(1 for h in state.history if h.get("phase") == 1)
        phase_2_count = sum(1 for h in state.history if h.get("phase") == 2)
        phase_3_count = sum(1 for h in state.history if h.get("phase") == 3)
        
        start_rank = state.history[0]["rank"] if state.history else 2000
        
        return {
            "total_questions": total_questions,
            "phases": {
                "phase_1_coarse_sweep": {
                    "name": "Coarse Sweep",
                    "questions": phase_1_count,
                    "description": "Wide-ranging binary search (±1500 rank steps) to quickly locate your vocabulary range",
                    "step_size": self.PHASE_1_STEP
                },
                "phase_2_fine_tuning": {
                    "name": "Fine Tuning",
                    "questions": phase_2_count,
                    "description": "Oscillating search (±200 rank steps) to refine the boundary",
                    "step_size": self.PHASE_2_STEP
                },
                "phase_3_verification": {
                    "name": "Verification",
                    "questions": phase_3_count,
                    "description": "Precise verification (±100 rank steps) to confirm the final boundary",
                    "step_size": self.PHASE_3_STEP
                }
            },
            "algorithm": "Adaptive Binary Search with 3-Phase Funnel",
            "question_format": "6-option multiple choice with variable correct answers (1-5 targets)",
            "scoring_method": "Multi-select: must select ALL correct options and NO incorrect options",
            "start_rank": start_rank,
            "final_bounds": {
                "low_bound": state.low_bound,
                "high_bound": state.high_bound,
                "range": state.high_bound - state.low_bound
            }
        }

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Used for trap validation (Discriminator Logic).
        Only accept traps where similarity < 0.6.
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Cosine similarity (0.0-1.0)
        """
        if not v1 or not v2 or len(v1) != len(v2):
            # Fallback: use heuristic (different word families = low similarity)
            return 0.3
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(v1, v2))
        
        # Calculate norms
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(a * a for a in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
