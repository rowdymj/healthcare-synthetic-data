"""
Healthcare Sandbox — FastAPI Server
=====================================
A running REST API over the synthetic healthcare dataset.

Start:
    cd agent-sandbox
    uvicorn server:app --reload --port 8000

Then open: http://localhost:8000/docs  (Swagger UI)
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sys
from pathlib import Path

# Import the query layer — auto-detects SQLite backend if healthcare.db exists
sys.path.insert(0, str(Path(__file__).parent))
from api_server import create_api

# ── App Setup ──────────────────────────────────────────────────────

app = FastAPI(
    title="Healthcare Sandbox API",
    description="""
A synthetic healthcare data platform for prototyping AI agents.

**4,297 covered lives** across 25 employers, 50 plans, 300 providers,
13,841 medical claims, 7,055 pharmacy claims, and full interaction history.

All data is synthetic. No real PHI/PII.

## Quick Start
- Browse endpoints below and click "Try it out"
- Use the `/tool` endpoint to execute any agent tool by name
- All member IDs follow the pattern `MBR-XXXXXXXX`
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api = create_api()


# ── Pydantic Models ────────────────────────────────────────────────

class ToolRequest(BaseModel):
    """Execute any agent tool by name."""
    tool_name: str = Field(..., description="Tool name from tool_schemas.json", example="lookup_member")
    params: dict = Field(default={}, description="Tool parameters", example={"last_name": "Smith"})

class AuthRequest(BaseModel):
    member_id: str
    provider_id: str
    service_description: str
    procedure_code: str
    diagnosis_code: str
    urgency: Optional[str] = "Standard"
    clinical_notes: Optional[str] = None

class DraftCaseNoteRequest(BaseModel):
    member_id: str
    category: str
    content: str
    related_claim_id: Optional[str] = None
    related_auth_id: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_date: Optional[str] = None

class SubmitCaseNoteRequest(BaseModel):
    draft_id: str

class AppealRequest(BaseModel):
    member_id: str
    appeal_reason: str
    claim_id: Optional[str] = None
    auth_id: Optional[str] = None
    supporting_documentation: Optional[str] = None
    expedited: Optional[bool] = False

class DocumentRequest(BaseModel):
    document_type: str = Field(..., description="EOB, denial_letter, auth_approval_letter, auth_denial_letter, id_card, welcome_letter, appeal_acknowledgment")
    member_id: str
    claim_id: Optional[str] = None
    auth_id: Optional[str] = None
    appeal_id: Optional[str] = None


# ── Generic Tool Endpoint ──────────────────────────────────────────

