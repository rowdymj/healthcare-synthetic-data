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
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "json"
KB_DIR = Path(__file__).parent / "knowledge-base"
RULES_DIR = Path(__file__).parent / "rules"
TEMPLATES_DIR = Path(__file__).parent / "templates"
TOOLS_PATH = Path(__file__).parent / "tools" / "tool_schemas.json"

_TEMPLATE_VAR_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def _load_allowed_tools():
    if not TOOLS_PATH.exists():
        return set()
    try:
        with open(TOOLS_PATH) as f:
            tool_schemas = json.load(f)
    except Exception:
        return set()
    tools = tool_schemas.get("anthropic_tools") or []
    return {t.get("name") for t in tools if t.get("name")}


ALLOWED_TOOLS = _load_allowed_tools()


def create_api(data_dir=None, force_json=False):
    """Factory: returns HealthcareDB if healthcare.db exists, else HealthcareAPI.

    Set force_json=True to always use the in-memory JSON backend.
    """
    if not force_json:
        db_path = (Path(data_dir) if data_dir else DATA_DIR).parent / "healthcare.db"
        if not db_path.exists():
            db_path = BASE_DIR / "data" / "healthcare.db"
        if db_path.exists():
            from db_backend import HealthcareDB
            print(f"[api_server] Using SQLite backend: {db_path.name}", file=sys.stderr)
            return HealthcareDB(db_path)
    print("[api_server] Using in-memory JSON backend", file=sys.stderr)
    return HealthcareAPI(data_dir)


