"""
Pipeline Step 4: Content Generation Level 2 - Multi-Layer Example Generation Agent

Generates 4 layers of example sentences for enriched senses:
1. Contextual Support (5-8 examples) - Enhanced for MCQ efficacy
2. Opposite Examples (2-3 per relationship from OPPOSITE_TO relationships)
3. Similar Examples (2-3 per relationship from RELATED_TO relationships)
4. Confused Examples (2-3 per relationship from CONFUSED_WITH relationships)

Usage:
    python3 -m src.agent_stage2 --word bank  # Enrich specific word
    python3 -m src.agent_stage2 --limit 10   # Enrich 10 pending senses
    python3 -m src.agent_stage2 --mock       # Simulate Level 2 content generation
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
from typing import List, Dict, Optional
from pathlib import Path
from src.database.neo4j_connection import Neo4jConnection
from src.models.learning_point import MultiLayerExamples, ExamplePair

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("⚠️ WARNING: GOOGLE_API_KEY not found. Agent will fail if run without --mock.")


def get_mock_multilayer_examples(sense_id: str, word: str, usage_ratio: float = 0.3) -> MultiLayerExamples:
    """Returns hardcoded data for testing without API key. Tiered by usage frequency."""
    print(f"⚠️ Using MOCK data for sense '{sense_id}'...")
    
    # Determine example count based on usage tier
    min_ex, max_ex, tier = get_tiered_example_count(usage_ratio)
    num_examples = (min_ex + max_ex) // 2  # Use middle of range
    
    # Generate tiered contextual examples for MCQ efficacy
    contextual_examples = [
            ExamplePair(
            example_en=f"This is a mock contextual example {i} for {word}.",
            example_zh_translation=f"這是 {word} 的測試例句 {i} (字面翻譯)。",
            example_zh_explanation=f"這是 {word} 的測試例句 {i} (說明)。"
        )
        for i in range(1, num_examples + 1)
    ]
    
    # Generate 2-3 examples per relationship type
    opposite_examples = [
            ExamplePair(
            example_en=f"This shows the opposite of {word} - example {i}.",
            example_zh_translation=f"這顯示了 {word} 的反義 {i} (字面翻譯)。",
            example_zh_explanation=f"這顯示了 {word} 的反義 {i} (說明)。",
                relationship_word="opposite_word",
                relationship_type="opposite"
            )
        for i in range(1, 3)  # 2 opposite examples
    ]
    
    similar_examples = [
            ExamplePair(
            example_en=f"This shows a similar word to {word} - example {i}.",
            example_zh_translation=f"這顯示了與 {word} 相似的詞 {i} (字面翻譯)。",
            example_zh_explanation=f"這顯示了與 {word} 相似的詞 {i} (說明)。",
                relationship_word="similar_word",
                relationship_type="similar"
            )
        for i in range(1, 3)  # 2 similar examples
    ]
    
    confused_examples = [
            ExamplePair(
            example_en=f"This clarifies confusion with {word} - example {i}.",
            example_zh_translation=f"這澄清了與 {word} 的混淆 {i} (字面翻譯)。",
            example_zh_explanation=f"這澄清了與 {word} 的混淆 {i} (說明)。",
                relationship_word="confused_word",
                relationship_type="confused"
            )
        for i in range(1, 3)  # 2 confused examples
    ]
    
    return MultiLayerExamples(
        sense_id=sense_id,
        examples_contextual=contextual_examples,
        examples_opposite=opposite_examples,
        examples_similar=similar_examples,
        examples_confused=confused_examples
    )


def fetch_relationships(conn: Neo4jConnection, word: str, sense_id: Optional[str] = None) -> Dict[str, List]:
    """
    Fetch relationship words WITH their definitions for better context.
    
    Now uses sense-specific relationships with quality filtering for better accuracy.
    Falls back to word-level relationships if sense-specific not available.
    
    Args:
        word: The word to find relationships for
        sense_id: Optional specific sense ID. If not provided, uses most common sense.
    
    Returns:
        {
            "opposites": [
                {"word": "withdraw", "definition_en": "...", "definition_zh": "..."},
                ...
            ],
            "similar": [...],
            "confused": [...]
        }
    """
    relationships = {
        "opposites": [],
        "similar": [],
        "confused": []
    }
    
    with conn.get_session() as session:
        # Fetch opposites WITH definitions from their primary senses
        # (OPPOSITE_TO is word-level, so this stays the same)
        result = session.run("""
            MATCH (w:Word {name: $word})-[:OPPOSITE_TO]->(opp:Word)
            MATCH (opp)-[:HAS_SENSE]->(s:Sense)
            WHERE s.definition_en IS NOT NULL
            WITH opp, s
            ORDER BY 
                CASE WHEN s.id STARTS WITH toLower(opp.name) THEN 1 ELSE 2 END,
                COALESCE(s.usage_ratio, 1.0) DESC
            RETURN DISTINCT opp.name as word,
                   s.definition_en as definition_en,
                   s.definition_zh as definition_zh
            LIMIT 3
        """, word=word)
        
        for record in result:
            relationships["opposites"].append({
                "word": record["word"],
                "definition_en": record.get("definition_en", ""),
                "definition_zh": record.get("definition_zh", "")
            })
        
        # Fetch similar/synonyms using NEW sense-specific relationships with quality filtering
        # Prioritize: SYNONYM_OF > CLOSE_SYNONYM > RELATED_TO
        # Filter by quality score >= 0.6
        if sense_id:
            # Use specific sense
            result = session.run("""
                MATCH (source_sense:Sense {id: $sense_id})
                MATCH (source_sense)-[r:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO]->(target_sense:Sense)
                WHERE r.quality_score >= 0.6
                MATCH (target_sense)<-[:HAS_SENSE]-(target_word:Word)
                WHERE target_sense.definition_en IS NOT NULL
                WITH target_word, target_sense, r,
                     CASE type(r)
                         WHEN 'SYNONYM_OF' THEN 1
                         WHEN 'CLOSE_SYNONYM' THEN 2
                         WHEN 'RELATED_TO' THEN 3
                         ELSE 4
                     END as priority
                ORDER BY priority, r.quality_score DESC, target_sense.usage_ratio DESC
                RETURN DISTINCT target_word.name as word,
                       target_sense.definition_en as definition_en,
                       target_sense.definition_zh as definition_zh,
                       type(r) as relationship_type,
                       r.quality_score as quality_score
                LIMIT 5
            """, sense_id=sense_id)
        else:
            # Use most common sense of the word
            result = session.run("""
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(source_sense:Sense)
                WITH source_sense
                ORDER BY COALESCE(source_sense.usage_ratio, 1.0) DESC
                LIMIT 1
                MATCH (source_sense)-[r:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO]->(target_sense:Sense)
                WHERE r.quality_score >= 0.6
                MATCH (target_sense)<-[:HAS_SENSE]-(target_word:Word)
                WHERE target_sense.definition_en IS NOT NULL
                WITH target_word, target_sense, r,
                     CASE type(r)
                         WHEN 'SYNONYM_OF' THEN 1
                         WHEN 'CLOSE_SYNONYM' THEN 2
                         WHEN 'RELATED_TO' THEN 3
                         ELSE 4
                     END as priority
                ORDER BY priority, r.quality_score DESC, target_sense.usage_ratio DESC
                RETURN DISTINCT target_word.name as word,
                       target_sense.definition_en as definition_en,
                       target_sense.definition_zh as definition_zh,
                       type(r) as relationship_type,
                       r.quality_score as quality_score
                LIMIT 5
            """, word=word)
        
        for record in result:
            relationships["similar"].append({
                "word": record["word"],
                "definition_en": record.get("definition_en", ""),
                "definition_zh": record.get("definition_zh", ""),
                "relationship_type": record.get("relationship_type", "RELATED_TO"),
                "quality_score": record.get("quality_score", 0.0)
            })
        
        # If no sense-specific relationships found, fall back to word-level (backward compatibility)
        if not relationships["similar"]:
            result = session.run("""
                MATCH (w:Word {name: $word})-[r:RELATED_TO]->(sim:Word)
                WHERE r.avg_quality >= 0.6
                MATCH (sim)-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_en IS NOT NULL
                WITH sim, s, r
                ORDER BY 
                    r.avg_quality DESC,
                    CASE WHEN s.id STARTS WITH toLower(sim.name) THEN 1 ELSE 2 END,
                    COALESCE(s.usage_ratio, 1.0) DESC
                RETURN DISTINCT sim.name as word,
                       s.definition_en as definition_en,
                       s.definition_zh as definition_zh,
                       r.avg_quality as quality_score
                LIMIT 3
            """, word=word)
            
            for record in result:
                relationships["similar"].append({
                    "word": record["word"],
                    "definition_en": record.get("definition_en", ""),
                    "definition_zh": record.get("definition_zh", ""),
                    "relationship_type": "RELATED_TO",
                    "quality_score": record.get("quality_score", 0.0)
                })
        
        # Fetch confused words WITH definitions and reasons
        # (CONFUSED_WITH is word-level, so this stays the same)
        result = session.run("""
            MATCH (w:Word {name: $word})-[r:CONFUSED_WITH]->(conf:Word)
            MATCH (conf)-[:HAS_SENSE]->(s:Sense)
            WHERE s.definition_en IS NOT NULL
            WITH conf, r, s
            ORDER BY 
                CASE WHEN s.id STARTS WITH toLower(conf.name) THEN 1 ELSE 2 END,
                COALESCE(s.usage_ratio, 1.0) DESC
            RETURN DISTINCT conf.name as word, 
                   r.reason as reason,
                   s.definition_en as definition_en,
                   s.definition_zh as definition_zh
            LIMIT 3
        """, word=word)
        
        for record in result:
            relationships["confused"].append({
                "word": record["word"],
                "reason": record.get("reason", "Unknown"),
                "definition_en": record.get("definition_en", ""),
                "definition_zh": record.get("definition_zh", "")
            })
    
    return relationships


def detect_cefr_level(
    cefr: Optional[str],
    moe_level: Optional[int],
    frequency_rank: Optional[int]
) -> str:
    """
    Detect CEFR level from available data.
    Priority: cefr > moe_level > frequency_rank > default
    """
    if cefr:
        return cefr
    
    if moe_level:
        moe_to_cefr = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}
        return moe_to_cefr.get(moe_level, "B1/B2")
    
    if frequency_rank:
        if frequency_rank < 500:
            return "A1/A2"
        elif frequency_rank < 2000:
            return "B1/B2"
        else:
            return "C1/C2"
    
    return "B1/B2"  # Default


def get_tiered_example_count(
    usage_ratio: Optional[float] = None,
    frequency_rank: Optional[int] = None,
    sense_id: Optional[str] = None,
    is_only_sense: bool = False
) -> tuple:
    """
    Determine contextual example count based on sense importance.
    
    Uses multiple heuristics since usage_ratio is often unavailable:
    1. usage_ratio (if available) - most accurate
    2. is_only_sense - single-sense words are primary by default
    3. sense_id ending (e.g., .01 vs .05) - lower = more common in WordNet
    4. frequency_rank - common words need more examples
    
    Primary senses: 15-20 examples - learners encounter constantly
    Common senses: 8-12 examples - regular exposure  
    Rare senses: 5-8 examples - occasional use
    
    Returns:
        (min_examples, max_examples, tier_name)
    """
    # Method 1: Use usage_ratio if available
    if usage_ratio is not None:
        if usage_ratio > 0.5:
            return (15, 20, "primary")
        elif usage_ratio > 0.2:
            return (8, 12, "common")
        else:
            return (5, 8, "rare")
    
    # Method 2: Single-sense words are primary
    if is_only_sense:
        # For common words (top 2000), give more examples
        if frequency_rank is not None and frequency_rank < 2000:
            return (15, 20, "primary")
        else:
            return (8, 12, "common")
    
    # Method 3: Use sense number from sense_id (e.g., "bank.n.01" -> 1)
    if sense_id:
        try:
            # Extract sense number from ID like "bank.n.01"
            sense_num = int(sense_id.split('.')[-1])
            if sense_num == 1:
                # First sense is typically most common
                if frequency_rank is not None and frequency_rank < 1000:
                    return (15, 20, "primary")
                elif frequency_rank is not None and frequency_rank < 3000:
                    return (8, 12, "common")
            elif sense_num <= 3:
                return (8, 12, "common")
            else:
                return (5, 8, "rare")
        except (ValueError, IndexError):
            pass
    
    # Method 4: Default based on frequency rank only
    if frequency_rank is not None:
        if frequency_rank < 500:
            return (12, 15, "high_freq")
        elif frequency_rank < 2000:
            return (8, 12, "common")
        else:
            return (5, 8, "rare")
    
    # Default fallback
    return (5, 8, "unknown")


def get_multilayer_examples(
    sense_id: str,
    word: str,
    definition_en: str,
    definition_zh: str,
    relationships: Dict[str, List],
    # Enhanced context parameters
    part_of_speech: Optional[str] = None,
    existing_example_en: Optional[str] = None,
    existing_example_zh: Optional[str] = None,
    usage_ratio: Optional[float] = None,
    frequency_rank: Optional[int] = None,
    moe_level: Optional[int] = None,
    cefr: Optional[str] = None,
    is_moe_word: bool = False,
    phrases: List[str] = None,
    is_only_sense: bool = False,
    mock: bool = False
) -> Optional[MultiLayerExamples]:
    """
    Calls Gemini to generate multi-layer examples for a sense.
    Uses enhanced prompt builder with full data structure utilization.
    Tiered example counts based on sense importance (usage_ratio, frequency_rank, sense position).
    """
    if mock:
        return get_mock_multilayer_examples(sense_id, word, usage_ratio or 0.3)
    
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing.")
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Detect CEFR level
    target_level = detect_cefr_level(cefr, moe_level, frequency_rank)
    
    # Determine tiered example count based on multiple heuristics
    min_examples, max_examples, usage_tier = get_tiered_example_count(
        usage_ratio=usage_ratio,
        frequency_rank=frequency_rank,
        sense_id=sense_id,
        is_only_sense=is_only_sense
    )
    
    # Determine which layers need API calls (hybrid approach)
    has_opposites = bool(relationships["opposites"])
    has_similar = bool(relationships["similar"])
    has_confused = bool(relationships["confused"])
    
    # Build relationship context strings WITH definitions
    if has_opposites:
        opposites_list = []
        for opp in relationships["opposites"]:
            opp_str = f'  * "{opp["word"]}" (definition: "{opp.get("definition_en", "")}")'
            opposites_list.append(opp_str)
        opposites_str = "\n".join(opposites_list)
    else:
        opposites_str = "None"
    
    if has_similar:
        similar_list = []
        for sim in relationships["similar"]:
            sim_str = f'  * "{sim["word"]}" (definition: "{sim.get("definition_en", "")}")'
            similar_list.append(sim_str)
        similar_str = "\n".join(similar_list)
    else:
        similar_str = "None"
    
    if has_confused:
        confused_list = []
        for conf in relationships["confused"]:
            conf_str = f'  * "{conf["word"]}" (definition: "{conf.get("definition_en", "")}", reason: {conf.get("reason", "Unknown")})'
            confused_list.append(conf_str)
        confused_str = "\n".join(confused_list)
    else:
        confused_str = "None"
    
    # Build context sections
    context_sections = [f"Target Sense: {sense_id}", f'Word: "{word}"']
    
    if part_of_speech:
        context_sections.append(f"Part of Speech: {part_of_speech}")
    
    if cefr:
        context_sections.append(f"CEFR Level: {cefr}")
    elif target_level:
        context_sections.append(f"CEFR Level: {target_level} (inferred)")
    
    if moe_level:
        context_sections.append(f"Taiwan MOE Level: {moe_level}")
        if is_moe_word:
            context_sections.append("⚠️ This word appears in Taiwan MOE exam vocabulary")
    
    if frequency_rank:
        context_sections.append(f"Frequency Rank: {frequency_rank} (lower = more common)")
    
    if usage_ratio:
        if usage_ratio > 0.7:
            context_sections.append(f"⚠️ This is the PRIMARY sense (usage ratio: {usage_ratio:.1%})")
        elif usage_ratio < 0.3:
            context_sections.append(f"Note: This is a LESS COMMON sense (usage ratio: {usage_ratio:.1%})")
    
    if existing_example_en:
        context_sections.append(f"\nExisting Example (from Level 1):")
        context_sections.append(f"  EN: {existing_example_en}")
        if existing_example_zh:
            context_sections.append(f"  ZH: {existing_example_zh}")
        context_sections.append("  → Generate NEW examples that are DIFFERENT from this one")
    
    if phrases:
        context_sections.append(f"\nCommon Phrases for this sense:")
        context_sections.append(f"  {', '.join(phrases[:5])}")
        context_sections.append("  → Consider using these phrases in examples if natural")
    
    context_str = "\n".join(context_sections)
    
    # Build prompt sections conditionally (hybrid approach)
    prompt_sections = []
    
    # Base instructions
    base_instructions = f"""
