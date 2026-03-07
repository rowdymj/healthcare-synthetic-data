#!/usr/bin/env python3
"""
Eval Runner — Automated scenario testing for the Healthcare Sandbox.

Loads eval scenarios from scenarios.json, executes each scenario's
expected tool chain with realistic parameters, scores results against
expected_facts and scoring fields, and reports pass/fail with scores.

Supports multiple adapters, tier-based eval selection, harness-eval mode
(LLM-driven via ClaudeProvider), governance-aware output, and CI gating.

Usage:
    python3 scripts/run_evals.py                     # run all tier-1 scenarios
    python3 scripts/run_evals.py --verbose            # show per-dimension scores
    python3 scripts/run_evals.py --filter Hard        # run only Hard scenarios
    python3 scripts/run_evals.py --adapter governance-api  # use governance API adapter
    python3 scripts/run_evals.py --tier 2             # run tier-2 evals (not yet available)
    python3 scripts/run_evals.py --ci                 # CI mode with strict governance gate
    python3 scripts/run_evals.py --output results.json  # write JSON results

Exit code: 0 if all pass, 1 if any fail. With --ci: governance failures always fail.
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCENARIOS_PATH = BASE_DIR / "agent-sandbox" / "scenarios" / "scenarios.json"

sys.path.insert(0, str(BASE_DIR / "agent-sandbox"))
from api_server import create_api


# ── Adapters ─────────────────────────────────────────────────────

class GovernanceAPIAdapter:
    """POST scenario results to /governance/validate for server-side validation."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def validate(self, scenario_result):
        """POST scenario result to /governance/validate for server-side validation."""
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            f"{self.base_url}/governance/validate",
            data=json.dumps(scenario_result, default=str).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            return json.loads(resp.read())
        except urllib.error.URLError as e:
            return {"error": f"governance-api not reachable: {e}"}


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


# ── Harness-Eval Runner (LLM-driven) ────────────────────────────

def load_tool_definitions():
    """Load tool schemas from tool_schemas.json as ToolDefinition objects."""
    from harness.model_provider import ToolDefinition

    schemas_path = BASE_DIR / "agent-sandbox" / "tools" / "tool_schemas.json"
    with open(schemas_path) as f:
        data = json.load(f)
    return [
        ToolDefinition(name=t["name"], description=t["description"], input_schema=t["input_schema"])
        for t in data["anthropic_tools"]
    ]


def run_harness_eval(api, scenario, verbose=False):
    """Run one scenario in harness-eval mode (LLM-driven).

    Returns (passed, details, called_tools, tool_results_text, audit, llm_response).
    """
    from harness.model_provider import ClaudeProvider
    from harness.audit import AuditLogger
    from harness.escalation import EscalationEngine, EscalationConfig

    tools = load_tool_definitions()

    provider = ClaudeProvider()
    session_id = f"eval-{scenario['id']}"
    audit = AuditLogger(session_id, scenario["id"])
    escalation = EscalationEngine(EscalationConfig())

    agent_role = scenario.get("agent_role", "healthcare agent")
    system_prompt = (
        f"You are a {agent_role}. "
        f"Help the member with their request. Use the available tools to look up information "
        f"and take actions. Be accurate and thorough."
    )
    messages = [{"role": "user", "content": scenario["user_prompt"]}]

    called_tools = []
    tool_results = []
    details = []
    MAX_TURNS = 10
    llm_response = ""

    for _ in range(MAX_TURNS):
        result = provider.complete_with_tools(system_prompt, messages, tools)

        if result.stop_reason == "end_turn":
            llm_response = result.content
            break

        if result.stop_reason == "tool_use":
            # Build assistant message with tool_use blocks
            assistant_content = []
            if result.content:
                assistant_content.append({"type": "text", "text": result.content})

            tool_result_blocks = []
            for tc in result.tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc.tool_use_id,
                    "name": tc.tool_name,
                    "input": tc.tool_input,
                })

                audit.log("tool_call", tool_name=tc.tool_name, tool_params=tc.tool_input)

                start = time.monotonic()
                tool_result = api.execute_tool(tc.tool_name, tc.tool_input)
                elapsed = (time.monotonic() - start) * 1000

                audit.log("tool_result", tool_name=tc.tool_name, tool_result=tool_result)
                called_tools.append(tc.tool_name)
                tool_results.append(json.dumps(tool_result, default=str))
                details.append({
                    "tool": tc.tool_name,
                    "status": "OK",
                    "ms": round(elapsed, 1),
                })

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tc.tool_use_id,
                    "content": json.dumps(tool_result, default=str),
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_result_blocks})
        else:
            # max_tokens or unexpected stop reason
            llm_response = result.content
            break

    audit.log("determination")

    tool_results_text = "\n".join(tool_results)
    return True, details, called_tools, tool_results_text, audit, llm_response


