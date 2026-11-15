# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A multi-tenant RAG agent built from `agent-project-template`, following the agent-standards pack (principles, review gates, playbooks and skills: https://github.com/ICSmartBanana/agent-standards). **Replace this section** with what your agent does, for whom, and its tenants.

The sample tenants (`tenant_a` Northwind Logistics, `tenant_b` Southfield Foods, and `shared`) are synthetic placeholders. See README "Replacing the sample data".

## Commands

The project uses `uv` with Python 3.12 (pinned in `.python-version`). Dependencies are locked in `uv.lock`. Copy `.env.example` to `.env` first.

```bash
uv sync                                   # install deps into .venv
docker compose up -d db                   # Postgres + pgvector on 127.0.0.1:5433
uv run python -m ingest.cli               # chunk, mask PII, embed, load a new kb_version
uv run pytest                             # all tests; `db`-marked ones skip if Postgres is down
uv run pytest tests/isolation             # tenant-isolation hard gates (needs db + ingest)
uv run pytest tests/data/test_corpus.py -k a-002   # one doc's corpus checks
uv run ruff check . && uv run ruff format --check .
uv run mypy app ingest evals
uv run uvicorn app.api.main:app --port 8000          # API
uv run streamlit run app/ui/streamlit_app.py         # UI (talks to the API)
docker compose up --build                 # db + api (:8000) + ui (:8501) in containers
uv run python -m evals.run --suite regression        # PR eval subset (calls the answer model)
uv run python -m evals.run --suite all               # full suite
uv run python -m evals.compare check --results evals/results/<run>.json   # gate a run vs thresholds
uv run python scripts/gen_docs.py --out build/docs   # model card, data register, eval report, changelog
uv run python scripts/governance_check.py origin/main  # governed areas changed without docs?
uvx pre-commit install                    # local gitleaks + ruff hooks
```

Use `127.0.0.1`, not `localhost`, for the database: on some Windows machines `localhost` tries IPv6 first and each connect stalls. Database schema changes go in `db/init/01_schema.sh`, which runs only on an empty volume, so after changing it run `docker compose down -v`, bring the db back up, then re-ingest. Keep shell scripts LF (`.gitattributes`), or the container can't run them.

## CI (`.github/workflows/`)

- `ci.yml` (every PR and push to main) runs these jobs:
  - lint: ruff and mypy
  - tests: Postgres via compose, then ingest, then pytest. The job fails if any `db` test was skipped.
  - security: Bandit, pip-audit, Semgrep `p/python` + `p/secrets`, Gitleaks over the full history
  - Trivy: on PRs that touch the Dockerfile or dependencies, and on main
  - governance: `scripts/governance_check.py`
  - docs: generated docs plus `docs/`, uploaded as the `governance-docs` artifact
- `eval.yml` runs on PRs that touch `app/`, `prompts/`, `ingest/`, `data/`, `evals/` or `db/`. It runs the regression subset, then `evals.compare check` against `evals/thresholds.yaml`, and posts the score table as a PR comment. It needs the `ANTHROPIC_API_KEY` repo secret. A hard-gate failure or a metric below its floor fails the job.
- `weekly.yml` (Mondays, or by hand) runs the full eval suite and a Trivy scan.
- Floors in `evals/thresholds.yaml` only ever go up. Before the first baseline, only hard gates are enforced. The regression baseline is derived from a full run with `evals.compare make-baseline`, not from a separate run.
- Scanner versions are pinned in the workflows. Use `# nosec <ID>` only with the justification on the line above, because Bandit parses any words after it.

## How a request flows

`app/api/main.py` (session token → `TenantContext`) → `app/agent.py:answer_question` → `app/retrieval.py` (role `agent_app`, `SET LOCAL app.tenant_id` in the transaction, plus a `tenant_id = ANY(...)` pre-filter) → abstain if the best score is below `RETRIEVAL.min_score` → drop `pii`-class chunks → `public`/`insight` chunks go in `<documents>`, `inference_only` in `<internal_context>` → `app/llm.py` (structured JSON output) → `app/guard.py` (PII mask, inference-only and system-prompt n-gram blocks, citation filter) → `app/tracing.py` (PII-masked JSONL in `.traces/`, plus Langfuse when `LANGFUSE_*` keys are set; IDs and scores only, never document text).

