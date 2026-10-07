from __future__ import annotations

from typing import Any

import networkx as nx


class PropagationAnalyzer:
    """Analyze potential incident propagation across services."""

    def __init__(
        self,
        temporal_graph: nx.DiGraph,
        dependency_graph: nx.DiGraph,
    ) -> None:
        self.temporal_graph = temporal_graph
        self.dependency_graph = dependency_graph

    def find_propagation_paths(
        self,
        max_hops: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Identify potential propagation paths using temporal and
        service dependency relationships.
        """
        propagation_paths: list[dict[str, Any]] = []

        for source_event, target_event in self.temporal_graph.edges:
            source_service = self.temporal_graph.nodes[source_event].get(
                "service"
            )
            target_service = self.temporal_graph.nodes[target_event].get(
                "service"
            )

            if not source_service or not target_service:
                continue

            if source_service == target_service:
                continue

            if not self._is_dependency_related(
                source_service,
                target_service,
            ):
                continue

            time_delta = self.temporal_graph.edges[
                source_event,
                target_event,
            ].get("time_delta_seconds")

            propagation_paths.append(
                {
                    "source_event": source_event,
                    "target_event": target_event,
                    "source_service": source_service,
                    "target_service": target_service,
                    "time_delta_seconds": time_delta,
                    "hop_count": 1,
                }
            )

        return propagation_paths

    def _is_dependency_related(
        self,
        source_service: str,
        target_service: str,
    ) -> bool:
        """Check whether two services have a dependency relationship."""

        if self.dependency_graph.has_edge(
            target_service,
            source_service,
        ):
            return True

        if self.dependency_graph.has_edge(
            source_service,
            target_service,
        ):
            return True

        return False