@app.post("/tool", tags=["Agent Tools"], summary="Execute any tool by name")
def execute_tool(request: ToolRequest):
    """
    Generic endpoint for agent tool execution. Pass the tool name and params
    exactly as defined in tool_schemas.json.

    This is the endpoint your agent framework calls.
    """
    result = api.execute_tool(request.tool_name, request.params)
    # Only 404 for truly unknown tools; data-not-found errors return 200
    # so agent frameworks can read the error message in the response body
    if "error" in result and str(result["error"]).startswith("Unknown tool:"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Members ────────────────────────────────────────────────────────

@app.get("/api/members", tags=["Members"], summary="Search members")
def search_members(
    member_id: Optional[str] = Query(None, description="Exact member ID"),
    subscriber_id: Optional[str] = Query(None, description="Subscriber ID"),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """Search for members by ID, name, or date of birth."""
    params = {k: v for k, v in {
        "member_id": member_id, "subscriber_id": subscriber_id,
        "first_name": first_name, "last_name": last_name,
        "date_of_birth": date_of_birth,
    }.items() if v is not None}
    if not params:
        return {"results": api.members[:20], "total": len(api.members), "note": "Showing first 20. Use filters to narrow."}
    return api.lookup_member(**params)


@app.get("/api/members/{member_id}", tags=["Members"], summary="Get member by ID")
def get_member(member_id: str):
    """Get a single member's full profile."""
    result = api.lookup_member(member_id=member_id)
    if not result.get("results"):
        raise HTTPException(status_code=404, detail=f"Member {member_id} not found")
    return result["results"][0]


@app.get("/api/members/{member_id}/coverage", tags=["Members"], summary="Get member coverage details")
def get_member_coverage(member_id: str):
    """Get plan, benefits, deductible/OOP status for a member."""
    return api.get_member_coverage(member_id)


@app.get("/api/members/{member_id}/dependents", tags=["Members"], summary="Get member dependents")
def get_member_dependents(member_id: str):
    """List all dependents enrolled under this subscriber."""
    return api.get_member_dependents(member_id)


@app.get("/api/members/{member_id}/accumulator", tags=["Members"], summary="Get deductible/OOP status")
def get_accumulator(member_id: str):
    """Get current plan year deductible and out-of-pocket accumulator."""
    return api.get_accumulator(member_id)


@app.get("/api/members/{member_id}/eligibility", tags=["Members"], summary="Check eligibility")
def check_eligibility(
    member_id: str,
    date_of_service: str = Query(None, description="YYYY-MM-DD — defaults to today if omitted"),
):
    """Verify if a member is eligible on a specific date."""
    if not date_of_service:
        date_of_service = datetime.now().strftime("%Y-%m-%d")
    return api.check_eligibility(member_id, date_of_service)


@app.get("/api/members/{member_id}/interactions", tags=["Members"], summary="Get interaction history")
def get_interactions(
    member_id: str,
    interaction_type: Optional[str] = Query("all", description="calls, messages, case_notes, or all"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: Optional[int] = Query(20),
):
    """Get call logs, secure messages, and case notes for a member."""
    return api.get_interaction_history(member_id, interaction_type, date_from, date_to, limit)


# ── Claims ─────────────────────────────────────────────────────────

@app.get("/api/claims", tags=["Claims"], summary="Search medical claims")
def search_claims(
    member_id: Optional[str] = Query(None),
    claim_status: Optional[str] = Query(None, description="Paid, Denied, Pending, Adjusted, Appealed"),
    date_from: Optional[str] = Query(None, description="Service date start YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="Service date end YYYY-MM-DD"),
    provider_id: Optional[str] = Query(None),
    diagnosis_code: Optional[str] = Query(None, description="ICD-10 code"),
    min_amount: Optional[float] = Query(None),
    limit: Optional[int] = Query(20),
):
    """Search medical claims with filters."""
    params = {k: v for k, v in {
        "member_id": member_id, "claim_status": claim_status,
        "date_from": date_from, "date_to": date_to,
        "provider_id": provider_id, "diagnosis_code": diagnosis_code,
        "min_amount": min_amount, "limit": limit,
    }.items() if v is not None}
    return api.search_claims(**params)


@app.get("/api/claims/{claim_id}", tags=["Claims"], summary="Get claim detail")
def get_claim_detail(claim_id: str):
    """Get full claim detail with all line items."""
    result = api.get_claim_detail(claim_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Pharmacy ───────────────────────────────────────────────────────

@app.get("/api/pharmacy-claims", tags=["Pharmacy"], summary="Search pharmacy claims")
def search_pharmacy_claims(
    member_id: Optional[str] = Query(None),
    medication_name: Optional[str] = Query(None, description="Partial match"),
    medication_category: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    formulary_status: Optional[str] = Query(None, description="Preferred, Non-Preferred, Specialty"),
    limit: Optional[int] = Query(20),
):
    """Search prescription/pharmacy claims."""
    params = {k: v for k, v in {
        "member_id": member_id, "medication_name": medication_name,
        "medication_category": medication_category, "date_from": date_from,
        "date_to": date_to, "formulary_status": formulary_status, "limit": limit,
    }.items() if v is not None}
    return api.search_pharmacy_claims(**params)


@app.get("/api/formulary/{plan_id}", tags=["Pharmacy"], summary="Check formulary")
def get_formulary(
    plan_id: str,
    medication_name: Optional[str] = Query(None),
    ndc: Optional[str] = Query(None),
):
    """Look up medication coverage, tier, and copay for a plan."""
    return api.get_plan_formulary(plan_id, medication_name, ndc)


# ── Providers ──────────────────────────────────────────────────────

@app.get("/api/providers", tags=["Providers"], summary="Search providers")
def search_providers(
    specialty: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    network_status: Optional[str] = Query(None, description="In-Network or Out-of-Network"),
    accepting_new_patients: Optional[bool] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    limit: Optional[int] = Query(20),
):
    """Search for healthcare providers."""
    params = {k: v for k, v in {
        "specialty": specialty, "name": name, "network_status": network_status,
        "accepting_new_patients": accepting_new_patients,
        "city": city, "state": state, "limit": limit,
    }.items() if v is not None}
    return api.search_providers(**params)


# ── Plans & Benefits ───────────────────────────────────────────────

@app.get("/api/plans", tags=["Plans & Benefits"], summary="List all plans")
def list_plans():
    """List all benefit plans."""
    return {"results": api.plans, "total": len(api.plans)}


@app.get("/api/plans/{plan_id}", tags=["Plans & Benefits"], summary="Get plan details")
def get_plan(plan_id: str):
    """Get full plan details including copays, deductibles, and coinsurance."""
    plan = api._plan_by_id.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return plan


@app.get("/api/plans/{plan_id}/benefits", tags=["Plans & Benefits"], summary="Check benefits")
def check_benefits(
    plan_id: str,
    service_category: Optional[str] = Query(None, description="e.g. Primary Care Visit, Emergency Room, Physical Therapy"),
):
    """Check what a plan covers for a service category."""
    if service_category:
        return api.check_benefits(plan_id, service_category)
    benefits = [b for b in api.benefits if b["plan_id"] == plan_id]
    return {"plan_id": plan_id, "benefits": benefits, "total": len(benefits)}


# ── Authorizations ─────────────────────────────────────────────────

@app.get("/api/authorizations", tags=["Authorizations"], summary="Search authorizations")
def search_authorizations(
    member_id: Optional[str] = Query(None),
    auth_id: Optional[str] = Query(None),
):
    """Look up authorizations by ID or member."""
    if auth_id:
        return api.get_authorization(auth_id=auth_id)
    if member_id:
        return api.get_authorization(member_id=member_id)
    return {"results": api.authorizations[:20], "total": len(api.authorizations)}


@app.post("/api/authorizations", tags=["Authorizations"], summary="Submit auth request")
def submit_auth(request: AuthRequest):
    """Submit a new prior authorization request."""
    return api.submit_authorization_request(**request.dict())


# ── Appeals ────────────────────────────────────────────────────────

@app.post("/api/appeals", tags=["Appeals"], summary="Initiate an appeal")
def initiate_appeal(request: AppealRequest):
    """File an appeal on a denied claim or authorization."""
    return api.initiate_appeal(**request.dict())


# ── Case Notes ─────────────────────────────────────────────────────

@app.post("/api/case-notes/draft", tags=["Case Notes"], summary="Draft a case note")
def draft_case_note(request: DraftCaseNoteRequest):
    """Draft a case note for user review. Returns a preview — not saved until submitted."""
    return api.draft_case_note(**request.dict())

@app.post("/api/case-notes/submit", tags=["Case Notes"], summary="Submit a drafted case note")
def submit_case_note(request: SubmitCaseNoteRequest):
    """Submit a previously drafted case note after user approval."""
    return api.submit_case_note(**request.dict())


# ── Documents ──────────────────────────────────────────────────────

@app.post("/api/documents", tags=["Documents"], summary="Generate a document")
def generate_document(request: DocumentRequest):
    """Generate a member-facing document (EOB, denial letter, ID card, etc.)."""
    return api.generate_document(**request.dict())


# ── Knowledge Base ─────────────────────────────────────────────────

@app.get("/api/knowledge-base", tags=["Knowledge Base"], summary="Search knowledge base")
def search_kb(
    query: str = Query(..., description="Natural language search"),
    section: Optional[str] = Query("all", description="plan_policies, coverage_guidelines, member_faq, business_rules, reference_data, etc."),
):
    """Search plan policies, FAQs, coverage guidelines, and formulary info."""
    return api.search_knowledge_base(query, section)


# ── Employers ──────────────────────────────────────────────────────

@app.get("/api/employers", tags=["Employers"], summary="List employers")
def list_employers():
    """List all employer organizations."""
    return {"results": api.employers, "total": len(api.employers)}


# ── Stats ──────────────────────────────────────────────────────────

@app.get("/api/stats", tags=["Platform"], summary="Dataset statistics")
def get_stats():
    """Get summary statistics for the entire dataset."""
    total_billed = sum(c["total_billed"] for c in api.medical_claims)
    total_paid = sum(c["total_plan_paid"] for c in api.medical_claims)
    total_rx = sum(c["total_cost"] for c in api.pharmacy_claims)
    denied = sum(1 for c in api.medical_claims if c["claim_status"] == "Denied")
    return {
        "entities": {
            "employers": len(api.employers),
            "plans": len(api.plans),
            "providers": len(api.providers),
            "members": len(api.members),
            "dependents": len(api.dependents),
            "total_covered_lives": len(api.members) + len(api.dependents),
            "medical_claims": len(api.medical_claims),
            "claim_lines": len(api.claim_lines),
            "pharmacy_claims": len(api.pharmacy_claims),
            "authorizations": len(api.authorizations),
            "call_logs": len(api.call_logs),
            "secure_messages": len(api.secure_messages),
            "case_notes": len(api.case_notes),
        },
        "financials": {
            "total_medical_billed": round(total_billed, 2),
            "total_medical_paid": round(total_paid, 2),
            "total_pharmacy_cost": round(total_rx, 2),
        },
        "rates": {
            "claim_denial_rate": round(denied / len(api.medical_claims) * 100, 1),
            "auth_approval_rate": round(sum(1 for a in api.authorizations if a["status"] == "Approved") / len(api.authorizations) * 100, 1),
        }
    }


@app.get("/", tags=["Platform"], summary="Health check")
def root():
    return {
        "service": "Healthcare Sandbox API",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0",
    }
