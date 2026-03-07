"""
Governance REST API — Mode 2 deployable service.

Exposes harness governance primitives (EscalationEngine, AuditLogger) as a
REST service for clients like Highmark that run Pega or ServiceNow and call
our governance API from their own orchestration layer.

Run: uvicorn governance.api:app --port 8001
"""

import os
import uuid
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from harness.escalation import EscalationEngine, EscalationConfig
from harness.audit import AuditLogger
from governance.workflow_definitions import WorkflowDefinitions

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Governance API",
    version="0.1.0",
    description="Mode 2 governance service — escalation + audit for external orchestrators.",
)

# ---------------------------------------------------------------------------
# Shared state (in-memory, resets on restart)
# ---------------------------------------------------------------------------

_workflow_defs = WorkflowDefinitions()
_escalation_engine = EscalationEngine(EscalationConfig())

# session_id -> list[dict]  (serialised AuditEntry dicts)
_audit_store: dict[str, list[dict]] = {}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_API_KEY = os.environ.get("GOVERNANCE_API_KEY", "")


def _check_api_key(x_api_key: Optional[str]) -> None:
    if not _API_KEY:
        return  # no key configured — open access (dev mode)
    if not x_api_key or x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ProposedAction(BaseModel):
    action_type: str
    is_adverse_determination: bool = False
    is_appeal_decision: bool = False
    is_clinical_complexity: bool = False
    claim_amount: float = 0.0
    confidence: float = 1.0
    missing_data_fraction: float = 0.0


class ValidateRequest(BaseModel):
    session_id: str
    workflow_id: str
    workflow_type: str
    proposed_action: ProposedAction


class GovernanceResponse(BaseModel):
    decision: str  # "allow" | "reject" | "escalate"
    mandatory: bool
    reason: str
    audit_id: str
    escalation_required: bool
    human_review_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/governance/validate", response_model=GovernanceResponse)
def validate(
    body: ValidateRequest,
    x_api_key: Optional[str] = Header(None),
):
    _check_api_key(x_api_key)

    # 1. Look up workflow rules
    rules = _workflow_defs.get_rules(body.workflow_type)

    # 2. Build the dict that EscalationEngine expects
    action = body.proposed_action
    workflow_result = {
        "is_adverse_determination": action.is_adverse_determination,
        "is_appeal_decision": action.is_appeal_decision,
        "is_clinical_complexity": action.is_clinical_complexity,
        "claim_amount": action.claim_amount,
        "confidence": action.confidence,
        "missing_data_fraction": action.missing_data_fraction,
    }

    # 3. Run escalation evaluation
    decision = _escalation_engine.evaluate(workflow_result)

    # 4. Determine response decision string
    if decision.mandatory:
        response_decision = "escalate"
    elif decision.should_escalate:
        response_decision = "escalate"
    else:
        response_decision = "allow"

    escalation_required = decision.should_escalate
    human_review_id = str(uuid.uuid4()) if escalation_required else None

    # 5. Log to audit trail
    audit_id = str(uuid.uuid4())
    audit = AuditLogger(body.session_id, body.workflow_id)

    # Log the proposed action as a tool_call equivalent
    audit.log(
        "tool_call",
        tool_name="governance_validate",
        tool_params={
            "workflow_type": body.workflow_type,
            "action_type": action.action_type,
            "claim_amount": action.claim_amount,
        },
    )

    # Log the escalation decision
    if escalation_required:
        audit.log(
            "escalation",
            escalation_reason=decision.reason,
            confidence=decision.confidence,
        )
    else:
        audit.log(
            "determination",
            confidence=decision.confidence,
        )

    # Log the tool result
    audit.log(
        "tool_result",
        tool_name="governance_validate",
        tool_result={
            "decision": response_decision,
            "mandatory": decision.mandatory,
            "escalation_required": escalation_required,
            "audit_id": audit_id,
        },
    )

    # Persist entries to shared store
    entries = audit.get_trail(body.session_id)
    if body.session_id not in _audit_store:
        _audit_store[body.session_id] = []
    for entry in entries:
        d = asdict(entry)
        d = {k: v for k, v in d.items() if v is not None}
        _audit_store[body.session_id].append(d)

    return GovernanceResponse(
        decision=response_decision,
        mandatory=decision.mandatory,
        reason=decision.reason,
        audit_id=audit_id,
        escalation_required=escalation_required,
        human_review_id=human_review_id,
    )


@app.get("/governance/audit/{session_id}")
def get_audit_trail(
    session_id: str,
    x_api_key: Optional[str] = Header(None),
):
    _check_api_key(x_api_key)
    entries = _audit_store.get(session_id, [])
    return {"session_id": session_id, "entries": entries}
