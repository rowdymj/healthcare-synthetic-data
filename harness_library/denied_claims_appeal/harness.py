"""
Denied claims appeal workflow harness.

Tool sequence:
1. lookup_member — verify member
2. search_claims — find the denied claim
3. get_claim_detail — retrieve full denial reason and clinical basis
4. get_authorization — check if auth was required and present
5. get_interaction_history — retrieve any prior member communications
6. initiate_appeal — file the appeal
7. generate_document — generate appeal acknowledgment letter

Mandatory escalation: ALL appeal determinations without exception.
The appeal decision itself requires human review regardless of outcome.

Regulatory basis: CMS WISeR, ERISA — appeals require licensed clinician
review for adverse benefit determinations.
"""

from harness.escalation import EscalationConfig


class AppealHarness:
    """Denied claims appeal workflow scaffold."""

    WORKFLOW_TYPE = "appeal"
    MANDATORY_ESCALATION = True  # Every appeal determination, no exceptions

    REQUIRED_TOOLS = [
        "lookup_member",
        "search_claims",
        "get_claim_detail",
        "initiate_appeal",
    ]

    OPTIONAL_TOOLS = [
        "get_authorization",
        "get_interaction_history",
        "generate_document",
    ]

    ALL_STEPS = [
        "lookup_member",
        "search_claims",
        "get_claim_detail",
        "get_authorization",
        "get_interaction_history",
        "initiate_appeal",
        "generate_document",
    ]

    def decompose(self, request: dict) -> list[dict]:
        """
        Returns ordered list of tool steps for this appeal request.

        Each step is a dict with:
        - tool: tool name
        - required: bool
        - params_from: list of prior steps whose results feed into this step's params
        - escalation_check: bool — should escalation engine evaluate after this step
        """
        steps = [
            {
                "tool": "lookup_member",
                "required": True,
                "params_from": [],
                "escalation_check": False,
            },
            {
                "tool": "search_claims",
                "required": True,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "get_claim_detail",
                "required": True,
                "params_from": ["search_claims"],
                "escalation_check": False,
            },
        ]

        # Check if auth was involved in the denial
        if request.get("auth_related", True):
            steps.append({
                "tool": "get_authorization",
                "required": False,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            })

        steps.extend([
            {
                "tool": "get_interaction_history",
                "required": False,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "initiate_appeal",
                "required": True,
                "params_from": ["lookup_member", "get_claim_detail"],
                "escalation_check": True,  # ALWAYS escalate — appeal decisions require human review
            },
            {
                "tool": "generate_document",
                "required": False,
                "params_from": ["initiate_appeal"],
                "escalation_check": False,
            },
        ])

        return steps

    def get_escalation_config(self) -> EscalationConfig:
        """
        Returns escalation config for appeal workflows.
        All mandatory triggers enabled — appeals always escalate.
        """
        return EscalationConfig(
            mandatory_triggers_adverse_determination=True,
            mandatory_triggers_high_dollar=True,
            mandatory_triggers_appeal_decision=True,
            mandatory_triggers_clinical_complexity=True,
            confidence_threshold=0.80,
            missing_data_threshold=0.15,
            high_dollar_threshold=10000.0,
        )
