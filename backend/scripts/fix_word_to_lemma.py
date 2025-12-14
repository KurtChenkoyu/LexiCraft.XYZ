#!/usr/bin/env python3
"""
Fix Word Field - Set word=lemma for non-inflections

This script fixes the vocabulary data by:
1. Keeping valid inflections (pressed → press, running → run)
2. Setting word=lemma for cases where word is a synonym/variant, not an inflection

Examples of fixes:
- doctor.n.01: word="docs" → word="doctor" (docs is not an inflection)
- acid.n.02: word="elvis" → word="acid" (elvis is slang, not inflection)

Examples kept as-is:
- press.v.01: word="pressed", lemma="press" (valid inflection)
- be.v.01: word="were", lemma="be" (valid irregular)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

# Configuration
VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"

# Irregular verb forms (word → lemma)
IRREGULAR_FORMS = {
    # be
    'am': 'be', 'is': 'be', 'are': 'be', 'was': 'be', 'were': 'be', 'been': 'be', 'being': 'be',
    # have
    'has': 'have', 'had': 'have', 'having': 'have',
    # do
    'does': 'do', 'did': 'do', 'done': 'do', 'doing': 'do',
    # go
    'goes': 'go', 'went': 'go', 'gone': 'go', 'going': 'go',
    # say
    'says': 'say', 'said': 'say', 'saying': 'say',
    # get
    'gets': 'get', 'got': 'get', 'gotten': 'get', 'getting': 'get',
    # make
    'makes': 'make', 'made': 'make', 'making': 'make',
    # know
    'knows': 'know', 'knew': 'know', 'known': 'know', 'knowing': 'know',
    # think
    'thinks': 'think', 'thought': 'think', 'thinking': 'think',
    # take
    'takes': 'take', 'took': 'take', 'taken': 'take', 'taking': 'take',
    # see
    'sees': 'see', 'saw': 'see', 'seen': 'see', 'seeing': 'see',
    # come
    'comes': 'come', 'came': 'come', 'coming': 'come',
    # give
    'gives': 'give', 'gave': 'give', 'given': 'give', 'giving': 'give',
    # find
    'finds': 'find', 'found': 'find', 'finding': 'find',
    # tell
    'tells': 'tell', 'told': 'tell', 'telling': 'tell',
    # put
    'puts': 'put', 'putting': 'put',
    # keep
    'keeps': 'keep', 'kept': 'keep', 'keeping': 'keep',
    # let
    'lets': 'let', 'letting': 'let',
    # begin
    'begins': 'begin', 'began': 'begin', 'begun': 'begin', 'beginning': 'begin',
    # run
    'runs': 'run', 'ran': 'run', 'running': 'run',
    # write
    'writes': 'write', 'wrote': 'write', 'written': 'write', 'writing': 'write',
    # read
    'reads': 'read', 'reading': 'read',  # read past tense same spelling
    # bring
    'brings': 'bring', 'brought': 'bring', 'bringing': 'bring',
    # sit
    'sits': 'sit', 'sat': 'sit', 'sitting': 'sit',
    # stand
    'stands': 'stand', 'stood': 'stand', 'standing': 'stand',
    # lose
    'loses': 'lose', 'lost': 'lose', 'losing': 'lose',
    # pay
    'pays': 'pay', 'paid': 'pay', 'paying': 'pay',
    # meet
    'meets': 'meet', 'met': 'meet', 'meeting': 'meet',
    # set
    'sets': 'set', 'setting': 'set',
    # lead
    'leads': 'lead', 'led': 'lead', 'leading': 'lead',
    # speak
    'speaks': 'speak', 'spoke': 'speak', 'spoken': 'speak', 'speaking': 'speak',
    # buy
    'buys': 'buy', 'bought': 'buy', 'buying': 'buy',
    # send
    'sends': 'send', 'sent': 'send', 'sending': 'send',
    # build
    'builds': 'build', 'built': 'build', 'building': 'build',
    # fall
    'falls': 'fall', 'fell': 'fall', 'fallen': 'fall', 'falling': 'fall',
    # cut
    'cuts': 'cut', 'cutting': 'cut',
    # sell
    'sells': 'sell', 'sold': 'sell', 'selling': 'sell',
    # break
    'breaks': 'break', 'broke': 'break', 'broken': 'break', 'breaking': 'break',
    # hit
    'hits': 'hit', 'hitting': 'hit',
    # eat
    'eats': 'eat', 'ate': 'eat', 'eaten': 'eat', 'eating': 'eat',
    # catch
    'catches': 'catch', 'caught': 'catch', 'catching': 'catch',
    # draw
    'draws': 'draw', 'drew': 'draw', 'drawn': 'draw', 'drawing': 'draw',
    # choose
    'chooses': 'choose', 'chose': 'choose', 'chosen': 'choose', 'choosing': 'choose',
    # grow
    'grows': 'grow', 'grew': 'grow', 'grown': 'grow', 'growing': 'grow',
    # win
    'wins': 'win', 'won': 'win', 'winning': 'win',
    # spend
    'spends': 'spend', 'spent': 'spend', 'spending': 'spend',
    # hear
    'hears': 'hear', 'heard': 'hear', 'hearing': 'hear',
    # drive
    'drives': 'drive', 'drove': 'drive', 'driven': 'drive', 'driving': 'drive',
    # swim
    'swims': 'swim', 'swam': 'swim', 'swum': 'swim', 'swimming': 'swim',
    # fly
    'flies': 'fly', 'flew': 'fly', 'flown': 'fly', 'flying': 'fly',
    # throw
    'throws': 'throw', 'threw': 'throw', 'thrown': 'throw', 'throwing': 'throw',
    # wear
    'wears': 'wear', 'wore': 'wear', 'worn': 'wear', 'wearing': 'wear',
    # rise
    'rises': 'rise', 'rose': 'rise', 'risen': 'rise', 'rising': 'rise',
    # hold
    'holds': 'hold', 'held': 'hold', 'holding': 'hold',
    # teach
    'teaches': 'teach', 'taught': 'teach', 'teaching': 'teach',
    # fight
    'fights': 'fight', 'fought': 'fight', 'fighting': 'fight',
    # sleep
    'sleeps': 'sleep', 'slept': 'sleep', 'sleeping': 'sleep',
    # feel
    'feels': 'feel', 'felt': 'feel', 'feeling': 'feel',
    # leave
    'leaves': 'leave', 'left': 'leave', 'leaving': 'leave',
    # mean
    'means': 'mean', 'meant': 'mean', 'meaning': 'mean',
    # show
    'shows': 'show', 'showed': 'show', 'shown': 'show', 'showing': 'show',
    # move
    'moves': 'move', 'moved': 'move', 'moving': 'move',
    # live
    'lives': 'live', 'lived': 'live', 'living': 'live',
    # turn
    'turns': 'turn', 'turned': 'turn', 'turning': 'turn',
    # start
    'starts': 'start', 'started': 'start', 'starting': 'start',
    # help
    'helps': 'help', 'helped': 'help', 'helping': 'help',
    # play
    'plays': 'play', 'played': 'play', 'playing': 'play',
    # like
    'likes': 'like', 'liked': 'like', 'liking': 'like',
    # want
    'wants': 'want', 'wanted': 'want', 'wanting': 'want',
    # need
    'needs': 'need', 'needed': 'need', 'needing': 'need',
    # look
    'looks': 'look', 'looked': 'look', 'looking': 'look',
    # use
    'uses': 'use', 'used': 'use', 'using': 'use',
    # work
    'works': 'work', 'worked': 'work', 'working': 'work',
    # try
    'tries': 'try', 'tried': 'try', 'trying': 'try',
    # ask
    'asks': 'ask', 'asked': 'ask', 'asking': 'ask',
    # call
    'calls': 'call', 'called': 'call', 'calling': 'call',
}


def is_valid_inflection(word: str, lemma: str) -> bool:
    """
    Check if word is a valid inflection of lemma.
    
    Returns True for:
    - Same word (case-insensitive)
    - Regular inflections (pressed/press, running/run, dogs/dog)
    - Irregular forms (went/go, bought/buy)
    """
    w = word.lower().strip()
    l = lemma.lower().strip()
    
    # Same word
    if w == l:
        return True
    
    # Check irregular forms
    if IRREGULAR_FORMS.get(w) == l:
        return True
    
    # Regular inflection patterns
    # -ed, -ing, -s, -es endings
    if w.endswith('ed') and (w[:-2] == l or w[:-1] == l or w[:-2] + 'e' == l):
        return True
    if w.endswith('ing') and (w[:-3] == l or w[:-3] + 'e' == l or w[:-4] == l):
        return True
    if w.endswith('s') and (w[:-1] == l or w[:-2] == l):
        return True
    if w.endswith('es') and (w[:-2] == l or w[:-1] == l):
        return True
    
    # Doubled consonant + ed/ing (stopped/stop, running/run)
    if len(w) > 3 and w[-3] == w[-4]:  # doubled consonant
        base = w[:-3]  # remove -ped, -ning, etc.
        if base == l or base + 'e' == l:
            return True
    
    # -ies → -y (tries/try)
    if w.endswith('ies') and w[:-3] + 'y' == l:
        return True
    
    # -ied → -y (tried/try)
    if w.endswith('ied') and w[:-3] + 'y' == l:
        return True
    
    # Lemma contains word or word contains lemma (partial match for compounds)
    if l in w or w in l:
        return True
    
    return False


def main():
    print(f"\n{'='*60}")
    print("🔧 Fixing Word Field - Set word=lemma for non-inflections")
    print(f"{'='*60}\n")
    
    # Load vocabulary
    print(f"📖 Loading {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    senses = data.get('senses', {})
    print(f"✅ Loaded {len(senses)} senses")
    
    # Create backup
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"vocabulary_{timestamp}_prewordfix.json"
    print(f"💾 Creating backup at {backup_path}...")
    shutil.copy(VOCAB_FILE, backup_path)
    
    # Fix word fields
    fixed_count = 0
    kept_count = 0
    already_correct = 0
    samples_fixed = []
    samples_kept = []
    
    for sense_id, sense_data in senses.items():
        word = sense_data.get('word', '')
        lemma = sense_data.get('lemma', '')
        
        if not lemma:
            continue
        
        if not word:
            # No word set, use lemma
            sense_data['word'] = lemma
            fixed_count += 1
            continue
        
        if word.lower() == lemma.lower():
            already_correct += 1
            continue
        
        if is_valid_inflection(word, lemma):
            # Keep valid inflection
            kept_count += 1
            if len(samples_kept) < 10:
                samples_kept.append(f"  {sense_id}: word=\"{word}\" (inflection of \"{lemma}\")")
        else:
            # Fix: word is a synonym/variant, not an inflection
            old_word = word
            sense_data['word'] = lemma
            fixed_count += 1
            if len(samples_fixed) < 15:
                samples_fixed.append(f"  {sense_id}: \"{old_word}\" → \"{lemma}\"")
    
    # Save updated vocabulary
    print(f"💾 Saving updated vocabulary...")
    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print("✅ Fix Complete!")
    print(f"{'='*60}")
    print(f"📊 Already correct (word=lemma): {already_correct}")
    print(f"📊 Kept as inflections: {kept_count}")
    print(f"📊 Fixed (word→lemma): {fixed_count}")
    
    if samples_fixed:
        print(f"\n📋 Sample fixes:")
        for sample in samples_fixed:
            print(sample)
    
    if samples_kept:
        print(f"\n📋 Sample inflections kept:")
        for sample in samples_kept:
            print(sample)
    
    print(f"\n📁 Backup: {backup_path}")
    print(f"📁 Updated: {VOCAB_FILE}")


if __name__ == "__main__":
    main()


