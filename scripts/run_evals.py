#!/usr/bin/env python3
"""
Eval Runner — Automated scenario testing for the Healthcare Sandbox.

Loads eval scenarios from scenarios.json, executes each scenario's
expected tool chain with realistic parameters, scores results against
expected_facts and scoring fields, and reports pass/fail with scores.

Usage:
    python3 scripts/run_evals.py              # run all scenarios
    python3 scripts/run_evals.py --verbose    # show per-dimension scores
    python3 scripts/run_evals.py --filter Hard # run only Hard scenarios

Exit code: 0 if all pass, 1 if any fail.
"""

import argparse
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


def params_draft_case_note(api, ctx):
    return {
        "member_id": ctx["member_id"],
        "category": "Eval Test",
        "content": "Automated eval scenario test — case note creation verified.",
    }, ctx


def params_submit_case_note(api, ctx):
    draft_id = next(iter(api.draft_notes), "DRAFT-0001")
    return {"draft_id": draft_id}, ctx


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
    "draft_case_note": params_draft_case_note,
    "submit_case_note": params_submit_case_note,
    "generate_document": params_generate_document,
}


# ── Scenario Runner ───────────────────────────────────────────────

import re


def run_scenario(api, scenario, verbose=False):
    """Run one scenario. Returns (passed, details, called_tools, tool_results_text)."""
    ctx = {}
    details = []
    passed = True
    called_tools = []
    tool_results = []

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

        called_tools.append(tool_name)
        tool_results.append(json.dumps(result, default=str))

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

    tool_results_text = "\n".join(tool_results)
    return passed, details, called_tools, tool_results_text


# ── Scoring ──────────────────────────────────────────────────────

def _parse_order_pairs(order_str):
    """Parse tool_call_order string into (before, after) pairs.

    Handles formats like:
      "lookup_member before get_accumulator"
      "lookup_member first, search_claims before get_claim_detail"
      "lookup_member before get_authorization before search_claims"
    """
    if not order_str:
        return []
    pairs = []
    # Split on comma to handle compound constraints
    for clause in order_str.split(","):
        clause = clause.strip()
        # Handle "X first" — means X before everything else (skip, just a hint)
        if clause.endswith(" first"):
            tool = clause.replace(" first", "").strip()
            pairs.append((tool, None))  # sentinel: tool must be first-ish
            continue
        if clause.endswith(" last"):
            tool = clause.replace(" last", "").strip()
            pairs.append((None, tool))  # sentinel: tool must be last-ish
            continue
        # Handle "A before B before C" chains
        parts = re.split(r"\s+before\s+", clause)
        for i in range(len(parts) - 1):
            pairs.append((parts[i].strip(), parts[i + 1].strip()))
    return pairs


def score_scenario(scenario, called_tools, tool_results_text):
    """Score a scenario against its expected_facts and scoring fields.

    Returns None if the scenario has no scoring fields (backward compat).
    Otherwise returns a dict with per-dimension scores and weighted total.
    """
    expected_facts = scenario.get("expected_facts")
    scoring = scenario.get("scoring")
    if not expected_facts or not scoring:
        return None

    weights = scoring["weights"]
    threshold = scoring.get("pass_threshold", 70)
    results_lower = tool_results_text.lower()

    # 1. correct_tools_called
    required = expected_facts.get("required_tool_calls", [])
    if required:
        matched = sum(1 for t in required if t in called_tools)
        tools_score = (matched / len(required)) * 100
    else:
        tools_score = 100.0

    # 2. correct_tool_order
    order_str = expected_facts.get("tool_call_order", "")
    order_pairs = _parse_order_pairs(order_str)
    if order_pairs:
        satisfied = 0
        total_pairs = 0
        for before, after in order_pairs:
            if before is None and after is not None:
                # "X last" — X should be after all other called tools
                if after in called_tools:
                    idx = called_tools.index(after)
                    satisfied += 1 if idx == len(called_tools) - 1 else 0
                total_pairs += 1
            elif after is None and before is not None:
                # "X first" — X should appear first
                if before in called_tools:
                    idx = called_tools.index(before)
                    satisfied += 1 if idx == 0 else 0
                total_pairs += 1
            else:
                # "A before B"
                total_pairs += 1
                if before in called_tools and after in called_tools:
                    idx_a = called_tools.index(before)
                    idx_b = called_tools.index(after)
                    if idx_a < idx_b:
                        satisfied += 1
        order_score = (satisfied / total_pairs) * 100 if total_pairs else 100.0
    else:
        order_score = 100.0

    # 3. facts_present (must_contain)
    must_contain = expected_facts.get("must_contain", [])
    if must_contain:
        found = sum(1 for phrase in must_contain if phrase.lower() in results_lower)
        facts_score = (found / len(must_contain)) * 100
    else:
        facts_score = 100.0

    # 4. no_forbidden_phrases (must_not_contain)
    must_not = expected_facts.get("must_not_contain", [])
    if must_not:
        clean = sum(1 for phrase in must_not if phrase.lower() not in results_lower)
        forbidden_score = (clean / len(must_not)) * 100
    else:
        forbidden_score = 100.0

    # 5. Weighted total
    dimension_scores = {
        "correct_tools_called": tools_score,
        "correct_tool_order": order_score,
        "facts_present": facts_score,
        "no_forbidden_phrases": forbidden_score,
    }
    weighted_sum = sum(
        dimension_scores[dim] * weights.get(dim, 0)
        for dim in dimension_scores
    )
    total_weight = sum(weights.values())
    weighted_total = weighted_sum / total_weight if total_weight else 0

    return {
        "dimensions": dimension_scores,
        "weighted_total": round(weighted_total, 1),
        "threshold": threshold,
        "passed": weighted_total >= threshold,
    }