def score_harness_eval(scenario, called_tools, tool_results_text, audit, llm_response):
    """Score a harness-eval scenario on 5 dimensions.

    Returns a dict with per-dimension scores, weighted total, and pass/fail.
    """
    from harness.escalation import EscalationEngine, EscalationConfig

    expected = scenario.get("expected_harness_behavior", {})
    scoring = scenario.get("scoring", {})
    weights = scoring.get("weights", {})

    default_weights = {
        "correct_tools_called": 20,
        "correct_tool_order": 15,
        "escalation_correct": 25,
        "audit_trail_complete": 20,
        "facts_present": 20,
    }
    for dim, w in default_weights.items():
        weights.setdefault(dim, w)

    threshold = scoring.get("pass_threshold", 70)
    combined_text = (tool_results_text + "\n" + (llm_response or "")).lower()

    # 1. required_tool_calls
    required = expected.get("required_tool_calls", [])
    if required:
        matched = sum(1 for t in required if t in called_tools)
        tools_score = (matched / len(required)) * 100
    else:
        tools_score = 100.0

    # 2. tool_call_order
    order_str = expected.get("tool_call_order", "")
    order_pairs = _parse_order_pairs(order_str)
    if order_pairs:
        satisfied = 0
        total_pairs = 0
        for before, after in order_pairs:
            if before is None and after is not None:
                if after in called_tools:
                    idx = called_tools.index(after)
                    satisfied += 1 if idx == len(called_tools) - 1 else 0
                total_pairs += 1
            elif after is None and before is not None:
                if before in called_tools:
                    idx = called_tools.index(before)
                    satisfied += 1 if idx == 0 else 0
                total_pairs += 1
            else:
                total_pairs += 1
                if before in called_tools and after in called_tools:
                    idx_a = called_tools.index(before)
                    idx_b = called_tools.index(after)
                    if idx_a < idx_b:
                        satisfied += 1
        order_score = (satisfied / total_pairs) * 100 if total_pairs else 100.0
    else:
        order_score = 100.0

    # 3. escalation_correct
    expected_escalation = expected.get("expected_escalation", {})
    if expected_escalation:
        engine = EscalationEngine(EscalationConfig())
        decision = engine.evaluate(expected_escalation.get("workflow_result", {}))
        should = expected_escalation.get("should_escalate", False)
        escalation_score = 100.0 if decision.should_escalate == should else 0.0
    else:
        escalation_score = 100.0

    # 4. audit_trail_complete
    expected_audit_types = expected.get("audit_entry_types", [])
    if expected_audit_types and audit:
        session_id = f"eval-{scenario['id']}"
        verification = audit.verify(session_id)
        audit_score = 100.0 if verification.get("complete", False) else 50.0
    else:
        audit_score = 100.0

    # 5. facts_present
    must_contain = expected.get("must_contain", [])
    if must_contain:
        found = sum(1 for phrase in must_contain if phrase.lower() in combined_text)
        facts_score = (found / len(must_contain)) * 100
    else:
        facts_score = 100.0

    dimension_scores = {
        "correct_tools_called": tools_score,
        "correct_tool_order": order_score,
        "escalation_correct": escalation_score,
        "audit_trail_complete": audit_score,
        "facts_present": facts_score,
    }

    weighted_sum = sum(
        dimension_scores[dim] * weights.get(dim, 0)
        for dim in dimension_scores
    )
    total_weight = sum(weights.get(dim, 0) for dim in dimension_scores)
    weighted_total = weighted_sum / total_weight if total_weight else 0

    return {
        "dimensions": dimension_scores,
        "weighted_total": round(weighted_total, 1),
        "threshold": threshold,
        "passed": weighted_total >= threshold,
    }


# ── Scoring (sandbox mode) ──────────────────────────────────────

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

    # 5. Weighted total (only use weights for dimensions this scorer computes)
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
    total_weight = sum(weights.get(dim, 0) for dim in dimension_scores)
    weighted_total = weighted_sum / total_weight if total_weight else 0

    return {
        "dimensions": dimension_scores,
        "weighted_total": round(weighted_total, 1),
        "threshold": threshold,
        "passed": weighted_total >= threshold,
    }


