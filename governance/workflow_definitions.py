"""
Workflow escalation rules — defines which workflows trigger mandatory escalation.

Each workflow type maps to a set of rules that determine whether the
EscalationEngine must be invoked and which trigger categories apply.
"""

WORKFLOW_ESCALATION_RULES = {
    "prior_auth": {
        "adverse_determination_possible": True,
        "mandatory_escalation_triggers": [
            "adverse_determination",
            "high_dollar",
            "clinical_complexity",
        ],
    },
    "appeal": {
        "adverse_determination_possible": True,
        "mandatory_escalation_triggers": ["appeal_decision"],
    },
    "claim_review": {
        "adverse_determination_possible": True,
        "mandatory_escalation_triggers": ["adverse_determination", "high_dollar"],
    },
    "eligibility_inquiry": {
        "adverse_determination_possible": False,
        "mandatory_escalation_triggers": [],
    },
    "benefits_inquiry": {
        "adverse_determination_possible": False,
        "mandatory_escalation_triggers": [],
    },
    "care_management": {
        "adverse_determination_possible": False,
        "mandatory_escalation_triggers": ["clinical_complexity"],
    },
}


class WorkflowDefinitions:
    """Lookup interface for workflow escalation rules."""

    def get_rules(self, workflow_type: str) -> dict:
        """Return the escalation rules for a workflow type, or empty defaults."""
        return WORKFLOW_ESCALATION_RULES.get(
            workflow_type,
            {"adverse_determination_possible": False, "mandatory_escalation_triggers": []},
        )

    def requires_escalation_check(self, workflow_type: str) -> bool:
        """True if this workflow type has any mandatory escalation triggers."""
        rules = self.get_rules(workflow_type)
        return len(rules["mandatory_escalation_triggers"]) > 0

    def get_mandatory_triggers(self, workflow_type: str) -> list[str]:
        """Return the list of mandatory trigger categories for this workflow type."""
        return self.get_rules(workflow_type)["mandatory_escalation_triggers"]
