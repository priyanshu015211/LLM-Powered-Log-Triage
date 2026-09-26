from src.event_intelligence.event_extractor import mine_template, classify_event_type


def test_template_mining_collapses_variable_tokens():
    t1 = mine_template("failed to connect to payment-service at 10.0.0.12: timeout after 342ms")
    t2 = mine_template("failed to connect to payment-service at 10.0.0.21: timeout after 981ms")
    assert t1 == t2
    assert "<IP>" in t1
    assert "<NUM>" in t1


def test_event_type_classification():
    assert classify_event_type("failed to connect to db: timeout") == "connection_failure"
    assert classify_event_type("user 1234 logged in") == "auth_event"
    assert classify_event_type("out of memory, restarting worker") == "resource_exhaustion"
