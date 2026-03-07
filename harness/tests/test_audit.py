"""Tests for harness.audit — audit trail logging and verification."""

import json

from harness.audit import AuditLogger


def _complete_logger():
    """Build a logger with a complete, valid audit trail."""
    logger = AuditLogger("sess-1", "wf-1", model="claude", prompt_version="v1")
    logger.log("tool_call", tool_name="lookup_member", tool_params={"member_id": "MBR-001"})
    logger.log("tool_result", tool_name="lookup_member", tool_result={"found": True})
    logger.log("determination", confidence=0.92)
    return logger


def test_complete_trail_passes_verify():
    logger = _complete_logger()
    result = logger.verify("sess-1")
    assert result["complete"] is True
    assert result["missing"] == []


def test_escalation_without_human_review_fails():
    logger = AuditLogger("sess-2", "wf-2")
    logger.log("tool_call", tool_name="search_claims")
    logger.log("tool_result", tool_name="search_claims")
    logger.log("escalation", escalation_reason="adverse determination")
    result = logger.verify("sess-2")
    assert result["complete"] is False
    assert "human_review" in result["missing"]


def test_tool_call_without_tool_result_fails():
    logger = AuditLogger("sess-3", "wf-3")
    logger.log("tool_call", tool_name="lookup_member")
    logger.log("determination")
    result = logger.verify("sess-3")
    assert result["complete"] is False
    assert any("tool_result" in m for m in result["missing"])


def test_get_trail_filters_by_session():
    logger = AuditLogger("sess-a", "wf-a")
    logger.log("tool_call", tool_name="lookup_member")

    # Manually add an entry with a different session_id
    logger._entries.append(
        logger.log.__func__.__code__  # won't work, do it properly
    ) if False else None

    # Add entry for different session by directly creating one
    from harness.audit import AuditEntry
    from datetime import datetime, timezone

    logger._entries.append(
        AuditEntry(
            session_id="sess-b",
            workflow_id="wf-b",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="tool_call",
            tool_name="search_claims",
        )
    )

    trail_a = logger.get_trail("sess-a")
    trail_b = logger.get_trail("sess-b")

    assert len(trail_a) == 1
    assert trail_a[0].tool_name == "lookup_member"
    assert len(trail_b) == 1
    assert trail_b[0].tool_name == "search_claims"


def test_to_jsonl_valid_json_lines():
    logger = _complete_logger()
    jsonl = logger.to_jsonl("sess-1")
    lines = jsonl.strip().split("\n")
    assert len(lines) == 3
    for line in lines:
        parsed = json.loads(line)
        assert "session_id" in parsed
        assert "event_type" in parsed
