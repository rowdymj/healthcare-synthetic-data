# Healthcare Agent Sandbox

Synthetic data platform for prototyping AI agents against realistic health insurance data. All data is fictional — no real PHI/PII.

## What's in the box

```
healthcare-synthetic-data/
├── data/                        # 33MB of synthetic healthcare data
│   ├── json/                    # 21 JSON files (primary format)
│   ├── csv/                     # CSV mirrors of all entities
│   ├── healthcare.db            # SQLite database (built from JSON)
│   └── schema.sql               # SQLite schema reference
├── agent-sandbox/               # API server + agent tooling
│   ├── server.py                # FastAPI server (23 endpoints)
│   ├── api_server.py            # Core query engine (18 tools, JSON backend)
│   ├── db_backend.py            # SQLite backend (same tool interface)
│   ├── mcp_server.py            # MCP server (Claude Desktop / Cursor / etc.)
│   ├── tools/tool_schemas.json  # Tool definitions (Anthropic + OpenAI formats)
│   ├── rules/business_rules.json        # 31 healthcare business rules
│   ├── scenarios/scenarios.json         # 20 eval test cases
│   ├── templates/document_templates.json # 7 document templates (EOB, denial letters, etc.)
│   ├── knowledge-base/knowledge_base.json # Plan policies, FAQs, guidelines
│   └── AGENT-SANDBOX-SPEC.md            # Detailed agent sandbox spec
├── docs/DATA-SPECIFICATION.md   # Data-derived data dictionary (field-level)
├── generator/                   # Python scripts that generated the data
│   ├── generate.py              # Base entity generator
│   └── generate_interactions.py # Call logs, messages, case notes
├── frontend/data-platform.jsx   # React + Tailwind data explorer component
├── scripts/                     # Dev utilities
│   ├── generate_data_spec.py    # Generate docs/DATA-SPECIFICATION.md
│   └── validate_data.py         # Referential integrity checks
└── index.html                   # Documentation site (open in browser)
```

## Developer guide

**Architecture at a glance**
- `data/json` is the source of truth for all entities.
- `agent-sandbox/api_server.py` loads all JSON into memory and implements the tool handlers.
- `agent-sandbox/db_backend.py` provides an optional SQLite backend with identical tool interface.
- `agent-sandbox/server.py` exposes REST endpoints (including `POST /tool` for agent frameworks).
- `agent-sandbox/mcp_server.py` exposes the same tools via MCP using `agent-sandbox/tools/tool_schemas.json`.

**Data backends**

The platform supports two data backends:

| Backend | Storage | Best for |
|---------|---------|----------|
| JSON (default) | In-memory from `data/json/*.json` | Quick start, no setup |
| SQLite | `data/healthcare.db` | Better query performance, SQL access |

The backend is auto-selected at startup based on whether `data/healthcare.db` exists.

**Setting up SQLite**

```bash
# Build the database from JSON source files
python3 scripts/build_database.py

# Rebuild (if JSON data changes)
python3 scripts/build_database.py --force
```

This creates `data/healthcare.db` (~16 MB) with:
- 23 tables with foreign key constraints
- Indexes on all foreign keys and commonly queried columns
- Identical tool interface — no code changes needed

To switch back to JSON, simply delete or rename the `.db` file.

Console output shows which backend is active:
```
[api_server] Using SQLite backend: healthcare.db
[data-source] lookup_member -> SQLite backend
```

**Behavioral notes**
- "Write" tools (`submit_authorization_request`, `create_case_note`, `initiate_appeal`) are in-memory only; restart resets them.
- `generate_document` renders templates in `agent-sandbox/templates/document_templates.json` and returns `document_text`.
- `search_knowledge_base` supports `section=business_rules` and `section=reference_data`.
- `rules/business_rules.json` is reference data; the API does not execute an adjudication pipeline.
- Search endpoints return `total` for full matches and cap `results` by `limit`.

**Data conventions**
- Coinsurance fields are integer percentages (e.g., `90` means 90%).
- Addresses are objects (`line1`, `line2`, `city`, `state`, `zip`).
- Dependents are also `member_id` values; `subscriber_member_id` points to the primary member.
- `docs/DATA-SPECIFICATION.md` is generated from the actual JSON files.

## Two ways to use this

This platform supports two integration patterns. The difference is the point.

---

### Path A: With MCP (recommended for demos)

MCP (Model Context Protocol) lets AI tools discover and use your data automatically. No glue code, no manual wiring. Point Claude at the server and start talking.

**1. Install dependencies**

```bash
cd agent-sandbox
pip install -r requirements.txt
```

Note: MCP requires Python 3.10+ and must be installed from GitHub:

```bash
python3.10 -m pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

**2. Add to Claude Desktop**

Open Claude Desktop → Settings → Developer → Edit Config. Add:

```json
{
  "mcpServers": {
    "healthcare-sandbox": {
      "command": "python3",
      "args": ["/your/path/to/agent-sandbox/mcp_server.py"]
    }
  }
}
```

**3. Restart Claude Desktop and start talking**

All 18 tools appear automatically. Try:

> "Look up member MBR-B5906016 and tell me about their coverage"

> "I got a bill for $1,200 for my MRI. I thought my insurance covered this."

> "My prior auth for knee replacement was denied. Help me appeal."

That's it. No curl commands, no API calls, no tool wiring. The agent has full access to the healthcare platform and reasons about which tools to use.

---

### Path B: Without MCP (traditional REST API)

This is how most teams build today — manual HTTP integration, custom tool wiring, and glue code.

**1. Install dependencies**

```bash
cd agent-sandbox
pip install -r requirements.txt
```

**2. Start the API server**

```bash
python3 -m uvicorn server:app --reload --port 8000
```

**3. Open Swagger docs**

Go to [http://localhost:8000/docs](http://localhost:8000/docs) — every endpoint is interactive.

**4. Try a few calls**

```bash
# Look up a member
curl http://localhost:8000/api/members/MBR-B5906016

# Get their claims
curl "http://localhost:8000/api/claims?member_id=MBR-B5906016&limit=5"

# Use the generic tool endpoint (for agent frameworks)
curl -X POST http://localhost:8000/tool \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "lookup_member", "params": {"member_id": "MBR-B5906016"}}'
```

**5. Wire up an agent manually**

Copy tool definitions from `tools/tool_schemas.json` into your agent config. Write HTTP client code to call `POST /tool`. Build the conversation loop. Handle errors. Parse responses.

**6. Run eval scenarios**

Load `scenarios/scenarios.json` — 20 test cases. Send each `user_prompt` to your agent, compare tool calls against `expected_tools` and `success_criteria`.

---

### The difference

| | With MCP | Without MCP |
|---|---|---|
| **Setup time** | 2 minutes (config file change) | Hours (write integration code) |
| **Tool discovery** | Automatic — agent sees all 18 tools | Manual — copy schemas, wire each one |
| **First demo** | Immediately — just start talking | After building conversation loop |
| **Tool selection** | Agent decides which tools to use | Developer pre-programs tool routing |
| **Multi-step reasoning** | Built in — agent chains tools naturally | Developer builds state machine |
| **Adding new tools** | Add to server, auto-discovered | Update schemas, update routing code |

## Dataset summary

| Entity | Records | Description |
|--------|---------|-------------|
| Employers | 25 | Companies offering health plans |
| Plans | 50 | Insurance plans with varied coverage |
| Benefits | 900 | 18 service categories per plan |
| Providers | 300 | Doctors, hospitals, specialists |
| Members | 2,000 | Primary subscribers |
| Dependents | 2,297 | Spouses and children |
| Eligibility | 4,297 | Coverage periods for all members/dependents |
| Medical Claims | 13,841 | Claims with realistic status distributions |
| Claim Lines | 24,206 | Line-item detail with CPT/ICD-10 codes |
| Pharmacy Claims | 7,055 | Prescription fills with NDC codes |
| Authorizations | 567 | Prior auth requests and decisions |
| Accumulators | 2,000 | Deductible/OOP tracking |
| Call Logs | 3,000 | Member service interactions |
| Secure Messages | 2,000 | Portal message threads |
| Case Notes | 1,500 | Internal case documentation |
| Agents | 20 | Service agent profiles |

## Key design decisions

- **Deterministic**: All generators use `random.seed(42)` — regenerating produces identical data
- **Referential integrity**: Claims reference real member IDs, dependents link to real members, eligibility ties to real plans
- **Realistic distributions**: Chronic condition prevalence, claim denial rate (~7.7%), auth approval rate (~56.1%) match industry patterns
- **ICD-10 / CPT / NDC codes**: Real code formats with realistic mappings (diagnosis → procedure → place of service)

## Documentation

- **`index.html`** — Open in a browser for a visual overview of everything in the platform
- **`docs/DATA-SPECIFICATION.md`** — Data-derived field-level dictionary generated from `data/json`
- **`agent-sandbox/AGENT-SANDBOX-SPEC.md`** — Agent tooling spec with architecture diagram and API examples
  - `search_knowledge_base` supports `section=business_rules` and `section=reference_data` for rules and reference codes

## Validation

Run a quick integrity check on the dataset:

```bash
python3 scripts/validate_data.py
```

## Regeneration

```bash
python3 generator/generate.py
python3 generator/generate_interactions.py
python3 scripts/generate_data_spec.py
python3 scripts/validate_data.py
```
