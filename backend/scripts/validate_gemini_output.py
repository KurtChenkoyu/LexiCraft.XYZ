#!/usr/bin/env python3
"""
Gemini Output Validator

Validates the quality and structure of Gemini-enriched vocabulary data.
Checks for:
- JSON structure validity
- Required fields presence
- sense_id references
- CEFR level appropriateness
- Collocation quality
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

INPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_gemini.json"


class GeminiValidator:
    """Validates Gemini-enriched vocabulary data."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = defaultdict(int)
    
    def load_data(self) -> dict:
        """Load vocabulary data."""
        print(f"📖 Loading {INPUT_FILE}")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_structure(self, sense_id: str, sense: dict):
        """Validate sense structure."""
        connections = sense.get('connections', {})
        
        # Check for required fields
        if not connections:
            self.warnings.append(f"{sense_id}: No connections object")
            return
        
        # Validate synonyms
        if 'synonyms' in connections:
            syn = connections['synonyms']
            if not isinstance(syn, dict):
                self.errors.append(f"{sense_id}: synonyms must be a dict")
            elif 'display_words' not in syn or 'sense_ids' not in syn:
                self.errors.append(f"{sense_id}: synonyms missing required fields")
            elif len(syn.get('display_words', [])) == 0:
                self.warnings.append(f"{sense_id}: empty synonyms list")
            self.stats['has_synonyms'] += 1
        
        # Validate antonyms
        if 'antonyms' in connections:
            ant = connections['antonyms']
            if not isinstance(ant, dict):
                self.errors.append(f"{sense_id}: antonyms must be a dict")
            elif 'display_words' not in ant or 'sense_ids' not in ant:
                self.errors.append(f"{sense_id}: antonyms missing required fields")
            self.stats['has_antonyms'] += 1
        
        # Validate collocations
        if 'collocations' in connections:
            colls = connections['collocations']
            if not isinstance(colls, list):
                self.errors.append(f"{sense_id}: collocations must be a list")
            else:
                for coll in colls:
                    # Check for broken collocations (single words or invalid patterns)
                    if ' ' not in coll:
                        self.warnings.append(f"{sense_id}: suspicious collocation '{coll}' (no space)")
                    elif len(coll.split()) < 2:
                        self.warnings.append(f"{sense_id}: suspicious collocation '{coll}'")
            self.stats['has_collocations'] += 1
        
        # Validate word_family
        if 'word_family' in connections:
            wf = connections['word_family']
            if not isinstance(wf, dict):
                self.errors.append(f"{sense_id}: word_family must be a dict")
            else:
                valid_pos = {'noun', 'verb', 'adjective', 'adverb'}
                for pos in wf.keys():
                    if pos not in valid_pos:
                        self.warnings.append(f"{sense_id}: unusual POS in word_family: {pos}")
            self.stats['has_word_family'] += 1
        
        # Validate forms
        if 'forms' in connections:
            forms = connections['forms']
            if not isinstance(forms, dict):
                self.errors.append(f"{sense_id}: forms must be a dict")
            else:
                valid_forms = {'comparative', 'superlative', 'past', 'past_participle', 'plural'}
                for form in forms.keys():
                    if form not in valid_forms:
                        self.warnings.append(f"{sense_id}: unusual form type: {form}")
            self.stats['has_forms'] += 1
        
        # Validate similar_words
        if 'similar_words' in connections:
            sim = connections['similar_words']
            if not isinstance(sim, dict):
                self.errors.append(f"{sense_id}: similar_words must be a dict")
            elif 'display_words' not in sim or 'sense_ids' not in sim:
                self.errors.append(f"{sense_id}: similar_words missing required fields")
            self.stats['has_similar'] += 1
    
    def validate_sense_ids(self, vocab_data: dict):
        """Validate that sense_ids reference real senses."""
        all_sense_ids = set(vocab_data['senses'].keys())
        
        for sense_id, sense in vocab_data['senses'].items():
            connections = sense.get('connections', {})
            
            # Check synonym sense_ids
            if 'synonyms' in connections:
                for ref_id in connections['synonyms'].get('sense_ids', []):
                    if ref_id not in all_sense_ids:
                        self.warnings.append(f"{sense_id}: synonym references unknown sense '{ref_id}'")
            
            # Check antonym sense_ids
            if 'antonyms' in connections:
                for ref_id in connections['antonyms'].get('sense_ids', []):
                    if ref_id not in all_sense_ids:
                        self.warnings.append(f"{sense_id}: antonym references unknown sense '{ref_id}'")
            
            # Check similar_words sense_ids
            if 'similar_words' in connections:
                for ref_id in connections['similar_words'].get('sense_ids', []):
                    if ref_id not in all_sense_ids:
                        self.warnings.append(f"{sense_id}: similar_word references unknown sense '{ref_id}'")
    
    def validate_cefr_appropriateness(self, vocab_data: dict):
        """Check if connections match CEFR levels."""
        # Map CEFR to difficulty
        cefr_order = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
        
        for sense_id, sense in vocab_data['senses'].items():
            word_cefr = sense.get('cefr', 'B1')
            word_level = cefr_order.get(word_cefr, 3)
            connections = sense.get('connections', {})
            
            # Check synonyms CEFR level
            if 'synonyms' in connections:
                for ref_id in connections['synonyms'].get('sense_ids', []):
                    if ref_id in vocab_data['senses']:
                        ref_sense = vocab_data['senses'][ref_id]
                        ref_cefr = ref_sense.get('cefr', 'B1')
                        ref_level = cefr_order.get(ref_cefr, 3)
                        
                        # Warn if synonym is 2+ levels harder
                        if ref_level > word_level + 1:
                            self.warnings.append(
                                f"{sense_id} ({word_cefr}): synonym '{ref_id}' is much harder ({ref_cefr})"
                            )
    
    def run(self):
        """Run all validations."""
        print("\n" + "="*60)
        print("🔍 Validating Gemini Output")
        print("="*60 + "\n")
        
        # Load data
        try:
            vocab_data = self.load_data()
        except FileNotFoundError:
            print(f"❌ Error: {INPUT_FILE} not found")
            print("Run enrich_with_gemini.py first!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON - {e}")
            sys.exit(1)
        
        senses = vocab_data.get('senses', {})
        total_senses = len(senses)
        print(f"✅ Loaded {total_senses} senses\n")
        
        # Run validations
        print("🔍 Validating structure...")
        for sense_id, sense in senses.items():
            self.validate_structure(sense_id, sense)
        
        print("🔍 Validating sense_id references...")
        self.validate_sense_ids(vocab_data)
        
        print("🔍 Validating CEFR appropriateness...")
        self.validate_cefr_appropriateness(vocab_data)
        
        # Report
        print("\n" + "="*60)
        print("📊 Validation Results")
        print("="*60)
        print(f"\nCoverage:")
        print(f"  - Synonyms: {self.stats['has_synonyms']}/{total_senses} ({self.stats['has_synonyms']/total_senses*100:.1f}%)")
        print(f"  - Antonyms: {self.stats['has_antonyms']}/{total_senses} ({self.stats['has_antonyms']/total_senses*100:.1f}%)")
        print(f"  - Collocations: {self.stats['has_collocations']}/{total_senses} ({self.stats['has_collocations']/total_senses*100:.1f}%)")
        print(f"  - Word Family: {self.stats['has_word_family']}/{total_senses} ({self.stats['has_word_family']/total_senses*100:.1f}%)")
        print(f"  - Forms: {self.stats['has_forms']}/{total_senses} ({self.stats['has_forms']/total_senses*100:.1f}%)")
        print(f"  - Similar: {self.stats['has_similar']}/{total_senses} ({self.stats['has_similar']/total_senses*100:.1f}%)")
        
        print(f"\n❌ Errors: {len(self.errors)}")
        if self.errors[:5]:
            print("  First 5:")
            for err in self.errors[:5]:
                print(f"    - {err}")
        
        print(f"\n⚠️  Warnings: {len(self.warnings)}")
        if self.warnings[:10]:
            print("  First 10:")
            for warn in self.warnings[:10]:
                print(f"    - {warn}")
        
        # Exit code
        if len(self.errors) > 0:
            print("\n❌ Validation FAILED - fix errors before deploying")
            sys.exit(1)
        elif len(self.warnings) > total_senses * 0.1:  # More than 10% warnings
            print(f"\n⚠️  Many warnings ({len(self.warnings)}) - review before deploying")
            sys.exit(0)
        else:
            print("\n✅ Validation PASSED - ready to deploy!")
            sys.exit(0)


if __name__ == "__main__":
    validator = GeminiValidator()
    validator.run()








