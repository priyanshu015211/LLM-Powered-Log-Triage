"""Adapters from upstream NetworkX-style graphs to explicit EvidenceLinks.

Graph structure alone does not decide evidence polarity. Callers must pass
annotations that name a candidate, polarity, and score. This module only checks
that each annotation corresponds to a relationship actually present upstream,
preserves direction, and attaches a small whitelist of graph metadata.

Annotation shape::
    {
        "source_event_id": "...",
        "target_event_id": "...",
        "candidate_event_id": "...",  # must be an endpoint
        "polarity": "supporting" | "contradicting",
        "score": 0.0..1.0,
        "reason": "optional explanation",
        "metadata": {"optional": "JSON-safe extras"}
    }
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol

from .schemas import EvidenceLink, EvidenceType


class DirectedGraphLike(Protocol):
    nodes: Any
    edges: Any

    def has_edge(self, u: Any, v: Any) -> bool: ...
    def get_edge_data(self, u: Any, v: Any, default: Any = None) -> Any: ...


_ALLOWED_ANNOTATION_KEYS = {
    "source_event_id", "target_event_id", "candidate_event_id",
    "polarity", "score", "reason", "metadata",
}


def _annotation(raw: Mapping[str, Any]) -> dict[str, Any]:
    unknown = set(raw) - _ALLOWED_ANNOTATION_KEYS
    if unknown:
        raise ValueError(f"Unknown evidence annotation field(s): {', '.join(sorted(unknown))}")
    required = {"source_event_id", "target_event_id", "candidate_event_id", "polarity", "score"}
    missing = required - set(raw)
    if missing:
        raise ValueError(f"Missing evidence annotation field(s): {', '.join(sorted(missing))}")
    return dict(raw)


def _metadata_copy(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("evidence annotation metadata must be a JSON object")
    return dict(value)


def temporal_links_from_graph(
    temporal_graph: DirectedGraphLike,
    annotations: Iterable[Mapping[str, Any]],
) -> list[EvidenceLink]:
    """Convert only explicitly annotated, directed temporal edges.

    An annotation for an edge that does not exist is rejected. Edge direction is
    preserved exactly: reverse edges are not silently treated as equivalent.
    """
    result: list[EvidenceLink] = []
    for raw in annotations:
        ann = _annotation(raw)
        source, target = ann["source_event_id"], ann["target_event_id"]
        if not temporal_graph.has_edge(source, target):
            raise ValueError(f"Annotated temporal edge does not exist: {source!r} -> {target!r}")
        edge = temporal_graph.get_edge_data(source, target, default={}) or {}
        metadata = _metadata_copy(ann.get("metadata"))
        # Whitelist JSON-compatible, meaningful graph attributes; do not dump
        # arbitrary NetworkX attributes into the evidence package.
        if "time_delta_seconds" in edge:
            metadata.setdefault("time_delta_seconds", edge["time_delta_seconds"])
        if "relationship" in edge:
            metadata.setdefault("graph_relationship", str(edge["relationship"]))
        result.append(EvidenceLink(
            source_event_id=source,
            target_event_id=target,
            candidate_event_id=ann["candidate_event_id"],
            evidence_type=EvidenceType.TEMPORAL,
            polarity=ann["polarity"],
            score=ann["score"],
            relation=str(edge.get("relationship") or "temporal_relationship"),
            reason=ann.get("reason"),
            metadata=metadata,
        ))
    return result


def dependency_links_from_graphs(
    temporal_graph: DirectedGraphLike,
    dependency_graph: DirectedGraphLike,
    annotations: Iterable[Mapping[str, Any]],
) -> list[EvidenceLink]:
    """Convert explicitly annotated event pairs with a service dependency.

    The event nodes are expected to have a ``service`` attribute, as produced by
    ``TemporalEventGraph``. Member 2's dependency convention is ``consumer ->
    dependency`` (for example ``checkout -> database``). Returned event-link
    direction follows that service edge direction, even when the annotation's
    input endpoints are reversed. The candidate remains one of the two events.

    No causal polarity is inferred: each annotation supplies it explicitly.
    An annotation without a corresponding service-dependency edge is an error.
    """
    result: list[EvidenceLink] = []
    for raw in annotations:
        ann = _annotation(raw)
        event_a, event_b = ann["source_event_id"], ann["target_event_id"]
        try:
            node_a = temporal_graph.nodes[event_a]
            node_b = temporal_graph.nodes[event_b]
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"Dependency annotation references an unknown event pair: {event_a!r}, {event_b!r}") from exc

        service_a, service_b = node_a.get("service"), node_b.get("service")
        if not isinstance(service_a, str) or not service_a.strip():
            raise ValueError(f"Event {event_a!r} has no usable service attribute")
        if not isinstance(service_b, str) or not service_b.strip():
            raise ValueError(f"Event {event_b!r} has no usable service attribute")
        if service_a == service_b:
            raise ValueError(
                f"Dependency evidence requires distinct services; both events use {service_a!r}"
            )

        # Preserve service dependency direction; normally exactly one branch is true.
        a_depends_on_b = dependency_graph.has_edge(service_a, service_b)
        b_depends_on_a = dependency_graph.has_edge(service_b, service_a)
        if not a_depends_on_b and not b_depends_on_a:
            raise ValueError(
                f"No service dependency exists between {service_a!r} and {service_b!r}"
            )
        if a_depends_on_b and b_depends_on_a:
            raise ValueError(
                f"Bidirectional service dependency between {service_a!r} and {service_b!r} "
                "is ambiguous for one annotation; annotate each direction separately"
            )
        if a_depends_on_b:
            source_event_id, target_event_id = event_a, event_b
            source_service, target_service = service_a, service_b
            direction = "source_service_depends_on_target_service"
            service_edge_data = dependency_graph.get_edge_data(service_a, service_b, default={}) or {}
        else:
            source_event_id, target_event_id = event_b, event_a
            source_service, target_service = service_b, service_a
            direction = "source_service_depends_on_target_service"
            service_edge_data = dependency_graph.get_edge_data(service_b, service_a, default={}) or {}

        metadata = _metadata_copy(ann.get("metadata"))
        metadata.setdefault("source_service", source_service)
        metadata.setdefault("dependency_service", target_service)
        metadata.setdefault("dependency_direction", direction)
        if "relationship" in service_edge_data:
            metadata.setdefault("graph_relationship", str(service_edge_data["relationship"]))

        result.append(EvidenceLink(
            source_event_id=source_event_id,
            target_event_id=target_event_id,
            candidate_event_id=ann["candidate_event_id"],
            evidence_type=EvidenceType.DEPENDENCY,
            polarity=ann["polarity"],
            score=ann["score"],
            relation=str(service_edge_data.get("relationship") or "service_dependency"),
            reason=ann.get("reason"),
            metadata=metadata,
        ))
    return result