You are a helpful language learning guide helping Taiwan EFL learners understand English expressions. 
Your role is to help learners CONNECT with the language naturally, not to teach or correct them.
Focus on creating pathways that help learners see how English expressions work.

IMPORTANT: Vary your explanation style. Do NOT default to "想像一下" (imagine) for every explanation.
Use diverse approaches: direct descriptions, natural metaphors, examples, or comparisons.
Only use "想像一下" when it genuinely helps create a clear connection pathway.

{context_str}

Definition (EN): {definition_en}
Definition (ZH): {definition_zh}

CRITICAL LANGUAGE REQUIREMENTS:
- Use SIMPLE, CLEAR English suitable for {target_level} level learners
- Keep sentences short (10-20 words maximum for {target_level})
- Use common, everyday words that {target_level} learners would know
- Avoid complex grammar structures beyond {target_level} level
- Make examples immediately understandable without explanation

CHINESE REQUIREMENTS (TWO VERSIONS NEEDED):
- For each English example, provide TWO Chinese versions:
  1. LITERAL TRANSLATION (word-for-word):
     * Shows how English constructs meaning
     * Helps learners see English sentence structure
     * Maps English words directly to Chinese
  
  2. EXPLANATION (identifies what the sentence REALLY means):
     * Actively find and explain nuances that might be easily missed when going from English to Chinese
     * Highlight cultural context, implied meanings, and idiomatic expressions
     * For idiomatic expressions OR words with non-literal meanings (e.g., "break" = opportunity, not just "to break something"): 
       Help learners CONNECT the literal meaning to the idiomatic/non-literal meaning
       - CRITICAL: ALWAYS start by showing the literal meaning FIRST, then show how it extends to idiomatic/non-literal
       - If the word has a non-literal meaning in this context (like "break" meaning opportunity), you MUST show the pathway
       - Create a natural CONNECTION and PATHWAY - show how the meaning flows from literal to idiomatic
       - Show the semantic pathway clearly: literal meaning → metaphor/evolution → idiomatic meaning
       - Structure: Start with literal → show metaphor/extension → arrive at idiomatic meaning
       - VARY your explanation style - do NOT default to "想像一下" for every explanation
       - Use diverse approaches:
         * Direct descriptions: "原本的意思是...，在這裡引申為..." (original meaning...extends to...)
         * Natural metaphors: "就像..." (like), "如同..." (as if) - embedded naturally in explanation
         * Examples: "例如..." (for example)
         * Comparisons: "可以想成..." (can think of it as)
         * Only use "想像一下" when it genuinely helps create a clear pathway
       - ALWAYS show literal meaning first, then show the connection pathway - don't jump straight to idiomatic
       - CRITICAL: NEVER start the explanation with disconnection statements like "不是指..." or "不是...而是" - these create disconnection
       - CRITICAL: NEVER use "字面上...但實際上" (literally...but actually) - this creates disconnection
       - NEVER create disconnection anywhere - idioms are EXTENSIONS, help learners see the connection pathway
       - CRITICAL: Do NOT add any disconnection statements (like "不是...而是", "不是指...而是指", "這裡的...不是指...而是指") at the START, MIDDLE, or END
       - Once you've shown the pathway, stop - do NOT add clarifying disconnection statements at the end
       - The explanation should ONLY show the connection pathway - no disconnection statements at all
       - Focus on helping learners CONNECT naturally, not teaching them - be a guide, not a teacher
       
       * EXAMPLE OF GOOD EXPLANATION (shows connection pathway):
         "原本你被困住，前面有一道牆擋著你 (literal break)。這道牆突然出現一個缺口 (metaphorical break)，讓你可以通過，繼續前進。所以「a break」就像是打破了阻礙你前進的困境，給你帶來一個新的開始和更好的機會 (idiomatic meaning)。"
         
         This shows: literal → metaphor → idiomatic (creates pathway, not disconnection)
       
       * EXAMPLE OF BAD EXPLANATION (creates disconnection - AVOID):
         "「break」在這裡不是指打破東西，而是指一個好機會。" ❌
         
         This creates disconnection ("不是...而是") instead of showing connection pathway
       
       * REQUIRED STRUCTURE FOR IDIOMATIC EXPRESSIONS:
         1. Start with literal meaning: "break" = 打破/中斷
         2. Show metaphor/extension: "就像打破阻礙..."
         3. Arrive at idiomatic: "所以引申為機會"
     * Explain subtle meanings that literal translation would lose
     * Use simple, everyday Chinese vocabulary that learners can understand
     * Use Traditional Chinese (Taiwan usage)
     * Help Taiwan EFL learners understand both the meaning AND what they might miss
