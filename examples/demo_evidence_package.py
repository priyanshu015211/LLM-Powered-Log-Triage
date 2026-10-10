"""Run a deterministic synthetic evidence-package demo (not a research result).

Usage from the repository root:
    python examples/demo_evidence_package.py
    python examples/demo_evidence_package.py --output outputs/demo/evidence_package.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx

from src.evidence import (
    EvidenceBuilder,
    EventStore,
    dependency_links_from_graphs,
    temporal_links_from_graph,
)


TIMES = {
    "db_error": "2026-10-08T10:00:00+00:00",
    "health_probe": "2026-10-08T10:00:01+00:00",
    "checkout_timeout": "2026-10-08T10:00:02+00:00",
    "payment_failure": "2026-10-08T10:00:03+00:00",
}


def build_demo_package():
    """Construct events, graph context, explicitly annotated links, and package."""
    id_by_name = {
        "db_error": "evt_0000000000000001",
        "health_probe": "evt_0000000000000002",
        "checkout_timeout": "evt_0000000000000003",
        "payment_failure": "evt_0000000000000004",
    }
    details = {
        "db_error": ("database", "ERROR", "connection pool exhausted"),
        "health_probe": ("database", "INFO", "database health probe succeeded"),
        "checkout_timeout": ("checkout", "ERROR", "checkout request timed out"),
        "payment_failure": ("payment", "ERROR", "payment failed after checkout timeout"),
    }
    records = []
    for line_number, name in enumerate(TIMES, start=1):
        service, severity, message = details[name]
        records.append({
            "event_id": id_by_name[name],
            "timestamp_iso": TIMES[name],
            "severity": severity,
            "service": service,
            "message": message,
            "template": message,
            "source_file": "synthetic_incident.log",
            "line_number": line_number,
        })
    store = EventStore(records)

    # Same node/edge contract as Member 2's TemporalEventGraph and
    # ServiceDependencyGraph: event nodes carry service; temporal edges preserve
    # earlier -> later; dependency edge is consumer -> provider.
    temporal = nx.DiGraph()
    for name, (service, severity, message) in details.items():
        temporal.add_node(
            id_by_name[name],
            timestamp=TIMES[name],
            service=service,
            level=severity,
            message=message,
        )
    temporal.add_edge(
        id_by_name["db_error"], id_by_name["health_probe"],
        time_delta_seconds=1.0, relationship="temporal_precedence",
    )
    temporal.add_edge(
        id_by_name["health_probe"], id_by_name["checkout_timeout"],
        time_delta_seconds=1.0, relationship="temporal_precedence",
    )
    temporal.add_edge(
        id_by_name["checkout_timeout"], id_by_name["payment_failure"],
        time_delta_seconds=1.0, relationship="temporal_precedence",
    )

    dependencies = nx.DiGraph()
    dependencies.add_edge("checkout", "database", relationship="service_dependency")
    dependencies.add_edge("payment", "checkout", relationship="service_dependency")

    temporal_links = temporal_links_from_graph(temporal, [
        {
            "source_event_id": id_by_name["health_probe"],
            "target_event_id": id_by_name["checkout_timeout"],
            "candidate_event_id": id_by_name["checkout_timeout"],
            "polarity": "contradicting",
            "score": 0.62,
            "reason": (
                "A successful database health probe immediately preceded the timeout; "
                "this is counterevidence to a sustained-outage explanation, not proof against it."
            ),
        },
        {
            "source_event_id": id_by_name["checkout_timeout"],
            "target_event_id": id_by_name["payment_failure"],
            "candidate_event_id": id_by_name["payment_failure"],
            "polarity": "supporting",
            "score": 0.88,
            "reason": "The payment failure followed the checkout timeout in the synthetic timeline.",
        },
    ])
    dependency_links = dependency_links_from_graphs(temporal, dependencies, [
        {
            # Candidate first; adapter preserves consumer -> dependency direction.
            "source_event_id": id_by_name["checkout_timeout"],
            "target_event_id": id_by_name["db_error"],
            "candidate_event_id": id_by_name["checkout_timeout"],
            "polarity": "supporting",
            "score": 0.91,
            "reason": (
                "The checkout service depends on the database, and the database "
                "logged pool exhaustion earlier in this synthetic incident."
            ),
        },
    ])

    builder = EvidenceBuilder(store)
    package = builder.build_package(
        incident_id="SYNTHETIC-INCIDENT-001",
        candidate_event_ids=[id_by_name["checkout_timeout"], id_by_name["payment_failure"]],
        evidence_links=[*temporal_links, *dependency_links],
        severity_scores={
            id_by_name["checkout_timeout"]: 0.85,
            id_by_name["payment_failure"]: 0.70,
        },
    )
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/demo/evidence_package.json"),
        help="Path for the serialized package (default: outputs/demo/evidence_package.json)",
    )
    args = parser.parse_args()
    package = build_demo_package()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(package.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Wrote synthetic evidence package: {args.output}")
    print(f"Candidates: {len(package.candidates)}; evidence items: {sum(len(c.evidence_items) for c in package.candidates)}")
    print("DEMO ONLY: these synthetic annotations are not measured RCA results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
