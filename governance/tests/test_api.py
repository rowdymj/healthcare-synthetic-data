"""Integration tests for the governance REST API."""

import os
import pytest
from fastapi.testclient import TestClient

# Set API key before importing app (env var read at import time)
os.environ["GOVERNANCE_API_KEY"] = "test-key"

from governance.api import app, _audit_store  # noqa: E402

HEADERS = {"X-API-Key": "test-key"}


@pytest.fixture(autouse=True)
def clear_audit_store():
    """Reset shared audit store between tests."""
    _audit_store.clear()
    yield
    _audit_store.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _validate(client, overrides=None):
    """Helper to POST a validate request with sensible defaults."""
    body = {
        "session_id": "test-session-1",
        "workflow_id": "wf-001",
        "workflow_type": "prior_auth",
        "proposed_action": {
            "action_type": "approve",
            "is_adverse_determination": False,
            "is_appeal_decision": False,
            "is_clinical_complexity": False,
            "claim_amount": 500.0,
            "confidence": 0.95,
            "missing_data_fraction": 0.0,
        },
    }
    if overrides:
        for key, val in overrides.items():
            if key == "proposed_action":
                body["proposed_action"].update(val)
            else:
                body[key] = val
    return client.post("/governance/validate", json=body, headers=HEADERS)


# ---------------------------------------------------------------------------
# Escalation tests
# ---------------------------------------------------------------------------


def test_adverse_determination_escalates(client):
    """Adverse determination triggers mandatory escalation."""
    resp = _validate(client, {
        "proposed_action": {"is_adverse_determination": True},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "escalate"
    assert data["mandatory"] is True
    assert data["escalation_required"] is True
    assert data["human_review_id"] is not None


def test_appeal_decision_escalates(client):
    """Appeal decision triggers mandatory escalation."""
    resp = _validate(client, {
        "workflow_type": "appeal",
        "proposed_action": {"is_appeal_decision": True},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "escalate"
    assert data["mandatory"] is True
    assert data["escalation_required"] is True


def test_high_dollar_escalates(client):
    """High dollar claim ($47k) triggers mandatory escalation."""
    resp = _validate(client, {
        "proposed_action": {"claim_amount": 47000.0},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "escalate"
    assert data["mandatory"] is True
    assert "high dollar" in data["reason"].lower()


def test_clean_case_allows(client):
    """Clean case with no triggers returns allow."""
    resp = _validate(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"
    assert data["mandatory"] is False
    assert data["escalation_required"] is False
    assert data["human_review_id"] is None


def test_low_confidence_escalates_not_mandatory(client):
    """Low confidence triggers escalation but not mandatory."""
    resp = _validate(client, {
        "proposed_action": {"confidence": 0.5},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "escalate"
    assert data["mandatory"] is False
    assert data["escalation_required"] is True


# ---------------------------------------------------------------------------
# Audit trail tests
# ---------------------------------------------------------------------------


def test_audit_trail_populated(client):
    """POST /validate creates audit entries retrievable via GET /audit."""
    _validate(client, {"session_id": "audit-test-1"})

    resp = client.get("/governance/audit/audit-test-1", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "audit-test-1"
    assert len(data["entries"]) >= 2  # at least tool_call + determination + tool_result


def test_audit_trail_empty_session(client):
    """GET /audit for unknown session returns empty list."""
    resp = client.get("/governance/audit/nonexistent", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["entries"] == []


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------


def test_missing_api_key_returns_401(client):
    """Request without X-API-Key header returns 401."""
    body = {
        "session_id": "s1",
        "workflow_id": "w1",
        "workflow_type": "prior_auth",
        "proposed_action": {
            "action_type": "approve",
            "is_adverse_determination": False,
            "is_appeal_decision": False,
            "is_clinical_complexity": False,
            "claim_amount": 0,
            "confidence": 1.0,
            "missing_data_fraction": 0.0,
        },
    }
    resp = client.post("/governance/validate", json=body)  # no headers
    assert resp.status_code == 401


def test_invalid_api_key_returns_401(client):
    """Request with wrong API key returns 401."""
    body = {
        "session_id": "s1",
        "workflow_id": "w1",
        "workflow_type": "prior_auth",
        "proposed_action": {
            "action_type": "approve",
            "is_adverse_determination": False,
            "is_appeal_decision": False,
            "is_clinical_complexity": False,
            "claim_amount": 0,
            "confidence": 1.0,
            "missing_data_fraction": 0.0,
        },
    }
    resp = client.post(
        "/governance/validate", json=body, headers={"X-API-Key": "wrong-key"}
    )
    assert resp.status_code == 401
