"""Escalation configuration for denied claims appeal workflows."""

from harness.escalation import EscalationEngine, EscalationConfig


def get_appeal_escalation_engine() -> EscalationEngine:
    """
    Returns an EscalationEngine configured for appeal workflows.
    ALL appeal determinations require human review — no exceptions.
    Mandatory triggers: adverse_determination, appeal_decision, high_dollar, clinical_complexity.
    """
    config = EscalationConfig(
        mandatory_triggers_adverse_determination=True,
        mandatory_triggers_high_dollar=True,
        mandatory_triggers_appeal_decision=True,
        mandatory_triggers_clinical_complexity=True,
        confidence_threshold=0.80,
        missing_data_threshold=0.15,
        high_dollar_threshold=10000.0,
    )
    return EscalationEngine(config)
