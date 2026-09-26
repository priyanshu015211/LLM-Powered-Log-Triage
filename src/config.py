"""
Central configuration for the preprocessing + event-intelligence pipeline
(Phases 1 & 2 of the project roadmap).
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_LOG_DIR = DATA_DIR / "raw"
SAMPLE_LOG_DIR = DATA_DIR / "sample"
OUTPUT_DIR = ROOT_DIR / "outputs"

PARSED_EVENTS_PATH = OUTPUT_DIR / "parsed_events.jsonl"
NORMALIZED_EVENTS_PATH = OUTPUT_DIR / "normalized_events.jsonl"
EXTRACTED_EVENTS_PATH = OUTPUT_DIR / "extracted_events.jsonl"
EMBEDDINGS_PATH = OUTPUT_DIR / "embeddings.npy"
SEMANTIC_GROUPS_PATH = OUTPUT_DIR / "semantic_groups.json"
PIPELINE_REPORT_PATH = OUTPUT_DIR / "pipeline_report.json"

# Embeddings — sentence-transformers is already in requirements.txt
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 64

# Clustering — default to agglomerative since it only needs scikit-learn,
# which is already a hard dependency. hdbscan is commented-out/optional in
# requirements.txt; uncomment it there and set this to "hdbscan" to use it.
CLUSTERING_ALGORITHM = "agglomerative"  # "hdbscan" | "kmeans" | "agglomerative"
HDBSCAN_MIN_CLUSTER_SIZE = 5
HDBSCAN_MIN_SAMPLES = 3
KMEANS_N_CLUSTERS = 12
AGGLOMERATIVE_DISTANCE_THRESHOLD = 0.35

TEMPLATE_MASK_PATTERNS = {
    "IP": r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
    "NUM": r"\d+",
    "UUID": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
    "HEX": r"\b0x[0-9a-fA-F]+\b",
    "PATH": r"(?:/[\w\-.]+){2,}",
    "EMAIL": r"\b[\w.-]+@[\w.-]+\.\w+\b",
}

SEVERITY_CANONICAL_ORDER = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
SEVERITY_ALIASES = {
    "DEBUG": "DEBUG", "TRACE": "DEBUG",
    "INFO": "INFO", "NOTICE": "INFO",
    "WARN": "WARN", "WARNING": "WARN",
    "ERROR": "ERROR", "ERR": "ERROR",
    "CRITICAL": "CRITICAL", "CRIT": "CRITICAL", "FATAL": "CRITICAL",
    "EMERGENCY": "CRITICAL", "ALERT": "CRITICAL",
}

RANDOM_SEED = 42