# ── Output Helpers ───────────────────────────────────────────────

def _is_governance(scenario):
    """Check if a scenario has governance metadata."""
    gov = scenario.get("governance", {})
    return gov.get("adverse_determination") or gov.get("human_review_required")


def _print_scenario_line(scenario, tag, score_str, tool_count, elapsed):
    """Print a single scenario result line."""
    print(
        f"{scenario['id']}  [{tag} {score_str}]  "
        f"{scenario['name']:<50s} ({tool_count} tools, {elapsed:.0f}ms)"
    )


def _print_verbose_details(details, score):
    """Print verbose per-tool details and dimension scores."""
    for d in details:
        note = f"  — {d['note']}" if d.get("note") else ""
        print(f"    {d['status']:4s}  {d['tool']:<35s} ({d['ms']:.0f}ms){note}")
    if score is not None:
        dims = score["dimensions"]
        parts = [f"{k}: {v:.0f}" for k, v in dims.items()]
        print(f"    {', '.join(parts)} -> {score['weighted_total']:.0f}")


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
    parser.add_argument(
        "--adapter",
        choices=["sandbox", "governance-api"],
        default="sandbox",
        help="Adapter to use for eval execution (default: sandbox).",
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "all"],
        default="1",
        help="Eval tier to run (default: 1).",
    )
    parser.add_argument(
        "--harness-eval",
        action="store_true",
        help="Run scenarios with expected_harness_behavior through ClaudeProvider (LLM calls).",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: strict governance enforcement, exit 1 on governance failures.",
    )
    parser.add_argument(
        "--output",
        default="eval-results.json",
        help="Path to write JSON results (default: eval-results.json).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    verbose = args.verbose
    difficulty_filter = args.filter

    # ── Tier handling ──
    if args.tier == "2":
        print("Tier 2 not yet available")
        sys.exit(0)
    # tier "1" and "all" both run tier 1 (only tier available)

    with open(SCENARIOS_PATH) as f:
        data = json.load(f)
    scenarios = data if isinstance(data, list) else data["scenarios"]

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

    # ── Adapter setup ──
    api = create_api(force_json=True)
    governance_adapter = None
    if args.adapter == "governance-api":
        governance_adapter = GovernanceAPIAdapter()

    total_pass = 0
    total_fail = 0
    total_ms = 0
    scored_totals = []
    results = []

    print()
    print("Healthcare Sandbox Eval Results")
    print(f"Adapter: {args.adapter} | Tier: {args.tier}")
    print("=" * 80)

    for scenario in scenarios:
        start = time.monotonic()

        # ── Mode selection: harness-eval vs sandbox ──
        # harness-eval requires --harness-eval flag AND scenario data
        has_harness = args.harness_eval and "expected_harness_behavior" in scenario
        if has_harness:
            passed, details, called_tools, tool_results_text, audit, llm_response = (
                run_harness_eval(api, scenario, verbose=verbose)
            )
        else:
            passed, details, called_tools, tool_results_text = run_scenario(
                api, scenario, verbose=verbose
            )
            audit = None
            llm_response = None

        elapsed = (time.monotonic() - start) * 1000
        total_ms += elapsed

        # ── Governance-API adapter validation ──
        governance_validation = None
        if governance_adapter and _is_governance(scenario):
            scenario_result = {
                "id": scenario["id"],
                "governance": scenario.get("governance"),
                "called_tools": called_tools,
                "tool_results": tool_results_text,
            }
            governance_validation = governance_adapter.validate(scenario_result)
            if governance_validation.get("error"):
                passed = False
                details.append({
                    "tool": "governance-api",
                    "status": "FAIL",
                    "ms": 0,
                    "note": governance_validation["error"],
                })

        # ── Scoring ──
        if has_harness:
            score = score_harness_eval(
                scenario, called_tools, tool_results_text, audit, llm_response
            )
            passed = passed and score["passed"]
            score_str = f"{score['weighted_total']:3.0f}"
            scored_totals.append(score["weighted_total"])
        else:
            score = score_scenario(scenario, called_tools, tool_results_text)
            if score is not None:
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
        is_gov = _is_governance(scenario)

        results.append({
            "id": scenario["id"],
            "name": scenario["name"],
            "category": scenario.get("category", ""),
            "difficulty": scenario["difficulty"],
            "passed": passed,
            "is_governance": is_gov,
            "tool_count": tool_count,
            "elapsed_ms": round(elapsed, 1),
            "details": details,
            "score": score,
            "governance_validation": governance_validation,
        })

    # ── Governance output section (printed first) ──
    governance_results = [r for r in results if r["is_governance"]]
    non_governance_results = [r for r in results if not r["is_governance"]]

    if governance_results:
        print()
        print("GOVERNANCE SCENARIOS")
        print("\u2550" * 80)
        gov_pass = 0
        gov_fail = 0
        gov_scores = []
        for r in governance_results:
            tag = "PASS" if r["passed"] else "FAIL"
            if r["score"]:
                s_str = f"{r['score']['weighted_total']:3.0f}"
                gov_scores.append(r["score"]["weighted_total"])
            else:
                s_str = " --"
            if r["passed"]:
                gov_pass += 1
            else:
                gov_fail += 1
            print(
                f"{r['id']}  [{tag} {s_str}]  "
                f"{r['name']:<50s} ({r['tool_count']} tools, {r['elapsed_ms']:.0f}ms)"
            )
            if verbose:
                _print_verbose_details(r["details"], r["score"])
        print("\u2500" * 80)
        gov_avg = sum(gov_scores) / len(gov_scores) if gov_scores else 0
        gov_summary = f"Governance: {gov_pass}/{len(governance_results)} passed | {gov_fail} failed"
        if gov_scores:
            gov_summary += f" | Avg score: {gov_avg:.0f}"
        print(gov_summary)

    print()
    print("ALL SCENARIOS")
    print("\u2550" * 80)
    for r in results:
        tag = "PASS" if r["passed"] else "FAIL"
        if r["score"]:
            s_str = f"{r['score']['weighted_total']:3.0f}"
        else:
            s_str = " --"
        print(
            f"{r['id']}  [{tag} {s_str}]  "
            f"{r['name']:<50s} ({r['tool_count']} tools, {r['elapsed_ms']:.0f}ms)"
        )
        if verbose:
            _print_verbose_details(r["details"], r["score"])

    print("=" * 80)
    total = total_pass + total_fail
    avg_score = sum(scored_totals) / len(scored_totals) if scored_totals else 0
    summary = f"{total_pass}/{total} passed | {total_fail} failed"
    if scored_totals:
        summary += f" | Avg score: {avg_score:.0f}"
    summary += f" | Total: {total_ms:.0f}ms"
    print(summary)
    print()

    # ── Category summary ──
    categories = {}
    for r in results:
        cat = r.get("category", "Other") or "Other"
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    print("Category Summary")
    print("\u2500" * 40)
    for cat in sorted(categories):
        c = categories[cat]
        pct = (c["passed"] / c["total"]) * 100 if c["total"] else 0
        print(f"  {cat:<25s} {c['passed']}/{c['total']}   {pct:.0f}%")
    print()

    # ── Failed scenarios detail ──
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

    # ── JSON output ──
    governance_pass = sum(1 for r in governance_results if r["passed"])
    governance_fail = sum(1 for r in governance_results if not r["passed"])
    gov_pass_rate = (governance_pass / len(governance_results) * 100) if governance_results else 100.0

    json_output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "adapter": args.adapter,
        "tier": int(args.tier) if args.tier != "all" else 1,
        "governance_summary": {
            "total": len(governance_results),
            "passed": governance_pass,
            "failed": governance_fail,
            "pass_rate": round(gov_pass_rate, 1),
        },
        "overall_summary": {
            "total": total,
            "passed": total_pass,
            "failed": total_fail,
            "pass_rate": round((total_pass / total) * 100 if total else 0, 1),
            "avg_score": round(avg_score),
        },
        "category_summary": categories,
        "scenarios": results,
    }

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    print(f"Results written to {output_path}")

    # ── CI gate ──
    if args.ci:
        governance_failures = [r for r in results if r.get("is_governance") and not r["passed"]]
        overall_pass_rate = (total_pass / total) * 100 if total else 0

        if governance_failures:
            print(f"\nCI FAILED: {len(governance_failures)} governance scenario(s) failed")
            for r in governance_failures:
                print(f"  {r['id']}  {r['name']}")
            return 1

        if overall_pass_rate < 80:
            print(f"\nCI FAILED: overall pass rate {overall_pass_rate:.0f}% < 80% threshold")
            return 1

        print(f"\nCI PASSED: governance 100%, overall {overall_pass_rate:.0f}%")
        return 0

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
