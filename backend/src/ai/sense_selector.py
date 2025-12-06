"""
AI Sense Selector

Uses Gemini to intelligently select the most useful word senses
from WordNet, avoiding academic/obscure meanings and prioritizing
senses relevant to B1/B2 Taiwan EFL learners.

Usage:
    from src.ai.sense_selector import select_senses
    
    senses = select_senses("drop", all_wordnet_senses, max_senses=2)
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .base import BaseAIModule, LLMConfig, get_default_config


@dataclass
class SelectedSense:
    """A selected sense from WordNet."""
    sense_id: str
    pos: str
    definition: str
    reason: str
    priority: int  # 1 = highest priority


class SenseSelector(BaseAIModule):
    """
    Selects the most useful WordNet senses for a word.
    
    Uses AI to filter out:
    - Academic/scientific senses (e.g., "quark color property")
    - Archaic/obsolete meanings
    - Over-specific technical terms
    - Nearly identical duplicate senses
    
    And prioritize:
    - Common everyday meanings
    - Multiple POS if commonly used (verb AND noun)
    - Senses relevant to Taiwan students
    """
    
    def get_prompt_template(self) -> str:
        return """You are helping build a vocabulary app for Taiwan B1/B2 English students.

Word: {word}
Frequency Rank: {frequency_rank} (lower = more common)
CEFR Level: {cefr}

All WordNet senses for "{word}":
{senses_json}

YOUR TASK: Select the {max_senses} MOST USEFUL senses for B1/B2 learners.

SELECTION CRITERIA:
1. PRIORITIZE daily usage over academic/technical meanings
   - ✅ "break" = pause/rest (common)
   - ❌ "break" = fracture of continuity in crystallography (academic)

2. INCLUDE different POS if commonly used
   - If "{word}" is commonly both verb AND noun, select one of each
   - Don't select 3 noun senses if verb is common too

3. AVOID these sense types:
   - Scientific/academic terminology
   - Archaic or obsolete meanings
   - Highly specialized professional jargon
   - Nearly identical overlapping meanings (pick the clearer one)

4. PREFER these characteristics:
   - Senses where the word appears as the primary lemma
   - Meanings a B1/B2 student would likely encounter
   - Senses that can be illustrated with clear examples
   - Meanings relevant to Taiwan daily life, school, or work

5. QUALITY CHECK each selection:
   - Is this sense something a high school student might need?
   - Can this sense be explained simply in 15 words or less?
   - Would a typical English conversation use this meaning?

Return a JSON object with this structure:
{{
    "selected": [
        {{
            "sense_id": "exact.sense.id.from.input",
            "pos": "n/v/adj/adv",
            "reason": "Brief reason for selection (1 sentence)",
            "priority": 1
        }},
        {{
            "sense_id": "...",
            "pos": "...",
            "reason": "...",
            "priority": 2
        }}
    ],
    "rejected_notable": [
        {{
            "sense_id": "...",
            "reason": "Too academic/obsolete/etc"
        }}
    ]
}}

