# Healthcare Agent Sandbox — Specification

## What This Is

A complete, self-contained dataset and tooling layer for building and testing AI agents that operate in a health insurance context. Everything is synthetic — no real PHI/PII — designed for prototyping, demos, and agent evaluation.

## Architecture

```
healthcare-synthetic-data/
├── data/                          ← The dataset (JSON + CSV)
│   ├── json/                      ← 21 JSON files, ~33 MB total
│   └── csv/                       ← 15 CSV files, ~9 MB total
│
├── agent-sandbox/                 ← Agent-specific layer
│   ├── tools/
│   │   └── tool_schemas.json      ← 18 tools in Anthropic + OpenAI format
│   ├── rules/
│   │   └── business_rules.json    ← Coverage, auth, adjudication, pharmacy rules
│   ├── knowledge-base/
│   │   └── knowledge_base.json    ← Plan policies, FAQs, clinical guidelines
│   ├── scenarios/
│   │   └── scenarios.json         ← 20 eval test cases with expected outcomes
│   ├── templates/
│   │   └── document_templates.json ← EOB, denial letter, auth letter, ID card, etc.
│   └── api_server.py              ← Python query layer (implements all 18 tools)
│
├── generator/                     ← Data generation scripts
│   ├── generate.py                ← Core dataset generator
│   └── generate_interactions.py   ← Interaction history generator
│
├── frontend/
│   └── data-platform.jsx          ← React data explorer UI
│
└── docs/
    └── DATA-SPECIFICATION.md      ← Full data spec for engineers
```

## The 18 Agent Tools

These are defined in `tools/tool_schemas.json` in both Anthropic and OpenAI function calling formats. Drop them directly into your agent's system prompt or tool configuration.

| Tool | What It Does | Key Params |
|------|-------------|------------|
| `lookup_member` | Find a member by ID, name, or DOB | member_id, last_name, date_of_birth |
| `get_member_coverage` | Get plan, benefits, deductible status | member_id |
| `get_member_dependents` | List spouse/children on a plan | member_id |
| `search_claims` | Search medical claims with filters | member_id, status, date range, provider |
| `get_claim_detail` | Full claim with line items | claim_id |
| `search_pharmacy_claims` | Search Rx claims | member_id, medication, category |
| `get_plan_formulary` | Check drug coverage and tier | plan_id, medication_name |
| `check_benefits` | What does the plan cover for X? | plan_id, service_category |
| `get_accumulator` | Deductible and OOP status | member_id |
| `check_eligibility` | Is member covered on a date? | member_id, date_of_service |
| `search_providers` | Find doctors by specialty/location | specialty, city, network_status |
| `get_authorization` | Look up prior auth status | auth_id or member_id |
| `submit_authorization_request` | Submit new prior auth | member_id, procedure, diagnosis |
| `get_interaction_history` | Call logs, messages, case notes | member_id, type filter |
| `create_case_note` | Document an interaction | member_id, category, content |
| `search_knowledge_base` | Search policies, FAQs, guidelines | query, section filter |
| `initiate_appeal` | File an appeal on a denial | member_id, claim_id, reason |
| `generate_document` | Create EOB, denial letter, ID card | document_type, member_id |

## Business Rules

Located in `rules/business_rules.json`. Four categories:

**Coverage Rules (10 rules)** — When is something covered? Key rules include: preventive care at $0, ER prudent layperson standard, HMO referral requirements, OOP maximum cap, mental health parity.

**Authorization Rules (6 rules)** — What needs prior auth? Inpatient admissions, advanced imaging, elective surgery, specialty drugs, DME over $500, extended therapy.

**Adjudication Rules (10 rules)** — How claims get processed. 10-step pipeline: eligibility check → duplicate check → timely filing → auth verification → network pricing → deductible → copay/coinsurance → OOP cap → COB → payment/denial.

**Pharmacy Rules (5 rules)** — Generic substitution, step therapy for diabetes drugs, quantity limits, specialty pharmacy mandate, mail order discounts.

## How to Use the API Layer

```python
from api_server import HealthcareAPI

api = HealthcareAPI()

# Look up a member
result = api.execute_tool("lookup_member", {"last_name": "Smith"})

# Search denied claims
result = api.execute_tool("search_claims", {"claim_status": "Denied", "limit": 5})

# Check if Ozempic is covered
result = api.execute_tool("get_plan_formulary", {
    "plan_id": "PLN-XXXXXXXX",
    "medication_name": "Ozempic"
})

# Get full interaction history
result = api.execute_tool("get_interaction_history", {
    "member_id": "MBR-XXXXXXXX",
    "interaction_type": "all"
})
```

Every tool from `tool_schemas.json` is implemented in `api_server.py`. The `execute_tool(name, params)` method routes to the correct handler.

## Eval Scenarios

Located in `scenarios/scenarios.json`. 20 test cases across difficulty levels:

- **Easy (6)**: Deductible lookup, provider search, ID card request, PT visit limits, telehealth, mail order
- **Medium (9)**: Claim denial explanation, medication coverage, eligibility verification, EOB explanation, HMO referral, COBRA, agent prep, ER coverage, newborn enrollment
- **Hard (5)**: Appeal initiation, multi-step claim+auth+surgery workflow, COB explanation, grievance handling, complex denial resolution

Each scenario includes: user prompt, expected tool calls, expected agent behavior, and success criteria.

## Document Templates

Located in `templates/document_templates.json`. 7 templates with `{{variable}}` placeholders:

- **EOB** — Explanation of Benefits with full financial breakdown
- **Claim Denial Letter** — Denial notification with appeal rights
- **Auth Approval Letter** — Prior auth approval confirmation
- **Auth Denial Letter** — Prior auth denial with appeal instructions
- **Member ID Card** — Digital ID card with copay info
- **Welcome Letter** — New member onboarding
- **Appeal Acknowledgment** — Confirmation that appeal was received

## Dataset Summary

| Entity | Records | Description |
|--------|---------|-------------|
| Employers | 25 | Organizations across industries |
| Plans | 50 | HMO/PPO/EPO/HDHP/POS × Bronze/Silver/Gold/Platinum |
| Benefits | 900 | 18 service categories per plan |
| Providers | 300 | 75% individual / 25% facility |
| Members | 2,000 | Primary subscribers |
| Dependents | 2,297 | Spouses and children |
| Eligibility | 4,297 | Coverage periods |
| Medical Claims | 13,841 | Professional and institutional |
| Claim Lines | 24,206 | Service-level detail |
| Pharmacy Claims | 7,055 | Prescription fills |
| Authorizations | 567 | Prior auth records |
| Accumulators | 2,000 | Deductible/OOP tracking |
| Call Logs | 3,000 | Phone interaction records |
| Secure Messages | 2,000 | Member portal messages |
| Case Notes | 1,500 | Agent documentation |
| Agents | 20 | Agent profiles |

**Financial totals**: $63.3M billed, $34.0M plan paid, $1.2M pharmacy
**Denial rate**: 7.7% | **Auth approval rate**: 56.1%

## Regenerating Data

Both generators use `random.seed(42)` for reproducibility. To regenerate:

```bash
cd healthcare-synthetic-data
python generator/generate.py              # Core dataset
python generator/generate_interactions.py  # Interaction history
```

Modify the seed or parameters in the scripts to generate different data.
