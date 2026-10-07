from __future__ import annotations

from pathlib import Path

INPUT_CONTEXT_MODEL = "gpt-4o-mini"
INPUT_CONTEXT_MODEL_LABEL = "GPT-4o Mini"
INPUT_CONTEXT_DIR = Path(__file__).resolve().parent.parent / "content" / "input_context"

MARKETING_PROMPT = (
    "Write 3 punchy taglines for our new eco-friendly sneaker launch, targeting Gen Z."
)

CODE_PROMPT = (
    "Write a Python function to reconcile duplicate customer records in a Postgres table"
)

STRIDECO_CONTEXT = """
# StrideCo brand guidelines

BRAND CONTEXT DOCUMENT — StrideCo Footwear
Internal Reference: Marketing Guidelines v4.2

COMPANY BACKGROUND
StrideCo was founded in 2011 in Bengaluru as a small-batch running shoe label. Over the past decade we have grown from a single retail outlet to a pan-India direct-to-consumer brand with an active customer base of approximately 1.2 million. Our early positioning centred on performance running, but market research conducted across 2019-2022 showed a substantial shift in our buyer base toward lifestyle and casual wear.

TARGET DEMOGRAPHIC
Our core segment is urban consumers aged 18-27, concentrated in Tier 1 and Tier 2 cities. Secondary segment is 28-35, skewing toward premium purchases. Survey data indicates our Gen Z buyers index heavily on social proof, creator partnerships, and visual-first discovery. They are notably resistant to conventional advertising language and respond best to copy that reads as conversational rather than promotional.

BRAND VOICE
Our tone is confident but never boastful. We avoid superlatives. We avoid exclamation marks. We favour short declarative sentences over elaborate constructions. Historically our most successful campaigns have used understatement rather than hyperbole.

PAST CAMPAIGN PERFORMANCE
The 2023 "Everyday Distance" campaign delivered a 34% lift in engagement. The 2024 "Built Here" campaign underperformed, with post-campaign brand tracking suggesting the messaging read as overly patriotic and alienated a portion of our urban base.

COMPETITOR POSITIONING
Our primary competitors occupy the performance-athletic space with heavy sponsorship spend. We deliberately position away from this, focusing on daily wear rather than athletic achievement.

*** COMPLIANCE — MANDATORY ***
Following a legal review in Q1, StrideCo marketing copy may NOT use the words "sustainable", "green", "eco-friendly", or "carbon neutral" in any consumer-facing material. Our legal team flagged these as unsubstantiated greenwashing claims under advertising standards guidance. Approved alternative phrasing: "planet-conscious" or "lower-impact". This restriction is non-negotiable and applies to all campaigns.
""".strip()

LEDGER_CONTEXT = """
# Ledger customer-data service

CODEBASE CONTEXT — Ledger Systems, customer-data service
File: customer_utils.py (excerpt)

import logging
import hashlib
from datetime import datetime, timezone
from typing import Optional, Iterable
from ledger.db import session_scope
from ledger.models import CustomerRecord, AuditEntry
from ledger.errors import ReconciliationError

logger = logging.getLogger(__name__)
DEFAULT_BATCH_SIZE = 500
AUDIT_SOURCE = "customer_utils"

def _utcnow():
    return datetime.now(timezone.utc)

def normalise_email(raw: str) -> str:
    if raw is None:
        return ""
    return raw.strip().lower()

def normalise_phone(raw: str) -> str:
    if raw is None:
        return ""
    digits = "".join(c for c in raw if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

def fingerprint(record) -> str:
    parts = [
        normalise_email(record.email),
        normalise_phone(record.phone),
        (record.postcode or "").strip().upper(),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

def write_audit(action: str, target, detail: Optional[str] = None):
    with session_scope() as s:
        s.add(AuditEntry(
            action=action,
            source=AUDIT_SOURCE,
            target_ref=target,
            detail=detail,
            created_at=_utcnow(),
        ))

def chunked(items: Iterable, size: int = DEFAULT_BATCH_SIZE):
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch

def load_active_records(limit: Optional[int] = None):
    with session_scope() as s:
        q = s.query(CustomerRecord).filter(CustomerRecord.is_active.is_(True))
        if limit:
            q = q.limit(limit)
        return q.all()

def group_by_fingerprint(records):
    groups = {}
    for r in records:
        groups.setdefault(fingerprint(r), []).append(r)
    return {k: v for k, v in groups.items() if len(v) > 1}

def pick_survivor(duplicates):
    return sorted(duplicates, key=lambda r: r.created_at)[0]

def soft_delete(record, reason: str):
    record.is_active = False
    record.deactivated_at = _utcnow()
    record.deactivation_reason = reason

def merge_field(survivor, loser, field: str):
    if getattr(survivor, field, None) in (None, ""):
        setattr(survivor, field, getattr(loser, field, None))

*** SCHEMA NOTE — READ BEFORE WRITING QUERIES ***
This service does NOT use `.id` as the primary key on CustomerRecord. The `.id` column exists but is a legacy auto-increment field that was never backfilled after the 2023 migration and is NULL for roughly 40% of rows. The actual primary key is `.merge_id` (UUID), and every foreign key across the schema references `merge_id`, not `id`. Any join, lookup, or delete written against `.id` will appear to work in local testing and silently drop or mismatch records in production. Always use `CustomerRecord.merge_id`.
""".strip()

INPUT_CONTEXT_CASES: dict[str, dict[str, str]] = {
    "Marketing ad agency": {
        "slot": "marketing",
        "title": "Marketing",
        "prompt": MARKETING_PROMPT,
        "file": "marketing_context.txt",
        "document": STRIDECO_CONTEXT,
    },
    "Code generation": {
        "slot": "code",
        "title": "Code",
        "prompt": CODE_PROMPT,
        "file": "code_context.txt",
        "document": LEDGER_CONTEXT,
    },
}

INPUT_CONTEXT_TOPICS = set(INPUT_CONTEXT_CASES)


def document_for(topic: str) -> str:
    case = INPUT_CONTEXT_CASES[topic]
    path = INPUT_CONTEXT_DIR / case["file"]
    if path.is_file():
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    return case["document"].strip()
