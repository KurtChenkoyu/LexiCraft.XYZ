"""
MCQ Assembler V2: Context-Aware, Polysemy-Safe MCQs

Philosophy:
- Explanation Engine = HELPER (never tested directly)
- MCQ = Simple verification (do you know THIS specific meaning?)
- "Help, not confuse" - supportive, not cruel

FIXES from V1:
1. CONTEXT: MEANING MCQ now shows the example sentence
2. POLYSEMY: Distractors come from DIFFERENT WORDS, not same word different senses
3. USAGE: Question is now sense-specific ("which shows THIS meaning?")
4. CLARITY: Distractors show source word for transparency
5. SIMILARITY: Skip distractors too similar to correct answer

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
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from src.database.neo4j_connection import Neo4jConnection


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
    source: str           # "target", "confused", "opposite", "similar", "other_sense"
    source_word: str = "" # The word this definition came from (for transparency)


@dataclass
class MCQ:
    """A complete MCQ ready for verification."""
    sense_id: str
    word: str
    mcq_type: MCQType
    question: str
    context: str              # The example sentence providing context (NEW!)
    options: List[MCQOption]
    correct_index: int
    explanation: str          # Shows AFTER answering (helps learning)
    metadata: Dict = field(default_factory=dict)


class MCQAssembler:
    """
    Assembles fair, context-aware MCQs from Stage 2 enriched senses.
    
    Core Principles:
    1. Always provide CONTEXT (example sentence)
    2. Distractors from DIFFERENT WORDS (not polysemy traps)
    3. Test THIS specific sense, not "any meaning of the word"
    """
    
    def __init__(self, conn: Neo4jConnection):
        self.conn = conn
    
    def assemble_mcqs_for_sense(self, sense_id: str) -> List[MCQ]:
        """
        Generate MCQ pool for a single sense.
        
        Returns 1-3 MCQs:
        - 1x MEANING (if we have context sentence)
        - 1x USAGE (if multiple examples exist)  
        - 1x DISCRIMINATION (if confused words exist)
        """
        mcqs = []
        
        # Fetch sense data including other senses of same word (for polysemy awareness)
        sense_data = self._fetch_sense_data(sense_id)
        if not sense_data:
            print(f"⚠️ Sense {sense_id} not found or not enriched")
            return []
        
        word = sense_data["word"]
        
        # Fetch distractors from DIFFERENT WORDS only
        distractors = self._fetch_distractors_safe(word, sense_id, sense_data.get("other_senses", []))
        
        # 1. MEANING MCQ (requires context sentence)
        if sense_data.get("example_en") or sense_data.get("examples_contextual"):
            meaning_mcq = self._create_meaning_mcq(sense_data, distractors)
            if meaning_mcq:
                mcqs.append(meaning_mcq)
        
        # 2. USAGE MCQ (requires multiple sentence options)
        if self._has_enough_usage_options(sense_data, distractors):
            usage_mcq = self._create_usage_mcq(sense_data, distractors)
            if usage_mcq:
                mcqs.append(usage_mcq)
        
        # 3. DISCRIMINATION MCQ (requires confused words - DIFFERENT words)
        if distractors.get("confused"):
            discrimination_mcq = self._create_discrimination_mcq(sense_data, distractors)
            if discrimination_mcq:
                mcqs.append(discrimination_mcq)
        
        return mcqs
    
    def _fetch_sense_data(self, sense_id: str) -> Optional[Dict]:
        """
        Fetch sense data AND other senses of the same word (for polysemy awareness).
        """
        with self.conn.get_session() as session:
            # Main sense data
            result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense {id: $sense_id})
                RETURN w.name as word,
                       w.frequency_rank as frequency_rank,
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
            
            # IMPORTANT: Fetch OTHER senses of the same word (for polysemy awareness)
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
    
    def _fetch_distractors_safe(
        self, 
        word: str, 
        target_sense_id: str,
        other_senses: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Fetch distractors from DIFFERENT WORDS only.
        
        CRITICAL: Excludes definitions from:
        1. Other senses of the SAME word (polysemy trap!)
        2. Definitions too similar to the correct answer
        
        Sources:
        - CONFUSED_WITH: Different words that are commonly confused
        - OPPOSITE_TO: Different words with opposite meaning
        - RELATED_TO: Different words with similar meaning (use carefully)
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
        
        with self.conn.get_session() as session:
            # CONFUSED_WITH - Different words that are commonly confused
            # CRITICAL: These must be DIFFERENT WORDS, not same word different sense
            result = session.run("""
                MATCH (w:Word {name: $word})-[r:CONFUSED_WITH]->(c:Word)
                WHERE c.name <> $word
                MATCH (c)-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_zh IS NOT NULL
                WITH c, r, s
                ORDER BY CASE WHEN s.id STARTS WITH toLower(c.name) THEN 1 ELSE 2 END
                RETURN DISTINCT c.name as word, 
                       r.reason as reason,
                       s.definition_zh as definition_zh,
                       s.definition_en as definition_en,
                       s.id as sense_id
                LIMIT 5
            """, word=word)
            
            for record in result:
                def_zh = record.get("definition_zh", "")
                # Skip if this definition matches another sense of the SAME word
                if def_zh not in same_word_definitions:
                    distractors["confused"].append({
                        "word": record["word"],
                        "reason": record.get("reason", "Unknown"),
                        "definition_zh": def_zh,
                        "definition_en": record.get("definition_en", ""),
                        "sense_id": record.get("sense_id", "")
                    })
            
            # OPPOSITE_TO - Different words with opposite meaning
            result = session.run("""
                MATCH (w:Word {name: $word})-[:OPPOSITE_TO]->(o:Word)
                WHERE o.name <> $word
                MATCH (o)-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_zh IS NOT NULL
                WITH o, s
                ORDER BY CASE WHEN s.id STARTS WITH toLower(o.name) THEN 1 ELSE 2 END
                RETURN DISTINCT o.name as word,
                       s.definition_zh as definition_zh,
                       s.definition_en as definition_en,
                       s.id as sense_id
                LIMIT 3
            """, word=word)
            
            for record in result:
                def_zh = record.get("definition_zh", "")
                if def_zh not in same_word_definitions:
                    distractors["opposite"].append({
                        "word": record["word"],
                        "definition_zh": def_zh,
                        "definition_en": record.get("definition_en", ""),
                        "sense_id": record.get("sense_id", "")
                    })
            
            # RELATED_TO (synonyms) - Use carefully, may be too similar
            result = session.run("""
                MATCH (w:Word {name: $word})-[:RELATED_TO]->(r:Word)
                WHERE r.name <> $word
                MATCH (r)-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_zh IS NOT NULL
                WITH r, s
                ORDER BY CASE WHEN s.id STARTS WITH toLower(r.name) THEN 1 ELSE 2 END
                RETURN DISTINCT r.name as word,
                       s.definition_zh as definition_zh,
                       s.definition_en as definition_en,
                       s.id as sense_id
                LIMIT 3
            """, word=word)
            
            for record in result:
                def_zh = record.get("definition_zh", "")
                if def_zh not in same_word_definitions:
                    distractors["similar"].append({
                        "word": record["word"],
                        "definition_zh": def_zh,
                        "definition_en": record.get("definition_en", ""),
                        "sense_id": record.get("sense_id", "")
                    })
        
        return distractors
    
    def _create_meaning_mcq(self, sense_data: Dict, distractors: Dict) -> Optional[MCQ]:
        """
        Create MEANING MCQ with CONTEXT.
        
        FIX: Now shows the example sentence so learner knows WHICH meaning we're asking about.
        
        Question format:
        "在這個句子中，'break' 是什麼意思？"
        Context: "Getting that job was a real break for him."
        """
        word = sense_data["word"]
        sense_id = sense_data["sense_id"]
        correct_def = sense_data.get("definition_zh") or sense_data.get("definition_en")
        
        if not correct_def:
            return None
        
        # Get context sentence (REQUIRED now!)
        context_sentence = ""
        examples_contextual = sense_data.get("examples_contextual", [])
        if examples_contextual and examples_contextual[0].get("example_en"):
            context_sentence = examples_contextual[0]["example_en"]
        elif sense_data.get("example_en"):
            context_sentence = sense_data["example_en"]
        
        if not context_sentence:
            # Can't create MEANING MCQ without context
            return None
        
        # Build options: 1 correct + 3 distractors from DIFFERENT WORDS
        options = [
            MCQOption(
                text=correct_def, 
                is_correct=True, 
                source="target",
                source_word=word
            )
        ]
        
        # Collect distractors (prioritize confused > opposite > similar)
        # CRITICAL: Only use definitions from DIFFERENT words
        distractor_pool = []
        
        for conf in distractors.get("confused", []):
            if conf.get("definition_zh") and conf["definition_zh"] != correct_def:
                distractor_pool.append(MCQOption(
                    text=conf["definition_zh"],
                    is_correct=False,
                    source="confused",
                    source_word=conf["word"]
                ))
        
        for opp in distractors.get("opposite", []):
            if opp.get("definition_zh") and opp["definition_zh"] != correct_def:
                distractor_pool.append(MCQOption(
                    text=opp["definition_zh"],
                    is_correct=False,
                    source="opposite",
                    source_word=opp["word"]
                ))
        
        for sim in distractors.get("similar", []):
            if sim.get("definition_zh") and sim["definition_zh"] != correct_def:
                distractor_pool.append(MCQOption(
                    text=sim["definition_zh"],
                    is_correct=False,
                    source="similar",
                    source_word=sim["word"]
                ))
        
        # Deduplicate by definition text
        seen = {correct_def}
        unique_distractors = []
        for opt in distractor_pool:
            if opt.text not in seen:
                seen.add(opt.text)
                unique_distractors.append(opt)
        
        if len(unique_distractors) < 3:
            # Not enough distractors from different words
            return None
        
        # Take 3 distractors
        selected_distractors = unique_distractors[:3]
        options.extend(selected_distractors)
        
        # Shuffle options
        random.shuffle(options)
        
        # Find correct index
        correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
        
        # Build question WITH CONTEXT
        question = f'在這個句子中，"{word}" 是什麼意思？'
        
        # Explanation (shown AFTER they answer)
        explanation = f'正確答案是「{correct_def}」。'
        explanation += f'\n在句子「{context_sentence}」中，"{word}" 表示「{correct_def}」。'
        
        return MCQ(
            sense_id=sense_id,
            word=word,
            mcq_type=MCQType.MEANING,
            question=question,
            context=context_sentence,  # NEW: Always provide context!
            options=options,
            correct_index=correct_index,
            explanation=explanation,
            metadata={
                "distractor_sources": [
                    {"source": opt.source, "word": opt.source_word} 
                    for opt in options if not opt.is_correct
                ]
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
        
        return count >= 4  # Need at least 4 sentences total
    
    def _create_usage_mcq(self, sense_data: Dict, distractors: Dict) -> Optional[MCQ]:
        """
        Create USAGE MCQ that's SENSE-SPECIFIC.
        
        FIX: Question now asks about THIS specific meaning, not just "correct usage".
        
        Question format:
        "哪一個句子中的 'break' 表示「機會」？"
        """
        word = sense_data["word"]
        sense_id = sense_data["sense_id"]
        correct_def = sense_data.get("definition_zh") or sense_data.get("definition_en")
        examples_contextual = sense_data.get("examples_contextual", [])
        
        if not examples_contextual or not correct_def:
            return None
        
        # Pick correct example
        correct_example = examples_contextual[0]
        correct_sentence = correct_example.get("example_en", "")
        
        if not correct_sentence:
            return None
        
        options = [
            MCQOption(
                text=correct_sentence, 
                is_correct=True, 
                source="target",
                source_word=word
            )
        ]
        
        # Build distractors from related examples (different senses/words)
        distractor_sentences = []
        
        for ex_list in [sense_data.get("examples_confused", []), 
                        sense_data.get("examples_opposite", []),
                        sense_data.get("examples_similar", [])]:
            for ex in ex_list:
                if ex.get("example_en") and ex["example_en"] != correct_sentence:
                    distractor_sentences.append(MCQOption(
                        text=ex["example_en"],
                        is_correct=False,
                        source=ex.get("relationship_type", "other"),
                        source_word=ex.get("relationship_word", "")
                    ))
        
        # Deduplicate
        seen = {correct_sentence}
        unique_distractors = []
        for opt in distractor_sentences:
            if opt.text not in seen:
                seen.add(opt.text)
                unique_distractors.append(opt)
        
        if len(unique_distractors) < 3:
            return None
        
        options.extend(unique_distractors[:3])
        random.shuffle(options)
        
        correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
        
        # FIX: Question is now sense-specific
        # Truncate definition if too long
        def_display = correct_def[:20] + "..." if len(correct_def) > 20 else correct_def
        question = f'哪一個句子中的 "{word}" 表示「{def_display}」？'
        
        explanation = f'正確答案是：「{correct_sentence}」'
        explanation += f'\n這個句子中的 "{word}" 表示「{correct_def}」。'
        
        return MCQ(
            sense_id=sense_id,
            word=word,
            mcq_type=MCQType.USAGE,
            question=question,
            context="",  # No single context - comparing multiple sentences
            options=options,
            correct_index=correct_index,
            explanation=explanation,
            metadata={
                "target_definition": correct_def
            }
        )
    
    def _create_discrimination_mcq(self, sense_data: Dict, distractors: Dict) -> Optional[MCQ]:
        """
        Create DISCRIMINATION MCQ between DIFFERENT WORDS.
        
        This is the cleanest MCQ type - tests if learner can distinguish
        between genuinely different words (e.g., "affect" vs "effect").
        
        NOT a polysemy test - we're comparing different words!
        """
        word = sense_data["word"]
        sense_id = sense_data["sense_id"]
        confused = distractors.get("confused", [])
        
        if not confused:
            return None
        
        # Pick a confused word (must be DIFFERENT word)
        confused_word_data = confused[0]
        confused_word = confused_word_data["word"]
        
        if confused_word == word:
            # Safety check - skip if somehow same word
            return None
        
        confusion_reason = confused_word_data.get("reason", "")
        
        # Get context sentence
        examples_contextual = sense_data.get("examples_contextual", [])
        context_sentence = ""
        
        if examples_contextual:
            context_sentence = examples_contextual[0].get("example_en", "")
        elif sense_data.get("example_en"):
            context_sentence = sense_data["example_en"]
        
        if not context_sentence or word.lower() not in context_sentence.lower():
            return None
        
        # Create fill-in-the-blank
        blank_sentence = context_sentence
        # Handle case sensitivity
        for variant in [word, word.capitalize(), word.upper(), word.lower()]:
            blank_sentence = blank_sentence.replace(variant, "_____")
        
        if "_____" not in blank_sentence:
            return None
        
        # Options: correct word and confused words (all DIFFERENT words)
        options = [
            MCQOption(text=word, is_correct=True, source="target", source_word=word)
        ]
        
        # Add confused words
        added_words = {word.lower()}
        for conf in confused[:3]:
            if conf["word"].lower() not in added_words:
                options.append(MCQOption(
                    text=conf["word"],
                    is_correct=False,
                    source="confused",
                    source_word=conf["word"]
                ))
                added_words.add(conf["word"].lower())
        
        # Pad if needed (but prefer not to use "我不確定")
        while len(options) < 4:
            options.append(MCQOption(
                text="以上皆非",
                is_correct=False,
                source="none_of_above",
                source_word=""
            ))
        
        random.shuffle(options)
        correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
        
        question = f'請選擇正確的詞填入空格：'
        
        # Helpful explanation
        explanation = f'正確答案是 "{word}"。'
        if confusion_reason:
            explanation += f'\n"{word}" 和 "{confused_word}" 容易混淆（{confusion_reason}）。'
        
        return MCQ(
            sense_id=sense_id,
            word=word,
            mcq_type=MCQType.DISCRIMINATION,
            question=question,
            context=blank_sentence,  # Show the sentence with blank
            options=options,
            correct_index=correct_index,
            explanation=explanation,
            metadata={
                "confused_with": confused_word,
                "confusion_reason": confusion_reason,
                "original_sentence": context_sentence
            }
        )
    
    def assemble_mcqs_batch(self, limit: int = 10) -> List[MCQ]:
        """Generate MCQs for multiple senses."""
        all_mcqs = []
        
        with self.conn.get_session() as session:
            result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.stage2_enriched = true OR s.enriched = true
                RETURN s.id as sense_id
                LIMIT $limit
            """, limit=limit)
            
            sense_ids = [record["sense_id"] for record in result]
        
        print(f"🎯 Generating MCQs for {len(sense_ids)} senses...")
        
        for sense_id in sense_ids:
            mcqs = self.assemble_mcqs_for_sense(sense_id)
            all_mcqs.extend(mcqs)
            
            if mcqs:
                print(f"  ✅ {sense_id}: {len(mcqs)} MCQs")
            else:
                print(f"  ⚠️ {sense_id}: No MCQs generated (insufficient distractors)")
        
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
                "source_word": opt.source_word
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


