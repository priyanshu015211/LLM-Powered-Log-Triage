"""
Semantic clustering (Phase 2: "Semantic clustering").

Groups embedded log events into semantic groups that Phase 3 (temporal +
dependency graph) will build nodes from, and that the future evidence
builder (Phase 4) packages for the LLM instead of raw individual log lines.

Three algorithms, configurable in src/config.py:
  - agglomerative : cosine-distance threshold, no fixed k — DEFAULT, since
                     it only needs scikit-learn (already a hard dependency)
  - kmeans        : fixed k, fast, useful for ablations
  - hdbscan       : density-based, finds natural cluster count, flags noise
                     (-1) — requires uncommenting `hdbscan` in requirements.txt
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

import numpy as np

from src import config
from src.preprocessing.schema import LogEvent


def _cluster_hdbscan(embeddings: np.ndarray) -> np.ndarray:
    import hdbscan

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=config.HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=config.HDBSCAN_MIN_SAMPLES,
        metric="euclidean",  # embeddings are pre-normalized, so euclidean ~ cosine
    )
    return clusterer.fit_predict(embeddings)


def _cluster_kmeans(embeddings: np.ndarray) -> np.ndarray:
    from sklearn.cluster import KMeans

    k = min(config.KMEANS_N_CLUSTERS, max(1, len(embeddings)))
    model = KMeans(n_clusters=k, random_state=config.RANDOM_SEED, n_init="auto")
    return model.fit_predict(embeddings)


def _cluster_agglomerative(embeddings: np.ndarray) -> np.ndarray:
    from sklearn.cluster import AgglomerativeClustering

    model = AgglomerativeClustering(
        n_clusters=None, distance_threshold=config.AGGLOMERATIVE_DISTANCE_THRESHOLD,
        metric="cosine", linkage="average",
    )
    return model.fit_predict(embeddings)


_ALGORITHMS = {
    "hdbscan": _cluster_hdbscan,
    "kmeans": _cluster_kmeans,
    "agglomerative": _cluster_agglomerative,
}


def cluster_embeddings(embeddings: np.ndarray, algorithm: Optional[str] = None) -> np.ndarray:
    if len(embeddings) == 0:
        return np.array([], dtype=int)
    algorithm = algorithm or config.CLUSTERING_ALGORITHM
    try:
        return _ALGORITHMS[algorithm](embeddings)
    except ImportError:
        print(f"[clustering] '{algorithm}' unavailable, falling back to agglomerative.")
        return _cluster_agglomerative(embeddings)


def assign_clusters(events: list[LogEvent], embeddings: np.ndarray, algorithm: Optional[str] = None) -> list[LogEvent]:
    labels = cluster_embeddings(embeddings, algorithm=algorithm)
    for event, label in zip(events, labels):
        event.semantic_cluster = int(label)
    return events


def summarize_clusters(events: list[LogEvent]) -> list[dict]:
    """Builds the "Semantic Groups" hand-off artifact — one entry per
    cluster with representative template, member count, services/hosts,
    severity mix and time span, ready for the temporal/dependency graph and
    the evidence builder to consume instead of raw log lines."""
    groups: dict[int, list[LogEvent]] = defaultdict(list)
    for e in events:
        groups[e.semantic_cluster].append(e)

    summaries = []
    for cluster_id, members in sorted(groups.items(), key=lambda kv: (kv[0] == -1, -len(kv[1]))):
        templates: dict[str, int] = defaultdict(int)
        for m in members:
            templates[m.template] += 1
        representative_template = max(templates.items(), key=lambda kv: kv[1])[0]

        timestamps = sorted(m.timestamp_iso for m in members if m.timestamp_iso)
        severities: dict[str, int] = defaultdict(int)
        for m in members:
            severities[m.severity] += 1

        summaries.append({
            "cluster_id": cluster_id,
            "is_noise": cluster_id == -1,
            "size": len(members),
            "representative_template": representative_template,
            "distinct_templates": len(templates),
            "services": sorted({m.service for m in members if m.service}),
            "hosts": sorted({m.host for m in members if m.host}),
            "event_types": sorted({m.event_type for m in members if m.event_type}),
            "severity_distribution": dict(severities),
            "time_span": {
                "start": timestamps[0] if timestamps else None,
                "end": timestamps[-1] if timestamps else None,
            },
            "event_ids": [m.event_id for m in members],
        })
    return summaries
