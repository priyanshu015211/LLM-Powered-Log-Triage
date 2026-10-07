from __future__ import annotations

from typing import Iterable

import networkx as nx


class ServiceDependencyGraph:
    """Represent dependencies between services as a directed graph."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    def build(
        self,
        dependencies: Iterable[tuple[str, str]],
    ) -> nx.DiGraph:
        """
        Build a service dependency graph.

        Each dependency is represented as:
            (service, dependency)

        For example:
            ("payment", "database")

        creates:
            payment -> database
        """
        self.graph.clear()

        for service, dependency in dependencies:
            self.graph.add_edge(
                service,
                dependency,
                relationship="service_dependency",
            )

        return self.graph

    def get_graph(self) -> nx.DiGraph:
        """Return the constructed dependency graph."""
        return self.graph