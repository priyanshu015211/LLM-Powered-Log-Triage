"""
Multi-format log parsing (Phase 1: "Improve parser" -> "Multi-format ingestion").

Extends the existing single-format parser in `log_preprocessor.py` (the
"[LEVEL] service: message" bracket format) rather than replacing it — that
function stays exactly as-is and its tests keep passing. This module adds
format *detection* on top, so any of several real-world log shapes route to
the right parser and normalize into the same `LogEvent` schema.

Add a new source format by writing a `_try_parse_X(line)` function and
registering it in `PARSERS` (order = priority; first match wins).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Callable, Optional

from src.preprocessing.log_preprocessor import extract_log_fields
from src.preprocessing.schema import LogEvent, LogFormat, Severity


# ---------------------------------------------------------------------------
# Format 0: the existing bracket format, reused as-is
# "YYYY-MM-DD HH:MM:SS [LEVEL] service: message"
# ---------------------------------------------------------------------------

def _try_parse_bracket(line: str) -> Optional[dict]:
    fields = extract_log_fields(line)
    if fields is None:
        return None
    ts = fields.get("timestamp")
    return {
        "ts": ts.isoformat() if ts is not None else None,
        "host": None,
        "severity": fields.get("level", "").upper(),
        "service": fields.get("service"),
        "message": fields.get("message", line),
        "log_format": LogFormat.BRACKET.value,
    }


# ---------------------------------------------------------------------------
# Format 1: syslog-style
# "Sep 20 08:01:03 host SEVERITY service[pid]: message"
# ---------------------------------------------------------------------------

_SYSLOG_RE = re.compile(
    r"^(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<severity>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|CRIT|FATAL)\s+"
    r"(?P<service>[\w\-.]+)\[(?P<pid>\d+)\]:\s*"
    r"(?P<message>.*)$"
)


def _try_parse_syslog(line: str) -> Optional[dict]:
    m = _SYSLOG_RE.match(line)
    if not m:
        return None
    d = m.groupdict()
    d["log_format"] = LogFormat.SYSLOG.value
    return d


# ---------------------------------------------------------------------------
# Format 2: Apache/nginx-style access log
# ---------------------------------------------------------------------------

_APACHE_RE = re.compile(
    r'^(?P<host>\S+)\s+\S+\s+\S+\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)'
)


def _try_parse_apache(line: str) -> Optional[dict]:
    m = _APACHE_RE.match(line)
    if not m:
        return None
    d = m.groupdict()
    status = int(d["status"])
    severity = Severity.ERROR.value if status >= 500 else (
        Severity.WARN.value if status >= 400 else Severity.INFO.value
    )
    d["severity"] = severity
    d["service"] = "gateway"
    d["message"] = f'{d["request"]} -> {d["status"]} ({d["bytes"]} bytes)'
    d["log_format"] = LogFormat.APACHE_ACCESS.value
    return d


# ---------------------------------------------------------------------------
# Format 3: JSON lines
# ---------------------------------------------------------------------------

def _try_parse_json(line: str) -> Optional[dict]:
    stripped = line.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return {
        "ts": obj.get("timestamp") or obj.get("time") or obj.get("ts"),
        "host": obj.get("host") or obj.get("hostname"),
        "severity": str(obj.get("level") or obj.get("severity") or "").upper(),
        "service": obj.get("service") or obj.get("app"),
        "message": obj.get("msg") or obj.get("message") or json.dumps(obj),
        "log_format": LogFormat.JSON_LOG.value,
    }


# ---------------------------------------------------------------------------
# Format 4: key=value
# ---------------------------------------------------------------------------

_KV_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')


def _try_parse_kv(line: str) -> Optional[dict]:
    pairs = dict(_KV_RE.findall(line))
    if len(pairs) < 3 or "level" not in {k.lower() for k in pairs}:
        return None
    norm = {k.lower(): v.strip('"') for k, v in pairs.items()}
    return {
        "ts": norm.get("ts") or norm.get("timestamp"),
        "host": norm.get("host") or norm.get("ip"),
        "severity": norm.get("level", "").upper(),
        "service": norm.get("service"),
        "message": norm.get("msg", line),
        "log_format": LogFormat.KEY_VALUE.value,
    }


def _fallback_plain_text(line: str) -> dict:
    return {
        "ts": None, "host": None,
        "severity": Severity.UNKNOWN.value,
        "service": None, "message": line,
        "log_format": LogFormat.PLAIN_TEXT.value,
    }


# Order matters: bracket format first since it's the "known good" existing
# parser, then most-specific-to-least-specific for the rest.
PARSERS: list[Callable[[str], Optional[dict]]] = [
    _try_parse_bracket,
    _try_parse_json,
    _try_parse_syslog,
    _try_parse_apache,
    _try_parse_kv,
]


def detect_and_parse(line: str) -> dict:
    for parser in PARSERS:
        result = parser(line)
        if result is not None:
            return result
    return _fallback_plain_text(line)


def _make_event_id(source_file: str, line_number: int, raw: str) -> str:
    return hashlib.sha1(f"{source_file}:{line_number}:{raw}".encode("utf-8")).hexdigest()[:16]


def parse_line(source_file: str, line_number: int, raw_line: str) -> LogEvent:
    parsed = detect_and_parse(raw_line)
    severity = parsed.get("severity") or Severity.UNKNOWN.value
    if severity not in {s.value for s in Severity}:
        severity = Severity.UNKNOWN.value

    return LogEvent(
        event_id=_make_event_id(source_file, line_number, raw_line),
        source_file=source_file,
        line_number=line_number,
        raw_message=raw_line,
        message=parsed.get("message", raw_line),
        timestamp_raw=parsed.get("ts"),
        host=parsed.get("host"),
        service=parsed.get("service"),
        process=parsed.get("service"),
        pid=parsed.get("pid"),
        severity=severity,
        log_format=parsed.get("log_format", LogFormat.UNKNOWN.value),
    )
