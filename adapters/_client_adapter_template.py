"""
Client Adapter Template
=======================
Implement this class to connect Shippy HC to your production systems.

Steps:
1. Copy this file to adapters/client_adapter.py (or your preferred name)
2. Replace each NotImplementedError with your real implementation
3. Wire each method to your claims platform / member DB / auth API
4. Run: python -c "from adapters.interface_validator import validate_adapter;
         from adapters.client_adapter import ClientAdapter;
         print(validate_adapter(ClientAdapter(config={})))"
5. Run the full eval suite: python scripts/run_evals.py --tier 1 --ci

Zero changes to harness/, governance/, or scripts/ required.
BAA must be executed before this adapter handles real PHI.
See docs/hipaa-compliance-plan.md.
"""


class ClientAdapter:
    """Production adapter — implement against your real systems."""

    def __init__(self, config: dict):
        """
        config: client-specific connection details
        e.g. {"base_url": "...", "api_key": "...", "tenant_id": "..."}
        """
        self.config = config

    # -- Member --

    def lookup_member(self, **params) -> dict:
        """
        Look up member by member_id, subscriber_id, or name+DOB.
        Route to: your member management system or eligibility API.
        Return shape: {"results": [...members...], "total": int}
        """
        raise NotImplementedError

    def get_member_coverage(self, **params) -> dict:
        """
        Get member's current coverage details including plan and benefits.
        Route to: your benefits/coverage system.
        Return shape: {"plan_id": str, "plan_name": str, "coverage": {...}}
        """
        raise NotImplementedError

    def get_member_dependents(self, **params) -> dict:
        """
        List all dependents enrolled under a subscriber.
        Route to: your enrollment/eligibility system.
        Return shape: {"dependents": [...], "total": int}
        """
        raise NotImplementedError

    # -- Claims --

    def search_claims(self, **params) -> dict:
        """
        Search medical claims by member, date range, status, provider, or diagnosis.
        Route to: your claims adjudication system.
        Return shape: {"results": [...claims...], "total": int}
        """
        raise NotImplementedError

    def get_claim_detail(self, **params) -> dict:
        """
        Get full claim detail including claim lines, amounts, and denial reason.
        Route to: your claims adjudication system.
        Return shape: {"claim_id": str, "claim_lines": [...], ...}
        """
        raise NotImplementedError

    def search_pharmacy_claims(self, **params) -> dict:
        """
        Search pharmacy/prescription claims by member, medication, or date range.
        Route to: your PBM (pharmacy benefit manager) or Rx claims system.
        Return shape: {"results": [...rx_claims...], "total": int}
        """
        raise NotImplementedError

    # -- Benefits + Eligibility --

    def check_benefits(self, **params) -> dict:
        """
        Check plan benefits for a specific service category.
        Route to: your benefits configuration system.
        Return shape: {"copay": float, "coinsurance": int, "auth_required": bool, ...}
        """
        raise NotImplementedError

    def get_accumulator(self, **params) -> dict:
        """
        Get member's deductible and out-of-pocket accumulator status.
        Route to: your accumulator tracking system.
        Return shape: {"deductible_used": float, "deductible_limit": float, "oop_used": float, ...}
        """
        raise NotImplementedError

    def check_eligibility(self, **params) -> dict:
        """
        Verify member eligibility for a specific date of service.
        Route to: your eligibility/enrollment system or 270/271 transaction.
        Return shape: {"eligible": bool, "plan_id": str, ...}
        """
        raise NotImplementedError

    def get_plan_formulary(self, **params) -> dict:
        """
        Look up formulary status and tier for a medication under a plan.
        Route to: your PBM formulary system.
        Return shape: {"results": [...medications...], "total": int}
        """
        raise NotImplementedError

    # -- Authorizations --

    def get_authorization(self, **params) -> dict:
        """
        Look up a prior authorization by ID or search by member.
        Route to: your utilization management / prior auth system.
        Return shape: {"auth_id": str, "status": str, ...} or {"results": [...]}
        """
        raise NotImplementedError

    def submit_authorization_request(self, **params) -> dict:
        """
        Submit a new prior authorization request.
        Route to: your utilization management system.
        Return shape: {"auth_id": str, "status": "Pending", ...}
        """
        raise NotImplementedError

    # -- Appeals --

    def initiate_appeal(self, **params) -> dict:
        """
        Initiate an appeal for a denied claim or authorization.
        Route to: your appeals & grievances system.
        Return shape: {"appeal_id": str, "status": "Submitted", ...}
        """
        raise NotImplementedError

    # -- Provider --

    def search_providers(self, **params) -> dict:
        """
        Search providers by specialty, name, network status, or location.
        Route to: your provider directory / credentialing system.
        Return shape: {"results": [...providers...], "total": int}
        """
        raise NotImplementedError

    # -- Interactions --

    def get_interaction_history(self, **params) -> dict:
        """
        Get member interaction history (calls, messages, case notes).
        Route to: your CRM or interaction management system.
        Return shape: {"results": [...interactions...], "total": int}
        """
        raise NotImplementedError

    def draft_case_note(self, **params) -> dict:
        """
        Draft a case note for review before submission.
        Route to: your case management system.
        Return shape: {"draft_id": str, "preview": {...}}
        """
        raise NotImplementedError

    def submit_case_note(self, **params) -> dict:
        """
        Submit a previously drafted case note.
        Route to: your case management system.
        Return shape: {"note_id": str, "status": "Submitted"}
        """
        raise NotImplementedError

    # -- Knowledge + Documents --

    def search_knowledge_base(self, **params) -> dict:
        """
        Search policies, FAQs, business rules, and reference data.
        Route to: your knowledge management system or policy repository.
        Return shape: {"results": [...articles...], "total": int}
        """
        raise NotImplementedError

    def generate_document(self, **params) -> dict:
        """
        Render a member-facing document (EOB, denial letter, ID card, etc.).
        Route to: your document generation / correspondence system.
        Return shape: {"document_type": str, "document_text": str}
        """
        raise NotImplementedError