"""
    
    additional_notes = []
    
    if is_moe_word and moe_level:
        additional_notes.append(f"- Pay special attention: This word is in Taiwan MOE exam vocabulary (Level {moe_level})")
    
    if usage_ratio and usage_ratio > 0.7:
        additional_notes.append(f"- This is the PRIMARY sense ({usage_ratio:.1%} usage) - make examples very clear")
    elif usage_ratio and usage_ratio < 0.3:
        additional_notes.append(f"- This is a less common sense ({usage_ratio:.1%} usage) - provide clear context")
    
    if additional_notes:
        base_instructions += "\n".join(additional_notes) + "\n"
    
    if part_of_speech:
        base_instructions += f"\nGRAMMAR NOTE: This is a {part_of_speech.upper()}. Examples must use correct {part_of_speech} grammar.\n"
    
    if existing_example_en:
        base_instructions += f"\nREFERENCE: You already have this example: \"{existing_example_en}\"\n"
        base_instructions += "  → Generate DIFFERENT examples that show other contexts/uses\n"
    
    base_instructions += "\nYour task is to generate example sentences organized into pedagogical layers:\n"
    
    prompt_sections.append(base_instructions)
    
    # Layer 1: Always included (REQUIRED) - Tiered by usage frequency for MCQ efficacy
    # Primary senses (>50% usage): 15-20 examples
    # Common senses (20-50% usage): 8-12 examples  
    # Rare senses (<20% usage): 5-8 examples
    usage_display = f"{usage_ratio:.1%}" if usage_ratio else "unknown"
    importance_note = "MORE" if usage_tier == "primary" else ("good" if usage_tier == "common" else "adequate")
    layer1_section = f"""
