"""
British to American Spelling Normalization

Converts British English spellings to American English for consistency.
The app uses American English as the primary spelling standard.

Usage:
    from src.data_sources.spelling import normalize_spelling
    
    american = normalize_spelling("colour")  # Returns "color"
    american = normalize_spelling("centre")  # Returns "center"
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from functools import lru_cache


# Common British → American spelling patterns
SPELLING_PATTERNS = [
    # -our → -or
    (r'(\w+)our\b', r'\1or'),
    # -ise/-isation → -ize/-ization
    (r'(\w+)ise\b', r'\1ize'),
    (r'(\w+)isation\b', r'\1ization'),
    # -tre → -ter
    (r'(\w+)tre\b', r'\1ter'),
    # -ogue → -og
    (r'(\w+)ogue\b', r'\1og'),
    # -ence → -ense (for specific words)
    # (handled in explicit mapping)
    # -yse → -yze
    (r'(\w+)yse\b', r'\1yze'),
    # -ll- → -l- (travelling → traveling)
    # (handled in explicit mapping due to complexity)
]


class SpellingNormalizer:
    """British to American spelling converter."""
    
    _instance = None
    _explicit_map: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self._load_mapping()
            self._loaded = True
    
    def _get_cache_path(self) -> Path:
        """Get path to spelling map file."""
        return Path(__file__).parent.parent.parent / 'data' / 'source' / 'spelling_map.json'
    
    def _load_mapping(self):
        """Load explicit spelling mappings."""
        cache_path = self._get_cache_path()
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self._explicit_map = json.load(f)
                print(f"✓ Loaded spelling map: {len(self._explicit_map)} words")
                return
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Spelling map error: {e}")
        
        # Initialize with common British → American mappings
        self._explicit_map = self._get_default_mappings()
        print(f"✓ Using default spelling map: {len(self._explicit_map)} words")
        
        # Save to cache
        self._save_cache()
    
    def _get_default_mappings(self) -> Dict[str, str]:
        """Get default British → American spelling mappings."""
        return {
            # -our → -or
            'colour': 'color',
            'colours': 'colors',
            'coloured': 'colored',
            'colouring': 'coloring',
            'colourful': 'colorful',
            'favour': 'favor',
            'favours': 'favors',
            'favoured': 'favored',
            'favouring': 'favoring',
            'favourite': 'favorite',
            'favourites': 'favorites',
            'favouritism': 'favoritism',
            'honour': 'honor',
            'honours': 'honors',
            'honoured': 'honored',
            'honouring': 'honoring',
            'honourable': 'honorable',
            'behaviour': 'behavior',
            'behaviours': 'behaviors',
            'behavioural': 'behavioral',
            'labour': 'labor',
            'labours': 'labors',
            'laboured': 'labored',
            'labouring': 'laboring',
            'labourer': 'laborer',
            'labourers': 'laborers',
            'neighbour': 'neighbor',
            'neighbours': 'neighbors',
            'neighbouring': 'neighboring',
            'neighbourhood': 'neighborhood',
            'neighbourhoods': 'neighborhoods',
            'humour': 'humor',
            'humours': 'humors',
            'humoured': 'humored',
            'humouring': 'humoring',
            'humorous': 'humorous',  # Same in both
            'flavour': 'flavor',
            'flavours': 'flavors',
            'flavoured': 'flavored',
            'flavouring': 'flavoring',
            'vapour': 'vapor',
            'vapours': 'vapors',
            'armour': 'armor',
            'armoured': 'armored',
            'armoury': 'armory',
            'harbour': 'harbor',
            'harbours': 'harbors',
            'harboured': 'harbored',
            'harbouring': 'harboring',
            'endeavour': 'endeavor',
            'endeavours': 'endeavors',
            'endeavoured': 'endeavored',
            'endeavouring': 'endeavoring',
            'savour': 'savor',
            'savours': 'savors',
            'savoury': 'savory',
            'rumour': 'rumor',
            'rumours': 'rumors',
            'rumoured': 'rumored',
            'vigour': 'vigor',
            'vigorous': 'vigorous',  # Same in both
            'odour': 'odor',
            'odours': 'odors',
            'splendour': 'splendor',
            
            # -re → -er
            'centre': 'center',
            'centres': 'centers',
            'centred': 'centered',
            'centring': 'centering',
            'theatre': 'theater',
            'theatres': 'theaters',
            'metre': 'meter',
            'metres': 'meters',
            'litre': 'liter',
            'litres': 'liters',
            'fibre': 'fiber',
            'fibres': 'fibers',
            'spectre': 'specter',
            'spectres': 'specters',
            'sombre': 'somber',
            'lustre': 'luster',
            'meagre': 'meager',
            'calibre': 'caliber',
            'sabre': 'saber',
            'manoeuvre': 'maneuver',
            'manoeuvres': 'maneuvers',
            'manoeuvred': 'maneuvered',
            'manoeuvring': 'maneuvering',
            
            # -ise/-isation → -ize/-ization
            'realise': 'realize',
            'realised': 'realized',
            'realising': 'realizing',
            'realisation': 'realization',
            'organise': 'organize',
            'organised': 'organized',
            'organising': 'organizing',
            'organisation': 'organization',
            'organisations': 'organizations',
            'organisational': 'organizational',
            'recognise': 'recognize',
            'recognised': 'recognized',
            'recognising': 'recognizing',
            'recognition': 'recognition',  # Same in both
            'apologise': 'apologize',
            'apologised': 'apologized',
            'apologising': 'apologizing',
            'criticise': 'criticize',
            'criticised': 'criticized',
            'criticising': 'criticizing',
            'emphasise': 'emphasize',
            'emphasised': 'emphasized',
            'emphasising': 'emphasizing',
            'specialise': 'specialize',
            'specialised': 'specialized',
            'specialising': 'specializing',
            'specialisation': 'specialization',
            'normalise': 'normalize',
            'normalised': 'normalized',
            'normalising': 'normalizing',
            'normalisation': 'normalization',
            'prioritise': 'prioritize',
            'prioritised': 'prioritized',
            'prioritising': 'prioritizing',
            'prioritisation': 'prioritization',
            'maximise': 'maximize',
            'maximised': 'maximized',
            'maximising': 'maximizing',
            'minimise': 'minimize',
            'minimised': 'minimized',
            'minimising': 'minimizing',
            'optimise': 'optimize',
            'optimised': 'optimized',
            'optimising': 'optimizing',
            'optimisation': 'optimization',
            'summarise': 'summarize',
            'summarised': 'summarized',
            'summarising': 'summarizing',
            'memorise': 'memorize',
            'memorised': 'memorized',
            'memorising': 'memorizing',
            'categorise': 'categorize',
            'categorised': 'categorized',
            'categorising': 'categorizing',
            'categorisation': 'categorization',
            'utilise': 'utilize',
            'utilised': 'utilized',
            'utilising': 'utilizing',
            'utilisation': 'utilization',
            'visualise': 'visualize',
            'visualised': 'visualized',
            'visualising': 'visualizing',
            'visualisation': 'visualization',
            'characterise': 'characterize',
            'characterised': 'characterized',
            'characterising': 'characterizing',
            'characterisation': 'characterization',
            
            # -yse → -yze
            'analyse': 'analyze',
            'analysed': 'analyzed',
            'analysing': 'analyzing',
            'analysis': 'analysis',  # Same in both
            'paralyse': 'paralyze',
            'paralysed': 'paralyzed',
            'paralysing': 'paralyzing',
            'catalyse': 'catalyze',
            'catalysed': 'catalyzed',
            'catalysing': 'catalyzing',
            
            # -ence → -ense
            'defence': 'defense',
            'defences': 'defenses',
            'defensive': 'defensive',  # Same in both
            'offence': 'offense',
            'offences': 'offenses',
            'offensive': 'offensive',  # Same in both
            'licence': 'license',  # Noun in British
            'licences': 'licenses',
            'pretence': 'pretense',
            'pretences': 'pretenses',
            
            # -ogue → -og
            'catalogue': 'catalog',
            'catalogues': 'catalogs',
            'catalogued': 'cataloged',
            'cataloguing': 'cataloging',
            'dialogue': 'dialog',
            'dialogues': 'dialogs',
            'monologue': 'monolog',
            'monologues': 'monologs',
            'prologue': 'prolog',
            'prologues': 'prologs',
            'epilogue': 'epilog',
            'epilogues': 'epilogs',
            'analogue': 'analog',
            'analogues': 'analogs',
            
            # Double consonants
            'travelling': 'traveling',
            'travelled': 'traveled',
            'traveller': 'traveler',
            'travellers': 'travelers',
            'cancelling': 'canceling',
            'cancelled': 'canceled',
            'cancellation': 'cancellation',  # Same in both
            'counselling': 'counseling',
            'counselled': 'counseled',
            'counsellor': 'counselor',
            'counsellors': 'counselors',
            'labelling': 'labeling',
            'labelled': 'labeled',
            'levelling': 'leveling',
            'levelled': 'leveled',
            'modelling': 'modeling',
            'modelled': 'modeled',
            'quarrelling': 'quarreling',
            'quarrelled': 'quarreled',
            'signalling': 'signaling',
            'signalled': 'signaled',
            'totalling': 'totaling',
            'totalled': 'totaled',
            'fuelling': 'fueling',
            'fuelled': 'fueled',
            'jewellery': 'jewelry',
            'marvellous': 'marvelous',
            'woollen': 'woolen',
            'skilful': 'skillful',
            'wilful': 'willful',
            'fulfil': 'fulfill',
            'fulfils': 'fulfills',
            'fulfilled': 'fulfilled',  # Same in both
            'fulfilling': 'fulfilling',  # Same in both
            'fulfilment': 'fulfillment',
            'instalment': 'installment',
            'instalments': 'installments',
            'enrol': 'enroll',
            'enrols': 'enrolls',
            'enrolled': 'enrolled',  # Same in both
            'enrolling': 'enrolling',  # Same in both
            'enrolment': 'enrollment',
            'enrolments': 'enrollments',
            
            # ae/oe → e
            'aeroplane': 'airplane',
            'aeroplanes': 'airplanes',
            'archaeology': 'archeology',
            'encyclopaedia': 'encyclopedia',
            'mediaeval': 'medieval',
            'paediatric': 'pediatric',
            'paediatrician': 'pediatrician',
            'anaemia': 'anemia',
            'anaemic': 'anemic',
            'anaesthesia': 'anesthesia',
            'anaesthetic': 'anesthetic',
            'foetus': 'fetus',
            'foetal': 'fetal',
            'oestrogen': 'estrogen',
            'diarrhoea': 'diarrhea',
            'manoeuvre': 'maneuver',
            'omelette': 'omelet',
            
            # Other differences
            'grey': 'gray',
            'greys': 'grays',
            'greyed': 'grayed',
            'greying': 'graying',
            'greyish': 'grayish',
            'pyjamas': 'pajamas',
            'tyre': 'tire',
            'tyres': 'tires',
            'aluminium': 'aluminum',
            'programme': 'program',  # For non-computer contexts
            'programmes': 'programs',
            'programmed': 'programmed',  # Same in both
            'programming': 'programming',  # Same in both
            'cheque': 'check',  # For bank cheques
            'cheques': 'checks',
            'plough': 'plow',
            'ploughs': 'plows',
            'ploughed': 'plowed',
            'ploughing': 'plowing',
            'mould': 'mold',
            'moulds': 'molds',
            'moulded': 'molded',
            'moulding': 'molding',
            'mouldy': 'moldy',
            'moult': 'molt',
            'moulted': 'molted',
            'moulting': 'molting',
            'smoulder': 'smolder',
            'smouldered': 'smoldered',
            'smouldering': 'smoldering',
            'sceptic': 'skeptic',
            'sceptics': 'skeptics',
            'sceptical': 'skeptical',
            'scepticism': 'skepticism',
            'draught': 'draft',
            'draughts': 'drafts',
            'draughty': 'drafty',
            'storey': 'story',  # Building floor
            'storeys': 'stories',
            'kerb': 'curb',  # Edge of road
            'kerbs': 'curbs',
            'gaol': 'jail',
            'gaols': 'jails',
            'gaoler': 'jailer',
            'gaolers': 'jailers',
            'sulphur': 'sulfur',
            'sulphuric': 'sulfuric',
            'jewellery': 'jewelry',
            'artefact': 'artifact',
            'artefacts': 'artifacts',
            'cosy': 'cozy',
            'cosier': 'cozier',
            'cosiest': 'coziest',
            'ageing': 'aging',
            'aged': 'aged',  # Same in both
            'moustache': 'mustache',
            'moustaches': 'mustaches',
            'connexion': 'connection',
            'connexions': 'connections',
            'enquiry': 'inquiry',
            'enquiries': 'inquiries',
            'enquire': 'inquire',
            'enquired': 'inquired',
            'enquiring': 'inquiring',
        }
    
    def _save_cache(self):
        """Save mapping to JSON cache."""
        cache_path = self._get_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(self._explicit_map, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Saved spelling map: {cache_path}")
    
    def normalize(self, word: str) -> Tuple[str, bool]:
        """
        Normalize British spelling to American.
        
        Args:
            word: Word to normalize
            
        Returns:
            Tuple of (normalized_word, was_changed)
        """
        word_lower = word.lower()
        
        # Check explicit mapping first
        if word_lower in self._explicit_map:
            american = self._explicit_map[word_lower]
            
            # Preserve original capitalization pattern
            if word.isupper():
                american = american.upper()
            elif word[0].isupper():
                american = american.capitalize()
            
            return american, True
        
        # Try pattern-based conversion
        for pattern, replacement in SPELLING_PATTERNS:
            if re.search(pattern, word_lower):
                american = re.sub(pattern, replacement, word_lower)
                
                # Preserve capitalization
                if word.isupper():
                    american = american.upper()
                elif word[0].isupper():
                    american = american.capitalize()
                
                return american, True
        
        # No change needed
        return word, False
    
    def is_british(self, word: str) -> bool:
        """Check if a word uses British spelling."""
        _, changed = self.normalize(word)
        return changed
    
    def add_mapping(self, british: str, american: str):
        """Add a new British → American spelling mapping."""
        self._explicit_map[british.lower()] = american.lower()


# Singleton instance
_normalizer = None


def get_normalizer() -> SpellingNormalizer:
    """Get the singleton SpellingNormalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = SpellingNormalizer()
    return _normalizer


