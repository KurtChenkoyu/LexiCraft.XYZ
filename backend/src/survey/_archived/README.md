# Archived V1 Files

This directory contains the original V1 LexiSurvey engine that used binary search methodology.

## Files

- `lexisurvey_engine_v1.py` - Original V1 engine (binary search, fixed phases)

## Why Archived

V1 had several critical bugs:
1. **Volume underestimation** (50-70% of actual vocabulary)
2. **Bounds inversion** (low_bound > high_bound)
3. **Unreliable reach** at lower vocabulary levels
4. **Fixed question count** (not adaptive)

V2 (now the main engine) fixes these issues using research-validated probability-based assessment.

## Migration

V2 is now the production engine at `../lexisurvey_engine.py`.

If rollback is needed:
1. Rename `lexisurvey_engine.py` → `lexisurvey_engine_v2_backup.py`
2. Copy `lexisurvey_engine_v1.py` → `../lexisurvey_engine.py`
3. Update imports in `src/api/survey.py`

**Note**: V1 bugs will return if rolled back. V2 is recommended.


