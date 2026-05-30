# Loader Relevance Validation

Date: 2026-05-31

Goal: compare human-expected context selection vs deterministic ARCHI OPS loader output.

## Cases tested

### 1. Bug SlyScan

Request: `corrige bug upload SlyScan`

Human-expected files:

- `docs/03_ARCHI_OPS_INDEX.md`
- `docs/07_TESTING_STRATEGY.md`
- `docs/08_DECISIONS_LOG.md`
- `docs/09_METRICS_V1.md`

Loader files:

- `docs/03_ARCHI_OPS_INDEX.md`

Metrics:

- `expected_files_count: 4`
- `matched_files_count: 1`
- `selection_precision: 0.25`

Assessment:

- deterministic selection works
- relevance is weak for a runtime-style bug
- index is too document-centric for this case

### 2. Architecture SlyPilot

Request: `analyse architecture SlyPilot`

Human-expected files:

- `docs/01_ARCHITECTURE.md`
- `README.md`
- `docs/03_ARCHI_OPS_INDEX.md`
- `docs/11_CONTEXT_SELECTION_CONTRACT.md`

Loader files:

- `docs/01_ARCHITECTURE.md`
- `docs/03_ARCHI_OPS_INDEX.md`
- `README.md`

Metrics:

- `expected_files_count: 4`
- `matched_files_count: 3`
- `selection_precision: 0.75`

Assessment:

- selection is broadly aligned
- one contract file is missing from the loader surface
- this case is acceptable for V1

### 3. Hermes explain

Request: `explique problème login Hermes`

Human-expected files:

- `docs/00_PROJECT_OVERVIEW.md`
- `README.md`
- `docs/04_SECURITY.md`

Loader files:

- `docs/00_PROJECT_OVERVIEW.md`
- `README.md`

Metrics:

- `expected_files_count: 3`
- `matched_files_count: 2`
- `selection_precision: 0.6667`

Assessment:

- selection is reasonable for an explain-style request
- security context is missing from the loader selection

## Conclusion

The loader mechanism is valid, but selection quality is not uniform.

What works:

- deterministic ordering
- profile limits
- stable packet enrichment

What fails:

- runtime-style bug selection is too weak
- the index is still too shallow for operational incidents

## Recommendation

Do not add provider integration yet.

Adjust the index first:

- add stronger runtime-oriented entries for SlyScan
- add security-oriented entries for Hermes explain / login cases
- keep the loader deterministic
- keep `intent_keywords` out of V1

The next step is index refinement, not provider hookup.