@lru_cache(maxsize=10000)
def normalize_spelling(word: str) -> str:
    """
    Convert British spelling to American.
    
    Args:
        word: Word to normalize
        
    Returns:
        American spelling (or original if no change needed)
        
    Example:
        >>> normalize_spelling("colour")
        'color'
        >>> normalize_spelling("centre")
        'center'
        >>> normalize_spelling("hello")
        'hello'
    """
    american, _ = get_normalizer().normalize(word)
    return american


def is_british_spelling(word: str) -> bool:
    """
    Check if a word uses British spelling.
    
    Example:
        >>> is_british_spelling("colour")
        True
        >>> is_british_spelling("color")
        False
    """
    return get_normalizer().is_british(word)


if __name__ == '__main__':
    print("\n--- Spelling Normalization Test ---\n")
    
    test_words = [
        'colour', 'colors',  # Should normalize / already American
        'centre', 'center',
        'realise', 'realize',
        'travelling', 'traveling',
        'defence', 'defense',
        'programme', 'program',
        'grey', 'gray',
        'hello',  # No change needed
        'analyse', 'analyze',
        'favourite', 'favorite',
    ]
    
    for word in test_words:
        normalized = normalize_spelling(word)
        is_brit = is_british_spelling(word)
        status = "→ " + normalized if is_brit else "✓"
        print(f"{word:15} {status}")

