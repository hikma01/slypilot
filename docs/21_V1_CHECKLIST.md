# SlyPilot V1 Checklist

## Validation checklist

- [x] repository structure exists
- [x] official tests pass
- [x] task packet builder generates packets
- [x] ARCHI OPS selection is deterministic
- [x] task packet guardrails are present
- [x] provider adapter exists and preserves dry-run behavior
- [x] simple JSONL history exists
- [x] offline benchmark supports the task packet value thesis

## Limits checklist

- [x] no embeddings
- [x] no vector search
- [x] no multi-provider routing
- [x] no advanced memory
- [x] no automatic history-based selection
- [x] no agent autonomy
- [x] no SQLite memory layer

## Operational checklist

- [x] use `python3 -m unittest discover`
- [x] keep the index manually maintained
- [x] keep history append-only
- [x] keep the architecture boundary deterministic
