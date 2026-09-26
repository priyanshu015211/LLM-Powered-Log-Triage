"""
Canonical log schema (Phase 1: "Define common log schema").

Every raw log line — regardless of which parser handled it, including the
existing single-format `log_preprocessor.extract_log_fields` — is eventually
converted into a `LogEvent`. This is the shared contract that Phase 2
(event extraction, embeddings, clustering) and later phases (temporal graph,
evidence builder, LLM integration) all read from.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import json


class LogFormat(str, Enum):
    BRACKET = "bracket"            # the original "[LEVEL] service: message" format
    SYSLOG = "syslog"
    JSON_LOG = "json_log"
    APACHE_ACCESS = "apache_access"
    KEY_VALUE = "key_value"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class LogEvent:
    """One canonical, normalized log record."""

    event_id: str
    source_file: str
    line_number: int

    raw_message: str
    message: str
    template: Optional[str] = None

    timestamp_raw: Optional[str] = None
    timestamp_iso: Optional[str] = None

    host: Optional[str] = None
    service: Optional[str] = None
    process: Optional[str] = None
    pid: Optional[str] = None

    severity: str = Severity.UNKNOWN.value
    log_format: str = LogFormat.UNKNOWN.value
    event_type: Optional[str] = None

    entities: dict = field(default_factory=dict)

    semantic_cluster: Optional[int] = None
    embedding_index: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @staticmethod
    def from_dict(d: dict) -> "LogEvent":
        return LogEvent(**d)
