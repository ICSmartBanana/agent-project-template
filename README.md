# agent-project-template

A starter repo for a **multi-tenant RAG agent** that follows the [agent-standards](https://github.com/ICSmartBanana/agent-standards) pack from the first commit. It is a small *working* agent, not an empty skeleton, so every CI gate is real on day one:

- **Tenant isolation at the data layer:** a session-only `TenantContext`, a mandatory SQL tenant filter, and Postgres FORCE row-level security as a second layer, with canary isolation tests.
- **Data classes:** `public`, `insight`, `inference_only` (never quoted) and `pii` (never sent to the model).
- **Cite or abstain:** citations filtered to retrieved documents, "I don't know" below a score threshold, out-of-scope refusal, and an AI disclosure on every answer.
- **Eval framework:** golden, overlap, leakage, PII/inference-only and adversarial sets; four zero-tolerance hard gates on every answer; floors that only go up.
- **CI:** lint and types, tests with Postgres, Bandit, pip-audit, Semgrep, Gitleaks, Trivy, a governance check, generated docs, a PR eval job with a score comment, and a weekly full run.
- **Governance pack:** use-case classification, data-source register, risk register (with tests that check its covering-test references), model card, human-oversight note, incident process and regulatory register.

It was extracted from `etrm-knowledge-agent`, the first agent built to these standards. The sample data (two fictional companies, Northwind Logistics and Southfield Foods, plus a shared knowledge base) is synthetic and small.

## Start a new agent

1. **Create the repo:** on GitHub, use **Use this template**, or run `gh repo create <name> --private --template ICSmartBanana/agent-project-template`. In Claude Code, the `scaffold-agent` skill from the agent-standards plugin walks you through this.
2. **Classify before coding:** fill in `docs/governance/use-case-classification.md` and run the **design gate** (agent-standards `review-gates/design.md`, or the `governance-checklist` skill).
3. **Set up locally:**
   ```bash
   cp .env.example .env            # set the three database passwords and ANTHROPIC_API_KEY
   uv sync
   docker compose up -d db         # Postgres + pgvector on 127.0.0.1:5433
   uv run python -m ingest.cli     # load the sample corpus
   uv run pytest                   # all tests, including isolation
   ```
4. **Replace the sample data** (see below), then re-ingest and re-run the tests.
5. **Write your eval sets** in `evals/sets/` (the `eval-set-from-documents` skill helps). Review them, freeze them, and commit them.
6. **Record the first baseline** and set floors in `evals/thresholds.yaml`. Until then, only the hard gates are enforced.
7. **Add the `ANTHROPIC_API_KEY` repo secret** so the `eval` workflow can run on PRs.

## Replacing the sample data

| File | What to change |
|---|---|
| `data/tenants.yaml` | Your client tenants: id, display name, identifiers (names that must never leak to another tenant), canary |
| `data/corpus/<tenant_id>/*.md` | Your documents, one folder per tenant plus `shared/`. Front matter: `doc_id`, `tenant_id`, `title`, `doc_type`, `data_class`, `status`, `effective_date`, optional `supersedes`/`contradicts`, and `keys` (values an answer would quote). Put each tenant's canary in exactly one of its documents. |
| `data/pii_registry.json` | Seeded PII values per tenant (for tests and the output guard) |
| `prompts/system_v1.md` | The scope line for your domain. A prompt change needs a new version and a CHANGELOG entry. |
| `app/pii.py` | The ID pattern (`EMPLOYEE_ID_RE`) for your domain |
| `evals/sets/*` | Your golden, overlap and red-team sets, and `regression.txt` |
| `docs/governance/*` | Every `<placeholder>`, owners, and the risk and regulatory registers |

`tests/data/test_corpus.py` checks the corpus: valid front matter, canaries, no tenant naming another, PII only in its own tenant's `pii`-class documents, and `keys` quoted verbatim.

## Commands

See [CLAUDE.md](CLAUDE.md).

## License

[MIT](LICENSE). Replace or keep it in repos you create from this template.