1. CONTEXTUAL SUPPORT (REQUIRED - {min_examples}-{max_examples} examples):
   - Provide {min_examples}-{max_examples} natural, modern example sentences that clearly illustrate this sense
   - This is a {usage_tier.upper()} sense (usage: {usage_display}), so we need {importance_note} examples for MCQ variety
   - Use SIMPLE English: short sentences, common words, clear structure
   - Show DIVERSE contexts/registers: formal, casual, written, spoken, school, work, daily life
   - Each example should solidify understanding of this specific sense
   - Examples must be immediately understandable to {{target_level}} learners
   - Avoid complex grammar or vocabulary beyond {{target_level}} level
   - Each example should be DISTINCT - avoid similar sentence structures or contexts
   - More examples = better MCQ variety for verification testing
"""
    
    if phrases:
        layer1_section += f"   - Consider using phrases like: {', '.join(phrases[:3])}\n"
    
    prompt_sections.append(layer1_section.format(target_level=target_level))
    
    # Layer 2: Only if opposites exist
    if has_opposites:
        layer2_section = f"""
2. OPPOSITE EXAMPLES:
{opposites_str}
   
   - For each antonym listed above, generate 2-3 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the antonym word in a natural sentence
     * Show clear contrast with the target sense
     * Highlight what aspect of the target sense is being contrasted
     * Make the distinction clear to help learners understand the difference
     * Keep language simple enough for {target_level} learners to understand immediately
     * Each example should show a DIFFERENT context or aspect of the contrast
   
   - Example structure:
     Target sense: "I deposited money at the bank." (simple, clear)
     Contrast 1: "He withdrew money from the bank." (shows opposite action: depositing vs withdrawing)
     Contrast 2: "She withdrew all her savings yesterday." (another context)
