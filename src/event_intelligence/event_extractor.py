"""
Event extraction (Phase 2: "Event extraction").

1. Template mining: masks variable tokens (IPs, numbers, UUIDs, paths) so
   structurally-identical log lines collapse to the same template.
2. Coarse event-type classification from keyword rules — a cheap categorical
   signal available before semantic clustering even runs, and useful on its
   own for Phase 3's temporal/dependency graphs.

This is a lightweight Drain-inspired masking pass, not a full Drain/Spell
streaming implementation — swap in `drain3` here later if the paper's
baselines need the real algorithm; only `LogEvent.template` needs to keep
being filled.
"""

from __future__ import annotations

import re

from src import config
from src.preprocessing.schema import LogEvent


_MASK_PATTERNS = {name: re.compile(pat) for name, pat in config.TEMPLATE_MASK_PATTERNS.items()}

_EVENT_TYPE_RULES: list[tuple[str, re.Pattern]] = [
    ("connection_failure", re.compile(r"failed to connect|connection refused|timeout", re.I)),
    ("auth_event", re.compile(r"logged in|login|authentication|unauthorized", re.I)),
    ("resource_exhaustion", re.compile(r"out of memory|capacity|disk full|pool at \d+%", re.I)),
    ("db_error", re.compile(r"deadlock|query failed|database", re.I)),
    ("payment_failure", re.compile(r"payment declined|insufficient funds|charge failed", re.I)),
    ("http_error", re.compile(r"\b5\d{2}\b|\b4\d{2}\b")),
    ("health_check", re.compile(r"health check", re.I)),
    ("restart", re.compile(r"restart", re.I)),
]


def mine_template(message: str) -> str:
    template = message
    for name in ["UUID", "IP", "EMAIL", "HEX", "PATH", "NUM"]:
        template = _MASK_PATTERNS[name].sub(f"<{name}>", template)
    return template


def classify_event_type(message: str) -> str:
    for label, pattern in _EVENT_TYPE_RULES:
        if pattern.search(message):
            return label
    return "other"


def extract_event(event: LogEvent) -> LogEvent:
    event.template = mine_template(event.message)
    event.event_type = classify_event_type(event.message)
    return event


def extract_events(events: list[LogEvent]) -> list[LogEvent]:
    return [extract_event(e) for e in events]


def template_frequency(events: list[LogEvent]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for e in events:
        freq[e.template] = freq.get(e.template, 0) + 1
    return dict(sorted(freq.items(), key=lambda kv: -kv[1]))
