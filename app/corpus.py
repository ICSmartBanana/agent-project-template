"""The tenant list (data/tenants.yaml) and the knowledge-base documents (data/corpus/).

The tenant list is data, not code: add a client by adding it to data/tenants.yaml and a folder of
documents under data/corpus/<tenant_id>/. Each document is Markdown with YAML front matter:

    doc_id, tenant_id, title, doc_type, data_class, status, effective_date,
    supersedes / contradicts (optional), keys (the values an answer would quote)

`keys` lets the eval gates recognise another tenant's facts in an answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.config import REPO_ROOT

DATA_DIR = REPO_ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
# Fixed id of the knowledge base every client tenant can read. The database policy uses it too.
SHARED_TENANT = "shared"
DATA_CLASSES = ("public", "insight", "inference_only", "pii")
STATUSES = ("current", "superseded")


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    display_name: str
    identifiers: tuple[str, ...]
    canary: str


@dataclass(frozen=True)
class Document:
    path: Path
    doc_id: str
    tenant_id: str
    title: str
    doc_type: str
    data_class: str
    status: str
    effective_date: str
    body: str
    keys: tuple[str, ...] = ()
    supersedes: str | None = None
    contradicts: str | None = None
    meta: dict[str, Any] = field(default_factory=dict, compare=False)


@lru_cache(maxsize=1)
def tenants() -> dict[str, Tenant]:
    """Client tenants, in file order."""
    raw = yaml.safe_load((DATA_DIR / "tenants.yaml").read_text(encoding="utf-8"))
    return {
        tid: Tenant(tid, t["display_name"], tuple(t.get("identifiers") or ()), t["canary"])
        for tid, t in raw["tenants"].items()
    }


def parse(path: Path) -> tuple[dict[str, Any], str]:
    _, meta, body = path.read_text(encoding="utf-8").split("---\n", 2)
    data: dict[str, Any] = yaml.safe_load(meta)
    return data, body


def load(path: Path) -> Document:
    m, body = parse(path)
    return Document(
        path=path,
        doc_id=m["doc_id"],
        tenant_id=m["tenant_id"],
        title=m["title"],
        doc_type=m["doc_type"],
        data_class=m["data_class"],
        status=m["status"],
        effective_date=str(m["effective_date"]),
        body=body,
        keys=tuple(str(k) for k in m.get("keys") or ()),
        supersedes=m.get("supersedes"),
        contradicts=m.get("contradicts"),
        meta=m,
    )


def corpus_files() -> list[Path]:
    return sorted(CORPUS_DIR.rglob("*.md"))


@lru_cache(maxsize=1)
def documents() -> tuple[Document, ...]:
    return tuple(load(p) for p in corpus_files())


def documents_of(tenant_id: str) -> list[Document]:
    return [d for d in documents() if d.tenant_id == tenant_id]