"""
        prompt_sections.append(layer2_section)
    
    # Layer 3: Only if similar exist
    if has_similar:
        layer3_section = f"""
3. SIMILAR EXAMPLES:
{similar_str}
   
   - For each synonym listed above, generate 2-3 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the synonym word in a natural sentence
     * Show subtle differences from the target sense
     * Help learners understand when to use this word vs. the synonym
     * Highlight the nuance between similar meanings
     * Keep language simple enough for {target_level} learners to understand immediately
     * Each example should demonstrate a DIFFERENT nuance or context
   
   - Example structure:
     Target sense: "I opened an account at the bank." (simple, clear)
     Similar 1: "I opened an account at the financial institution." (shows synonym, but "bank" is more common/casual)
     Similar 2: "The financial institution offers many services." (another context)
"""
        prompt_sections.append(layer3_section)
    
    # Layer 4: Only if confused exist
    if has_confused:
        layer4_section = f"""
4. CONFUSED EXAMPLES:
{confused_str}
   
   - For each confused word listed above, generate 2-3 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the confused word in a natural sentence
     * Clearly show the distinction from the target sense
     * Address the specific confusion reason (Sound/Spelling/L1/Usage)
     * Help Taiwan EFL learners avoid common errors
     * Keep language simple enough for {target_level} learners to understand immediately
     * Each example should clarify a DIFFERENT aspect of the confusion
   
   - Example structure:
     Target sense: "I need to deposit money at the bank." (simple, clear)
     Confused 1: "The river bank was flooded." (clarifies: financial bank vs river bank)
     Confused 2: "We sat on the bank of the river." (another context showing different meaning)
"""
        prompt_sections.append(layer4_section)
    
    # Common requirements
    common_requirements = f"""
CRITICAL REQUIREMENTS:
- All examples must use SIMPLE, CLEAR English suitable for {target_level} level learners
- Keep sentences short (10-20 words maximum)
- Use common, everyday vocabulary
- Avoid complex grammar structures, idioms, or advanced vocabulary
- All examples must be natural, modern English (not outdated)
- For each English example, provide TWO Chinese versions:
  1. Literal translation (word-for-word, shows English structure)
  2. Explanation that identifies what the sentence REALLY means, especially:
     * Nuances that might be easily missed when going from English to Chinese
     * Cultural context, implied meanings, idiomatic expressions
     * For idiomatic expressions OR words with non-literal meanings (e.g., "break" = opportunity, not just "to break something"): 
       Help learners CONNECT the literal meaning to the idiomatic/non-literal meaning
       - CRITICAL: ALWAYS start by showing the literal meaning of the WORD itself FIRST (e.g., "break" = 打破/中斷)
       - Then show how this literal meaning extends to the idiomatic/non-literal meaning
       - If the word has a non-literal meaning in this context (like "break" meaning opportunity), you MUST show the pathway
       - Create a natural CONNECTION and PATHWAY - show how the meaning flows from literal to idiomatic
       - Show the semantic pathway clearly: literal word meaning → metaphor/evolution → idiomatic meaning
       - Structure: Start with literal word meaning → show metaphor/extension → arrive at idiomatic meaning
       - EXAMPLE: For "break" = opportunity, show: "break" (打破/中斷) → breaks barriers/obstacles → opportunity
       - VARY your explanation style - do NOT default to "想像一下" for every explanation
       - Use diverse approaches: direct descriptions, natural metaphors (embedded), examples, comparisons
       - ALWAYS show literal meaning first, then show the connection pathway - don't jump straight to idiomatic
       - CRITICAL: NEVER start the explanation with disconnection statements like "不是指..." or "不是...而是" - these create disconnection
       - CRITICAL: NEVER use "字面上...但實際上" (literally...but actually) - this creates disconnection
       - NEVER create disconnection anywhere - idioms are EXTENSIONS, help learners see the connection pathway
       - CRITICAL: Do NOT add any disconnection statements (like "不是...而是", "不是指...而是指", "這裡的...不是指...而是指") at the START, MIDDLE, or END
       - Once you've shown the pathway, stop - do NOT add clarifying disconnection statements at the end
       - The explanation should ONLY show the connection pathway - no disconnection statements at all
     * Subtle differences that literal translation would lose