# ── Main ──────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Healthcare Sandbox eval scenarios."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show tool-by-tool detail for each scenario.",
    )
    parser.add_argument(
        "--filter",
        metavar="DIFFICULTY",
        help="Run only scenarios matching a difficulty value (case-insensitive).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    verbose = args.verbose
    difficulty_filter = args.filter

    with open(SCENARIOS_PATH) as f:
        data = json.load(f)
    scenarios = data["scenarios"]

    if difficulty_filter:
        valid_difficulties = sorted({s["difficulty"] for s in scenarios})
        difficulty_lookup = {d.lower(): d for d in valid_difficulties}
        matched_difficulty = difficulty_lookup.get(difficulty_filter.lower())
        if not matched_difficulty:
            valid = ", ".join(valid_difficulties)
            raise SystemExit(
                f"Invalid --filter value: {difficulty_filter!r}. "
                f"Valid values: {valid}"
            )
        scenarios = [s for s in scenarios if s["difficulty"] == matched_difficulty]

    api = create_api(force_json=True)

    total_pass = 0
    total_fail = 0
    total_ms = 0
    scored_totals = []
    results = []

    print()
    print("Healthcare Sandbox Eval Results")
    print("=" * 80)

    for scenario in scenarios:
        start = time.monotonic()
        passed, details, called_tools, tool_results_text = run_scenario(
            api, scenario, verbose=verbose
        )
        elapsed = (time.monotonic() - start) * 1000
        total_ms += elapsed

        # Score against expected_facts if available
        score = score_scenario(scenario, called_tools, tool_results_text)
        if score is not None:
            # Scoring overrides the tool-execution-only pass/fail
            passed = passed and score["passed"]
            score_str = f"{score['weighted_total']:3.0f}"
            scored_totals.append(score["weighted_total"])
        else:
            score_str = " --"

        if passed:
            total_pass += 1
            tag = "PASS"
        else:
            total_fail += 1
            tag = "FAIL"

        tool_count = len(scenario["expected_tools"])
        line = (
            f"{scenario['id']}  [{tag} {score_str}]  "
            f"{scenario['name']:<50s} ({tool_count} tools, {elapsed:.0f}ms)"
        )
        print(line)

        if verbose:
            for d in details:
                note = f"  — {d['note']}" if d.get("note") else ""
                print(f"    {d['status']:4s}  {d['tool']:<35s} ({d['ms']:.0f}ms){note}")
            if score is not None:
                dims = score["dimensions"]
                print(
                    f"    Tools: {dims['correct_tools_called']:.0f}  "
                    f"Order: {dims['correct_tool_order']:.0f}  "
                    f"Facts: {dims['facts_present']:.0f}  "
                    f"Forbidden: {dims['no_forbidden_phrases']:.0f}  "
                    f"-> {score['weighted_total']:.0f}"
                )

        results.append({
            "id": scenario["id"],
            "name": scenario["name"],
            "difficulty": scenario["difficulty"],
            "passed": passed,
            "tool_count": tool_count,
            "elapsed_ms": round(elapsed, 1),
            "details": details,
            "score": score,
        })

    print("=" * 80)
    total = total_pass + total_fail
    avg_score = sum(scored_totals) / len(scored_totals) if scored_totals else 0
    summary = f"{total_pass}/{total} passed | {total_fail} failed"
    if scored_totals:
        summary += f" | Avg score: {avg_score:.0f}"
    summary += f" | Total: {total_ms:.0f}ms"
    print(summary)
    print()

    if total_fail > 0:
        print("Failed scenarios:")
        for r in results:
            if not r["passed"]:
                print(f"  {r['id']}  {r['name']}")
                for d in r["details"]:
                    if d["status"] in ("FAIL", "SKIP"):
                        print(f"    {d['status']}  {d['tool']}: {d.get('note') or d.get('reason')}")
                if r.get("score"):
                    dims = r["score"]["dimensions"]
                    for dim, val in dims.items():
                        if val < 100:
                            print(f"    {dim}: {val:.0f}")
        print()

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
