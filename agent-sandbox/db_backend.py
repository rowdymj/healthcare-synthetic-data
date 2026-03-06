"""
Healthcare Sandbox — SQLite Backend
=====================================
Drop-in replacement for the in-memory JSON query layer.
Same interface as HealthcareAPI, backed by healthcare.db.

Auto-detected by api_server.py when data/healthcare.db exists.
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "data" / "healthcare.db"


def _dict_factory(cursor, row):
    """Return query results as dicts instead of tuples."""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


def _bool_fields(d, *keys):
    """Convert SQLite 0/1 ints back to Python bools for specific keys."""
    for k in keys:
        if k in d and d[k] is not None:
            d[k] = bool(d[k])
    return d


def _unflatten_address(d):
    """Reconstruct nested address object from flat address_* columns."""
    addr_keys = ["address_line1", "address_line2", "address_city", "address_state", "address_zip"]
    if any(k in d for k in addr_keys):
        d["address"] = {
            "line1": d.pop("address_line1", None),
            "line2": d.pop("address_line2", None),
            "city": d.pop("address_city", None),
            "state": d.pop("address_state", None),
            "zip": d.pop("address_zip", None),
        }
    return d


class HealthcareDB:
    """SQLite-backed query layer — same interface as HealthcareAPI."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = _dict_factory
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")

        # Load non-DB resources (knowledge base, templates, rules)
        base = Path(__file__).parent
        self.knowledge_base = self._load_json(base / "knowledge-base" / "knowledge_base.json", {})
        self.business_rules = self._load_json(base / "rules" / "business_rules.json", {})
        self.document_templates = self._load_json(
            base / "templates" / "document_templates.json", {}
        ).get("templates", [])

        # Tool allowlist
        from api_server import ALLOWED_TOOLS
        self._tool_allowlist = ALLOWED_TOOLS

        # In-memory stores for write tools (append-only, reset on restart)
        self._sim_authorizations = []
        self._sim_appeals = []
        self._sim_case_notes = []
        self.draft_notes = {}

    @staticmethod
    def _load_json(path, default=None):
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default if default is not None else []

    def _q(self, sql, params=()):
        """Execute a read query, return list of dicts."""
        return self._conn.execute(sql, params).fetchall()

    def _one(self, sql, params=()):
        """Execute a read query, return single dict or None."""
        row = self._conn.execute(sql, params).fetchone()
        return row

    # ── Tool Router ────────────────────────────────────────────────

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        print(f"[data-source] {tool_name} -> SQLite backend", file=sys.stderr)
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

    def _enrich_member(self, m):
        """Add chronic_conditions array and unflatten address."""
        if m is None:
            return None
        _unflatten_address(m)
        conds = self._q(
            "SELECT condition_name FROM member_chronic_conditions WHERE member_id = ?",
            (m["member_id"],)
        )
        m["chronic_conditions"] = [c["condition_name"] for c in conds]
        return m

    def lookup_member(self, member_id=None, subscriber_id=None,
                      first_name=None, last_name=None, date_of_birth=None):
        conditions = []
        params = []
        if member_id:
            conditions.append("member_id = ?")
            params.append(member_id)
        if subscriber_id:
            conditions.append("subscriber_id = ?")
            params.append(subscriber_id)
        if last_name:
            conditions.append("LOWER(last_name) = LOWER(?)")
            params.append(last_name)
        if first_name:
            conditions.append("LOWER(first_name) = LOWER(?)")
            params.append(first_name)
        if date_of_birth:
            conditions.append("date_of_birth = ?")
            params.append(date_of_birth)

        if not conditions:
            return {"error": "No search criteria provided", "results": []}

        # Get total count of all matches
        where = " AND ".join(conditions)
        count_sql = f"SELECT COUNT(*) as cnt FROM members WHERE {where}"
        count_result = self._conn.execute(count_sql, params).fetchone()
        total = count_result['cnt'] if count_result else 0
        
        # Get paginated results (limit 10)
        sql = f"SELECT * FROM members WHERE {where} LIMIT 10"
        results = self._q(sql, params)
        for r in results:
            self._enrich_member(r)
        if not results:
            return {"error": "No members found", "results": []}
        return {"results": results, "total": total}

    def get_member_coverage(self, member_id):
        member = self._one("SELECT * FROM members WHERE member_id = ?", (member_id,))
        if not member:
            return {"error": f"Member {member_id} not found"}
        self._enrich_member(member)

        plan = self._one("SELECT * FROM plans WHERE plan_id = ?", (member["plan_id"],))
        employer = self._one("SELECT employer_id, name FROM employers WHERE employer_id = ?",
                             (member["employer_id"],))
        benefits = self._q("SELECT * FROM benefits WHERE plan_id = ?", (member["plan_id"],))
        for b in benefits:
            _bool_fields(b, "requires_auth", "requires_referral")
        accum = self._one("SELECT * FROM accumulators WHERE member_id = ?", (member_id,))
        elig = self._q("SELECT * FROM eligibility WHERE member_id = ?", (member_id,))
        for e in elig:
            _bool_fields(e, "cobra_flag")
        return {
            "member": member,
            "plan": plan,
            "employer": employer,
            "benefits": benefits,
            "accumulator": accum,
            "eligibility_periods": elig,
        }

    def get_member_dependents(self, member_id):
        deps = self._q("SELECT * FROM dependents WHERE subscriber_member_id = ?", (member_id,))
        return {"member_id": member_id, "dependents": deps, "count": len(deps)}

    # ── Claims Tools ───────────────────────────────────────────────

    def search_claims(self, member_id=None, claim_status=None, date_from=None,
                      date_to=None, provider_id=None, diagnosis_code=None,
                      min_amount=None, limit=20):
        conditions = []
        params = []
        if member_id:
            conditions.append("member_id = ?"); params.append(member_id)
        if claim_status:
            conditions.append("claim_status = ?"); params.append(claim_status)
        if date_from:
            conditions.append("service_date >= ?"); params.append(date_from)
        if date_to:
            conditions.append("service_date <= ?"); params.append(date_to)
        if provider_id:
            conditions.append("provider_id = ?"); params.append(provider_id)
        if diagnosis_code:
            conditions.append("primary_diagnosis = ?"); params.append(diagnosis_code)
        if min_amount is not None:
            conditions.append("total_billed >= ?"); params.append(min_amount)

        where = " AND ".join(conditions) if conditions else "1=1"

        count_sql = f"SELECT COUNT(*) as cnt FROM medical_claims WHERE {where}"
        total = self._one(count_sql, params)["cnt"]

        sql = f"SELECT * FROM medical_claims WHERE {where}"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        results = self._q(sql, params)
        return {"results": results, "total": total}

    def get_claim_detail(self, claim_id):
        claim = self._one("SELECT * FROM medical_claims WHERE claim_id = ?", (claim_id,))
        if not claim:
            return {"error": f"Claim {claim_id} not found"}
        lines = self._q("SELECT * FROM claim_lines WHERE claim_id = ?", (claim_id,))
        provider = self._one("SELECT * FROM providers WHERE provider_id = ?",
                             (claim["provider_id"],))
        if provider:
            _unflatten_address(provider)
            provider["languages"] = [r["language"] for r in self._q(
                "SELECT language FROM provider_languages WHERE provider_id = ?",
                (provider["provider_id"],)
            )]
            _bool_fields(provider, "accepting_new_patients")
        member = self._one("SELECT first_name, last_name FROM members WHERE member_id = ?",
                           (claim["member_id"],))
        return {
            "claim": claim,
            "claim_lines": lines,
            "provider": provider,
            "member_name": f"{member['first_name']} {member['last_name']}" if member else None,
        }

    # ── Pharmacy Tools ─────────────────────────────────────────────

    def search_pharmacy_claims(self, member_id=None, medication_name=None,
                                medication_category=None, date_from=None,
                                date_to=None, formulary_status=None, limit=20):
        conditions = []
        params = []
        if member_id:
            conditions.append("member_id = ?"); params.append(member_id)
        if medication_name:
            conditions.append("LOWER(medication_name) LIKE ?")
            params.append(f"%{medication_name.lower()}%")
        if medication_category:
            conditions.append("medication_category = ?"); params.append(medication_category)
        if date_from:
            conditions.append("fill_date >= ?"); params.append(date_from)
        if date_to:
            conditions.append("fill_date <= ?"); params.append(date_to)
        if formulary_status:
            conditions.append("formulary_status = ?"); params.append(formulary_status)

        where = " AND ".join(conditions) if conditions else "1=1"
        total = self._one(f"SELECT COUNT(*) as cnt FROM pharmacy_claims WHERE {where}", params)["cnt"]

        sql = f"SELECT * FROM pharmacy_claims WHERE {where}"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        results = self._q(sql, params)
        for r in results:
            _bool_fields(r, "prior_auth_required")
        return {"results": results, "total": total}

    def get_plan_formulary(self, plan_id, medication_name=None, ndc=None):
        plan = self._one("SELECT * FROM plans WHERE plan_id = ?", (plan_id,))
        if not plan:
            return {"error": f"Plan {plan_id} not found"}

        conditions = []
        params = []
        if medication_name:
            conditions.append("LOWER(name) LIKE ?")
            params.append(f"%{medication_name.lower()}%")
        if ndc:
            conditions.append("ndc = ?"); params.append(ndc)

        where = " AND ".join(conditions) if conditions else "1=1"
        meds = self._q(f"SELECT * FROM reference_medications WHERE {where}", params)

        results = []
        copay_map = {
            "Generic": "copay_rx_generic",
            "Preferred Brand": "copay_rx_preferred_brand",
            "Non-Preferred": "copay_rx_non_preferred",
            "Specialty": "copay_rx_specialty",
        }
        for med in meds:
            cost = med["avg_cost"] or 0
            tier = ("Generic" if cost < 30 else
                    "Preferred Brand" if cost < 200 else
                    "Non-Preferred" if cost < 500 else "Specialty")
            results.append({
                "medication": med,
                "tier": tier,
                "copay": plan.get(copay_map.get(tier, "copay_rx_generic")),
                "prior_auth_required": cost > 200,
                "step_therapy_required": med["category"] in ["Diabetes"] and cost > 100,
            })
        return {"plan_id": plan_id, "plan_name": plan["plan_name"], "formulary_results": results}

    # ── Benefits & Eligibility ─────────────────────────────────────

    def check_benefits(self, plan_id, service_category):
        plan = self._one("SELECT * FROM plans WHERE plan_id = ?", (plan_id,))
        if not plan:
            return {"error": f"Plan {plan_id} not found"}
        benefits = self._q(
            "SELECT * FROM benefits WHERE plan_id = ? AND LOWER(category) LIKE ?",
            (plan_id, f"%{service_category.lower()}%")
        )
        for b in benefits:
            _bool_fields(b, "requires_auth", "requires_referral")
        return {
            "plan_id": plan_id,
            "plan_name": plan["plan_name"],
            "plan_type": plan["plan_type"],
            "tier": plan["tier"],
            "service_category": service_category,
            "benefits": benefits,
            "plan_copays": {
                "pcp": plan["copay_pcp"],
                "specialist": plan["copay_specialist"],
                "er": plan["copay_er"],
                "urgent_care": plan["copay_urgent_care"],
            },
        }

    def get_accumulator(self, member_id):
        accum = self._one("SELECT * FROM accumulators WHERE member_id = ?", (member_id,))
        if not accum:
            return {"error": f"No accumulator found for {member_id}"}
        return accum

    def check_eligibility(self, member_id, date_of_service):
        periods = self._q("SELECT * FROM eligibility WHERE member_id = ?", (member_id,))
        for p in periods:
            _bool_fields(p, "cobra_flag")
        if not periods:
            return {"member_id": member_id, "eligible": False, "reason": "No eligibility records found"}
        for p in periods:
            start = p["effective_date"]
            end = p.get("termination_date") or "2099-12-31"
            if start <= date_of_service <= end and p["status"] in ["Active", "COBRA"]:
                return {"member_id": member_id, "eligible": True, "period": p}
        return {"member_id": member_id, "eligible": False, "reason": "Not eligible on date of service"}

    # ── Provider Tools ─────────────────────────────────────────────

    def _enrich_provider(self, p):
        if p is None:
            return None
        _unflatten_address(p)
        _bool_fields(p, "accepting_new_patients")
        langs = self._q("SELECT language FROM provider_languages WHERE provider_id = ?",
                        (p["provider_id"],))
        p["languages"] = [l["language"] for l in langs]
        return p

    def search_providers(self, specialty=None, name=None, network_status=None,
                          accepting_new_patients=None, city=None, state=None, limit=20):
        conditions = []
        params = []
        if specialty:
            conditions.append("LOWER(specialty) LIKE ?")
            params.append(f"%{specialty.lower()}%")
        if name:
            conditions.append("LOWER(name) LIKE ?")
            params.append(f"%{name.lower()}%")
        if network_status:
            conditions.append("network_status = ?"); params.append(network_status)
        if accepting_new_patients is not None:
            conditions.append("accepting_new_patients = ?")
            params.append(1 if accepting_new_patients else 0)
        if city:
            conditions.append("LOWER(address_city) = LOWER(?)")
            params.append(city)
        if state:
            conditions.append("LOWER(address_state) = LOWER(?)")
            params.append(state)

        where = " AND ".join(conditions) if conditions else "1=1"
        total = self._one(f"SELECT COUNT(*) as cnt FROM providers WHERE {where}", params)["cnt"]

        sql = f"SELECT * FROM providers WHERE {where}"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        results = self._q(sql, params)
        for r in results:
            self._enrich_provider(r)
        return {"results": results, "total": total}

    # ── Authorization Tools ────────────────────────────────────────

    def get_authorization(self, auth_id=None, member_id=None):
        if auth_id:
            auth = self._one("SELECT * FROM authorizations WHERE auth_id = ?", (auth_id,))
            if not auth:
                return {"error": f"Authorization {auth_id} not found"}
            return auth
        if member_id:
            auths = self._q("SELECT * FROM authorizations WHERE member_id = ?", (member_id,))
            return {"member_id": member_id, "authorizations": auths, "count": len(auths)}
        return {"error": "Provide auth_id or member_id"}

    def submit_authorization_request(self, member_id, provider_id, service_description,
                                      procedure_code, diagnosis_code, urgency="Standard",
                                      clinical_notes=None):
        member = self._one("SELECT * FROM members WHERE member_id = ?", (member_id,))
        if not member:
            return {"error": f"Member {member_id} not found"}
        provider = self._one("SELECT * FROM providers WHERE provider_id = ?", (provider_id,))
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

        # Count existing auths for unique ID
        existing = self._one("SELECT COUNT(*) as cnt FROM authorizations")["cnt"]
        new_auth = {
            "auth_id": f"AUTH-SIM-{existing + len(self._sim_authorizations) + 1:04d}",
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
            "message": "Authorization request submitted for review.",
        }
        self._sim_authorizations.append(new_auth)
        return new_auth

    # ── Interaction History Tools ──────────────────────────────────

    def get_interaction_history(self, member_id, interaction_type="all",
                                 date_from=None, date_to=None, limit=20):
        result = {}
        if interaction_type in ("calls", "all"):
            conditions = ["member_id = ?"]
            params = [member_id]
            if date_from:
                conditions.append("call_date >= ?"); params.append(date_from)
            if date_to:
                conditions.append("call_date <= ?"); params.append(date_to)
            where = " AND ".join(conditions)
            calls = self._q(f"SELECT * FROM call_logs WHERE {where} LIMIT ?", params + [limit])
            for c in calls:
                _bool_fields(c, "first_call_resolution")
            result["calls"] = calls

        if interaction_type in ("messages", "all"):
            conditions = ["member_id = ?"]
            params = [member_id]
            if date_from:
                conditions.append("sent_date >= ?"); params.append(date_from)
            if date_to:
                conditions.append("sent_date <= ?"); params.append(date_to)
            where = " AND ".join(conditions)
            result["messages"] = self._q(
                f"SELECT * FROM secure_messages WHERE {where} LIMIT ?", params + [limit])

        if interaction_type in ("case_notes", "all"):
            conditions = ["member_id = ?"]
            params = [member_id]
            if date_from:
                conditions.append("created_date >= ?"); params.append(date_from)
            if date_to:
                conditions.append("created_date <= ?"); params.append(date_to)
            where = " AND ".join(conditions)
            notes = self._q(f"SELECT * FROM case_notes WHERE {where} LIMIT ?", params + [limit])
            for n in notes:
                _bool_fields(n, "follow_up_required")
            result["case_notes"] = notes

        return {"member_id": member_id, **result}

    def draft_case_note(self, member_id, category, content,
                         related_claim_id=None, related_auth_id=None,
                         follow_up_required=False, follow_up_date=None):
        existing = self._one("SELECT COUNT(*) as cnt FROM case_notes")["cnt"]
        draft_id = f"DRAFT-{existing + len(self._sim_case_notes) + len(self.draft_notes) + 1:04d}"
        note = {
            "draft_id": draft_id,
            "note_id": f"NOTE-SIM-{existing + len(self._sim_case_notes) + 1:04d}",
            "member_id": member_id,
            "case_id": f"CASE-SIM-{existing + len(self._sim_case_notes) + 1:04d}",
            "author": "System",
            "category": category,
            "note_type": "Agent Note",
            "content": content,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "related_claim_id": related_claim_id,
            "related_auth_id": related_auth_id,
            "follow_up_required": follow_up_required,
            "follow_up_date": follow_up_date,
            "status": "Draft",
            "message": "Draft created. Present this to the user for review, then call submit_case_note with the draft_id to save.",
        }
        self.draft_notes[draft_id] = note
        return note

    def submit_case_note(self, draft_id):
        if draft_id not in self.draft_notes:
            return {"error": f"Draft not found: {draft_id}. Call draft_case_note first."}
        note = self.draft_notes.pop(draft_id)
        del note["draft_id"]
        note["status"] = "Open"
        note["message"] = "Case note submitted successfully."
        self._sim_case_notes.append(note)
        return note

    # ── Knowledge Base Tools ───────────────────────────────────────

    def search_knowledge_base(self, query, section="all", keywords=None):
        query_lower = query.lower()
        results = []
        kb_sections = list(self.knowledge_base.keys())
        rule_sections = [k for k in self.business_rules.keys() if not k.startswith("_")]

        # Reference data comes from DB now
        reference_map = {
            "reference_diagnosis_codes": "SELECT code, description, category FROM reference_diagnosis_codes",
            "reference_procedure_codes": "SELECT code, description, category, avg_cost FROM reference_procedure_codes",
            "reference_place_of_service": "SELECT code, description FROM reference_place_of_service",
            "reference_medications": "SELECT name, ndc, category, avg_cost, days_supply FROM reference_medications",
        }

        sections_to_search = []
        if section == "all":
            sections_to_search = kb_sections + rule_sections + list(reference_map.keys())
        elif section == "business_rules":
            sections_to_search = rule_sections
        elif section == "reference_data":
            sections_to_search = list(reference_map.keys())
        else:
            sections_to_search = [section]

        for sec in sections_to_search:
            if sec in self.knowledge_base:
                items = self.knowledge_base.get(sec, [])
            elif sec in rule_sections:
                items = self.business_rules.get(sec, [])
            elif sec in reference_map:
                items = self._q(reference_map[sec])
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
        member = self._one("SELECT * FROM members WHERE member_id = ?", (member_id,))
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
            "message": "Appeal submitted. You will receive written acknowledgment within 5 business days.",
        }
        self._sim_appeals.append(appeal)
        return appeal

    # ── Document Generation ────────────────────────────────────────
    # (Delegates to same template logic — needs member/claim/auth lookups via SQL)

    def _format_address(self, address):
        if not address:
            return ""
        parts = []
        if address.get("line1"): parts.append(address["line1"])
        if address.get("line2"): parts.append(address["line2"])
        csz = " ".join(p for p in [address.get("city"), address.get("state"), address.get("zip")] if p)
        if csz: parts.append(csz)
        return "\n".join(parts)

    def _format_money(self, value):
        if value is None: return None
        try: return f"{float(value):.2f}"
        except (TypeError, ValueError): return str(value)

    def _render_template(self, template_text, context):
        import re
        def repl(match):
            key = match.group(1)
            value = context.get(key)
            return str(value) if value is not None else "N/A"
        return re.sub(r"{{\s*([a-zA-Z0-9_]+)\s*}}", repl, template_text)

    def _get_template(self, document_type):
        for t in self.document_templates:
            if t.get("type") == document_type:
                return t
        return None

    def _find_appeal(self, appeal_id=None, member_id=None, claim_id=None, auth_id=None):
        for a in reversed(self._sim_appeals):
            if appeal_id and a.get("appeal_id") == appeal_id: return a
            if member_id and a.get("member_id") != member_id: continue
            if claim_id and a.get("claim_id") != claim_id: continue
            if auth_id and a.get("auth_id") != auth_id: continue
            return a
        return None

    def generate_document(self, document_type, member_id, claim_id=None, auth_id=None, appeal_id=None):
        member = self._one("SELECT * FROM members WHERE member_id = ?", (member_id,))
        if not member:
            return {"error": f"Member {member_id} not found"}
        self._enrich_member(member)
        template = self._get_template(document_type)
        if not template:
            return {"error": f"Unknown document type: {document_type}"}

        plan = self._one("SELECT * FROM plans WHERE plan_id = ?", (member["plan_id"],))
        employer = self._one("SELECT * FROM employers WHERE employer_id = ?", (member.get("employer_id"),))
        pcp = self._one("SELECT * FROM providers WHERE provider_id = ?", (member.get("pcp_provider_id"),))
        if pcp: _unflatten_address(pcp)

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
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }

        if document_type in ("EOB", "denial_letter"):
            if not claim_id:
                return {"error": "claim_id is required for this document type"}
            claim = self._one("SELECT * FROM medical_claims WHERE claim_id = ?", (claim_id,))
            if not claim:
                return {"error": f"Claim {claim_id} not found"}
            provider = self._one("SELECT * FROM providers WHERE provider_id = ?", (claim.get("provider_id"),))
            if provider: _unflatten_address(provider)
            lines = self._q("SELECT * FROM claim_lines WHERE claim_id = ?", (claim_id,))
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
            auth = self._one("SELECT * FROM authorizations WHERE auth_id = ?", (auth_id,))
            if not auth:
                return {"error": f"Authorization {auth_id} not found"}
            provider = self._one("SELECT * FROM providers WHERE provider_id = ?", (auth.get("provider_id"),))
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

    # ── Properties used by server.py for stats/list endpoints ──────

    @property
    def members(self):
        return self._q("SELECT * FROM members")

    @property
    def plans(self):
        return self._q("SELECT * FROM plans")

    @property
    def employers(self):
        return self._q("SELECT * FROM employers")

    @property
    def benefits(self):
        return self._q("SELECT * FROM benefits")

    @property
    def medical_claims(self):
        return self._q("SELECT * FROM medical_claims")

    @property
    def claim_lines(self):
        return self._q("SELECT * FROM claim_lines")

    @property
    def pharmacy_claims(self):
        return self._q("SELECT * FROM pharmacy_claims")

    @property
    def authorizations(self):
        return self._q("SELECT * FROM authorizations")

    @property
    def call_logs(self):
        return self._q("SELECT * FROM call_logs")

    @property
    def secure_messages(self):
        return self._q("SELECT * FROM secure_messages")

    @property
    def case_notes(self):
        return self._q("SELECT * FROM case_notes")

    @property
    def dependents(self):
        return self._q("SELECT * FROM dependents")

    @property
    def providers(self):
        rows = self._q("SELECT * FROM providers")
        for r in rows:
            self._enrich_provider(r)
        return rows

    @property
    def agents(self):
        return self._q("SELECT * FROM agents")

    @property
    def _plan_by_id(self):
        """Dict-like accessor for server.py's get_plan endpoint."""
        return {p["plan_id"]: p for p in self._q("SELECT * FROM plans")}

    @property
    def _provider_by_id(self):
        """Dict-like accessor in case server.py references it directly."""
        rows = self._q("SELECT * FROM providers")
        result = {}
        for r in rows:
            self._enrich_provider(r)
            result[r["provider_id"]] = r
        return result

    @property
    def _employer_by_id(self):
        return {e["employer_id"]: e for e in self._q("SELECT * FROM employers")}

    @property
    def _member_by_id(self):
        rows = self._q("SELECT * FROM members")
        result = {}
        for r in rows:
            self._enrich_member(r)
            result[r["member_id"]] = r
        return result


