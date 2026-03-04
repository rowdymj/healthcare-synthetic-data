# Eval Runner Design

**Date**: 2026-03-04
**Status**: Approved

## Goal

Automated scenario testing that validates all 18 tools work correctly across 20 eval scenarios, with CI integration.

## Architecture

Single script (`scripts/run_evals.py`) that:
1. Loads scenarios from `agent-sandbox/scenarios/scenarios.json`
2. Executes each scenario's `expected_tools` in sequence with realistic params
3. Chains context between tools in a scenario (e.g., member_id from lookup feeds into claims search)
4. Reports pass/fail table with timing
5. Returns exit code 0/1 for CI

## Decisions

- **Tool execution only** — no LLM calls, validates the sandbox works end-to-end
- **Inline param mapping** — tool-to-params logic lives in the script, not separate config files
- **Context chaining** — within a scenario, earlier tool results feed later tool params
- **CI-friendly** — exit code 0 all pass, 1 any fail

## Output Format

```
Healthcare Sandbox Eval Results
================================
EVAL-001  [PASS]  Member looks up their deductible status     (2 tools, 12ms)
...
================================
20/20 passed | 0 failed | Total: 340ms
```

## Not In Scope

- LLM-based eval (agent choosing tools)
- Response quality scoring
- Separate param config files per scenario
