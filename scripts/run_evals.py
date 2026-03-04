#!/usr/bin/env python3
"""
Eval Runner — Automated scenario testing for the Healthcare Sandbox.

Loads 20 eval scenarios from scenarios.json, executes each scenario's
expected tool chain with realistic parameters, and reports pass/fail.

Usage:
    python3 scripts/run_evals.py              # run all scenarios
    python3 scripts/run_evals.py --verbose    # show tool-by-tool detail
    python3 scripts/run_evals.py --filter Hard # run only Hard scenarios

Exit code: 0 if all pass, 1 if any fail.
"""

import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCENARIOS_PATH = BASE_DIR / "agent-sandbox" / "scenarios" / "scenarios.json"

sys.path.insert(0, str(BASE_DIR / "agent-sandbox"))
from api_server import create_api


# ── Tool Parameter Generators ─────────────────────────────────────
# Each function takes (api, ctx) and returns (params_dict, updated_ctx).
# ctx carries state across tools within a scenario (member_id, claim_id, etc.)

def _pick_member(api):
    """Pick a member that has claims, auths, and interactions for rich testing."""
    for m in api.members:
        mid = m["member_id"]
        has_claims = any(c["member_id"] == mid for c in api.medical_claims)
        has_auths = any(a["member_id"] == mid for a in api.authorizations)
        if has_claims and has_auths:
            return m
    return api.members[0]


def params_lookup_member(api, ctx):
    member = ctx.get("_seed_member") or _pick_member(api)
    ctx["_seed_member"] = member
    ctx["member_id"] = member["member_id"]
    ctx["plan_id"] = member.get("plan_id")
    ctx["employer_id"] = member.get("employer_id")
    return {"member_id": member["member_id"]}, ctx


def params_get_accumulator(api, ctx):
    return {"member_id": ctx["member_id"]}, ctx


def params_get_member_coverage(api, ctx):
    return {"member_id": ctx["member_id"]}, ctx


def params_get_member_dependents(api, ctx):
    return {"member_id": ctx["member_id"]}, ctx


def params_check_eligibility(api, ctx):
    return {"member_id": ctx["member_id"], "date_of_service": "2025-03-15"}, ctx


def params_search_claims(api, ctx):
    mid = ctx["member_id"]
    params = {"member_id": mid, "limit": 5}
    result = api.execute_tool("search_claims", params)
    claims = result.get("results", [])
    if claims:
        ctx["claim_id"] = claims[0]["claim_id"]
        ctx["provider_id"] = claims[0].get("provider_id")
    return params, ctx


def params_get_claim_detail(api, ctx):
    claim_id = ctx.get("claim_id")
    if not claim_id:
        for c in api.medical_claims:
            if c["member_id"] == ctx["member_id"]:
                claim_id = c["claim_id"]
                ctx["claim_id"] = claim_id
                break
    return {"claim_id": claim_id or api.medical_claims[0]["claim_id"]}, ctx


def params_check_benefits(api, ctx):
    plan_id = ctx.get("plan_id") or api.plans[0]["plan_id"]
    return {"plan_id": plan_id, "service_category": "Primary Care Visit"}, ctx


def params_search_providers(api, ctx):
    return {"specialty": "Cardiology", "limit": 5}, ctx


def params_get_plan_formulary(api, ctx):
    plan_id = ctx.get("plan_id") or api.plans[0]["plan_id"]
    return {"plan_id": plan_id, "medication_name": "Metformin"}, ctx


def params_search_pharmacy_claims(api, ctx):
    return {"member_id": ctx["member_id"], "limit": 5}, ctx


def params_search_knowledge_base(api, ctx):
    return {"query": "deductible"}, ctx


def params_get_authorization(api, ctx):
    return {"member_id": ctx["member_id"]}, ctx


def params_get_interaction_history(api, ctx):
    return {"member_id": ctx["member_id"]}, ctx


def params_submit_authorization_request(api, ctx):
    provider_id = ctx.get("provider_id") or api.providers[0]["provider_id"]
    return {
        "member_id": ctx["member_id"],
        "provider_id": provider_id,
        "service_description": "MRI knee",
        "procedure_code": "73721",
        "diagnosis_code": "M17.11",
    }, ctx


def params_initiate_appeal(api, ctx):
    return {
        "member_id": ctx["member_id"],
        "appeal_reason": "Eval test: prior auth was obtained but not linked to claim",
        "claim_id": ctx.get("claim_id"),
    }, ctx


def params_create_case_note(api, ctx):
    return {
        "member_id": ctx["member_id"],
        "category": "Eval Test",
        "content": "Automated eval scenario test — case note creation verified.",
    }, ctx


