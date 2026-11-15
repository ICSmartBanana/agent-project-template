# Data-source register

| | |
|---|---|
| Version | 0.1 (<date>) |
| Owner | <agent owner> |
| Review | On every change to `data/` (enforced by the governance check), and monthly with the risk register |

> **Template.** The rows below describe the sample corpus that ships with `agent-project-template`. Replace them with your own knowledge bases.

## Knowledge bases

| Knowledge base | `tenant_id` | Source | Owner | Docs | PII present | Visible to | Retention | Last update |
|---|---|---|---|---|---|---|---|---|
| Northwind Logistics (sample) | `tenant_a` | Hand-written sample, `data/corpus/tenant_a/` | <owner> | 7 | Yes, seeded (4 values) | Tenant A users only | Deletable by removing its folder and re-ingesting | <date> |
| Southfield Foods (sample) | `tenant_b` | Hand-written sample, `data/corpus/tenant_b/` | <owner> | 7 | Yes, seeded (4 values) | Tenant B users only | As above | <date> |
| Shared guidance (sample) | `shared` | Hand-written sample, `data/corpus/shared/` | <owner> | 2 | No | All tenants | As above | <date> |

Client data is never used to train or fine-tune a model.

## Data classes and allowed use

| `data_class` | Allowed use | Enforced by |
|---|---|---|
| `public` | May be quoted and cited | n/a |
| `insight` | May be quoted and cited | n/a |
| `inference_only` | May inform an answer; never quoted, never cited | Separate `<internal_context>` block; output guard blocks 8-word verbatim overlap; `inference_only` eval gate |
| `pii` | Never sent to the model | Dropped after retrieval (`app/agent.py`); PII masked at ingestion; `pii` eval gate |

## Deliberately messy test data

Clean synthetic data hides real failures, so the sample corpus includes:

| What | Where | Tested by |
|---|---|---|
| A superseded policy version | `a-004` (superseded by `a-001`) | `eval:adversarial` |
| A prompt injection hidden in a document (`INJECTION-TEST-0001`) | `b-004` | `eval:adversarial`, `gate:system_prompt_or_injection` |
| An inference-only analysis per tenant | `a-006`, `b-006` | `eval:pii_inference`, `gate:inference_only` |
| A contact list (seeded PII) per tenant | `a-007`, `b-007` | `eval:pii_inference`, `gate:pii` |
| A canary per tenant | `a-005`, `b-005` | `tests/isolation/` |
| The same topics with different facts per tenant | expenses, payment terms, IT support | `eval:overlap` |

`tests/data/test_corpus.py` checks the corpus on every PR.

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Data owner(s) | | | |
