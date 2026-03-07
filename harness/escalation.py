"""
Escalation engine — governance primitive for mandatory human-in-the-loop review.

TX, AZ, MD law prohibits AI as the sole basis for adverse determinations.
The mandatory escalation gate in evaluate() enforces this requirement.
"""

from dataclasses import dataclass


@dataclass
class EscalationConfig:
    mandatory_triggers_adverse_determination: bool = True
    mandatory_triggers_high_dollar: bool = True
    mandatory_triggers_appeal_decision: bool = True
    mandatory_triggers_clinical_complexity: bool = True
    confidence_threshold: float = 0.75
    missing_data_threshold: float = 0.20
    high_dollar_threshold: float = 10000.0


@dataclass
class EscalationDecision:
    should_escalate: bool
    mandatory: bool
    reason: str
    confidence: float = 1.0


class EscalationEngine:
    def __init__(self, config: EscalationConfig):
        self.config = config

    def is_mandatory(self, workflow_result: dict) -> bool:
        c = self.config
        if c.mandatory_triggers_adverse_determination and workflow_result.get("is_adverse_determination"):
            return True
        if c.mandatory_triggers_high_dollar:
            amount = workflow_result.get("claim_amount", 0.0)
            if workflow_result.get("is_high_dollar") or amount >= c.high_dollar_threshold:
                return True
        if c.mandatory_triggers_appeal_decision and workflow_result.get("is_appeal_decision"):
            return True
        if c.mandatory_triggers_clinical_complexity and workflow_result.get("is_clinical_complexity"):
            return True
        return False

    def evaluate(self, workflow_result: dict) -> EscalationDecision:
        # 1. Mandatory triggers — hard gate, cannot be bypassed
        if self.is_mandatory(workflow_result):
            reasons = []
            c = self.config
            if c.mandatory_triggers_adverse_determination and workflow_result.get("is_adverse_determination"):
                reasons.append("adverse determination")
            if c.mandatory_triggers_high_dollar:
                amount = workflow_result.get("claim_amount", 0.0)
                if workflow_result.get("is_high_dollar") or amount >= c.high_dollar_threshold:
                    reasons.append("high dollar claim")
            if c.mandatory_triggers_appeal_decision and workflow_result.get("is_appeal_decision"):
                reasons.append("appeal decision")
            if c.mandatory_triggers_clinical_complexity and workflow_result.get("is_clinical_complexity"):
                reasons.append("clinical complexity")
            return EscalationDecision(
                should_escalate=True,
                mandatory=True,
                reason=f"Mandatory escalation: {', '.join(reasons)}",
                confidence=workflow_result.get("confidence", 1.0),
            )

        # 2. Low confidence
        confidence = workflow_result.get("confidence", 1.0)
        if confidence < self.config.confidence_threshold:
            return EscalationDecision(
                should_escalate=True,
                mandatory=False,
                reason=f"Low confidence ({confidence:.2f} < {self.config.confidence_threshold})",
                confidence=confidence,
            )

        # 3. High missing data
        missing = workflow_result.get("missing_data_fraction", 0.0)
        if missing > self.config.missing_data_threshold:
            return EscalationDecision(
                should_escalate=True,
                mandatory=False,
                reason=f"Missing data ({missing:.2f} > {self.config.missing_data_threshold})",
                confidence=confidence,
            )

        # 4. No escalation needed
        return EscalationDecision(
            should_escalate=False,
            mandatory=False,
            reason="No escalation triggers met",
            confidence=confidence,
        )
