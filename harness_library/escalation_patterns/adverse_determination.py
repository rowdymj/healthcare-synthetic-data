"""
Reusable mandatory escalation trigger for any workflow that can produce
an adverse determination.

Import this in any workflow harness that has adverse determination risk.
This is not a standalone engine — it wraps EscalationEngine with the
specific configuration for adverse determination workflows.
"""

from harness.escalation import EscalationEngine, EscalationConfig


def get_adverse_determination_engine(
    confidence_threshold: float = 0.75,
    high_dollar_threshold: float = 10000.0,
) -> EscalationEngine:
    """
    Returns an EscalationEngine with adverse determination mandatory trigger.
    All other mandatory triggers also active.
    Confidence and high-dollar thresholds are configurable per workflow.
    """
    config = EscalationConfig(
        mandatory_triggers_adverse_determination=True,
        mandatory_triggers_high_dollar=True,
        mandatory_triggers_appeal_decision=True,
        mandatory_triggers_clinical_complexity=True,
        confidence_threshold=confidence_threshold,
        missing_data_threshold=0.20,
        high_dollar_threshold=high_dollar_threshold,
    )
    return EscalationEngine(config)
