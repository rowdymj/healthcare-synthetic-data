"""
Audit logger — append-only governance trail for healthcare AI workflows.

Every tool call, escalation, human review, and determination is recorded.
verify() checks completeness against regulatory requirements.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


VALID_EVENT_TYPES = {
    "tool_call",
    "tool_result",
    "escalation",
    "human_review",
    "determination",
    "error",
    "recovery",
}


@dataclass
class AuditEntry:
    session_id: str
    workflow_id: str
    timestamp: str
    event_type: str
    tool_name: Optional[str] = None
    tool_params: Optional[dict] = None
    tool_result: Optional[dict] = None
    escalation_reason: Optional[str] = None
    human_reviewer_id: Optional[str] = None
    human_decision: Optional[str] = None
    confidence: Optional[float] = None
    model: str = ""
    prompt_version: str = ""


class AuditLogger:
    def __init__(
        self,
        session_id: str,
        workflow_id: str,
        model: str = "",
        prompt_version: str = "",
    ):
        self.session_id = session_id
        self.workflow_id = workflow_id
        self.model = model
        self.prompt_version = prompt_version
        self._entries: list[AuditEntry] = []

    def log(self, event_type: str, **kwargs) -> AuditEntry:
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'. Must be one of: {VALID_EVENT_TYPES}"
            )
        entry = AuditEntry(
            session_id=self.session_id,
            workflow_id=self.workflow_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            model=self.model,
            prompt_version=self.prompt_version,
            **kwargs,
        )
        self._entries.append(entry)
        return entry

    def get_trail(self, session_id: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.session_id == session_id]

    def verify(self, session_id: str) -> dict:
        trail = self.get_trail(session_id)
        missing = []

        event_types = [e.event_type for e in trail]

        # Must have at least one tool_call
        if "tool_call" not in event_types:
            missing.append("tool_call")

        # Must have determination OR escalation
        has_determination = "determination" in event_types
        has_escalation = "escalation" in event_types
        if not has_determination and not has_escalation:
            missing.append("determination")

        # If escalation exists, must have subsequent human_review
        if has_escalation:
            escalation_idx = event_types.index("escalation")
            subsequent = event_types[escalation_idx + 1 :]
            if "human_review" not in subsequent:
                missing.append("human_review")

        # Every tool_call must have a paired tool_result
        tool_calls = []
        tool_results = []
        for e in trail:
            if e.event_type == "tool_call":
                tool_calls.append(e.tool_name)
            elif e.event_type == "tool_result":
                tool_results.append(e.tool_name)

        for i, call_name in enumerate(tool_calls):
            if i >= len(tool_results) or tool_results[i] != call_name:
                missing.append(f"tool_result for {call_name}")
                break

        return {"complete": len(missing) == 0, "missing": missing}

    def to_jsonl(self, session_id: str) -> str:
        trail = self.get_trail(session_id)
        lines = []
        for entry in trail:
            d = asdict(entry)
            # Remove None values for cleaner output
            d = {k: v for k, v in d.items() if v is not None}
            lines.append(json.dumps(d, default=str))
        return "\n".join(lines)
