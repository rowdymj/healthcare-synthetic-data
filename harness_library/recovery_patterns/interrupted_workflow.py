"""
Standard checkpoint/resume pattern for interrupted workflows.

Use this when a workflow is interrupted mid-execution (tool timeout,
session boundary, system error). The pattern preserves completed steps
and resumes from the last successful checkpoint.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class WorkflowCheckpoint:
    workflow_id: str
    workflow_type: str
    completed_steps: list[str] = field(default_factory=list)
    last_successful_step: Optional[str] = None
    step_results: dict = field(default_factory=dict)
    escalation_pending: bool = False


def save_checkpoint(checkpoint: WorkflowCheckpoint) -> dict:
    """Serialize checkpoint for storage."""
    return asdict(checkpoint)


def load_checkpoint(data: dict) -> WorkflowCheckpoint:
    """Deserialize checkpoint from storage."""
    return WorkflowCheckpoint(
        workflow_id=data["workflow_id"],
        workflow_type=data["workflow_type"],
        completed_steps=data.get("completed_steps", []),
        last_successful_step=data.get("last_successful_step"),
        step_results=data.get("step_results", {}),
        escalation_pending=data.get("escalation_pending", False),
    )


def resume_from_checkpoint(
    checkpoint: WorkflowCheckpoint,
    all_steps: list[str],
) -> list[str]:
    """
    Returns the list of remaining steps given a checkpoint.
    Steps already in completed_steps are skipped.
    """
    return [s for s in all_steps if s not in checkpoint.completed_steps]
