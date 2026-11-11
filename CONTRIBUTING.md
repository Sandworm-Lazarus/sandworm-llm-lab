# Contributing

Add sources that fit this collection's purpose. Record canonical repository, immutable revision, entry/blob identity, requirements, a concrete task and license evidence in `catalog/arsenal.json`. Keep Entry and Overview status consistent with the actual inspection; do not add runtime claims without reproducible evidence.

Regenerate and validate after edits:

```bash
python3 scripts/arsenal.py render
python3 scripts/arsenal.py check
```

Use original summaries and pinned links. Do not copy upstream bundles or include private data and credentials. Propose changes to the shared catalog/CLI in the collection hub when they affect multiple repositories.
