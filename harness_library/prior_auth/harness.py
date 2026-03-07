"""
Prior authorization workflow harness.

Tool sequence for a complete prior auth review:
1. lookup_member — verify member exists and is active
2. check_eligibility — confirm coverage active on date of service
3. get_member_coverage — retrieve plan benefits and auth requirements
4. get_plan_formulary — check if procedure is covered (if pharmacy)
5. get_authorization — check for existing auth on this procedure
6. submit_authorization_request — submit new auth request
7. generate_document — generate determination letter (if auth approved)

Mandatory escalation: ANY adverse determination (denial, partial auth,
step therapy requirement). No exceptions.

Regulatory basis: TX HB 4, AZ SB 1001, MD HB 358 — AI cannot be sole
basis for adverse determination.
"""

from harness.escalation import EscalationConfig


class PriorAuthHarness:
    """Prior authorization workflow scaffold."""

    WORKFLOW_TYPE = "prior_auth"

    REQUIRED_TOOLS = [
        "lookup_member",
        "check_eligibility",
        "get_member_coverage",
        "get_authorization",
    ]

    OPTIONAL_TOOLS = [
        "get_plan_formulary",
        "submit_authorization_request",
        "generate_document",
    ]

    ESCALATION_TOOLS = [
        "submit_authorization_request",  # triggers escalation if denial
    ]

    ALL_STEPS = [
        "lookup_member",
        "check_eligibility",
        "get_member_coverage",
        "get_plan_formulary",
        "get_authorization",
        "submit_authorization_request",
        "generate_document",
    ]

    def decompose(self, request: dict) -> list[dict]:
        """
        Returns ordered list of tool steps for this request.

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
                "tool": "check_eligibility",
                "required": True,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "get_member_coverage",
                "required": True,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
        ]

        # Pharmacy requests need formulary check
        if request.get("is_pharmacy", False):
            steps.append({
                "tool": "get_plan_formulary",
                "required": True,
                "params_from": ["get_member_coverage"],
                "escalation_check": False,
            })

        steps.extend([
            {
                "tool": "get_authorization",
                "required": True,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "submit_authorization_request",
                "required": True,
                "params_from": ["lookup_member", "check_eligibility", "get_member_coverage"],
                "escalation_check": True,  # escalation gate after submission
            },
            {
                "tool": "generate_document",
                "required": False,
                "params_from": ["submit_authorization_request"],
                "escalation_check": False,
            },
        ])

        return steps

    def get_escalation_config(self) -> EscalationConfig:
        """
        Returns escalation config tuned for prior auth workflows.
        Tighter thresholds than default for clinical decision-making.
        """
        return EscalationConfig(
            mandatory_triggers_adverse_determination=True,
            mandatory_triggers_high_dollar=True,
            mandatory_triggers_appeal_decision=True,
            mandatory_triggers_clinical_complexity=True,
            confidence_threshold=0.80,    # tighter for clinical decisions
            missing_data_threshold=0.15,  # less tolerance for missing data
            high_dollar_threshold=10000.0,
        )
