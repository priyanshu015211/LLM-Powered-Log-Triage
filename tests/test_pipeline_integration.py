"""
End-to-end sanity check for the Phase 1 + Phase 2 pipeline. This is slower
than the other unit tests since it runs a real sentence-transformers model
if available (falls back to TF-IDF if not) — run with `pytest -k pipeline`
to isolate it.
"""

from src import config
from src.pipeline import run_pipeline


def test_full_pipeline_end_to_end(tmp_path, monkeypatch):
    out_dir = tmp_path / "outputs"
    sample_dir = tmp_path / "sample"
    monkeypatch.setattr(config, "SAMPLE_LOG_DIR", sample_dir)
    monkeypatch.setattr(config, "RAW_LOG_DIR", tmp_path / "raw_empty")
    monkeypatch.setattr(config, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(config, "PARSED_EVENTS_PATH", out_dir / "parsed_events.jsonl")
    monkeypatch.setattr(config, "NORMALIZED_EVENTS_PATH", out_dir / "normalized_events.jsonl")
    monkeypatch.setattr(config, "EXTRACTED_EVENTS_PATH", out_dir / "extracted_events.jsonl")
    monkeypatch.setattr(config, "EMBEDDINGS_PATH", out_dir / "embeddings.npy")
    monkeypatch.setattr(config, "SEMANTIC_GROUPS_PATH", out_dir / "semantic_groups.json")
    monkeypatch.setattr(config, "PIPELINE_REPORT_PATH", out_dir / "pipeline_report.json")

    result = run_pipeline()
    assert len(result["events"]) > 0
    assert result["embeddings"].shape[0] == len(result["events"])
    assert len(result["semantic_groups"]) > 0
    assert all(e.semantic_cluster is not None for e in result["events"])
