"""Escalation configuration for prior auth workflows."""

from harness.escalation import EscalationEngine, EscalationConfig


def get_prior_auth_escalation_engine() -> EscalationEngine:
    """
    Returns an EscalationEngine configured for prior auth workflows.
    Mandatory triggers: adverse_determination, high_dollar, clinical_complexity.
    Confidence threshold: 0.80 (tighter than default 0.75 for clinical decisions).
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
