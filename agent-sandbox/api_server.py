"""
Healthcare Sandbox API Query Layer
====================================
Loads the synthetic dataset and implements every tool from tool_schemas.json.
Use this as the backend for agent tool execution.

Usage:
    from api_server import HealthcareAPI
    api = HealthcareAPI()
    result = api.execute_tool("lookup_member", {"last_name": "Smith"})
"""

import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data" / "json"
KB_DIR = Path(__file__).parent / "knowledge-base"


class HealthcareAPI:
    """In-memory query layer over the synthetic healthcare dataset."""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._load_data()

    def _load_data(self):
        """Load all JSON data files into memory."""
        def load(filename):
            path = self.data_dir / filename
            if path.exists():
                with open(path) as f:
                    return json.load(f)
            return []

        self.members = load("members.json")
        self.dependents = load("dependents.json")
        self.employers = load("employers.json")
        self.plans = load("plans.json")
        self.benefits = load("benefits.json")
        self.providers = load("providers.json")
        self.eligibility = load("eligibility.json")
        self.medical_claims = load("medical_claims.json")
        self.claim_lines = load("claim_lines.json")
        self.pharmacy_claims = load("pharmacy_claims.json")
        self.authorizations = load("authorizations.json")
        self.accumulators = load("accumulators.json")
        self.call_logs = load("call_logs.json")
        self.secure_messages = load("secure_messages.json")
        self.case_notes = load("case_notes.json")
        self.agents = load("agents.json")
        self.medications = load("reference_medications.json")

        # Load knowledge base
        kb_path = KB_DIR / "knowledge_base.json"
        if kb_path.exists():
            with open(kb_path) as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = {}

        # Build indexes for fast lookup
        self._member_by_id = {m["member_id"]: m for m in self.members}
        self._dep_by_id = {d["member_id"]: d for d in self.dependents}
        self._plan_by_id = {p["plan_id"]: p for p in self.plans}
        self._provider_by_id = {p["provider_id"]: p for p in self.providers}
        self._employer_by_id = {e["employer_id"]: e for e in self.employers}

    # ── Tool Router ────────────────────────────────────────────────

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        """Route a tool call to the appropriate handler. Returns a dict."""
        handler = getattr(self, tool_name, None)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return handler(**params)
        except TypeError as e:
            return {"error": f"Invalid parameters: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    # ── Member Tools ───────────────────────────────────────────────

    def lookup_member(self, member_id=None, subscriber_id=None,
                      first_name=None, last_name=None, date_of_birth=None):
        results = []
        for m in self.members:
            if member_id and m["member_id"] == member_id:
                results.append(m); continue
            if subscriber_id and m["subscriber_id"] == subscriber_id:
                results.append(m); continue
            if last_name and m["last_name"].lower() == last_name.lower():
                if first_name and m["first_name"].lower() != first_name.lower():
                    continue
                results.append(m); continue
            if date_of_birth and m["date_of_birth"] == date_of_birth:
                results.append(m)
        if not results:
            return {"error": "No members found", "results": []}
        return {"results": results[:10], "total": len(results)}

    def get_member_coverage(self, member_id):
        member = self._member_by_id.get(member_id)
        if not member:
            return {"error": f"Member {member_id} not found"}
        plan = self._plan_by_id.get(member["plan_id"])
        employer = self._employer_by_id.get(member["employer_id"])
        accum = next((a for a in self.accumulators if a["member_id"] == member_id), None)
        elig = [e for e in self.eligibility if e["member_id"] == member_id]
        return {
            "member": member,
            "plan": plan,
            "employer": {"employer_id": employer["employer_id"], "name": employer["name"]} if employer else None,
            "accumulator": accum,
            "eligibility_periods": elig
        }

    def get_member_dependents(self, member_id):
        deps = [d for d in self.dependents
                if d.get("subscriber_member_id") == member_id]
        return {"member_id": member_id, "dependents": deps, "count": len(deps)}

    # ── Claims Tools ───────────────────────────────────────────────

    def search_claims(self, member_id=None, claim_status=None, date_from=None,
                      date_to=None, provider_id=None, diagnosis_code=None,
                      min_amount=None, limit=20):
        results = []
        for c in self.medical_claims:
            if member_id and c["member_id"] != member_id:
                continue
            if claim_status and c["claim_status"] != claim_status:
                continue
            if date_from and c["service_date"] < date_from:
                continue
            if date_to and c["service_date"] > date_to:
                continue
            if provider_id and c["provider_id"] != provider_id:
                continue
            if diagnosis_code and c["primary_diagnosis"] != diagnosis_code:
                continue
            if min_amount and c["total_billed"] < min_amount:
                continue
            results.append(c)
            if len(results) >= limit:
                break
        return {"results": results, "total": len(results)}

    def get_claim_detail(self, claim_id):
        claim = next((c for c in self.medical_claims if c["claim_id"] == claim_id), None)
        if not claim:
            return {"error": f"Claim {claim_id} not found"}
        lines = [cl for cl in self.claim_lines if cl["claim_id"] == claim_id]
        provider = self._provider_by_id.get(claim["provider_id"])
        member = self._member_by_id.get(claim["member_id"])
        return {
            "claim": claim,
            "claim_lines": lines,
            "provider": provider,
            "member_name": f"{member['first_name']} {member['last_name']}" if member else None
        }

    # ── Pharmacy Tools ─────────────────────────────────────────────

    def search_pharmacy_claims(self, member_id=None, medication_name=None,
                                medication_category=None, date_from=None,
                                date_to=None, formulary_status=None, limit=20):
        results = []
        for rx in self.pharmacy_claims:
            if member_id and rx["member_id"] != member_id:
                continue
            if medication_name and medication_name.lower() not in rx["medication_name"].lower():
                continue
            if medication_category and rx["medication_category"] != medication_category:
                continue
            if date_from and rx["fill_date"] < date_from:
                continue
            if date_to and rx["fill_date"] > date_to:
                continue
            if formulary_status and rx["formulary_status"] != formulary_status:
                continue
            results.append(rx)
            if len(results) >= limit:
                break
        return {"results": results, "total": len(results)}

    def get_plan_formulary(self, plan_id, medication_name=None, ndc=None):
        plan = self._plan_by_id.get(plan_id)
        if not plan:
            return {"error": f"Plan {plan_id} not found"}
        results = []
        for med in self.medications:
            if medication_name and medication_name.lower() not in med["name"].lower():
                continue
            if ndc and med["ndc"] != ndc:
                continue
            tier = "Generic" if med["avg_cost"] < 30 else "Preferred Brand" if med["avg_cost"] < 200 else "Non-Preferred" if med["avg_cost"] < 500 else "Specialty"
            copay_key = {"Generic": "copay_rx_generic", "Preferred Brand": "copay_rx_preferred_brand", "Non-Preferred": "copay_rx_non_preferred", "Specialty": "copay_rx_specialty"}
            results.append({
                "medication": med,
                "tier": tier,
                "copay": plan.get(copay_key.get(tier, "copay_rx_generic")),
                "prior_auth_required": med["avg_cost"] > 200,
                "step_therapy_required": med["category"] in ["Diabetes"] and med["avg_cost"] > 100
            })
        return {"plan_id": plan_id, "plan_name": plan["plan_name"], "formulary_results": results}

    # ── Benefits & Eligibility ─────────────────────────────────────

    def check_benefits(self, plan_id, service_category):
        plan = self._plan_by_id.get(plan_id)
        if not plan:
            return {"error": f"Plan {plan_id} not found"}
        matching = [b for b in self.benefits
                    if b["plan_id"] == plan_id and service_category.lower() in b["category"].lower()]
        return {
            "plan_id": plan_id,
            "plan_name": plan["plan_name"],
            "plan_type": plan["plan_type"],
            "tier": plan["tier"],
            "service_category": service_category,
            "benefits": matching,
            "plan_copays": {
                "pcp": plan["copay_pcp"],
                "specialist": plan["copay_specialist"],
                "er": plan["copay_er"],
                "urgent_care": plan["copay_urgent_care"]
            }
        }

    def get_accumulator(self, member_id):
        accum = next((a for a in self.accumulators if a["member_id"] == member_id), None)
        if not accum:
            return {"error": f"No accumulator found for {member_id}"}
        return accum

    def check_eligibility(self, member_id, date_of_service):
        periods = [e for e in self.eligibility if e["member_id"] == member_id]
        if not periods:
            return {"member_id": member_id, "eligible": False, "reason": "No eligibility records found"}
        for p in periods:
            start = p["effective_date"]
            end = p.get("termination_date") or "2099-12-31"
            if start <= date_of_service <= end and p["status"] in ["Active", "COBRA"]:
                return {"member_id": member_id, "eligible": True, "period": p}
        return {"member_id": member_id, "eligible": False, "reason": "Not eligible on date of service"}

    # ── Provider Tools ─────────────────────────────────────────────

    def search_providers(self, specialty=None, name=None, network_status=None,
                          accepting_new_patients=None, city=None, state=None, limit=20):
        results = []
        for p in self.providers:
            if specialty and specialty.lower() not in p["specialty"].lower():
                continue
            if name and name.lower() not in p["name"].lower():
                continue
            if network_status and p["network_status"] != network_status:
                continue
            if accepting_new_patients is not None and p["accepting_new_patients"] != accepting_new_patients:
                continue
            if city and p["address"]["city"].lower() != city.lower():
                continue
            if state and p["address"]["state"].lower() != state.lower():
                continue
            results.append(p)
            if len(results) >= limit:
                break
        return {"results": results, "total": len(results)}

    # ── Authorization Tools ────────────────────────────────────────

    def get_authorization(self, auth_id=None, member_id=None):
        if auth_id:
            auth = next((a for a in self.authorizations if a["auth_id"] == auth_id), None)
            if not auth:
                return {"error": f"Authorization {auth_id} not found"}
            return auth
        if member_id:
            auths = [a for a in self.authorizations if a["member_id"] == member_id]
            return {"member_id": member_id, "authorizations": auths, "count": len(auths)}
        return {"error": "Provide auth_id or member_id"}

    def submit_authorization_request(self, member_id, provider_id, service_description,
                                      procedure_code, diagnosis_code, urgency="Standard",
                                      clinical_notes=None):
        member = self._member_by_id.get(member_id)
        if not member:
            return {"error": f"Member {member_id} not found"}
        provider = self._provider_by_id.get(provider_id)
        if not provider:
            return {"error": f"Provider {provider_id} not found"}
        new_auth = {
            "auth_id": f"AUTH-SIM-{len(self.authorizations) + 1:04d}",
            "member_id": member_id,
            "plan_id": member["plan_id"],
            "provider_id": provider_id,
            "service_description": service_description,
            "procedure_code": procedure_code,
            "status": "Pending",
            "request_date": datetime.now().strftime("%Y-%m-%d"),
            "urgency": urgency,
            "clinical_notes": clinical_notes or "",
            "message": "Authorization request submitted for review."
        }
        return new_auth

    # ── Interaction History Tools ──────────────────────────────────

    def get_interaction_history(self, member_id, interaction_type="all",
                                 date_from=None, date_to=None, limit=20):
        result = {}
        if interaction_type in ("calls", "all"):
            calls = [c for c in self.call_logs if c["member_id"] == member_id]
            if date_from:
                calls = [c for c in calls if c["call_date"] >= date_from]
            if date_to:
                calls = [c for c in calls if c["call_date"] <= date_to]
            result["calls"] = calls[:limit]

        if interaction_type in ("messages", "all"):
            msgs = [m for m in self.secure_messages if m["member_id"] == member_id]
            if date_from:
                msgs = [m for m in msgs if m["sent_date"] >= date_from]
            if date_to:
                msgs = [m for m in msgs if m["sent_date"] <= date_to]
            result["messages"] = msgs[:limit]

        if interaction_type in ("case_notes", "all"):
            notes = [n for n in self.case_notes if n["member_id"] == member_id]
            if date_from:
                notes = [n for n in notes if n["created_date"] >= date_from]
            if date_to:
                notes = [n for n in notes if n["created_date"] <= date_to]
            result["case_notes"] = notes[:limit]

        return {"member_id": member_id, **result}

    def create_case_note(self, member_id, category, content,
                          related_claim_id=None, related_auth_id=None,
                          follow_up_required=False, follow_up_date=None):
        note = {
            "note_id": f"NOTE-SIM-{len(self.case_notes) + 1:04d}",
            "member_id": member_id,
            "category": category,
            "content": content,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "related_claim_id": related_claim_id,
            "related_auth_id": related_auth_id,
            "follow_up_required": follow_up_required,
            "follow_up_date": follow_up_date,
            "status": "Open",
            "message": "Case note created successfully."
        }
        return note

    # ── Knowledge Base Tools ───────────────────────────────────────

    def search_knowledge_base(self, query, section="all", keywords=None):
        query_lower = query.lower()
        results = []
        sections_to_search = [section] if section != "all" else list(self.knowledge_base.keys())
        for sec in sections_to_search:
            items = self.knowledge_base.get(sec, [])
            for item in items:
                searchable = json.dumps(item).lower()
                if query_lower in searchable:
                    results.append({"section": sec, **item})
                    continue
                if keywords:
                    if any(kw.lower() in searchable for kw in keywords):
                        results.append({"section": sec, **item})
        return {"query": query, "results": results[:10], "total": len(results)}

    # ── Appeal Tools ───────────────────────────────────────────────

    def initiate_appeal(self, member_id, appeal_reason, claim_id=None,
                         auth_id=None, supporting_documentation=None, expedited=False):
        member = self._member_by_id.get(member_id)
        if not member:
            return {"error": f"Member {member_id} not found"}
        appeal = {
            "appeal_id": f"APL-SIM-{datetime.now().strftime('%Y%m%d%H%M')}",
            "member_id": member_id,
            "claim_id": claim_id,
            "auth_id": auth_id,
            "appeal_reason": appeal_reason,
            "supporting_documentation": supporting_documentation,
            "expedited": expedited,
            "status": "Received",
            "submitted_date": datetime.now().strftime("%Y-%m-%d"),
            "expected_decision_date": "30 calendar days (72 hours if expedited)",
            "message": "Appeal submitted. You will receive written acknowledgment within 5 business days."
        }
        return appeal

    # ── Document Generation ────────────────────────────────────────

    def generate_document(self, document_type, member_id, claim_id=None, auth_id=None):
        member = self._member_by_id.get(member_id)
        if not member:
            return {"error": f"Member {member_id} not found"}
        plan = self._plan_by_id.get(member["plan_id"])
        return {
            "document_type": document_type,
            "member_id": member_id,
            "member_name": f"{member['first_name']} {member['last_name']}",
            "plan_name": plan["plan_name"] if plan else None,
            "claim_id": claim_id,
            "auth_id": auth_id,
            "status": "generated",
            "message": f"{document_type} document generated for {member['first_name']} {member['last_name']}. See document_templates.json for the template structure."
        }


# ── Quick test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    api = HealthcareAPI()
    print(f"Loaded: {len(api.members)} members, {len(api.medical_claims)} claims, {len(api.providers)} providers")

    # Test a few tools
    print("\n--- lookup_member(last_name='Smith') ---")
    r = api.execute_tool("lookup_member", {"last_name": "Smith"})
    print(f"  Found {r.get('total', 0)} members")

    print("\n--- search_claims(claim_status='Denied', limit=3) ---")
    r = api.execute_tool("search_claims", {"claim_status": "Denied", "limit": 3})
    print(f"  Found {r.get('total', 0)} denied claims")

    print("\n--- search_providers(specialty='Cardiology', limit=3) ---")
    r = api.execute_tool("search_providers", {"specialty": "Cardiology", "limit": 3})
    print(f"  Found {r.get('total', 0)} cardiologists")

    print("\n--- search_knowledge_base(query='deductible') ---")
    r = api.execute_tool("search_knowledge_base", {"query": "deductible"})
    print(f"  Found {r.get('total', 0)} KB results")

    print("\nAll tools operational.")
