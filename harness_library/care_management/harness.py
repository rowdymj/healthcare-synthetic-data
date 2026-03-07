"""
Care management routing and outreach harness.

Tool sequence:
1. lookup_member — verify member
2. get_member_coverage — understand plan and care management eligibility
3. search_claims — recent utilization pattern
4. search_pharmacy_claims — medication adherence signals
5. get_interaction_history — prior care management contacts
6. draft_case_note — document outreach attempt
7. submit_case_note — log to member record

Escalation: clinical_complexity trigger for members with 3+ chronic
conditions or recent high-acuity utilization (ER + hospitalization).
No adverse determination in this workflow — escalation is clinical
routing, not regulatory compliance.
"""

from harness.escalation import EscalationConfig


class CareManagementHarness:
    """Care management routing and outreach scaffold."""

    WORKFLOW_TYPE = "care_management"
    COMPLEXITY_CONDITION_THRESHOLD = 3  # escalate if 3+ chronic conditions

    REQUIRED_TOOLS = [
        "lookup_member",
        "get_member_coverage",
        "search_claims",
    ]

    OPTIONAL_TOOLS = [
        "search_pharmacy_claims",
        "get_interaction_history",
        "draft_case_note",
        "submit_case_note",
    ]

    ALL_STEPS = [
        "lookup_member",
        "get_member_coverage",
        "search_claims",
        "search_pharmacy_claims",
        "get_interaction_history",
        "draft_case_note",
        "submit_case_note",
    ]

    def decompose(self, request: dict) -> list[dict]:
        """
        Returns ordered list of tool steps for care management outreach.

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
                "tool": "get_member_coverage",
                "required": True,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "search_claims",
                "required": True,
                "params_from": ["lookup_member"],
                "escalation_check": True,  # check complexity after seeing utilization
            },
            {
                "tool": "search_pharmacy_claims",
                "required": False,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "get_interaction_history",
                "required": False,
                "params_from": ["lookup_member"],
                "escalation_check": False,
            },
            {
                "tool": "draft_case_note",
                "required": False,
                "params_from": ["lookup_member", "search_claims"],
                "escalation_check": False,
            },
            {
                "tool": "submit_case_note",
                "required": False,
                "params_from": ["draft_case_note"],
                "escalation_check": False,
            },
        ]

        return steps

    def get_escalation_config(self) -> EscalationConfig:
        """
        Returns escalation config for care management workflows.
        No adverse determination triggers — escalation is clinical routing only.
        Clinical complexity is the primary trigger.
        """
        return EscalationConfig(
            mandatory_triggers_adverse_determination=False,
            mandatory_triggers_high_dollar=False,
            mandatory_triggers_appeal_decision=False,
            mandatory_triggers_clinical_complexity=True,
            confidence_threshold=0.70,    # more lenient for outreach
            missing_data_threshold=0.25,  # more tolerance — outreach, not adjudication
            high_dollar_threshold=50000.0,  # only extreme cases
        )

    def assess_complexity(self, member_data: dict) -> bool:
        """
        Returns True if the member's clinical profile suggests care management
        escalation to a nurse or clinical reviewer.
        """
        chronic_conditions = member_data.get("chronic_conditions", [])
        return len(chronic_conditions) >= self.COMPLEXITY_CONDITION_THRESHOLD
