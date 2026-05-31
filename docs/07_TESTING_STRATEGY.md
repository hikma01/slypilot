# Testing Strategy

V1 tests should focus on:

- repository structure
- documentation presence
- importability of package entry points
- presence of official metrics documentation
- explicit validation of the repository contract, not runtime business logic
- dry-run packet generation and file persistence
- warning behavior when ARCHI OPS minimal index is missing
- deterministic ARCHI OPS selection
- packet enrichment with selected files, maps, and reasons
- bounded profile limits for minimal, standard, and premium

## Official command

Use a single official command for V1:

```bash
python3 -m unittest discover
```

This command must execute all tests that are part of the V1 harness.

## Test style rule

- All tests must be written in `unittest` style.
- Do not rely on `pytest`-only discovery.
- Keep the harness small and deterministic.
