import re
from datetime import datetime


def normalize_log_line(log_line):
    """
    Normalize a raw log line by removing unnecessary whitespace
    and standardizing common log fields.
    """
    log_line = log_line.strip()
    log_line = re.sub(r"\s+", " ", log_line)

    return log_line


def extract_log_fields(log_line):
    """
    Extract basic fields from a log entry.

    Expected format:
    YYYY-MM-DD HH:MM:SS [LEVEL] SERVICE: MESSAGE
    """
    pattern = (
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} "
        r"\d{2}:\d{2}:\d{2})\s+"
        r"\[(?P<level>\w+)\]\s+"
        r"(?P<service>[\w-]+):\s*"
        r"(?P<message>.*)"
    )

    match = re.match(pattern, log_line)

    if not match:
        return None

    data = match.groupdict()

    try:
        data["timestamp"] = datetime.strptime(
            data["timestamp"],
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return None

    return data


def preprocess_log(log_line):
    """
    Normalize a raw log and extract structured information.
    """
    normalized = normalize_log_line(log_line)

    if not normalized:
        return None

    return extract_log_fields(normalized)
