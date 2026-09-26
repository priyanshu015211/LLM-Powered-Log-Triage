from src.preprocessing.parsers import parse_line
from src.preprocessing.ingestion import generate_sample_dataset


def test_parse_bracket_format_still_works():
    line = "2026-09-20 10:30:00 [ERROR] api: Database connection timeout"
    event = parse_line("test.log", 1, line)
    assert event.severity == "ERROR"
    assert event.service == "api"
    assert "timeout" in event.message.lower()
    assert event.log_format == "bracket"


def test_parse_syslog_line():
    line = "Sep 20 08:01:03 10.0.0.11 ERROR payment-service[4213]: failed to connect to auth-service at 10.0.0.21: timeout after 342ms"
    event = parse_line("test.log", 1, line)
    assert event.service == "payment-service"
    assert event.severity == "ERROR"
    assert event.pid == "4213"


def test_parse_json_line():
    line = '{"level": "ERROR", "msg": "payment declined for order ORD-1234", "service": "payment-service", "timestamp": "2026-09-20T08:01:03Z", "host": "10.0.0.12"}'
    event = parse_line("test.jsonl", 1, line)
    assert event.severity == "ERROR"
    assert event.service == "payment-service"


def test_sample_dataset_generation(tmp_path):
    files = generate_sample_dataset(out_dir=tmp_path, n_per_format=10)
    assert len(files) == 5  # bracket, syslog, apache, json, kv
    for f in files:
        assert f.exists() and f.stat().st_size > 0
