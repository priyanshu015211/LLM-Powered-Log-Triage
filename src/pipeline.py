"""
Phase 1 + Phase 2 pipeline orchestrator:

Raw Logs -> Parsing -> Normalization -> Event Extraction -> Embeddings -> Semantic Groups

Run directly:
    python -m src.pipeline

Or import `run_pipeline()` to get the LogEvent list, embeddings matrix and
semantic group summaries programmatically — this is this module's public
interface for Phase 3 (temporal/dependency graph) and Phase 4 (evidence
builder / LLM integration) to build on top of.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src import config
from src.preprocessing.ingestion import load_dataset, iter_raw_lines, generate_sample_dataset
from src.preprocessing.parsers import parse_line
from src.preprocessing.normalizer import normalize_events
from src.preprocessing.schema import LogEvent
from src.event_intelligence.event_extractor import extract_events, template_frequency
from src.event_intelligence.embeddings import embed_events
from src.event_intelligence.clustering import assign_clusters, summarize_clusters


def _write_jsonl(events: list[LogEvent], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(e.to_json() + "\n")


def run_pipeline(raw_dir: Path | None = None, save_outputs: bool = True) -> dict:
    report: dict = {"stages": {}}
    t0 = time.time()

    files = load_dataset(raw_dir)
    if not files:
        print("[pipeline] No raw or sample logs found — generating synthetic sample dataset.")
        generate_sample_dataset()
        files = load_dataset(raw_dir)
    report["stages"]["ingestion"] = {"files": [str(f) for f in files], "n_files": len(files)}

    events: list[LogEvent] = []
    for path in files:
        for line_no, raw_line in iter_raw_lines(path):
            events.append(parse_line(str(path.name), line_no, raw_line))
    report["stages"]["parsing"] = {"n_events": len(events)}
    if save_outputs:
        _write_jsonl(events, config.PARSED_EVENTS_PATH)

    events = normalize_events(events)
    report["stages"]["normalization"] = {
        "n_events": len(events),
        "unresolved_timestamps": sum(1 for e in events if e.timestamp_iso is None),
        "unresolved_severities": sum(1 for e in events if e.severity == "UNKNOWN"),
    }
    if save_outputs:
        _write_jsonl(events, config.NORMALIZED_EVENTS_PATH)

    events = extract_events(events)
    freq = template_frequency(events)
    report["stages"]["event_extraction"] = {
        "n_events": len(events),
        "n_distinct_templates": len(freq),
        "top_templates": list(freq.items())[:10],
    }
    if save_outputs:
        _write_jsonl(events, config.EXTRACTED_EVENTS_PATH)

    embeddings = embed_events(events, save_path=config.EMBEDDINGS_PATH if save_outputs else None)
    report["stages"]["embeddings"] = {"shape": list(embeddings.shape)}

    events = assign_clusters(events, embeddings)
    group_summaries = summarize_clusters(events)
    report["stages"]["semantic_clustering"] = {
        "n_clusters": len([g for g in group_summaries if not g["is_noise"]]),
        "n_noise_events": sum(g["size"] for g in group_summaries if g["is_noise"]),
        "algorithm": config.CLUSTERING_ALGORITHM,
    }
    if save_outputs:
        config.SEMANTIC_GROUPS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(config.SEMANTIC_GROUPS_PATH, "w", encoding="utf-8") as f:
            json.dump(group_summaries, f, indent=2)

    report["total_runtime_seconds"] = round(time.time() - t0, 3)
    report["n_events_final"] = len(events)

    if save_outputs:
        with open(config.PIPELINE_REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return {"events": events, "embeddings": embeddings, "semantic_groups": group_summaries, "report": report}


def _print_report(report: dict) -> None:
    print("\n" + "=" * 60)
    print("PREPROCESSING + EVENT INTELLIGENCE PIPELINE — RUN REPORT")
    print("=" * 60)
    for stage, info in report["stages"].items():
        print(f"\n[{stage}]")
        for k, v in info.items():
            if k == "top_templates":
                print("  top_templates:")
                for tmpl, count in v:
                    print(f"    ({count:>3}x) {tmpl}")
            else:
                print(f"  {k}: {v}")
    print(f"\nTotal runtime: {report['total_runtime_seconds']}s")
    print(f"Final event count: {report['n_events_final']}")
    print("=" * 60)


if __name__ == "__main__":
    result = run_pipeline()
    _print_report(result["report"])
    print(f"\nOutputs written to: {config.OUTPUT_DIR}")
