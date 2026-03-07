"""
Reusable confidence-based escalation trigger.

Use this for workflows where mandatory escalation is not required
but low-confidence decisions should still be routed to a reviewer.
"""

from harness.escalation import EscalationEngine, EscalationConfig


def get_confidence_threshold_engine(
    confidence_threshold: float = 0.75,
    missing_data_threshold: float = 0.20,
) -> EscalationEngine:
    """
    Returns an EscalationEngine with only soft escalation triggers.
    No mandatory triggers — escalation is advisory, not regulatory.
    """
    config = EscalationConfig(
        mandatory_triggers_adverse_determination=False,
        mandatory_triggers_high_dollar=False,
        mandatory_triggers_appeal_decision=False,
        mandatory_triggers_clinical_complexity=False,
        confidence_threshold=confidence_threshold,
        missing_data_threshold=missing_data_threshold,
    )
    return EscalationEngine(config)
