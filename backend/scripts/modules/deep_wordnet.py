"""
Deep WordNet Extractor - Layer 1

Extracts all relationship types from WordNet, not just synonyms/antonyms.
Includes: derivations, similar, attributes, also-sees, entailments, causes.
"""

import threading
from typing import Dict, List, Set
from nltk.corpus import wordnet as wn
from .vocabulary_loader import VocabularyLoader


class DeepWordNetExtractor:
    """Extracts deep WordNet relationships."""
    
    def __init__(self, vocab_loader: VocabularyLoader):
        """Initialize with vocabulary loader."""
        self.vocab_loader = vocab_loader
        self.stats = {
            'total_processed': 0,
            'derivations_added': 0,
            'morphological_added': 0,
            'similar_added': 0,
            'attributes_added': 0,
            'also_sees_added': 0,
            'entailments_added': 0,
            'causes_added': 0,
            'broken_refs_fixed': 0,
        }
        self.stats_lock = threading.Lock()  # Thread-safe stats
    
    def extract_all(self, sense_id: str) -> Dict:
        """
        Extract all WordNet relationships for a sense.
        
        Returns a dict with all relationship types.
        """
        try:
            synset = wn.synset(sense_id)
        except Exception as e:
            print(f"⚠️  Could not find WordNet synset for {sense_id}: {e}")
            return self._empty_result()
        
        self.stats['total_processed'] += 1
        
        # Get the actual word from our vocabulary
        sense_data = self.vocab_loader.get_sense(sense_id)
        actual_word = sense_data.get('word') if sense_data else None
        
        result = {
            # Existing relationships (keep these)
            'related': self._get_synonyms(synset),
            'opposite': self._get_antonyms(synset),
            
            # NEW: Deep relationships
            'derivations': self._get_derivations(synset),
            'morphological': self._get_morphological_forms(synset, actual_word),
            'similar': self._get_similar(synset),
            'attributes': self._get_attributes(synset),
            'also_sees': self._get_also_sees(synset),
            'entailments': self._get_entailments(synset),
            'causes': self._get_causes(synset),
        }
        
        # Track stats (thread-safe)
        with self.stats_lock:
            self.stats['total_processed'] += 1
            if result['derivations']:
                self.stats['derivations_added'] += len(result['derivations'])
            if result['morphological']:
                # Count total morphological forms
                total_morph = sum(len(v) for v in result['morphological'].values())
                self.stats['morphological_added'] += total_morph
            if result['similar']:
                self.stats['similar_added'] += len(result['similar'])
            if result['attributes']:
                self.stats['attributes_added'] += len(result['attributes'])
            if result['also_sees']:
                self.stats['also_sees_added'] += len(result['also_sees'])
            if result['entailments']:
                self.stats['entailments_added'] += len(result['entailments'])
            if result['causes']:
                self.stats['causes_added'] += len(result['causes'])
        
        return result
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'related': [],
            'opposite': [],
            'derivations': [],
            'morphological': {},
            'similar': [],
            'attributes': [],
            'also_sees': [],
            'entailments': [],
            'causes': [],
        }
    
    def _get_synonyms(self, synset) -> List[str]:
        """Get synonyms (same synset lemmas)."""
        synonyms = set()
        for lemma in synset.lemmas():
            related_synset = lemma.synset()
            if related_synset.name() != synset.name():
                synonyms.add(related_synset.name())
        return list(synonyms)
    
    def _get_antonyms(self, synset) -> List[str]:
        """Get antonyms."""
        antonyms = set()
        for lemma in synset.lemmas():
            for antonym in lemma.antonyms():
                antonyms.add(antonym.synset().name())
        return list(antonyms)
    
    def _get_derivations(self, synset) -> List[str]:
        """
        Extract derivationally related forms (cross-POS).
        E.g., formal -> formality, formalize, formally
        """
        derivations = set()
        for lemma in synset.lemmas():
            for related in lemma.derivationally_related_forms():
                derivations.add(related.synset().name())
        return list(derivations)
    
    def _get_morphological_forms(self, synset, actual_word: str = None) -> Dict[str, List[str]]:
        """
        Extract morphological variants (same POS, different forms).
        - Adjectives: comparative, superlative (poor, poorer, poorest)
        - Verbs: conjugations (run, runs, running, ran)
        - Nouns: plurals (child, children)
        
        Args:
            synset: WordNet synset
            actual_word: The actual word from vocabulary (overrides synset name)
        
        Returns dict with form types as keys.
        """
        from nltk.corpus import wordnet as wn
        
        forms = {}
        # Use actual_word if provided, otherwise fall back to synset name
        word = actual_word if actual_word else synset.name().split('.')[0]
        word = word.replace('_', ' ')
        pos = synset.pos()
        
        # Find the base form using morphy (in case word is already inflected)
        base_form = wn.morphy(word, pos) if pos != 'r' else word
        if not base_form:
            base_form = word  # Fall back to original if morphy fails
        
        # Use base form for generating morphological variants
        word = base_form
        
        # For adjectives: try to find comparative/superlative
        if pos == 'a' or pos == 's':
            # Handle irregular comparatives first
            irregular_comps = {
                'good': ('better', 'best'),
                'bad': ('worse', 'worst'),
                'little': ('less', 'least'),
                'much': ('more', 'most'),
                'many': ('more', 'most'),
                'far': ('farther', 'farthest'),
            }
            
            if word in irregular_comps:
                comp, superl = irregular_comps[word]
                if not forms.get('comparative'):
                    forms['comparative'] = []
                if not forms.get('superlative'):
                    forms['superlative'] = []
                forms['comparative'].append(comp)
                forms['superlative'].append(superl)
            else:
                # Try regular forms only for simple adjectives (not compound)
                if ' ' not in word and len(word) <= 8:
                    candidates = []
                    
                    # Pattern 1: word + er/est (big, bigger, biggest)
                    if word[-1] not in 'ey':
                        candidates.append((f"{word}er", f"{word}est"))
                    
                    # Pattern 2: double consonant + er/est (big -> bigger)
                    if len(word) >= 3 and word[-1] in 'bdgmnprt' and word[-2] not in 'aeiou':
                        candidates.append((f"{word}{word[-1]}er", f"{word}{word[-1]}est"))
                    
                    # Pattern 3: y -> ier/iest (happy -> happier)
                    if word.endswith('y') and len(word) > 2:
                        candidates.append((f"{word[:-1]}ier", f"{word[:-1]}iest"))
                    
                    # Verify candidates exist in WordNet
                    for comp, superl in candidates:
                        # Only add if WordNet recognizes them
                        if wn.synsets(comp, pos='a') or wn.synsets(comp, pos='s'):
                            if 'comparative' not in forms:
                                forms['comparative'] = []
                            if comp not in forms['comparative']:
                                forms['comparative'].append(comp)
                        
                        if wn.synsets(superl, pos='a') or wn.synsets(superl, pos='s'):
                            if 'superlative' not in forms:
                                forms['superlative'] = []
                            if superl not in forms['superlative']:
                                forms['superlative'].append(superl)
        
        # For verbs: find conjugations using WordNet's morphy
        elif pos == 'v':
            conjugations = set()
            
            # Handle irregular verbs first (most common ones)
            irregular_verbs = {
                'be': ['am', 'is', 'are', 'was', 'were', 'being', 'been'],
                'have': ['has', 'having', 'had'],
                'do': ['does', 'doing', 'did', 'done'],
                'go': ['goes', 'going', 'went', 'gone'],
                'get': ['gets', 'getting', 'got', 'gotten'],
                'make': ['makes', 'making', 'made'],
                'take': ['takes', 'taking', 'took', 'taken'],
                'come': ['comes', 'coming', 'came'],
                'see': ['sees', 'seeing', 'saw', 'seen'],
                'know': ['knows', 'knowing', 'knew', 'known'],
                'think': ['thinks', 'thinking', 'thought'],
                'say': ['says', 'saying', 'said'],
                'give': ['gives', 'giving', 'gave', 'given'],
                'find': ['finds', 'finding', 'found'],
                'tell': ['tells', 'telling', 'told'],
                'become': ['becomes', 'becoming', 'became'],
                'leave': ['leaves', 'leaving', 'left'],
                'feel': ['feels', 'feeling', 'felt'],
                'bring': ['brings', 'bringing', 'brought'],
                'begin': ['begins', 'beginning', 'began', 'begun'],
                'keep': ['keeps', 'keeping', 'kept'],
                'hold': ['holds', 'holding', 'held'],
                'write': ['writes', 'writing', 'wrote', 'written'],
                'stand': ['stands', 'standing', 'stood'],
                'hear': ['hears', 'hearing', 'heard'],
                'let': ['lets', 'letting'],
                'mean': ['means', 'meaning', 'meant'],
                'set': ['sets', 'setting'],
                'meet': ['meets', 'meeting', 'met'],
                'run': ['runs', 'running', 'ran'],
                'pay': ['pays', 'paying', 'paid'],
                'sit': ['sits', 'sitting', 'sat'],
                'speak': ['speaks', 'speaking', 'spoke', 'spoken'],
                'lie': ['lies', 'lying', 'lay', 'lain'],
                'lead': ['leads', 'leading', 'led'],
                'read': ['reads', 'reading'],
                'grow': ['grows', 'growing', 'grew', 'grown'],
                'lose': ['loses', 'losing', 'lost'],
                'fall': ['falls', 'falling', 'fell', 'fallen'],
                'send': ['sends', 'sending', 'sent'],
                'build': ['builds', 'building', 'built'],
                'understand': ['understands', 'understanding', 'understood'],
                'draw': ['draws', 'drawing', 'drew', 'drawn'],
                'break': ['breaks', 'breaking', 'broke', 'broken'],
                'spend': ['spends', 'spending', 'spent'],
                'cut': ['cuts', 'cutting'],
                'rise': ['rises', 'rising', 'rose', 'risen'],
                'drive': ['drives', 'driving', 'drove', 'driven'],
                'buy': ['buys', 'buying', 'bought'],
                'wear': ['wears', 'wearing', 'wore', 'worn'],
                'choose': ['chooses', 'choosing', 'chose', 'chosen'],
                'seek': ['seeks', 'seeking', 'sought'],
                'throw': ['throws', 'throwing', 'threw', 'thrown'],
                'catch': ['catches', 'catching', 'caught'],
                'deal': ['deals', 'dealing', 'dealt'],
                'win': ['wins', 'winning', 'won'],
                'forget': ['forgets', 'forgetting', 'forgot', 'forgotten'],
                'sell': ['sells', 'selling', 'sold'],
                'fight': ['fights', 'fighting', 'fought'],
                'teach': ['teaches', 'teaching', 'taught'],
                'eat': ['eats', 'eating', 'ate', 'eaten'],
                'drink': ['drinks', 'drinking', 'drank', 'drunk'],
                'sing': ['sings', 'singing', 'sang', 'sung'],
                'swim': ['swims', 'swimming', 'swam', 'swum'],
                'fly': ['flies', 'flying', 'flew', 'flown'],
            }
            
            if word in irregular_verbs:
                # Use the irregular forms directly
                conjugations = set(irregular_verbs[word])
            else:
                # Generate regular verb patterns
                patterns = []
                
                if word.endswith('e') and len(word) > 2:
                    # Verbs ending in 'e': like -> likes, liking, liked
                    patterns = [
                        f"{word}s",          # likes
                        f"{word[:-1]}ing",   # liking
                        f"{word}d",          # liked
                    ]
                elif word.endswith('y') and len(word) > 2 and word[-2] not in 'aeiou':
                    # Verbs ending in consonant+y: carry -> carries, carrying, carried
                    patterns = [
                        f"{word[:-1]}ies",   # carries
                        f"{word}ing",        # carrying
                        f"{word[:-1]}ied",   # carried
                    ]
                elif len(word) >= 3 and word[-1] in 'bdgmnprt' and word[-2] in 'aeiou' and word[-3] not in 'aeiou':
                    # CVC pattern (stop, plan): double final consonant
                    patterns = [
                        f"{word}s",              # stops
                        f"{word}{word[-1]}ing",  # stopping
                        f"{word}{word[-1]}ed",   # stopped
                    ]
                else:
                    # Regular verbs: walk -> walks, walking, walked
                    patterns = [
                        f"{word}s",      # walks
                        f"{word}ing",    # walking
                        f"{word}ed",     # walked
                    ]
                
                # Verify each pattern with morphy
                for form in patterns:
                    try:
                        if wn.morphy(form, 'v') == word:
                            conjugations.add(form)
                    except:
                        pass
            
            if conjugations:
                forms['conjugations'] = sorted(list(conjugations))
        
        # For nouns: find plurals
        elif pos == 'n':
            if ' ' not in word:  # Only for simple nouns
                plural_candidates = []
                
                if word.endswith('y') and len(word) > 2 and word[-2] not in 'aeiou':
                    plural_candidates.append(f"{word[:-1]}ies")
                elif word.endswith(('s', 'x', 'z', 'ch', 'sh')):
                    plural_candidates.append(f"{word}es")
                else:
                    plural_candidates.append(f"{word}s")
                
                for plural in plural_candidates:
                    try:
                        if wn.morphy(plural, 'n') == word:
                            forms['plural'] = [plural]
                            break
                    except:
                        pass
        
        return forms

    
    def _get_similar(self, synset) -> List[str]:
        """
        Get similar adjectives (satellite adjectives).
        E.g., formal -> conventional, official
        """
        similar = set()
        try:
            for s in synset.similar_tos():
                similar.add(s.name())
        except AttributeError:
            # Not an adjective, no similar_tos method
            pass
        return list(similar)
    
    def _get_attributes(self, synset) -> List[str]:
        """
        Get attributes (adjective ↔ noun).
        E.g., heavy ↔ weight
        """
        attributes = set()
        try:
            for attr in synset.attributes():
                attributes.add(attr.name())
        except AttributeError:
            pass
        return list(attributes)
    
    def _get_also_sees(self, synset) -> List[str]:
        """Get related concepts (also-sees)."""
        also_sees = set()
        try:
            for also in synset.also_sees():
                also_sees.add(also.name())
        except AttributeError:
            pass
        return list(also_sees)
    
    def _get_entailments(self, synset) -> List[str]:
        """
        Get entailments (verb implications).
        E.g., snore -> sleep
        """
        entailments = set()
        try:
            for ent in synset.entailments():
                entailments.add(ent.name())
        except AttributeError:
            pass
        return list(entailments)
    
    def _get_causes(self, synset) -> List[str]:
        """
        Get causes (verb A causes verb B).
        E.g., kill -> die
        """
        causes = set()
        try:
            for cause in synset.causes():
                causes.add(cause.name())
        except AttributeError:
            pass
        return list(causes)
    
    def fix_broken_references(self, connections: Dict) -> Dict:
        """
        Fix references to non-existent senses.
        E.g., formal.a.03 -> informal.a.03 (doesn't exist) -> informal.a.01
        """
        fixed = {}
        for rel_type, sense_ids in connections.items():
            # Skip 'confused' - it has objects with {sense_id, reason}, not just IDs
            if rel_type == 'confused':
                fixed[rel_type] = sense_ids
                continue
            
            if not isinstance(sense_ids, list):
                # Skip non-list values
                fixed[rel_type] = sense_ids
                continue
            
            fixed[rel_type] = []
            for sense_id in sense_ids:
                # Skip if this is a dict (shouldn't happen, but safety check)
                if isinstance(sense_id, dict):
                    continue
                if self.vocab_loader.sense_exists(sense_id):
                    fixed[rel_type].append(sense_id)
                else:
                    # Try to find a valid sense of the same word
                    word = self.vocab_loader.extract_word_from_sense_id(sense_id)
                    available_senses = self.vocab_loader.get_senses_for_word(word)
                    
                    if available_senses:
                        # Use first available sense (ideally match by POS, but simplified for now)
                        replacement = available_senses[0]
                        fixed[rel_type].append(replacement)
                        print(f"⚠️  Fixed broken ref: {sense_id} → {replacement}")
                        with self.stats_lock:
                            self.stats['broken_refs_fixed'] += 1
                    else:
                        print(f"❌ Could not fix broken ref: {sense_id} (no senses for '{word}')")
        
        return fixed
    
    def get_stats(self) -> Dict:
        """Get extraction statistics."""
        return self.stats.copy()

