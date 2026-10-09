from __future__ import annotations

from typing import Any

import networkx as nx


def extract_temporal_features(
    graph: nx.DiGraph,
) -> list[dict[str, Any]]:
    """Extract temporal features from a temporal event graph."""

    features: list[dict[str, Any]] = []

    for source, target, data in graph.edges(data=True):
        time_delta = data.get("time_delta_seconds")

        features.append(
            {
                "source_event": source,
                "target_event": target,
                "time_delta_seconds": time_delta,
                "temporal_proximity": (
                    1.0 / (1.0 + time_delta)
                    if time_delta is not None and time_delta >= 0
                    else 0.0
                ),
            }
        )

    return features


def extract_dependency_features(
    graph: nx.DiGraph,
) -> dict[str, dict[str, int]]:
    """Extract structural dependency features for each service."""

    features: dict[str, dict[str, int]] = {}

    for service in graph.nodes:
        features[service] = {
            "upstream_count": graph.in_degree(service),
            "downstream_count": graph.out_degree(service),
        }

    return features


def extract_propagation_features(
    propagation_paths: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract features from detected propagation paths."""

    features: list[dict[str, Any]] = []

    for path in propagation_paths:
        features.append(
            {
                "source_service": path["source_service"],
                "target_service": path["target_service"],
                "propagation_delay_seconds": path.get(
                    "time_delta_seconds"
                ),
                "hop_count": path.get("hop_count", 0),
            }
        )

    return features