from __future__ import annotations

from datetime import datetime
from typing import Any

import networkx as nx


class TemporalEventGraph:
    """Build a directed graph representing temporal relationships between events."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    def build(self, events: list[dict[str, Any]]) -> nx.DiGraph:
        """
        Build a temporal event graph from structured log events.

        Events are sorted chronologically. Each event becomes a node, and
        consecutive events are connected by a directed temporal edge.
        """
        self.graph.clear()

        if not events:
            return self.graph

        sorted_events = sorted(
            events,
            key=lambda event: event["timestamp"],
        )

        for index, event in enumerate(sorted_events):
            event_id = event.get("event_id", f"E{index}")

            self.graph.add_node(
                event_id,
                timestamp=event["timestamp"],
                level=event.get("level"),
                service=event.get("service"),
                message=event.get("message"),
            )

        for current, following in zip(sorted_events, sorted_events[1:]):
            current_id = current.get(
                "event_id",
                f"E{sorted_events.index(current)}",
            )
            following_id = following.get(
                "event_id",
                f"E{sorted_events.index(following)}",
            )

            time_delta = (
                following["timestamp"] - current["timestamp"]
            ).total_seconds()

            self.graph.add_edge(
                current_id,
                following_id,
                time_delta_seconds=time_delta,
                relationship="temporal_precedence",
            )

        return self.graph

    def get_graph(self) -> nx.DiGraph:
        """Return the constructed temporal graph."""
        return self.graph