- Examples must clearly illustrate the target sense
- For Layers 2-4, the relationship words MUST appear in the examples
- Make examples immediately understandable without explanation

Return a strict JSON object matching this schema:
{{
    "sense_id": "{sense_id}",
    "examples_contextual": [
        {{
            "example_en": "...",
            "example_zh_translation": "...",
            "example_zh_explanation": "...",
            "context_label": "formal" | "casual" | "written" | "spoken" | null
        }},
        ...
    ],
"""
    
    # Add schema sections conditionally
    if has_opposites:
        common_requirements += """
    "examples_opposite": [
        {{
            "example_en": "...",
            "example_zh_translation": "...",
            "example_zh_explanation": "...",
            "relationship_word": "...",
            "relationship_type": "opposite"
        }},
        ...
    ],
"""
    
    if has_similar:
        common_requirements += """
    "examples_similar": [
        {{
            "example_en": "...",
            "example_zh_translation": "...",
            "example_zh_explanation": "...",
            "relationship_word": "...",
            "relationship_type": "similar"
        }},
        ...
    ],
"""
    
    if has_confused:
        common_requirements += """
    "examples_confused": [
        {{
            "example_en": "...",
            "example_zh_translation": "...",
            "example_zh_explanation": "...",
            "relationship_word": "...",
            "relationship_type": "confused"
        }},
        ...
    ],
"""
    
    common_requirements += f"""
}}

IMPORTANT: 
- Generate {min_examples}-{max_examples} contextual examples (Layer 1) - REQUIRED for MCQ efficacy
- This sense is {usage_tier.upper()} priority (usage: {usage_display}) - {'generate MORE examples!' if usage_tier == 'primary' else 'generate adequate examples'}
- Generate 2-3 examples per relationship word for Layers 2-4 ONLY if relationship words are provided (not "None")
- If a layer has no relationships, return empty array []
- All relationship words must appear in their respective examples
- Use SIMPLE English: short sentences, common words, clear structure
- All examples must be immediately understandable to {{target_level}} learners
- Each example should be DISTINCT - different contexts, different sentence structures
- More examples = better variety for multiple-choice verification testing
- For each English example, provide TWO Chinese versions:
  1. Literal translation (word-for-word, shows English structure)
  2. Explanation that identifies what the sentence REALLY means, especially nuances that might be easily missed when going from English to Chinese
