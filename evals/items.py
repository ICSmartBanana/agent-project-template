"""Load every eval set into one list of EvalItem, and define the frozen regression subset."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.corpus import tenants

SETS_DIR = Path(__file__).resolve().parent / "sets"
LONG_PADDING = (
    "I have been reading through a lot of material this week about how our internal processes "
    "work, including approvals, payments and month-end, and I want to make sure I understand "
    "the timetable properly before I start covering for a colleague who is going on leave "
    "next week. "
) * 6

NOT_ANSWERED = ["no_information", "out_of_scope", "declined"]
_WAIT_RE = re.compile(r"\bwait\b", re.IGNORECASE)


def question_problems(question: str, keys: list[str]) -> list[str]:
    """Quality rules for a generated golden question. Empty list means it is acceptable."""
    problems = []
    if "\n" in question:
        problems.append("contains a line break (more than just the question)")
    if _WAIT_RE.search(question):
        problems.append("contains drafting text such as 'Wait'")
    if len(question) > 300:
        problems.append("longer than 300 characters")
    if not question.rstrip().endswith("?"):
        problems.append("does not end with a question mark")
    problems += [f"contains the answer value {k!r}" for k in keys if k.lower() in question.lower()]
    return problems


@dataclass(frozen=True)
class EvalItem:
    id: str
    suite: str
    tenant_id: str
    question: str
    history: list[dict[str, str]] = field(default_factory=list)
    must_include: list[list[str]] = field(default_factory=list)
    must_not_include: list[str] = field(default_factory=list)
    expected_doc_ids: list[str] = field(default_factory=list)
    expect_outcome: list[str] | None = None


def _yaml(name: str) -> Any:
    return yaml.safe_load((SETS_DIR / name).read_text(encoding="utf-8"))


def golden() -> list[EvalItem]:
    path = SETS_DIR / "golden.jsonl"
    if not path.exists():
        return []
    return [
        EvalItem(suite="golden", **json.loads(line))
        for line in path.read_text("utf-8").splitlines()
    ]


def overlap() -> list[EvalItem]:
    items = []
    for topic, questions in _yaml("overlap.yaml").items():
        for qi, q in enumerate(questions, 1):
            for tid in tenants():
                if tid in q:
                    items.append(
                        EvalItem(
                            id=f"overlap-{topic}-{qi:02d}-{tid}",
                            suite="overlap",
                            tenant_id=tid,
                            question=q["question"],
                            expect_outcome=["answered"],
                            **q[tid],
                        )
                    )
    return items


def redteam() -> list[EvalItem]:
    src = _yaml("redteam.yaml")
    clients = tenants()
    items: list[EvalItem] = []
    for asker in clients:
        n = 0
        for other in (c for c in clients if c != asker):
            for tpl in src["leakage_templates"]:
                n += 1
                o = clients[other]
                name = o.identifiers[0] if o.identifiers else o.display_name
                q = tpl.format(other=name, other_display=o.display_name)
                items.append(EvalItem(f"leakage-{asker}-{n:02d}", "leakage", asker, q))
        for q in src["leakage_untargeted"]:
            n += 1
            items.append(EvalItem(f"leakage-{asker}-{n:02d}", "leakage", asker, q))
        for i, q in enumerate(src["pii_inference"].get(asker, []), 1):
            items.append(EvalItem(f"pii-{asker}-{i:02d}", "pii_inference", asker, q))
        for i, q in enumerate(src["system_prompt_attacks"], 1):
            items.append(
                EvalItem(
                    f"adv-sysprompt-{asker}-{i}",
                    "adversarial",
                    asker,
                    q,
                    expect_outcome=NOT_ANSWERED,
                )
            )
        for i, q in enumerate(src["out_of_scope"], 1):
            items.append(
                EvalItem(
                    f"adv-scope-{asker}-{i}", "adversarial", asker, q, expect_outcome=NOT_ANSWERED
                )
            )
    for i, raw in enumerate(src["adversarial"], 1):
        raw = dict(raw)
        raw["question"] = raw["question"].replace("LONG_PADDING", LONG_PADDING)
        items.append(EvalItem(id=f"adv-{i:02d}-{raw['tenant_id']}", suite="adversarial", **raw))
    return items


def all_items() -> list[EvalItem]:
    return golden() + overlap() + redteam()


def regression_ids() -> set[str]:
    path = SETS_DIR / "regression.txt"
    return set(path.read_text("utf-8").split()) if path.exists() else set()


def select(suite: str) -> list[EvalItem]:
    items = all_items()
    if suite == "all":
        return items
    if suite == "regression":
        ids = regression_ids()
        return [i for i in items if i.id in ids]
    return [i for i in items if i.suite == suite]
