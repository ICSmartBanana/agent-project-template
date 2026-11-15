"""The knowledge-base corpus is well formed and safe to ingest (offline, no database).

Run after every change to data/: front matter is valid, each tenant's canary sits in exactly one
of its own documents, no document names another tenant, seeded PII appears only in its own
tenant's contact lists (pii class), and every `keys` value is quoted verbatim in its document.
"""

from __future__ import annotations

import json

import pytest

from app.config import REPO_ROOT
from app.corpus import DATA_CLASSES, SHARED_TENANT, STATUSES, Document, documents, tenants

DOCS = documents()
REGISTRY: dict[str, list[dict[str, str]]] = json.loads(
    (REPO_ROOT / "data" / "pii_registry.json").read_text("utf-8")
)


@pytest.mark.parametrize("doc", DOCS, ids=[d.doc_id for d in DOCS])
def test_front_matter_is_valid(doc: Document) -> None:
    assert doc.tenant_id in {*tenants(), SHARED_TENANT}, "tenant not in data/tenants.yaml"
    assert doc.path.parent.name == doc.tenant_id, "file is in another tenant's folder"
    assert doc.data_class in DATA_CLASSES
    assert doc.status in STATUSES
    ids = {d.doc_id for d in DOCS if d.tenant_id == doc.tenant_id}
    for ref in (doc.supersedes, doc.contradicts):
        assert ref is None or ref in ids, f"{ref} is not a document of {doc.tenant_id}"


@pytest.mark.parametrize("doc", DOCS, ids=[d.doc_id for d in DOCS])
def test_keys_are_quoted_verbatim(doc: Document) -> None:
    assert [k for k in doc.keys if k not in doc.body] == []


def test_doc_ids_are_unique() -> None:
    ids = [d.doc_id for d in DOCS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("tenant", list(tenants()))
def test_canary_is_in_exactly_one_own_document(tenant: str) -> None:
    canary = tenants()[tenant].canary
    holders = [d for d in DOCS if canary in d.body]
    assert len(holders) == 1 and holders[0].tenant_id == tenant


@pytest.mark.parametrize("doc", DOCS, ids=[d.doc_id for d in DOCS])
def test_no_document_names_another_tenant(doc: Document) -> None:
    others = [t for tid, t in tenants().items() if tid != doc.tenant_id]
    named = [i for t in others for i in t.identifiers if i in doc.body]
    assert named == []


def test_seeded_pii_only_in_own_contact_lists() -> None:
    misplaced = [
        (d.doc_id, item["value"])
        for owner, items in REGISTRY.items()
        for item in items
        for d in DOCS
        if item["value"] in d.body and (d.tenant_id != owner or d.data_class != "pii")
    ]
    assert misplaced == []


def test_registry_tenants_are_known() -> None:
    assert set(REGISTRY) <= set(tenants())
