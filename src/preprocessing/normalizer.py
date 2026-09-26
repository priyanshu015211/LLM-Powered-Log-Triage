"""
Normalization (Phase 1, extends "Log normalization" already listed as
implemented in the README) — brings every parser's output into the
canonical schema: ISO-8601 UTC timestamps, a 5-level severity scale,
cleaned host/service names, and extracted entities (IPs, status codes,
latency, error codes) that later phases (evidence builder, LLM integration)
can read directly instead of re-parsing message strings.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser

from src import config
from src.preprocessing.schema import LogEvent, Severity


_IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_STATUS_RE = re.compile(r"\b([1-5]\d{2})\b(?=\s*(?:\(|bytes|$))")
_MS_RE = re.compile(r"\b(\d+)\s*ms\b", re.IGNORECASE)
_ERRCODE_RE = re.compile(r"\b(ERR|ERROR)[_\-]?(\d{2,5})\b", re.IGNORECASE)

# Strips a leading "service[pid]:" prefix that some formats embed inside the
# message body itself (e.g. key=value logs) so identical events collapse to
# the same message/template regardless of which parser produced them.
_EMBEDDED_PREFIX_RE = re.compile(r"^[\w\-.]+\[\d+\]:\s*")


def normalize_timestamp(ts_raw: Optional[str], reference_year: int = 2026) -> Optional[str]:
    """Parses a variety of timestamp formats into ISO-8601 UTC. Syslog
    timestamps ('Sep 20 08:01:03') have no year, so a reference year is
    injected — swap this for file mtime or a known collection window in
    production."""
    if not ts_raw:
        return None

    candidate = ts_raw
    m = re.match(r"^(\d{1,2}/\w{3}/\d{4}):(\d{2}:\d{2}:\d{2}\s*[+-]\d{4})$", ts_raw)
    if m:
        candidate = f"{m.group(1)} {m.group(2)}"

    try:
        dt = dateutil_parser.parse(candidate, default=datetime(reference_year, 1, 1))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        return None


def normalize_severity(sev_raw: Optional[str]) -> str:
    if not sev_raw:
        return Severity.UNKNOWN.value
    return config.SEVERITY_ALIASES.get(sev_raw.strip().upper(), Severity.UNKNOWN.value)


def normalize_host(host_raw: Optional[str]) -> Optional[str]:
    return host_raw.strip().strip(",") if host_raw else None


def normalize_service(service_raw: Optional[str]) -> Optional[str]:
    return service_raw.strip().lower().replace("_", "-") if service_raw else None


def strip_embedded_prefix(message: str) -> str:
    return _EMBEDDED_PREFIX_RE.sub("", message)


def extract_entities(message: str) -> dict:
    entities: dict = {}
    ips = _IP_RE.findall(message)
    if ips:
        entities["ips"] = sorted(set(ips))
    status_match = _STATUS_RE.search(message)
    if status_match:
        entities["status_code"] = int(status_match.group(1))
    ms_match = _MS_RE.search(message)
    if ms_match:
        entities["latency_ms"] = int(ms_match.group(1))
    err_match = _ERRCODE_RE.search(message)
    if err_match:
        entities["error_code"] = err_match.group(0).upper()
    return entities


def normalize_event(event: LogEvent) -> LogEvent:
    event.timestamp_iso = normalize_timestamp(event.timestamp_raw)
    event.severity = normalize_severity(event.severity)
    event.host = normalize_host(event.host)
    event.service = normalize_service(event.service)
    event.message = strip_embedded_prefix(event.message)
    event.entities = extract_entities(event.message)
    return event


def normalize_events(events: list[LogEvent]) -> list[LogEvent]:
    return [normalize_event(e) for e in events]