# ── Quick test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python3 scripts/build_database.py")
        exit(1)

    db = HealthcareDB()
    print(f"Connected to {DB_PATH.name}")

    r = db.execute_tool("lookup_member", {"member_id": "MBR-B5906016"})
    print(f"\nlookup_member: {r['results'][0]['first_name']} {r['results'][0]['last_name']}")
    print(f"  Chronic conditions: {r['results'][0].get('chronic_conditions')}")
    print(f"  Address: {r['results'][0].get('address', {}).get('city')}")

    r = db.execute_tool("search_claims", {"member_id": "MBR-B5906016", "limit": 3})
    print(f"\nsearch_claims: {r['total']} total, showing {len(r['results'])}")

    r = db.execute_tool("get_claim_detail", {"claim_id": r['results'][0]['claim_id']})
    print(f"\nget_claim_detail: {r['claim']['claim_id']} — {r['member_name']}")
    print(f"  Provider: {r['provider']['name']}")
    print(f"  Lines: {len(r['claim_lines'])}")

    r = db.execute_tool("search_providers", {"specialty": "Cardiology", "limit": 3})
    print(f"\nsearch_providers(Cardiology): {r['total']} total")

    r = db.execute_tool("check_eligibility", {"member_id": "MBR-B5906016", "date_of_service": "2025-06-15"})
    print(f"\ncheck_eligibility: eligible={r.get('eligible')}")

    print("\nAll tools operational (SQLite backend).")