def params_generate_document(api, ctx):
    params = {"document_type": "id_card", "member_id": ctx["member_id"]}
    return params, ctx


PARAM_GENERATORS = {
    "lookup_member": params_lookup_member,
    "get_accumulator": params_get_accumulator,
    "get_member_coverage": params_get_member_coverage,
    "get_member_dependents": params_get_member_dependents,
    "check_eligibility": params_check_eligibility,
    "search_claims": params_search_claims,
    "get_claim_detail": params_get_claim_detail,
    "check_benefits": params_check_benefits,
    "search_providers": params_search_providers,
    "get_plan_formulary": params_get_plan_formulary,
    "search_pharmacy_claims": params_search_pharmacy_claims,
    "search_knowledge_base": params_search_knowledge_base,
    "get_authorization": params_get_authorization,
    "get_interaction_history": params_get_interaction_history,
    "submit_authorization_request": params_submit_authorization_request,
    "initiate_appeal": params_initiate_appeal,
    "create_case_note": params_create_case_note,
    "generate_document": params_generate_document,
}


# ── Scenario Runner ───────────────────────────────────────────────

def run_scenario(api, scenario, verbose=False):
    """Run one scenario. Returns (passed: bool, details: list[dict])."""
    ctx = {}
    details = []
    passed = True

    for tool_name in scenario["expected_tools"]:
        gen = PARAM_GENERATORS.get(tool_name)
        if not gen:
            details.append({"tool": tool_name, "status": "SKIP", "reason": "no param generator", "ms": 0})
            passed = False
            continue

        params, ctx = gen(api, ctx)
        start = time.monotonic()
        result = api.execute_tool(tool_name, params)
        elapsed = (time.monotonic() - start) * 1000

        has_error = isinstance(result, dict) and "error" in result
        is_fatal = has_error and any(
            result["error"].startswith(prefix)
            for prefix in ("Unknown tool:", "Invalid parameters:")
        )

        status = "FAIL" if is_fatal else "OK"
        if is_fatal:
            passed = False

        detail = {"tool": tool_name, "status": status, "ms": round(elapsed, 1)}
        if has_error:
            detail["note"] = result["error"]
        if verbose:
            detail["params"] = params

        details.append(detail)

    return passed, details


# ── Main ──────────────────────────────────────────────────────────

def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    difficulty_filter = None
    if "--filter" in sys.argv:
        idx = sys.argv.index("--filter")
        if idx + 1 < len(sys.argv):
            difficulty_filter = sys.argv[idx + 1]

    with open(SCENARIOS_PATH) as f:
        data = json.load(f)
    scenarios = data["scenarios"]

    if difficulty_filter:
        scenarios = [s for s in scenarios if s["difficulty"].lower() == difficulty_filter.lower()]
        if not scenarios:
            print(f"No scenarios match difficulty filter: {difficulty_filter}")
            sys.exit(1)

    api = create_api(force_json=True)

    total_pass = 0
    total_fail = 0
    total_ms = 0
    results = []

    print()
    print("Healthcare Sandbox Eval Results")
    print("=" * 72)

    for scenario in scenarios:
        start = time.monotonic()
        passed, details = run_scenario(api, scenario, verbose=verbose)
        elapsed = (time.monotonic() - start) * 1000
        total_ms += elapsed

        if passed:
            total_pass += 1
            tag = "PASS"
        else:
            total_fail += 1
            tag = "FAIL"

        tool_count = len(scenario["expected_tools"])
        line = f"{scenario['id']}  [{tag}]  {scenario['name']:<50s} ({tool_count} tools, {elapsed:.0f}ms)"
        print(line)

        if verbose:
            for d in details:
                note = f"  — {d['note']}" if d.get("note") else ""
                print(f"    {d['status']:4s}  {d['tool']:<35s} ({d['ms']:.0f}ms){note}")

        results.append({
            "id": scenario["id"],
            "name": scenario["name"],
            "difficulty": scenario["difficulty"],
            "passed": passed,
            "tool_count": tool_count,
            "elapsed_ms": round(elapsed, 1),
            "details": details,
        })

    print("=" * 72)
    total = total_pass + total_fail
    print(f"{total_pass}/{total} passed | {total_fail} failed | Total: {total_ms:.0f}ms")
    print()

    if total_fail > 0:
        print("Failed scenarios:")
        for r in results:
            if not r["passed"]:
                print(f"  {r['id']}  {r['name']}")
                for d in r["details"]:
                    if d["status"] in ("FAIL", "SKIP"):
                        print(f"    {d['status']}  {d['tool']}: {d.get('note') or d.get('reason')}")
        print()

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
