"""
DEPRECATED: Export Vocabulary Data from Neo4j to JSON

This script has been DEPRECATED in favor of:
    python backend/scripts/enrich_vocabulary_v2.py

The V2 enrichment script:
- Produces a V3 schema with embedded connections
- Includes CONFUSED_WITH relationships for MCQ distractors
- Has a denormalized structure (no separate lookups needed)
- Mines confused words from Levenshtein distance and curated lists

If you need to export vocabulary data, use:
    cd backend
    python scripts/enrich_vocabulary_v2.py --resume  # Resume from checkpoint
    python scripts/enrich_vocabulary_v2.py --limit 100  # Test with 100 words

This script is kept for reference but should NOT be used.
"""

import sys

def main():
    print("=" * 60)
    print("⚠️  DEPRECATED SCRIPT")
    print("=" * 60)
    print()
    print("This script (export_vocabulary_json.py) has been deprecated.")
    print()
    print("Please use instead:")
    print("    python scripts/enrich_vocabulary_v2.py")
    print()
    print("The V2 script produces a V3 schema with:")
    print("  - Embedded connections (no separate lookups)")
    print("  - CONFUSED_WITH relationships for MCQ distractors")
    print("  - Pre-built indices (byWord, byBand, byPos)")
    print("  - Denormalized structure for fast access")
    print()
    print("Usage:")
    print("    cd backend")
    print("    python scripts/enrich_vocabulary_v2.py --resume")
    print()
    return 1


if __name__ == '__main__':
    sys.exit(main())