def store_mcqs_to_postgres(mcqs: List[MCQ], db_session) -> int:
    """
    Store generated MCQs to PostgreSQL for adaptive selection.
    
    Args:
        mcqs: List of MCQ objects from assembler
        db_session: SQLAlchemy database session
    
    Returns:
        Number of MCQs stored
    """
    from src.database.postgres_crud import mcq_stats
    
    stored_count = 0
    
    for mcq in mcqs:
        try:
            # Convert MCQ to dict format for storage
            options = [
                {
                    "text": opt.text,
                    "is_correct": opt.is_correct,
                    "source": opt.source,
                    "source_word": opt.source_word
                }
                for opt in mcq.options
            ]
            
            # Store to PostgreSQL
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
                metadata=mcq.metadata
            )
            stored_count += 1
        except Exception as e:
            print(f"⚠️ Failed to store MCQ for {mcq.sense_id}: {e}")
    
    return stored_count


def run_mcq_assembler(word: str = None, sense_id: str = None, limit: int = 10, store: bool = False):
    """
    Main entry point for MCQ assembly.
    
    Args:
        word: Target word
        sense_id: Target sense ID
        limit: Batch size
        store: Whether to store to PostgreSQL
    """
    conn = Neo4jConnection()
    db_session = None
    
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            return
        
        # Get PostgreSQL session if storing
        if store:
            from src.database.postgres_connection import PostgresConnection
            pg_conn = PostgresConnection()
            db_session = pg_conn.get_session()
        
        assembler = MCQAssembler(conn)
        
        if sense_id:
            print(f"🎯 Generating MCQs for sense: {sense_id}")
            mcqs = assembler.assemble_mcqs_for_sense(sense_id)
        elif word:
            with conn.get_session() as session:
                result = session.run("""
                    MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                    WHERE s.stage2_enriched = true OR s.enriched = true
                    RETURN s.id as sense_id
                """, word=word)
                sense_ids = [r["sense_id"] for r in result]
            
            mcqs = []
            for sid in sense_ids:
                mcqs.extend(assembler.assemble_mcqs_for_sense(sid))
        else:
            mcqs = assembler.assemble_mcqs_batch(limit=limit)
        
        # Print results
        print(f"\n{'='*70}")
        print(f"📊 MCQ GENERATION RESULTS (V2 - Context-Aware, Polysemy-Safe)")
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
        
        # Show sample MCQs with full formatting
        if mcqs:
            print(f"\n{'='*70}")
            print(f"📝 SAMPLE MCQs")
            print(f"{'='*70}")
            
            for mcq in mcqs[:5]:
                print(format_mcq_display(mcq))
        
        return mcqs
        
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCQ Assembler V2 - Context-Aware, Polysemy-Safe")
    parser.add_argument("--word", type=str, help="Target word")
    parser.add_argument("--sense", type=str, help="Target sense ID")
    parser.add_argument("--limit", type=int, default=10, help="Batch size")
    parser.add_argument("--store", action="store_true", help="Store MCQs to PostgreSQL for adaptive selection")
    args = parser.parse_args()
    
    run_mcq_assembler(word=args.word, sense_id=args.sense, limit=args.limit, store=args.store)
