# Changelog

Every change to prompts, models, retrieval settings, knowledge bases, eval sets or guardrails gets an entry here. The CI governance check enforces it.

## [Unreleased]

### Added
- Initial template, extracted from `etrm-knowledge-agent` (milestones M2 to M4):
  - the agent (FastAPI, Streamlit, retrieval with row-level security, output guard, tracing)
  - ingest
  - the eval framework and CI workflows
  - the governance pack
- Tenants are configured in `data/tenants.yaml` instead of in code.
- A small hand-written sample corpus for two tenants plus `shared`, with the deliberate messiness the standards ask for (superseded version, injected instruction, inference-only notes, contact lists, canaries, overlapping topics).
- `tests/data/test_corpus.py` validates any corpus. It replaces the spec-based validator, which relied on the LLM data generator; that generator is not part of the template.
- `evals.compare` and `scripts/gen_docs.py` work before the first baseline exists: only the hard gates are enforced.
