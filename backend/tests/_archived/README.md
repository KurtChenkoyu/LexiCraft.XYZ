# Archived V1 Test Files

This directory contains the original V1 test files.

## Files

- `test_algorithm_correctness_v1.py` - V1 algorithm tests (33 tests, all passing)
- `test_survey_simulation_v1.py` - V1 simulation tests (15 tests, 7 passing with real Neo4j)

## Why Archived

V1 tests were written for the binary search algorithm. V2 uses a different approach:
- Probability-based estimation (not binary search)
- Adaptive band sampling (not fixed phases)
- Confidence-based stopping (not fixed questions)

## Current Tests

V2 tests are now at:
- `../test_algorithm_correctness.py` - V2 algorithm tests (28 tests)
- `../test_survey_simulation.py` - V2 simulation tests (probabilistic users)

## Reference

These files are kept for:
- Historical reference
- Understanding V1 behavior
- Comparison with V2 improvements