IMPORTANT:
- Select exactly {max_senses} senses (or fewer if not enough useful ones exist)
- sense_id must EXACTLY match one from the input list
- Priority 1 = most common/important, 2 = second most important, etc.
- Include at least one notable rejection to show you filtered properly
"""
    
    def select(
        self,
        word: str,
        wordnet_senses: List[Dict[str, Any]],
        max_senses: int = 2,
        frequency_rank: int = None,
        cefr: str = None
    ) -> List[SelectedSense]:
        """
        Select the most useful senses for a word.
        
        Args:
            word: The target word
            wordnet_senses: List of senses from WordNet, each with:
                - id: Sense ID (e.g., "drop.v.01")
                - definition: WordNet definition
                - pos: Part of speech
                - lemmas: List of lemma names
            max_senses: Maximum senses to select (1-3)
            frequency_rank: Word frequency rank (for context)
            cefr: CEFR level (A1-C2)
            
        Returns:
            List of SelectedSense objects, ordered by priority
        """
        if not wordnet_senses:
            return []
        
        # If only 1-2 senses available, return them all
        if len(wordnet_senses) <= max_senses:
            return [
                SelectedSense(
                    sense_id=s['id'],
                    pos=s.get('pos', 'n'),
                    definition=s['definition'],
                    reason="Only available sense",
                    priority=i + 1
                )
                for i, s in enumerate(wordnet_senses)
            ]
        
        # Format senses for prompt
        senses_for_prompt = []
        for s in wordnet_senses:
            senses_for_prompt.append({
                'id': s['id'],
                'definition': s['definition'],
                'pos': s.get('pos', 'unknown'),
                'lemmas': s.get('lemmas', [])
            })
        
        prompt = self.format_prompt(
            word=word,
            frequency_rank=frequency_rank or 'unknown',
            cefr=cefr or 'B1/B2',
            senses_json=json.dumps(senses_for_prompt, indent=2),
            max_senses=max_senses
        )
        
        try:
            result = self.generate_json(prompt)
            
            selected = []
            for item in result.get('selected', []):
                # Find the original sense data
                original = next(
                    (s for s in wordnet_senses if s['id'] == item['sense_id']),
                    None
                )
                
                if original:
                    selected.append(SelectedSense(
                        sense_id=item['sense_id'],
                        pos=item.get('pos', original.get('pos', 'n')),
                        definition=original['definition'],
                        reason=item.get('reason', ''),
                        priority=item.get('priority', len(selected) + 1)
                    ))
            
            # Sort by priority
            selected.sort(key=lambda x: x.priority)
            
            return selected[:max_senses]
        
        except Exception as e:
            # Fallback: return first N senses if AI fails
            print(f"⚠️ Sense selection failed for '{word}': {e}")
            return [
                SelectedSense(
                    sense_id=s['id'],
                    pos=s.get('pos', 'n'),
                    definition=s['definition'],
                    reason="Fallback selection",
                    priority=i + 1
                )
                for i, s in enumerate(wordnet_senses[:max_senses])
            ]


# Singleton instance
_selector = None


def get_selector(config: LLMConfig = None) -> SenseSelector:
    """Get or create the sense selector instance."""
    global _selector
    if _selector is None:
        _selector = SenseSelector(config)
    return _selector


def select_senses(
    word: str,
    wordnet_senses: List[Dict[str, Any]],
    max_senses: int = 2,
    frequency_rank: int = None,
    cefr: str = None
) -> List[SelectedSense]:
    """
    Select the most useful senses for a word.
    
    Args:
        word: The target word
        wordnet_senses: List of WordNet senses
        max_senses: Maximum senses to select
        frequency_rank: Word frequency rank
        cefr: CEFR level
        
    Returns:
        List of SelectedSense objects
        
    Example:
        >>> from nltk.corpus import wordnet as wn
        >>> senses = [{'id': s.name(), 'definition': s.definition(), 'pos': s.pos()} 
        ...           for s in wn.synsets('drop')]
        >>> selected = select_senses('drop', senses, max_senses=2)
        >>> print([s.sense_id for s in selected])
        ['drop.v.01', 'drop.n.02']
    """
    return get_selector().select(
        word=word,
        wordnet_senses=wordnet_senses,
        max_senses=max_senses,
        frequency_rank=frequency_rank,
        cefr=cefr
    )


if __name__ == '__main__':
    import nltk
    from nltk.corpus import wordnet as wn
    
    # Ensure WordNet is available
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')
        nltk.download('omw-1.4')
    
    print("\n--- Sense Selector Test ---\n")
    
    test_words = ['drop', 'bank', 'run', 'break']
    
    for word in test_words:
        print(f"\n=== {word.upper()} ===")
        
        # Get all WordNet senses
        synsets = wn.synsets(word)
        wordnet_senses = [
            {
                'id': s.name(),
                'definition': s.definition(),
                'pos': s.pos(),
                'lemmas': [l.name() for l in s.lemmas()]
            }
            for s in synsets
        ]
        
        print(f"Total WordNet senses: {len(wordnet_senses)}")
        
        # Select best senses
        selected = select_senses(word, wordnet_senses, max_senses=2)
        
        print(f"Selected {len(selected)} senses:")
        for s in selected:
            print(f"  [{s.priority}] {s.sense_id} ({s.pos})")
            print(f"      Definition: {s.definition[:60]}...")
            print(f"      Reason: {s.reason}")

