"""
SandboxAdapter — routes all HealthcarePlatform calls to HealthcareAPI (synthetic data).

Build-phase adapter — PHI-free, deterministic, seed(42).
At production, replace with ClientAdapter implementing the same interface.
Zero harness changes required.
"""

import sys
from pathlib import Path

# Add agent-sandbox to path so we can import api_server
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent-sandbox"))
from api_server import create_api


class SandboxAdapter:
    """Wraps HealthcareAPI.execute_tool() behind the HealthcarePlatform contract."""

    def __init__(self, data_dir=None, force_json=False):
        self.api = create_api(data_dir=data_dir, force_json=force_json)

    # -- Member --

    def lookup_member(self, **params) -> dict:
        return self.api.execute_tool("lookup_member", params)

    def get_member_coverage(self, **params) -> dict:
        return self.api.execute_tool("get_member_coverage", params)

    def get_member_dependents(self, **params) -> dict:
        return self.api.execute_tool("get_member_dependents", params)

    # -- Claims --

    def search_claims(self, **params) -> dict:
        return self.api.execute_tool("search_claims", params)

    def get_claim_detail(self, **params) -> dict:
        return self.api.execute_tool("get_claim_detail", params)

    def search_pharmacy_claims(self, **params) -> dict:
        return self.api.execute_tool("search_pharmacy_claims", params)

    # -- Benefits + Eligibility --

    def check_benefits(self, **params) -> dict:
        return self.api.execute_tool("check_benefits", params)

    def get_accumulator(self, **params) -> dict:
        return self.api.execute_tool("get_accumulator", params)

    def check_eligibility(self, **params) -> dict:
        return self.api.execute_tool("check_eligibility", params)

    def get_plan_formulary(self, **params) -> dict:
        return self.api.execute_tool("get_plan_formulary", params)

    # -- Authorizations --

    def get_authorization(self, **params) -> dict:
        return self.api.execute_tool("get_authorization", params)

    def submit_authorization_request(self, **params) -> dict:
        return self.api.execute_tool("submit_authorization_request", params)

    # -- Appeals --

    def initiate_appeal(self, **params) -> dict:
        return self.api.execute_tool("initiate_appeal", params)

    # -- Provider --

    def search_providers(self, **params) -> dict:
        return self.api.execute_tool("search_providers", params)

    # -- Interactions --

    def get_interaction_history(self, **params) -> dict:
        return self.api.execute_tool("get_interaction_history", params)

    def draft_case_note(self, **params) -> dict:
        return self.api.execute_tool("draft_case_note", params)

    def submit_case_note(self, **params) -> dict:
        return self.api.execute_tool("submit_case_note", params)

    # -- Knowledge + Documents --

    def search_knowledge_base(self, **params) -> dict:
        return self.api.execute_tool("search_knowledge_base", params)

    def generate_document(self, **params) -> dict:
        return self.api.execute_tool("generate_document", params)
