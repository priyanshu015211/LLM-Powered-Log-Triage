"""
Log ingestion (Phase 1: "Add ingestion" -> "Multi-format ingestion").

Discovers raw log files, and — since data/raw/ is empty until the team
plugs in a real dataset — generates a small synthetic multi-format sample
set so the pipeline is runnable and testable immediately.
"""

from __future__ import annotations

import json as _json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, List

from src import config


def iter_raw_lines(path: Path) -> Iterator[tuple[int, str]]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if line.strip():
                yield i, line


def discover_log_files(directory: Path, patterns: tuple[str, ...] = ("*.log", "*.txt", "*.json", "*.jsonl")) -> List[Path]:
    files: List[Path] = []
    for pattern in patterns:
        files.extend(sorted(directory.glob(pattern)))
    return files


def load_dataset(directory: Path | None = None) -> List[Path]:
    directory = directory or config.RAW_LOG_DIR
    files = discover_log_files(directory)
    if not files:
        files = discover_log_files(config.SAMPLE_LOG_DIR)
    return files


# ---------------------------------------------------------------------------
# Synthetic multi-format sample dataset
# Real dataset to consider: Loghub (https://github.com/logpai/loghub)
# ---------------------------------------------------------------------------

_SERVICES = ["auth-service", "payment-service", "order-service", "inventory-service", "gateway"]
_HOSTS = ["10.0.0.11", "10.0.0.12", "10.0.0.13", "10.0.0.21", "10.0.0.22"]

_BRACKET_TEMPLATES = [
    ("INFO", "user logged in successfully"),
    ("WARN", "connection pool approaching capacity"),
    ("ERROR", "Connection failed"),
    ("ERROR", "Database connection timeout"),
    ("CRITICAL", "out of memory, restarting worker"),
]

_SYSLOG_TEMPLATES = [
    ("INFO", "{service}[{pid}]: request completed in {ms}ms status={status}"),
    ("WARN", "{service}[{pid}]: connection pool at {pct}% capacity"),
    ("ERROR", "{service}[{pid}]: failed to connect to {dep} at {ip}: timeout after {ms}ms"),
    ("ERROR", "{service}[{pid}]: database query failed: deadlock detected on table orders"),
    ("CRITICAL", "{service}[{pid}]: out of memory, restarting worker"),
    ("INFO", "{service}[{pid}]: health check passed"),
]

_APACHE_TEMPLATE = '{ip} - - [{ts}] "GET /api/v1/{resource} HTTP/1.1" {status} {bytes}'

_JSON_TEMPLATES = [
    {"level": "INFO", "msg": "user {user_id} logged in", "service": "auth-service"},
    {"level": "ERROR", "msg": "payment declined for order {order_id}: insufficient funds", "service": "payment-service"},
    {"level": "WARN", "msg": "retrying inventory lookup for sku {sku}", "service": "inventory-service"},
    {"level": "ERROR", "msg": "upstream gateway returned 502 for {ip}", "service": "gateway"},
]

_KV_TEMPLATE = 'ts={ts} level={level} service={service} host={ip} msg="{msg}"'


def _rand_ts(base: datetime, i: int) -> datetime:
    return base + timedelta(seconds=i * random.randint(1, 8))


def generate_sample_dataset(out_dir: Path | None = None, n_per_format: int = 60, seed: int = 42) -> List[Path]:
    random.seed(seed)
    out_dir = out_dir or config.SAMPLE_LOG_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    base_time = datetime(2026, 9, 20, 8, 0, 0)
    written: List[Path] = []

    # bracket format (matches the existing log_preprocessor's expected shape)
    bracket_path = out_dir / "app_bracket.log"
    with open(bracket_path, "w") as f:
        for i in range(n_per_format):
            level, msg = random.choice(_BRACKET_TEMPLATES)
            ts = _rand_ts(base_time, i)
            service = random.choice(_SERVICES)
            f.write(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {service}: {msg}\n")
    written.append(bracket_path)

    # syslog-style
    syslog_path = out_dir / "app_syslog.log"
    with open(syslog_path, "w") as f:
        for i in range(n_per_format):
            level, tmpl = random.choice(_SYSLOG_TEMPLATES)
            ts = _rand_ts(base_time, i)
            line = tmpl.format(
                service=random.choice(_SERVICES), pid=random.randint(1000, 9999),
                ms=random.randint(5, 4000), status=random.choice([200, 200, 200, 500, 503]),
                pct=random.randint(60, 99), dep=random.choice(_SERVICES), ip=random.choice(_HOSTS),
            )
            f.write(f"{ts.strftime('%b %d %H:%M:%S')} {random.choice(_HOSTS)} {level} {line}\n")
    written.append(syslog_path)

    # Apache-access-style
    apache_path = out_dir / "gateway_access.log"
    with open(apache_path, "w") as f:
        for i in range(n_per_format):
            ts = _rand_ts(base_time, i)
            line = _APACHE_TEMPLATE.format(
                ip=random.choice(_HOSTS), ts=ts.strftime("%d/%b/%Y:%H:%M:%S +0000"),
                resource=random.choice(["orders", "users", "inventory", "payments"]),
                status=random.choice([200, 201, 400, 404, 500, 502]), bytes=random.randint(120, 15000),
            )
            f.write(line + "\n")
    written.append(apache_path)

    # JSON-lines
    json_path = out_dir / "services.jsonl"
    with open(json_path, "w") as f:
        for i in range(n_per_format):
            ts = _rand_ts(base_time, i)
            rec = dict(random.choice(_JSON_TEMPLATES))
            rec["msg"] = rec["msg"].format(
                user_id=random.randint(1000, 9999), order_id=f"ORD-{random.randint(10000,99999)}",
                sku=f"SKU-{random.randint(100,999)}", ip=random.choice(_HOSTS),
            )
            rec["timestamp"] = ts.isoformat() + "Z"
            rec["host"] = random.choice(_HOSTS)
            f.write(_json.dumps(rec) + "\n")
    written.append(json_path)

    # key=value
    kv_path = out_dir / "infra_metrics.log"
    with open(kv_path, "w") as f:
        for i in range(n_per_format):
            ts = _rand_ts(base_time, i)
            level, tmpl = random.choice(_SYSLOG_TEMPLATES)
            msg = tmpl.format(
                service=random.choice(_SERVICES), pid=random.randint(1000, 9999),
                ms=random.randint(5, 4000), status=random.choice([200, 500]),
                pct=random.randint(60, 99), dep=random.choice(_SERVICES), ip=random.choice(_HOSTS),
            )
            f.write(_KV_TEMPLATE.format(
                ts=ts.isoformat(), level=level, service=random.choice(_SERVICES),
                ip=random.choice(_HOSTS), msg=msg,
            ) + "\n")
    written.append(kv_path)

    return written


if __name__ == "__main__":
    for p in generate_sample_dataset():
        print(f"wrote {p}")
