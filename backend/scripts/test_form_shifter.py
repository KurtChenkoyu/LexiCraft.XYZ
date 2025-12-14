#!/usr/bin/env python3
"""
Test Script for FORM SHIFTER MCQ Type

Tests the new FORM SHIFTER MCQ type on 10 senses to see quality.

Usage:
    python3 backend/scripts/test_form_shifter.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.mcq_assembler import MCQAssembler, MCQType, MCQOption, MCQ, format_mcq_display
from src.services.vocabulary_store import vocabulary_store
import random


def _pos_to_chinese(pos: str) -> str:
    """Convert POS tag to Chinese."""
    pos_map = {
        'n': '名詞',
        'v': '動詞',
        'a': '形容詞',
        'r': '副詞',
        's': '形容詞'
    }
    return pos_map.get(pos.lower(), pos)


def find_word_family(word: str, pos: str, vocab_store, exclude_sense_id: str = None):
    """Find words that share the same root (morphological family)."""
    word_lower = word.lower()
    family = []
    
    # Search for words starting with the same root (4+ chars)
    # This finds morphological variants like: decide -> decision, decisive
    root = word_lower[:4] if len(word_lower) >= 4 else word_lower
    
    # Normalize POS for comparison (a and s are both adjectives)
    def normalize_pos(p):
        if p in ('a', 's'):
            return 'adj'
        return p.lower()
    
    target_pos_norm = normalize_pos(pos)
    
    for sense_id, sense in vocab_store._senses.items():
        if sense_id == exclude_sense_id:
            continue
            
        sense_word = sense.get("word", "").lower()
        sense_pos = sense.get("pos", "")
        
        if not sense_pos:
            continue
        
        sense_pos_norm = normalize_pos(sense_pos)
        
        # Check if it shares the root and has different POS
        if (sense_word.startswith(root) and 
            sense_pos_norm != target_pos_norm and
            sense_word != word_lower):
            family.append({
                "word": sense.get("word"),
                "pos": sense_pos,
                "sense_id": sense_id,
                "definition_zh": sense.get("definition_zh", "")
            })
    
    return family[:5]  # Limit to 5


def create_form_shifter_mcq(assembler: MCQAssembler, sense_data: dict) -> MCQ | None:
    """
    Create FORM SHIFTER MCQ: Test word form (POS) selection.
    
    Logic:
    1. Target word has POS (e.g., "decision" = noun)
    2. Find word family members with DIFFERENT POS (e.g., "decide" = verb, "decisive" = adj)
    3. Use example sentence, replace target word with blank
    4. Options: target word + 3 word family members with different POS
    """
    target_word = sense_data["word"]
    target_pos = sense_data.get("pos")
    target_sense_id = sense_data["sense_id"]
    example_en = sense_data.get("example_en", "")
    
    if not example_en or not target_pos:
        return None
    
    # Strategy 1: Find word family (morphological variants)
    different_pos_words = find_word_family(
        target_word, 
        target_pos, 
        assembler.vocab,
        exclude_sense_id=target_sense_id
    )
    
    # Strategy 2: Fallback to related senses with different POS
    if len(different_pos_words) < 3:
        related_senses = assembler.vocab.get_related_senses(target_sense_id)
        
        # Normalize POS for comparison
        def normalize_pos(p):
            if p in ('a', 's'):
                return 'adj'
            return p.lower() if p else ''
        
        target_pos_norm = normalize_pos(target_pos)
        
        for rel in related_senses:
            rel_pos = rel.get("pos")
            rel_word = rel.get("word", "")
            if rel_pos and normalize_pos(rel_pos) != target_pos_norm and rel_word:
                different_pos_words.append({
                    "word": rel_word,
                    "pos": rel_pos,
                    "sense_id": rel.get("sense_id"),
                    "definition_zh": rel.get("definition_zh", "")
                })
    
    # Need at least 3 distractors with different POS
    if len(different_pos_words) < 3:
        return None  # Not enough variety
    
    # Create sentence with blank
    # Try to replace word in sentence (case-insensitive)
    blank_sentence = example_en
    word_lower = target_word.lower()
    
    # Try different case variations
    replaced = False
    for variant in [target_word, target_word.capitalize(), target_word.upper(), target_word.lower()]:
        if variant in blank_sentence:
            blank_sentence = blank_sentence.replace(variant, "______", 1)
            replaced = True
            break
    
    if not replaced:
        # Fallback: just add blank at end
        blank_sentence = f"{example_en} ______"
    
    # Build options
    options = [
        MCQOption(
            text=target_word, 
            is_correct=True, 
            source="target", 
            tier=0,
            pos=target_pos
        )
    ]
    
    # Add 3 different-POS distractors
    for distractor in different_pos_words[:3]:
        options.append(MCQOption(
            text=distractor["word"],
            is_correct=False,
            source="form_shifter",
            tier=5,
            pos=distractor["pos"],
            source_word=distractor["word"]
        ))
    
    random.shuffle(options)
    correct_index = next(i for i, opt in enumerate(options) if opt.is_correct)
    
    question = "Choose the correct form of the word to complete the sentence."
    
    pos_chinese = _pos_to_chinese(target_pos)
    explanation = f'正確答案是「{target_word}」。在這個句子中需要{pos_chinese}形式。'
    
    return MCQ(
        sense_id=target_sense_id,
        word=target_word,
        mcq_type=MCQType.MEANING,  # Use MEANING as placeholder for now
        question=question,
        context=blank_sentence,
        options=options,
        correct_index=correct_index,
        explanation=explanation,
        metadata={
            "form_shifter": True,
            "target_pos": target_pos,
            "distractor_pos": [d["pos"] for d in different_pos_words[:3]]
        }
    )


def test_form_shifter_on_10_senses():
    """Test FORM SHIFTER MCQ generation on 10 senses."""
    print("\n" + "="*70)
    print("🧱 TESTING FORM SHIFTER MCQ TYPE")
    print("="*70)
    
    if not vocabulary_store.is_loaded:
        print("❌ VocabularyStore not loaded. Run enrich_vocabulary_v2.py first.")
        return
    
    print(f"✅ Using VocabularyStore V{vocabulary_store.version}")
    
    assembler = MCQAssembler()
    
    # Get all senses
    all_senses = list(vocabulary_store._senses.values())
    
    # Filter for senses with:
    # 1. example_en
    # 2. pos
    # 3. related connections
    candidates = []
    for sense in all_senses:
        if (sense.get("example_en") and 
            sense.get("pos") and 
            sense.get("connections", {}).get("related")):
            candidates.append(sense)
    
    print(f"\n📊 Found {len(candidates)} candidate senses (with example_en, pos, and related connections)")
    
    # Test on first 10 that can generate FORM SHIFTER MCQs
    tested = 0
    successful = 0
    
    for sense in candidates:
        if tested >= 10:
            break
        
        sense_id = sense.get("id")
        if not sense_id:
            continue
        
        # Build sense_data format
        sense_data = {
            "word": sense.get("word", ""),
            "pos": sense.get("pos"),
            "sense_id": sense_id,
            "example_en": sense.get("example_en", ""),
            "definition_zh": sense.get("definition_zh", "")
        }
        
        # Try to create FORM SHIFTER MCQ
        mcq = create_form_shifter_mcq(assembler, sense_data)
        
        if mcq:
            successful += 1
            print(f"\n{'='*70}")
            print(f"✅ FORM SHIFTER MCQ #{successful} - {sense_id}")
            print(f"{'='*70}")
            print(f"Word: {mcq.word} (POS: {mcq.options[0].pos})")
            print(f"Question: {mcq.question}")
            print(f"Context: {mcq.context}")
            print(f"\nOptions:")
            for i, opt in enumerate(mcq.options):
                marker = "✅" if opt.is_correct else "  "
                pos_info = f" [{opt.pos}]" if opt.pos else ""
                print(f"  {marker} {chr(65+i)}) {opt.text}{pos_info}")
            print(f"\nExplanation: {mcq.explanation}")
            print(f"Distractor POS: {mcq.metadata.get('distractor_pos', [])}")
        else:
            # Show why it failed
            related_senses = assembler.vocab.get_related_senses(sense_id)
            target_pos = sense.get("pos")
            different_pos_count = sum(1 for rel in related_senses 
                                     if rel.get("pos") and rel.get("pos") != target_pos)
            print(f"\n⚠️  Skipped {sense_id}: Only {different_pos_count} related words with different POS (need 3+)")
        
        tested += 1
    
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY")
    print(f"{'='*70}")
    print(f"Tested: {tested} senses")
    print(f"Successful: {successful} FORM SHIFTER MCQs generated")
    print(f"Success rate: {successful/tested*100:.1f}%" if tested > 0 else "N/A")
    
    return successful


if __name__ == "__main__":
    test_form_shifter_on_10_senses()