Tenants come from `data/tenants.yaml` (`app/corpus.py`); the shared tenant's id is fixed as `shared`, because the database policy uses it.

Database roles: `agent_owner` is the image's superuser, which bypasses RLS, so it is for admin only. `agent_schema` owns the tables and is bound by FORCE RLS. `agent_app` is the API. `agent_ingest` has BYPASSRLS and is never used by the API.

Evals (`evals/`): sets live in `evals/sets/`, hand-written or generated once, reviewed and frozen. `regression.txt` is the frozen PR subset. `evals/gates.py` runs the hard gates (leakage, PII, inference-only, system prompt/injection) deterministically on **every** answer, with no LLM judge. Leakage is detected from other tenants' identifiers, canaries, seeded PII and document `keys`. Baselines go in `evals/baselines/`; run outputs go to `evals/results/` (git-ignored).

## Data

- `data/corpus/<tenant_id>/<doc_id>.md`: YAML front matter (`doc_id`, `tenant_id`, `title`, `doc_type`, `data_class`, `status`, `effective_date`, optional `supersedes`/`contradicts`, `keys`), then Markdown with `##` sections (the chunk boundaries).
- Messy data is deliberate (a superseded version, the injected instruction `INJECTION-TEST-0001` in `b-004`, inference-only notes, contact lists). Don't "fix" it. `docs/governance/data-source-register.md` lists it.
- After any data change, run `tests/data/test_corpus.py`, re-ingest, and update the data-source register and CHANGELOG (the governance check enforces the docs).

## Governance pack

`docs/governance/README.md` indexes it. `tests/governance/test_registers.py` parses the risk and regulatory registers:

- Every risk's **Covering tests** use the `` `pytest:file::test` ``, `` `gate:name` ``, `` `eval:suite` `` or `` `ci:job` `` format, and each reference must still exist. When you rename or delete a test, gate, suite or CI job, update the register in the same change.
- Every regulatory row needs ISO review dates, at most 92 days apart.
- Relative links in the pack must resolve.

Sign-off tables belong to the named approvers. Never fill one in on someone else's behalf.

## Architecture invariants (must hold in all code)

A change that weakens any of these is a defect, even if the tests pass.

1. **Tenant isolation is enforced at the data layer, never by the prompt.** Retrieval requires a `TenantContext` built only from the authenticated session. No code path may derive a tenant from user text. SQL always filters `tenant_id IN (:tenant, 'shared')`. Postgres row-level security, keyed on a per-transaction setting, is the second layer.
2. **Every chunk carries `tenant_id`, `data_class` and `kb_version`.**
3. **PII handling.** PII is masked at ingestion. The output guard masks PII regex matches and seeded-registry matches. `pii`-class chunks never reach the model. PII is redacted before anything goes to traces or logs.
4. **Inference-only content is never quoted.** It goes to the model in a separate tagged block, and the output checker blocks verbatim n-gram overlap with it.
5. **Cite or abstain.** Every answer cites its sources, or the agent says it doesn't know. It refuses out-of-scope topics, never reveals the system prompt, and always shows an AI disclosure notice.
6. **Traceability.** Every request is traced with client id, retrieved chunks and scores, model, `prompt_version` and `kb_version`. Prompts are versioned files under `prompts/`.
7. **Swappable providers.** The embedder and the LLM sit behind interfaces.

## Evaluation and change rules

- Every change to a prompt, model, retrieval setting or knowledge base needs an eval score report before it merges (agent-standards `playbooks/change.md`).
- **Leakage, PII, inference-only and system-prompt/injection are hard gates: zero failures.**
- PRs run only the regression subset. Eval sets are generated once, reviewed and committed, never regenerated on each run.
- Branch protection may not be available on private free-plan repos. The working rule is: **never merge a red PR**.

## Models and cost

- Pin model IDs in `app/config.py` (and update `ANSWER_PRICE_PER_MTOK` with them). Use a cheaper model for bulk work such as eval-set generation.
- Use prompt caching on the system prompt.
- Secrets live in `.env` (git-ignored): `ANTHROPIC_API_KEY`, the database passwords, and optionally `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_HOST`. Set a spend limit on every API key.
