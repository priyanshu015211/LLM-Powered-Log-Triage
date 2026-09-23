from src.preprocessing.log_preprocessor import (
    normalize_log_line,
    extract_log_fields,
    preprocess_log,
)


def test_normalize_log_line():
    log = "  2026-09-20   10:30:00   [ERROR]   database: Connection failed  "

    result = normalize_log_line(log)

    assert result == (
        "2026-09-20 10:30:00 [ERROR] database: Connection failed"
    )


def test_extract_log_fields():
    log = (
        "2026-09-20 10:30:00 "
        "[ERROR] database: Connection failed"
    )

    result = extract_log_fields(log)

    assert result is not None
    assert result["level"] == "ERROR"
    assert result["service"] == "database"
    assert result["message"] == "Connection failed"


def test_preprocess_log():
    log = (
        "2026-09-20 10:30:00 "
        "[ERROR] api: Database connection timeout"
    )

    result = preprocess_log(log)

    assert result is not None
    assert result["service"] == "api"
    assert result["level"] == "ERROR"
