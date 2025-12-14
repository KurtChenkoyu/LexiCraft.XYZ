# Vocabulary JSON Schema V3

## Overview

Version 3.0 of vocabulary.json uses a **denormalized, sense-centric** structure. All data for a sense is embedded directly, eliminating multiple lookups.

## Schema

```json
{
  "version": "3.0",
  "exportedAt": "2025-12-07T15:00:00.000Z",
  "stats": {
    "senses": 10470,
    "words": 3019,
    "validated": 9500,
    "withConfused": 2500
  },
  
  "senses": {
    "accept.v.01": {
      "id": "accept.v.01",
      "word": "accept",
      "pos": "v",
      "frequency_rank": 500,
      "moe_level": 1,
      "cefr": "A2",
      "tier": 1,
      
      "definition_en": "to take something offered",
      "definition_zh": "接受",
      "definition_zh_explanation": "「接受」指的是願意收下別人給的東西...",
      "translation_source": "ai",
      
      "example_en": "She decided to accept the job offer.",
      "example_zh_translation": "她決定接受那份工作機會。",
      "example_zh_explanation": "「accept」在這裡的意思是...",
      "example_context": "work",
      "validated": true,
      
      "connections": {
        "related": ["receive.v.01", "take.v.01"],
        "opposite": ["reject.v.01", "refuse.v.01"],
        "confused": [
          {"sense_id": "except.v.01", "reason": "spelling"},
          {"sense_id": "expect.v.01", "reason": "spelling"}
        ],
        "phrases": [],
        "morphological": ["acceptance.n.01", "acceptable.a.01"]
      },
      
      "other_senses": ["accept.v.02", "accept.v.03"],
      
      "network": {
        "hop_1_count": 5,
        "hop_2_count": 12,
        "total_reachable": 25,
        "total_xp": 150
      }
    }
  },
  
  "indices": {
    "byWord": {
      "accept": ["accept.v.01", "accept.v.02", "accept.v.03"]
    },
    "byBand": {
      "1000": ["accept.v.01", "the.r.01", ...],
      "2000": [...],
      "3000": [...]
    },
    "byPos": {
      "v": ["accept.v.01", "run.v.01", ...],
      "n": ["dog.n.01", "cat.n.01", ...],
      "a": ["good.a.01", "bad.a.01", ...],
      "r": ["quickly.r.01", ...]
    }
  }
}
```

## Field Descriptions

### Root Level

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version ("3.0") |
| `exportedAt` | string | ISO timestamp of export |
| `stats` | object | Summary statistics |
| `senses` | object | Map of sense_id → sense data |
| `indices` | object | Lookup indices for fast querying |

### Sense Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Sense ID (e.g., "accept.v.01") |
| `word` | string | Yes | The word |
| `pos` | string | Yes | Part of speech (n, v, a, r, s) |
| `frequency_rank` | int | Yes | Frequency rank (lower = more common) |
| `moe_level` | int | No | Taiwan MOE difficulty level (1-6) |
| `cefr` | string | Yes | CEFR level (A1, A2, B1, B2, C1, C2) |
| `tier` | int | Yes | Block tier (1-3) |
| `definition_en` | string | Yes | English definition |
| `definition_zh` | string | Yes | Chinese translation |
| `definition_zh_explanation` | string | No | Explanation of meaning in Chinese |
| `translation_source` | string | No | Source: "omw", "cc-cedict", "ai" |
| `example_en` | string | Yes | Example sentence in English |
| `example_zh_translation` | string | No | Chinese translation of example |
| `example_zh_explanation` | string | No | Explanation of example usage |
| `example_context` | string | No | Context category (school, family, etc.) |
| `validated` | bool | Yes | Whether example passed validation |
| `connections` | object | Yes | Relationship connections |
| `other_senses` | array | Yes | Other sense IDs of same word (for polysemy) |
| `network` | object | Yes | Network/hop statistics |

### Connections Object

| Field | Type | Description |
|-------|------|-------------|
| `related` | array[string] | Related sense IDs (synonyms, hypernyms) |
| `opposite` | array[string] | Opposite sense IDs (antonyms) |
| `confused` | array[object] | Commonly confused words with reasons |
| `phrases` | array[string] | Related phrase sense IDs |
| `morphological` | array[string] | Morphologically related sense IDs |

### Confused Entry

| Field | Type | Description |
|-------|------|-------------|
| `sense_id` | string | The confused sense ID |
| `reason` | string | Why they're confused: "spelling", "sound", "semantic" |

### Network Object

| Field | Type | Description |
|-------|------|-------------|
| `hop_1_count` | int | Direct connections count |
| `hop_2_count` | int | 2-hop connections count |
| `total_reachable` | int | Total reachable nodes in network |
| `total_xp` | int | Total potential XP from network |

### Indices

| Index | Type | Description |
|-------|------|-------------|
| `byWord` | object | word → [sense_ids] for word lookup |
| `byBand` | object | band → [sense_ids] for frequency band queries |
| `byPos` | object | pos → [sense_ids] for POS filtering |

## Key Changes from V2

1. **Removed `words` dict** - Word data is embedded in each sense
2. **Added `other_senses`** - For polysemy checking without extra lookup
3. **Added `confused` connections** - CONFUSED_WITH relationships with reasons
4. **Flattened hop data** - `hop_1/hop_2/hop_3` → simpler `network` object
5. **Added `indices`** - Pre-built indices for fast lookups
6. **Denormalized** - All data in one place per sense

## Usage Examples

### Get sense data (single lookup)
```python
sense = vocabulary["senses"]["accept.v.01"]
# Everything is here - no extra lookups needed
```

### Get senses for a word
```python
sense_ids = vocabulary["indices"]["byWord"]["accept"]
# ["accept.v.01", "accept.v.02", "accept.v.03"]
```

### Get senses in frequency band
```python
band_1000_senses = vocabulary["indices"]["byBand"]["1000"]
```

### Get confused words (for MCQ distractors)
```python
confused = sense["connections"]["confused"]
# [{"sense_id": "except.v.01", "reason": "spelling"}]
```

### Get other senses of same word (polysemy check)
```python
other_senses = sense["other_senses"]
# ["accept.v.02", "accept.v.03"]
```

