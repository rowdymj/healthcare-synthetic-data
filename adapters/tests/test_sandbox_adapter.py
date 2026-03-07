"""Integration tests for SandboxAdapter — confirms it correctly wraps HealthcareAPI."""

import pytest

from adapters.sandbox_adapter import SandboxAdapter
from adapters.interface_validator import validate_adapter, REQUIRED_METHODS


@pytest.fixture(scope="module")
def adapter():
    return SandboxAdapter(force_json=True)


# ---------------------------------------------------------------------------
# Interface validation
# ---------------------------------------------------------------------------


def test_instantiates_without_error():
    SandboxAdapter()


def test_validate_adapter_all_19_methods(adapter):
    result = validate_adapter(adapter)
    assert result["valid"] is True
    assert result["missing"] == []
    assert result["total"] == 19
    assert len(result["implemented"]) == 19


# ---------------------------------------------------------------------------
# Core tool operations
# ---------------------------------------------------------------------------


def test_lookup_member(adapter):
    result = adapter.lookup_member(member_id="MBR-ANCHOR-B")
    assert "error" not in result or result.get("results")
    assert len(result["results"]) > 0
    assert result["results"][0]["member_id"] == "MBR-ANCHOR-B"


def test_search_claims(adapter):
    result = adapter.search_claims(member_id="MBR-ANCHOR-B", limit=3)
    assert "results" in result
    assert result["total"] > 0


def test_get_authorization(adapter):
    result = adapter.get_authorization(member_id="MBR-ANCHOR-B")
    # Should return results or a single auth
    assert isinstance(result, dict)


def test_check_eligibility(adapter):
    result = adapter.check_eligibility(
        member_id="MBR-ANCHOR-B", date_of_service="2025-06-01"
    )
    assert isinstance(result, dict)
    assert "eligible" in result


def test_search_knowledge_base(adapter):
    result = adapter.search_knowledge_base(query="prior authorization")
    assert "results" in result
    assert len(result["results"]) > 0


# ---------------------------------------------------------------------------
# Smoke test — all 19 methods callable without raising
# ---------------------------------------------------------------------------


def test_all_methods_callable(adapter):
    """Invoke every method with minimal params to confirm no AttributeError or TypeError."""
    # Methods that need no required params
    adapter.lookup_member(member_id="MBR-ANCHOR-B")
    adapter.get_member_coverage(member_id="MBR-ANCHOR-B")
    adapter.get_member_dependents(member_id="MBR-ANCHOR-B")
    adapter.search_claims(member_id="MBR-ANCHOR-B", limit=1)
    adapter.get_claim_detail(claim_id="CLM-MB-001")
    adapter.search_pharmacy_claims(member_id="MBR-ANCHOR-B", limit=1)
    adapter.check_benefits(plan_id="PLN-462CF8A4", service_category="Emergency Room")
    adapter.get_accumulator(member_id="MBR-ANCHOR-B")
    adapter.check_eligibility(member_id="MBR-ANCHOR-B", date_of_service="2025-06-01")
    adapter.get_plan_formulary(plan_id="PLN-462CF8A4")
    adapter.get_authorization(member_id="MBR-ANCHOR-B")
    adapter.submit_authorization_request(
        member_id="MBR-ANCHOR-B",
        provider_id="PRV-BE948BE3",
        service_description="Test",
        procedure_code="99213",
        diagnosis_code="M17.11",
    )
    adapter.initiate_appeal(member_id="MBR-ANCHOR-B", appeal_reason="Test appeal")
    adapter.search_providers(specialty="Cardiology", limit=1)
    adapter.get_interaction_history(member_id="MBR-ANCHOR-B", limit=1)

    # draft + submit case note
    draft = adapter.draft_case_note(
        member_id="MBR-ANCHOR-B", category="Billing", content="Test note"
    )
    if "draft_id" in draft:
        adapter.submit_case_note(draft_id=draft["draft_id"])

    adapter.search_knowledge_base(query="appeal")
    adapter.generate_document(
        document_type="id_card", member_id="MBR-ANCHOR-B"
    )
