"""
Interface validator — confirms an adapter implements all 19 HealthcarePlatform methods.

Usage:
    from adapters.interface_validator import validate_adapter
    from adapters.sandbox_adapter import SandboxAdapter
    print(validate_adapter(SandboxAdapter()))
"""

REQUIRED_METHODS = [
    "lookup_member",
    "get_member_coverage",
    "get_member_dependents",
    "search_claims",
    "get_claim_detail",
    "search_pharmacy_claims",
    "check_benefits",
    "get_accumulator",
    "check_eligibility",
    "get_plan_formulary",
    "get_authorization",
    "submit_authorization_request",
    "initiate_appeal",
    "search_providers",
    "get_interaction_history",
    "draft_case_note",
    "submit_case_note",
    "search_knowledge_base",
    "generate_document",
]


def validate_adapter(adapter) -> dict:
    """
    Check that an adapter instance implements all 19 required HealthcarePlatform methods.
    Returns: {"valid": bool, "missing": list[str], "implemented": list[str], "total": int}
    """
    missing = [
        m for m in REQUIRED_METHODS
        if not hasattr(adapter, m) or not callable(getattr(adapter, m))
    ]
    implemented = [m for m in REQUIRED_METHODS if m not in missing]
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "implemented": implemented,
        "total": len(REQUIRED_METHODS),
    }
