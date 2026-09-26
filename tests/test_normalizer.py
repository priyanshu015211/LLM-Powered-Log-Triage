from src.preprocessing.normalizer import (
    normalize_severity, normalize_timestamp, strip_embedded_prefix, extract_entities,
)


def test_normalize_severity_aliases():
    assert normalize_severity("WARNING") == "WARN"
    assert normalize_severity("crit") == "CRITICAL"
    assert normalize_severity(None) == "UNKNOWN"
    assert normalize_severity("bogus") == "UNKNOWN"


def test_normalize_timestamp_syslog_style():
    iso = normalize_timestamp("Sep 20 08:01:03", reference_year=2026)
    assert iso is not None and iso.startswith("2026-09-20")


def test_normalize_timestamp_apache_style():
    iso = normalize_timestamp("20/Sep/2026:08:01:03 +0000")
    assert iso is not None and iso.startswith("2026-09-20")


def test_strip_embedded_prefix_collapses_duplicate_events():
    a = strip_embedded_prefix("auth-service[4213]: health check passed")
    b = "health check passed"
    assert a == b


def test_extract_entities():
    entities = extract_entities("failed to connect to auth-service at 10.0.0.21: timeout after 342ms")
    assert entities["ips"] == ["10.0.0.21"]
    assert entities["latency_ms"] == 342
