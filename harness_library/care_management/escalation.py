"""Escalation configuration for care management workflows."""

from harness.escalation import EscalationEngine, EscalationConfig


def get_care_management_escalation_engine() -> EscalationEngine:
    """
    Returns an EscalationEngine configured for care management workflows.
    No adverse determination triggers — escalation is clinical routing only.
    Clinical complexity is the primary mandatory trigger.
    """
    config = EscalationConfig(
        mandatory_triggers_adverse_determination=False,
        mandatory_triggers_high_dollar=False,
        mandatory_triggers_appeal_decision=False,
        mandatory_triggers_clinical_complexity=True,
        confidence_threshold=0.70,
        missing_data_threshold=0.25,
        high_dollar_threshold=50000.0,
    )
    return EscalationEngine(config)
