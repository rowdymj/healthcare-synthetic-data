"""
Reusable high-dollar threshold trigger.

Use this for workflows where high-cost items require human review
regardless of clinical complexity or adverse determination status.
"""

from harness.escalation import EscalationEngine, EscalationConfig


def get_high_dollar_engine(
    high_dollar_threshold: float = 10000.0,
    confidence_threshold: float = 0.75,
) -> EscalationEngine:
    """
    Returns an EscalationEngine with high-dollar mandatory trigger.
    Adverse determination and appeal triggers disabled — only dollar amount matters.
    """
    config = EscalationConfig(
        mandatory_triggers_adverse_determination=False,
        mandatory_triggers_high_dollar=True,
        mandatory_triggers_appeal_decision=False,
        mandatory_triggers_clinical_complexity=False,
        confidence_threshold=confidence_threshold,
        missing_data_threshold=0.20,
        high_dollar_threshold=high_dollar_threshold,
    )
    return EscalationEngine(config)
