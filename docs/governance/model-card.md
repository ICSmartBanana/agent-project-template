# Model card: <agent name>

| | |
|---|---|
| Status | **Template: complete before the pre-release gate** |
| Version | 0.1 (<date>) |
| Owner | <agent owner> |
| Review | On every change to the model, prompt, retrieval settings or knowledge bases, and monthly with the risk register |

This card describes a **system**: an agent built on a third-party model, not a model we trained. It has two parts:

- **This file:** purpose, intended use, limits and reasoning. It changes only when someone decides something.
- **The generated card:** `model-card.md` in the `governance-docs` CI artifact, built by `uv run python scripts/gen_docs.py`. It holds the facts that change with the code: model IDs, prompt version, retrieval settings, baseline scores, thresholds and change history.

Where the two disagree, the generated card is right about the facts, and this file should be updated.

## Purpose and intended use

<What questions it answers, for whom, from which knowledge.>

- **Intended users:** <roles>
- **Intended setting:** <POC on synthetic data / production>
- **EU AI Act tier:** <tier> ([use-case classification](use-case-classification.md))

## Out of scope

- Decisions about individuals.
- Acting on any system (the agent has no tools). Giving it tools is a re-classification trigger.
- <Anything else: real data before approvals, general chat, other companies.>

## System overview

| Component | Choice | Notes |
|---|---|---|
| Answer model | Pinned ID in `app/config.py` | Third-party model through its API. Not trained or fine-tuned on client data. |
| Embeddings | `fastembed` bge-small, run locally | No document text leaves the machine for embedding |
| Retrieval | Postgres + pgvector, tenant pre-filter plus FORCE row-level security | `app/retrieval.py`, `db/init/01_schema.sh` |
| Output guard | PII masking, inference-only and system-prompt n-gram blocks, citation filter | `app/guard.py` |
| Tracing | Local JSONL, plus Langfuse when keys are set | IDs and scores only, never document text; PII masked |

## Knowledge bases

See the [data-source register](data-source-register.md).

## Evaluation

Frozen sets in `evals/sets/`: golden, overlap, leakage, PII and inference-only, adversarial, and the regression subset. Four hard gates are checked on every answer with zero tolerance. Results: the generated card and the score table that the `eval` workflow posts on PRs.

## Known limitations

<Replace and extend. Typical ones:>

- It can be wrong; quality metrics are exact-match checks, not LLM-judged faithfulness.
- PII detection is pattern- and registry-based; real names need NER.
- It prefers current over superseded documents only as well as the `status` field is maintained.

## Data handling

- Client data is never used to train or fine-tune any model.
- PII is masked at ingestion, blocked at output and redacted from traces.
- Each client's data can be deleted without touching the others.

## Human oversight and incidents

See the [human-oversight note](human-oversight.md) and the [incident process](incident-process.md).

## Change history

[`CHANGELOG.md`](../../CHANGELOG.md), copied into the generated card.

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Agent owner | | | |