class HealthcareAPI:
    """In-memory query layer over the synthetic healthcare dataset."""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._load_data()
        self._tool_allowlist = ALLOWED_TOOLS

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
        self.appeals = load("appeals.json")
        self.accumulators = load("accumulators.json")
        self.call_logs = load("call_logs.json")
        self.secure_messages = load("secure_messages.json")
        self.case_notes = load("case_notes.json")
        self.agents = load("agents.json")
        self.medications = load("reference_medications.json")
        self.reference_diagnosis_codes = load("reference_diagnosis_codes.json")
        self.reference_procedure_codes = load("reference_procedure_codes.json")
        self.reference_place_of_service = load("reference_place_of_service.json")

        # Load knowledge base
        kb_path = KB_DIR / "knowledge_base.json"
        if kb_path.exists():
            with open(kb_path) as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = {}

        # Load business rules
        rules_path = RULES_DIR / "business_rules.json"
        if rules_path.exists():
            with open(rules_path) as f:
                self.business_rules = json.load(f)
        else:
            self.business_rules = {}

        # Load document templates
        templates_path = TEMPLATES_DIR / "document_templates.json"
        if templates_path.exists():
            with open(templates_path) as f:
                self.document_templates = json.load(f).get("templates", [])
        else:
            self.document_templates = []

        # Build indexes for fast lookup
        self._member_by_id = {m["member_id"]: m for m in self.members}
        self._dep_by_id = {d["member_id"]: d for d in self.dependents}
        self._plan_by_id = {p["plan_id"]: p for p in self.plans}
        self._provider_by_id = {p["provider_id"]: p for p in self.providers}
        self._employer_by_id = {e["employer_id"]: e for e in self.employers}

    # ── Tool Router ────────────────────────────────────────────────

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        """Route a tool call to the appropriate handler. Returns a dict."""
        print(f"[data-source] {tool_name} -> JSON backend", file=sys.stderr)
        if self._tool_allowlist and tool_name not in self._tool_allowlist:
            return {"error": f"Unknown tool: {tool_name}"}
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
        benefits = [b for b in self.benefits if b["plan_id"] == member["plan_id"]]
        accum = next((a for a in self.accumulators if a["member_id"] == member_id), None)
        elig = [e for e in self.eligibility if e["member_id"] == member_id]
        return {
            "member": member,
            "plan": plan,
            "employer": {"employer_id": employer["employer_id"], "name": employer["name"]} if employer else None,
            "benefits": benefits,
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
        total = 0
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
            if min_amount is not None and c["total_billed"] < min_amount:
                continue
            total += 1
            if limit is None or len(results) < limit:
                results.append(c)
        return {"results": results, "total": total}

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
        total = 0
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
            total += 1
            if limit is None or len(results) < limit:
                results.append(rx)
        return {"results": results, "total": total}

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
        total = 0
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
            total += 1
            if limit is None or len(results) < limit:
                results.append(p)
        return {"results": results, "total": total}

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
        service_lower = (service_description or "").lower()
        if any(k in service_lower for k in ["mri", "ct", "pet", "scan", "imaging"]):
            service_category = "Imaging"
        elif any(k in service_lower for k in ["surgery", "surgical", "procedure"]):
            service_category = "Outpatient Surgery"
        elif any(k in service_lower for k in ["therapy", "pt", "ot", "st"]):
            service_category = "Physical Therapy"
        elif any(k in service_lower for k in ["dme", "durable", "equipment"]):
            service_category = "Durable Medical Equipment"
        else:
            service_category = "Other"
        new_auth = {
            "auth_id": f"AUTH-SIM-{len(self.authorizations) + 1:04d}",
            "member_id": member_id,
            "plan_id": member["plan_id"],
            "provider_id": provider_id,
            "auth_type": "Prior Authorization",
            "service_description": service_description,
            "procedure_code": procedure_code,
            "service_category": service_category,
            "status": "Pending",
            "request_date": datetime.now().strftime("%Y-%m-%d"),
            "decision_date": None,
            "effective_date": None,
            "expiration_date": None,
            "approved_units": None,
            "requested_units": 1,
            "denial_reason": None,
            "urgency": urgency,
            "clinical_notes": clinical_notes or "",
            "reviewer": None,
            "message": "Authorization request submitted for review."
        }
        self.authorizations.append(new_auth)
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
            "case_id": f"CASE-SIM-{len(self.case_notes) + 1:04d}",
            "author": "System",
            "category": category,
            "note_type": "Agent Note",
            "content": content,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "related_claim_id": related_claim_id,
            "related_auth_id": related_auth_id,
            "follow_up_required": follow_up_required,
            "follow_up_date": follow_up_date,
            "status": "Open",
            "message": "Case note created successfully."
        }
        self.case_notes.append(note)
        return note

    # ── Knowledge Base Tools ───────────────────────────────────────

    def search_knowledge_base(self, query, section="all", keywords=None):
        query_lower = query.lower()
        results = []
        kb_sections = list(self.knowledge_base.keys())
        rule_sections = [k for k in self.business_rules.keys() if not k.startswith("_")]
        reference_sections = [
            "reference_diagnosis_codes",
            "reference_procedure_codes",
            "reference_place_of_service",
            "reference_medications",
        ]

        sections_to_search = []
        if section == "all":
            sections_to_search = kb_sections + rule_sections + reference_sections
        elif section == "business_rules":
            sections_to_search = rule_sections
        elif section == "reference_data":
            sections_to_search = reference_sections
        else:
            sections_to_search = [section]

        for sec in sections_to_search:
            if sec in self.knowledge_base:
                items = self.knowledge_base.get(sec, [])
            elif sec in rule_sections:
                items = self.business_rules.get(sec, [])
            elif sec == "reference_diagnosis_codes":
                items = self.reference_diagnosis_codes
            elif sec == "reference_procedure_codes":
                items = self.reference_procedure_codes
            elif sec == "reference_place_of_service":
                items = self.reference_place_of_service
            elif sec == "reference_medications":
                items = self.medications
            else:
                items = []
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
        submitted_date = datetime.now().strftime("%Y-%m-%d")
        appeal = {
            "appeal_id": f"APL-SIM-{datetime.now().strftime('%Y%m%d%H%M')}",
            "member_id": member_id,
            "claim_id": claim_id,
            "auth_id": auth_id,
            "appeal_reason": appeal_reason,
            "supporting_documentation": supporting_documentation,
            "expedited": expedited,
            "status": "Received",
            "submitted_date": submitted_date,
            "received_date": submitted_date,
            "expected_decision_date": "30 calendar days (72 hours if expedited)",
            "message": "Appeal submitted. You will receive written acknowledgment within 5 business days."
        }
        self.appeals.append(appeal)
        return appeal

    # ── Document Generation ────────────────────────────────────────

    def _format_address(self, address):
        if not address:
            return ""
        parts = []
        line1 = address.get("line1")
        line2 = address.get("line2")
        city = address.get("city")
        state = address.get("state")
        zip_code = address.get("zip")
        if line1:
            parts.append(line1)
        if line2:
            parts.append(line2)
        city_state_zip = " ".join(p for p in [city, state, zip_code] if p)
        if city_state_zip:
            parts.append(city_state_zip)
        return "\n".join(parts)

    def _format_money(self, value):
        if value is None:
            return None
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    def _render_template(self, template_text, context):
        def repl(match):
            key = match.group(1)
            value = context.get(key)
            if value is None:
                return "N/A"
            return str(value)
        return _TEMPLATE_VAR_RE.sub(repl, template_text)

    def _get_template(self, document_type):
        for template in self.document_templates:
            if template.get("type") == document_type:
                return template
        return None

    def _find_appeal(self, appeal_id=None, member_id=None, claim_id=None, auth_id=None):
        if appeal_id:
            return next((a for a in self.appeals if a.get("appeal_id") == appeal_id), None)
        for a in reversed(self.appeals):
            if member_id and a.get("member_id") != member_id:
                continue
            if claim_id and a.get("claim_id") != claim_id:
                continue
            if auth_id and a.get("auth_id") != auth_id:
                continue
            return a
        return None

    def generate_document(self, document_type, member_id, claim_id=None, auth_id=None, appeal_id=None):
        member = self._member_by_id.get(member_id)
        if not member:
            return {"error": f"Member {member_id} not found"}
        template = self._get_template(document_type)
        if not template:
            return {"error": f"Unknown document type: {document_type}"}

        plan = self._plan_by_id.get(member["plan_id"])
        employer = self._employer_by_id.get(member.get("employer_id"))
        pcp = self._provider_by_id.get(member.get("pcp_provider_id"))
        current_date = datetime.now().strftime("%Y-%m-%d")

        context = {
            "member_name": f"{member['first_name']} {member['last_name']}",
            "member_id": member_id,
            "subscriber_id": member.get("subscriber_id"),
            "member_address": self._format_address(member.get("address")),
            "plan_name": plan.get("plan_name") if plan else None,
            "plan_type": plan.get("plan_type") if plan else None,
            "network_name": plan.get("network_name") if plan else None,
            "group_number": employer.get("employer_id") if employer else None,
            "pcp_name": pcp.get("name") if pcp else None,
            "pcp_phone": pcp.get("phone") if pcp else None,
            "copay_pcp": self._format_money(plan.get("copay_pcp")) if plan else None,
            "copay_specialist": self._format_money(plan.get("copay_specialist")) if plan else None,
            "copay_er": self._format_money(plan.get("copay_er")) if plan else None,
            "copay_rx_generic": self._format_money(plan.get("copay_rx_generic")) if plan else None,
            "deductible_individual": self._format_money(plan.get("deductible_individual")) if plan else None,
            "oop_max_individual": self._format_money(plan.get("out_of_pocket_max_individual")) if plan else None,
            "current_date": current_date,
        }

        if document_type in ("EOB", "denial_letter"):
            if not claim_id:
                return {"error": "claim_id is required for this document type"}
            claim = next((c for c in self.medical_claims if c["claim_id"] == claim_id), None)
            if not claim:
                return {"error": f"Claim {claim_id} not found"}
            provider = self._provider_by_id.get(claim.get("provider_id"))
            lines = [cl for cl in self.claim_lines if cl["claim_id"] == claim_id]
            procedure_description = lines[0]["procedure_description"] if lines else None
            context.update({
                "claim_id": claim_id,
                "service_date": claim.get("service_date"),
                "provider_name": provider.get("name") if provider else None,
                "diagnosis_description": claim.get("primary_diagnosis_description"),
                "procedure_description": procedure_description,
                "billed_amount": self._format_money(claim.get("total_billed")),
                "allowed_amount": self._format_money(claim.get("total_allowed")),
                "plan_paid": self._format_money(claim.get("total_plan_paid")),
                "member_responsibility": self._format_money(claim.get("total_member_responsibility")),
                "discount_amount": self._format_money((claim.get("total_billed") or 0) - (claim.get("total_allowed") or 0)),
                "deductible_applied": None,
                "copay_applied": None,
                "coinsurance_applied": None,
                "claim_status": claim.get("claim_status"),
                "check_number": claim.get("check_number"),
                "payment_date": claim.get("payment_date"),
                "denial_reason": claim.get("denial_reason"),
                "appeal_deadline": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            })

        if document_type in ("auth_approval_letter", "auth_denial_letter"):
            if not auth_id:
                return {"error": "auth_id is required for this document type"}
            auth = next((a for a in self.authorizations if a["auth_id"] == auth_id), None)
            if not auth:
                return {"error": f"Authorization {auth_id} not found"}
            provider = self._provider_by_id.get(auth.get("provider_id"))
            context.update({
                "auth_id": auth_id,
                "service_description": auth.get("service_description"),
                "provider_name": provider.get("name") if provider else None,
                "approved_units": auth.get("approved_units") or auth.get("requested_units"),
                "effective_date": auth.get("effective_date"),
                "expiration_date": auth.get("expiration_date"),
                "denial_reason": auth.get("denial_reason"),
                "reviewer_name": auth.get("reviewer"),
            })

        if document_type == "appeal_acknowledgment":
            appeal = self._find_appeal(appeal_id=appeal_id, member_id=member_id, claim_id=claim_id, auth_id=auth_id)
            if not appeal:
                return {"error": "appeal_id, claim_id, or auth_id must reference an existing appeal"}
            context.update({
                "appeal_id": appeal.get("appeal_id"),
                "claim_id": appeal.get("claim_id"),
                "auth_id": appeal.get("auth_id"),
                "received_date": appeal.get("received_date") or appeal.get("submitted_date"),
                "expected_decision_date": appeal.get("expected_decision_date"),
            })

        document_text = self._render_template(template.get("template_text", ""), context)
        return {
            "document_type": document_type,
            "template_id": template.get("template_id"),
            "member_id": member_id,
            "claim_id": claim_id,
            "auth_id": auth_id,
            "appeal_id": appeal_id,
            "status": "generated",
            "document_text": document_text,
            "variables": template.get("variables", []),
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
