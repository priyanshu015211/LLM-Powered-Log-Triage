def test_project_setup():
    assert True
from examples.demo_evidence_package import build_demo_package
from src.evidence import EvidencePackage


def test_demo_builds_valid_serializable_evidence_package():
    package = build_demo_package()
    encoded = package.model_dump_json()
    restored = EvidencePackage.model_validate_json(encoded)
    assert restored.incident_id == "SYNTHETIC-INCIDENT-001"
    assert len(restored.candidates) == 2
    checkout = next(c for c in restored.candidates if c.candidate.service == "checkout")
    assert checkout.supporting_events
    assert checkout.contradicting_events
    assert checkout.dependency_score == 0.91
    assert checkout.contradiction_score == 0.62
