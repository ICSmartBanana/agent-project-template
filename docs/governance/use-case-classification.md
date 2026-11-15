# Use-case classification: <agent name>

| | |
|---|---|
| Status | **Template: fill in before writing code** (design gate) |
| Version | 0.1 (<date>) |
| Prepared for review by | <agent owner> |
| Review due | Before the design gate, then quarterly with the regulatory register |
| Basis | EU AI Act (Reg. (EU) 2024/1689, as amended by Reg. (EU) 2026/1744), NIST AI RMF 1.0, NIST AI 600-1 |

> This is an engineering self-assessment written before coding, as the agent-standards pack requires. It is not legal advice. Before any use with real client data, someone qualified in EU AI Act compliance should confirm it. The `scaffold-agent` skill in the agent-standards plugin drafts this document from a short interview.

## 1. System description

<What the agent does, for whom, and with what data. For example: a retrieval-augmented chatbot that answers a logged-in client user's questions from that client's knowledge base plus a shared knowledge base, cites its sources, and says it doesn't know when retrieval finds nothing relevant.>

- **Users:** <professionals or consumers? which roles?>
- **Outputs:** <text answers with citations, read by a person?>
- **Actions:** <none, or list each tool and what it can change>
- **Underlying model:** <provider and model family; trained or fine-tuned by us? (usually no)>
- **Data:** <synthetic for the POC? real personal data later?>

## 2. Role under the EU AI Act

- <Provider of an AI system / deployer, with reasoning.>
- <Not a provider of a general-purpose AI model, so Chapter V duties fall on the model vendor.>

## 3. Risk-tier assessment

| Tier | Assessment | Reasoning |
|---|---|---|
| Prohibited practices (Art. 5) | <Yes/No> | |
| High risk, Annex I (product safety) | <Yes/No> | |
| High risk, Annex III | <Yes/No> | Check every Annex III area, especially critical infrastructure, employment, essential services and credit. |
| Limited risk, transparency (Art. 50) | <Yes/No> | A system that talks to people must tell them it is an AI (Art. 50(1), applies since 2 Aug 2026). |
| Minimal risk | <Yes/No> | |

**Result:** <tier>.

## 4. Obligations that follow and how we meet them

| Obligation | How we meet it | Evidence |
|---|---|---|
| Art. 50(1): tell users they are interacting with AI | Disclosure notice on every answer | `tests/api/test_api.py::test_disclosure_on_every_answer` |
| <GDPR or other data law, if real personal data> | PII masked at ingestion, output guard, trace redaction, per-client deletion | PII eval gate; data-source register |
| <Client contract terms> | Client data never used to train or fine-tune models | Model card; data-source register |

## 5. Voluntary alignment (NIST AI RMF)

The governance pack is organised as **Govern** (this document, the regulatory register, review gates), **Map** (data-source register, risk register), **Measure** (eval sets and CI gates) and **Manage** (incident process, human-oversight note).

## 6. Triggers for re-classification

Redo this assessment if any of these happens:

- the agent gets tools that write to or act on any system
- its outputs feed automatically into operational, financial or HR decisions
- it is offered to consumers or the public
- it starts making or supporting decisions about individuals
- the model provider changes, or the law or Commission guidelines change

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Agent owner | | | |