"""
    
    prompt_sections.append(common_requirements)
    
    # Combine all sections
    prompt = "\n".join(prompt_sections)
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        response_text = response.text.strip()
        
        # Try to fix common JSON issues
        import re
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
        
        # Fix invalid Unicode escapes (common Gemini issue)
        # Replace invalid \uXXXX patterns with proper Unicode escapes or actual characters
        def fix_unicode_escape(match):
            try:
                # Try to decode the hex value
                hex_val = match.group(1)
                if len(hex_val) == 4:
                    code_point = int(hex_val, 16)
                    return chr(code_point)
                else:
                    # Invalid length, return as-is
                    return match.group(0)
            except (ValueError, OverflowError):
                # If we can't decode it, try to escape it properly
                return match.group(0)
        
        # Fix invalid \uXXXX escapes (where XXXX might be incomplete or invalid)
        # Pattern: \u followed by 1-4 hex digits
        response_text = re.sub(r'\\u([0-9a-fA-F]{1,4})', fix_unicode_escape, response_text)
        
        # Also handle cases where \u is followed by non-hex (replace with actual character if possible)
        # This handles cases like \u7684 where it should be a valid Unicode character
        try:
            # Try to decode the entire string as UTF-8 first
            response_text = response_text.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # If that fails, try a more conservative approach
            pass
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                # Apply same Unicode fixes
                json_text = re.sub(r'\\u([0-9a-fA-F]{1,4})', fix_unicode_escape, json_text)
                try:
                    data = json.loads(json_text)
                except json.JSONDecodeError:
                    # Last resort: try to manually fix common issues
                    # Replace any remaining invalid escapes with a placeholder
                    json_text = re.sub(r'\\u[0-9a-fA-F]{0,3}(?![0-9a-fA-F])', '?', json_text)
                    try:
                        data = json.loads(json_text)
                    except json.JSONDecodeError:
                        print(f"JSON Parse Error for {sense_id}: {json_err}")
                        print(f"Response: {response_text[:500]}")
                        return None
            else:
                print(f"JSON Parse Error for {sense_id}: {json_err}")
                print(f"Response: {response_text[:500]}")
                return None
        
        # Validate and convert to Pydantic model
        # Ensure missing layers are empty arrays (for hybrid approach)
        if not has_opposites and "examples_opposite" not in data:
            data["examples_opposite"] = []
        if not has_similar and "examples_similar" not in data:
            data["examples_similar"] = []
        if not has_confused and "examples_confused" not in data:
            data["examples_confused"] = []
        
        return MultiLayerExamples(**data)
        
    except Exception as e:
        print(f"Gemini API Error for {sense_id}: {e}")
        return None


def update_graph_stage2(conn: Neo4jConnection, examples: MultiLayerExamples):
    """
    Updates Sense node with Level 2 multi-layer examples.
    Stores examples as JSON strings (Neo4j doesn't support arrays of maps).
    """
    with conn.get_session() as session:
        # Convert ExamplePair objects to dicts, then to JSON strings
        # Filter out None values (Neo4j doesn't accept None in maps)
        contextual_list = [
            {k: v for k, v in {
                "example_en": ex.example_en,
                "example_zh_translation": ex.example_zh_translation,
                "example_zh_explanation": ex.example_zh_explanation,
                "context_label": ex.context_label
            }.items() if v is not None}
            for ex in examples.examples_contextual
        ]
        
        opposite_list = [
            {k: v for k, v in {
                "example_en": ex.example_en,
                "example_zh_translation": ex.example_zh_translation,
                "example_zh_explanation": ex.example_zh_explanation,
                "relationship_word": ex.relationship_word,
                "relationship_type": ex.relationship_type
            }.items() if v is not None}
            for ex in examples.examples_opposite
        ]
        
        similar_list = [
            {k: v for k, v in {
                "example_en": ex.example_en,
                "example_zh_translation": ex.example_zh_translation,
                "example_zh_explanation": ex.example_zh_explanation,
                "relationship_word": ex.relationship_word,
                "relationship_type": ex.relationship_type
            }.items() if v is not None}
            for ex in examples.examples_similar
        ]
        
        confused_list = [
            {k: v for k, v in {
                "example_en": ex.example_en,
                "example_zh_translation": ex.example_zh_translation,
                "example_zh_explanation": ex.example_zh_explanation,
                "relationship_word": ex.relationship_word,
                "relationship_type": ex.relationship_type
            }.items() if v is not None}
            for ex in examples.examples_confused
        ]
        
        # Store as JSON strings (Neo4j doesn't support arrays of maps)
        # Version 3 = Tiered prompt with 15-20/8-12/5-8 contextual examples (December 2025)
        query = """
        MATCH (s:Sense {id: $sense_id})
        SET s.examples_contextual = $contextual,
            s.examples_opposite = $opposite,
            s.examples_similar = $similar,
            s.examples_confused = $confused,
            s.stage2_enriched = true,
            s.stage2_version = 3,
            s.stage2_enriched_at = datetime()
        """
        
        session.run(
            query,
            sense_id=examples.sense_id,
            contextual=json.dumps(contextual_list, ensure_ascii=False),
            opposite=json.dumps(opposite_list, ensure_ascii=False),
            similar=json.dumps(similar_list, ensure_ascii=False),
            confused=json.dumps(confused_list, ensure_ascii=False)
        )


def load_checkpoint(checkpoint_file: str = "level2_checkpoint.json") -> Dict:
    """Load checkpoint data if it exists."""
    checkpoint_path = Path(checkpoint_file)
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, 'r') as f:
                return json.load(f)
        except:
            return {"processed_senses": [], "start_time": None, "total_processed": 0}
    return {"processed_senses": [], "start_time": None, "total_processed": 0}


def save_checkpoint(checkpoint_file: str, processed_senses: List[str], total_processed: int, start_time: float):
    """Save checkpoint data."""
    checkpoint_path = Path(checkpoint_file)
    checkpoint_data = {
        "processed_senses": processed_senses[-1000:],  # Keep last 1000 for resume
        "total_processed": total_processed,
        "start_time": start_time,
        "last_updated": time.time()
    }
    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)


def load_vocabulary_metadata() -> Dict[str, Dict]:
    """
    Load vocabulary.json to get frequency_rank and other metadata not in Neo4j.
    Returns dict of sense_id -> {frequency_rank, usage_ratio, is_only_sense, ...}
    """
    vocab_path = Path(__file__).parent.parent / "data" / "vocabulary.json"
    if not vocab_path.exists():
        print(f"⚠️ vocabulary.json not found at {vocab_path}, tier detection will use fallbacks")
        return {}
    
    try:
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        
        # V3 format has senses nested under "senses" key
        senses_data = vocab_data.get("senses", {})
        if not senses_data:
            print(f"⚠️ No senses found in vocabulary.json")
            return {}
        
        # Count senses per word to identify single-sense words
        from collections import Counter
        word_sense_counts = Counter(s.get("word") for s in senses_data.values())
        
        # Extract just the metadata we need
        metadata = {}
        for sense_id, sense in senses_data.items():
            word = sense.get("word", "")
            metadata[sense_id] = {
                "frequency_rank": sense.get("frequency_rank"),
                "usage_ratio": sense.get("usage_ratio"),
                "is_only_sense": word_sense_counts.get(word, 0) == 1,
            }
        return metadata
    except Exception as e:
        print(f"⚠️ Error loading vocabulary.json: {e}")
        import traceback
        traceback.print_exc()
        return {}


def run_stage2_agent(
    conn: Neo4jConnection,
    target_word: str = None,
    limit: Optional[int] = None,
    mock: bool = False,
    checkpoint_file: str = "level2_checkpoint.json",
    resume: bool = True,
    force: bool = False
):
    """
    Run Content Level 2 generation agent with checkpoint/resume support.
    
    Args:
        conn: Neo4j connection
        target_word: Specific word to process (optional)
        limit: Maximum number of senses to process (None = all)
        mock: Use mock data instead of API
        checkpoint_file: Path to checkpoint file
        resume: Whether to resume from checkpoint
        force: Force re-enrichment of already enriched senses (for prompt upgrades)
    """
    print("🎯 Starting Content Level 2 Multi-Layer Example Generation Agent...")
    if force:
        print("   ⚠️ FORCE MODE: Will re-enrich already enriched senses")
    
    # Load vocabulary metadata for tiered example counts
    vocab_metadata = load_vocabulary_metadata()
    if vocab_metadata:
        print(f"📚 Loaded vocabulary metadata for {len(vocab_metadata)} senses")
    
    # Load checkpoint if resuming
    checkpoint = load_checkpoint(checkpoint_file) if resume else {"processed_senses": [], "total_processed": 0}
    processed_senses = set(checkpoint.get("processed_senses", []))
    total_processed = checkpoint.get("total_processed", 0)
    start_time = checkpoint.get("start_time") or time.time()
    
    if resume and processed_senses:
        print(f"📋 Resuming from checkpoint: {len(processed_senses)} senses already processed")
        print(f"   Total processed so far: {total_processed}")
    
    with conn.get_session() as session:
        # 1. Fetch Candidates (Senses with Level 1 but not Level 2, or all if force=True)
        # Enhanced: Fetch all available properties
        # Force mode: Include already enriched senses (for prompt upgrades)
        stage2_filter = "" if force else "AND (s.stage2_enriched IS NULL OR s.stage2_enriched = false)"
        
        if target_word:
            result = session.run(f"""
                MATCH (w:Word {{name: $word}})-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true 
                  {stage2_filter}
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
            # Build query with optional limit
            query = f"""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true 
                  {stage2_filter}
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
        print(f"Found {len(tasks)} senses to enrich with multi-layer examples.")
        
        if not tasks:
            print("✅ No senses need Level 2 content generation.")
            return
        
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
        
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for idx, record in enumerate(tasks, 1):
            word = record["word"]
            sense_id = record["sense_id"]
            definition_en = record.get("definition_en", "")
            definition_zh = record.get("definition_zh", "")
            
            # Enhanced: Extract all available properties
            part_of_speech = record.get("part_of_speech")
            existing_example_en = record.get("existing_example_en")
            existing_example_zh = record.get("existing_example_zh")
            usage_ratio = record.get("usage_ratio")
            frequency_rank = record.get("frequency_rank")
            moe_level = record.get("moe_level")
            cefr = record.get("cefr")
            is_moe_word = record.get("is_moe_word", False)
            phrases = record.get("phrases") or []
            
            # Supplement with vocabulary.json metadata (Neo4j often missing frequency_rank)
            is_only_sense = False
            if sense_id in vocab_metadata:
                vocab_meta = vocab_metadata[sense_id]
                if frequency_rank is None:
                    frequency_rank = vocab_meta.get("frequency_rank")
                if usage_ratio is None:
                    usage_ratio = vocab_meta.get("usage_ratio")
                is_only_sense = vocab_meta.get("is_only_sense", False)
            
            # Progress indicator
            progress_pct = (idx / total_tasks * 100) if total_tasks > 0 else 0
            print(f"\n[{idx}/{total_tasks} ({progress_pct:.1f}%)] Enriching sense '{sense_id}' (word: '{word}')...")
            
            # Show tier info
            min_ex, max_ex, tier = get_tiered_example_count(
                usage_ratio=usage_ratio,
                frequency_rank=frequency_rank,
                sense_id=sense_id,
                is_only_sense=is_only_sense
            )
            tier_info = f"  📊 Tier: {tier.upper()} ({min_ex}-{max_ex} examples)"
            if frequency_rank:
                tier_info += f", rank={frequency_rank}"
            if is_only_sense:
                tier_info += ", single-sense word"
            print(tier_info)
            
            if cefr:
                print(f"  CEFR Level: {cefr}")
            if is_moe_word:
                print(f"  ⚠️ MOE exam vocabulary (Level {moe_level})")
            
            try:
                # Fetch relationships (with definitions) - now uses sense-specific relationships
                relationships = fetch_relationships(conn, word, sense_id=sense_id)
                print(f"  Found: {len(relationships['opposites'])} opposites, "
                      f"{len(relationships['similar'])} similar, "
                      f"{len(relationships['confused'])} confused words")
                
                # Generate multi-layer examples with enhanced context + tiered counts
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
                    is_only_sense=is_only_sense,
                    mock=mock
                )
                
                if examples:
                    # Update graph
                    update_graph_stage2(conn, examples)
                    success_count += 1
                    processed_senses.add(sense_id)
                    total_processed += 1
                    processed_count += 1
                    
                    print(f"  ✅ Enriched with {len(examples.examples_contextual)} contextual, "
                          f"{len(examples.examples_opposite)} opposite, "
                          f"{len(examples.examples_similar)} similar, "
                          f"{len(examples.examples_confused)} confused examples")
                    
                    # Save checkpoint every 10 successes
                    if processed_count % 10 == 0:
                        save_checkpoint(checkpoint_file, list(processed_senses), total_processed, start_time)
                        elapsed = time.time() - start_time
                        rate = total_processed / elapsed if elapsed > 0 else 0
                        remaining = total_tasks - idx
                        eta_seconds = remaining / rate if rate > 0 else 0
                        print(f"  💾 Checkpoint saved. Rate: {rate:.2f} senses/sec, ETA: {eta_seconds/60:.1f} min")
                else:
                    error_count += 1
                    print(f"  ⚠️ No examples generated for '{sense_id}'")
                    
            except Exception as e:
                error_count += 1
                print(f"  ❌ Failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Final checkpoint save
        save_checkpoint(checkpoint_file, list(processed_senses), total_processed, start_time)
        
        # Summary
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ Batch Complete!")
        print(f"   Processed: {success_count} successful, {error_count} errors")
        print(f"   Total processed: {total_processed}")
        print(f"   Time elapsed: {elapsed/60:.1f} minutes")
        if success_count > 0:
            print(f"   Average rate: {success_count/elapsed*60:.1f} senses/minute")
        print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Level 2: Multi-Layer Example Generation")
    parser.add_argument("--word", type=str, help="Target word to enrich")
    parser.add_argument("--limit", type=int, default=None, help="Batch size (None = all remaining)")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no API key)")
    parser.add_argument("--checkpoint", type=str, default="level2_checkpoint.json", help="Checkpoint file path")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from checkpoint")
    parser.add_argument("--force", action="store_true", help="Force re-enrichment of already enriched senses (for upgraded prompts)")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            run_stage2_agent(
                conn, 
                target_word=args.word, 
                limit=args.limit, 
                mock=args.mock,
                checkpoint_file=args.checkpoint,
                resume=not args.no_resume,
                force=args.force
            )
    finally:
        conn.close()

