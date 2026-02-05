# Healthcare Agent Sandbox

Synthetic data platform for prototyping AI agents against realistic health insurance data. All data is fictional — no real PHI/PII.

## What's in the box

```
healthcare-synthetic-data/
├── data/                        # 33MB of synthetic healthcare data
│   ├── json/                    # 21 JSON files (primary format)
│   └── csv/                     # CSV mirrors of all entities
├── agent-sandbox/               # API server + agent tooling
│   ├── server.py                # FastAPI server (23 endpoints)
│   ├── api_server.py            # Core query engine (18 tools)
│   ├── mcp_server.py            # MCP server (Claude Desktop / Cursor / etc.)
│   ├── tools/tool_schemas.json  # Tool definitions (Anthropic + OpenAI formats)
│   ├── rules/business_rules.json        # 31 healthcare business rules
│   ├── scenarios/scenarios.json         # 20 eval test cases
│   ├── templates/document_templates.json # 7 document templates (EOB, denial letters, etc.)
│   ├── knowledge-base/knowledge_base.json # Plan policies, FAQs, guidelines
│   └── AGENT-SANDBOX-SPEC.md            # Detailed agent sandbox spec
├── docs/DATA-SPECIFICATION.md   # Full data model spec (field-level docs)
├── generator/                   # Python scripts that generated the data
│   ├── generate.py              # Base entity generator
│   └── generate_interactions.py # Call logs, messages, case notes
├── frontend/data-platform.jsx   # React + Tailwind data explorer component
└── index.html                   # Documentation site (open in browser)
```

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
- **Realistic distributions**: Chronic condition prevalence, claim denial rates (~12%), auth approval rates (~75%) match industry patterns
- **ICD-10 / CPT / NDC codes**: Real code formats with realistic mappings (diagnosis → procedure → place of service)

## Documentation

- **`index.html`** — Open in a browser for a visual overview of everything in the platform
- **`docs/DATA-SPECIFICATION.md`** — Full field-level spec for every entity, with join patterns and distribution notes
- **`agent-sandbox/AGENT-SANDBOX-SPEC.md`** — Agent tooling spec with architecture diagram and API examples
