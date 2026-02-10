#!/usr/bin/env python3
"""
build_database.py — Generate healthcare.db from JSON source files.

Creates a SQLite database with:
  - 16 entity tables + 4 reference tables + 3 junction tables
  - Foreign key constraints (enforced via PRAGMA foreign_keys = ON)
  - Indexes on every foreign key and commonly queried column
  - Flattened address objects and normalized array fields

Usage:
    python3 scripts/build_database.py          # from project root
    python3 scripts/build_database.py --force   # overwrite existing .db

The JSON files in data/json/ remain the canonical source of truth.
This script is idempotent — re-run it any time the JSON changes.
"""

import json
import sqlite3
import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = PROJECT_ROOT / "data" / "json"
DB_PATH = PROJECT_ROOT / "data" / "healthcare.db"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- Reference / lookup tables (no foreign keys)
-- ============================================================

CREATE TABLE IF NOT EXISTS reference_diagnosis_codes (
    code            TEXT PRIMARY KEY,
    description     TEXT,
    category        TEXT
);

CREATE TABLE IF NOT EXISTS reference_procedure_codes (
    code            TEXT PRIMARY KEY,
    description     TEXT,
    category        TEXT,
    avg_cost        REAL
);

CREATE TABLE IF NOT EXISTS reference_place_of_service (
    code            TEXT PRIMARY KEY,
    description     TEXT
);

CREATE TABLE IF NOT EXISTS reference_medications (
    name            TEXT PRIMARY KEY,
    ndc             TEXT,
    category        TEXT,
    avg_cost        REAL,
    days_supply     INTEGER
);

-- ============================================================
-- Core entities
-- ============================================================

CREATE TABLE IF NOT EXISTS employers (
    employer_id     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    tax_id          TEXT,
    industry        TEXT,
    size_category   TEXT,
    employee_count  INTEGER,
    address_line1   TEXT,
    address_line2   TEXT,
    address_city    TEXT,
    address_state   TEXT,
    address_zip     TEXT,
    phone           TEXT,
    effective_date  TEXT,
    status          TEXT
);

CREATE TABLE IF NOT EXISTS plans (
    plan_id                     TEXT PRIMARY KEY,
    employer_id                 TEXT REFERENCES employers(employer_id),
    plan_name                   TEXT,
    plan_type                   TEXT,
    tier                        TEXT,
    effective_date              TEXT,
    termination_date            TEXT,
    status                      TEXT,
    deductible_individual       INTEGER,
    deductible_family           INTEGER,
    out_of_pocket_max_individual INTEGER,
    out_of_pocket_max_family    INTEGER,
    monthly_premium_individual  REAL,
    monthly_premium_family      REAL,
    coinsurance_in_network      INTEGER,
    coinsurance_out_of_network  INTEGER,
    copay_pcp                   INTEGER,
    copay_specialist            INTEGER,
    copay_er                    INTEGER,
    copay_urgent_care           INTEGER,
    copay_rx_generic            INTEGER,
    copay_rx_preferred_brand    INTEGER,
    copay_rx_non_preferred      INTEGER,
    copay_rx_specialty          INTEGER,
    network_name                TEXT,
    pharmacy_benefit_manager    TEXT
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id             TEXT PRIMARY KEY,
    npi                     TEXT,
    name                    TEXT NOT NULL,
    type                    TEXT,
    specialty               TEXT,
    tax_id                  TEXT,
    address_line1           TEXT,
    address_line2           TEXT,
    address_city            TEXT,
    address_state           TEXT,
    address_zip             TEXT,
    phone                   TEXT,
    accepting_new_patients  INTEGER,  -- boolean: 0/1
    network_status          TEXT,
    rating                  REAL,
    effective_date          TEXT
);

CREATE TABLE IF NOT EXISTS agents (
    agent_id                    TEXT PRIMARY KEY,
    name                        TEXT NOT NULL,
    department                  TEXT,
    role                        TEXT,
    hire_date                   TEXT,
    avg_handle_time_seconds     INTEGER,
    satisfaction_score          REAL
);

CREATE TABLE IF NOT EXISTS members (
    member_id           TEXT PRIMARY KEY,
    subscriber_id       TEXT,
    employer_id         TEXT REFERENCES employers(employer_id),
    plan_id             TEXT REFERENCES plans(plan_id),
    first_name          TEXT,
    last_name           TEXT,
    date_of_birth       TEXT,
    age                 INTEGER,
    gender              TEXT,
    ssn_last4           TEXT,
    email               TEXT,
    phone               TEXT,
    address_line1       TEXT,
    address_line2       TEXT,
    address_city        TEXT,
    address_state       TEXT,
    address_zip         TEXT,
    coverage_type       TEXT,
    relationship        TEXT,
    pcp_provider_id     TEXT REFERENCES providers(provider_id),
    status              TEXT,
    enrollment_date     TEXT,
    termination_date    TEXT
);

CREATE TABLE IF NOT EXISTS dependents (
    member_id               TEXT PRIMARY KEY,
    subscriber_id           TEXT,
    subscriber_member_id    TEXT REFERENCES members(member_id),
    employer_id             TEXT REFERENCES employers(employer_id),
    plan_id                 TEXT REFERENCES plans(plan_id),
    first_name              TEXT,
    last_name               TEXT,
    date_of_birth           TEXT,
    gender                  TEXT,
    relationship            TEXT,
    status                  TEXT,
    enrollment_date         TEXT
);

CREATE TABLE IF NOT EXISTS benefits (
    benefit_id          TEXT PRIMARY KEY,
    plan_id             TEXT REFERENCES plans(plan_id),
    category            TEXT,
    network_tier        TEXT,
    cost_sharing_type   TEXT,
    deductible_applies  TEXT,
    description         TEXT,
    annual_limit        INTEGER,
    requires_auth       INTEGER,  -- boolean: 0/1
    requires_referral   INTEGER   -- boolean: 0/1
);

CREATE TABLE IF NOT EXISTS eligibility (
    eligibility_id      TEXT PRIMARY KEY,
    member_id           TEXT NOT NULL,  -- FK checked at insert (members or dependents)
    plan_id             TEXT REFERENCES plans(plan_id),
    coverage_type       TEXT,
    effective_date      TEXT,
    termination_date    TEXT,
    status              TEXT,
    cobra_flag          INTEGER  -- boolean: 0/1
);

CREATE TABLE IF NOT EXISTS accumulators (
    accumulator_id      TEXT PRIMARY KEY,
    member_id           TEXT NOT NULL,  -- references members or dependents
    plan_id             TEXT REFERENCES plans(plan_id),
    plan_year           INTEGER,
    deductible_limit    REAL,
    deductible_used     REAL,
    deductible_remaining REAL,
    oop_max_limit       REAL,
    oop_used            REAL,
    oop_remaining       REAL,
    last_updated        TEXT
);

-- ============================================================
-- Claims
-- ============================================================

CREATE TABLE IF NOT EXISTS medical_claims (
    claim_id                        TEXT PRIMARY KEY,
    member_id                       TEXT NOT NULL,
    plan_id                         TEXT REFERENCES plans(plan_id),
    provider_id                     TEXT REFERENCES providers(provider_id),
    claim_type                      TEXT,
    claim_status                    TEXT,
    service_date                    TEXT,
    received_date                   TEXT,
    processed_date                  TEXT,
    primary_diagnosis               TEXT,
    primary_diagnosis_description   TEXT,
    secondary_diagnosis             TEXT,
    place_of_service                TEXT,
    place_of_service_description    TEXT,
    total_billed                    REAL,
    total_allowed                   REAL,
    total_plan_paid                 REAL,
    total_member_responsibility     REAL,
    denial_reason                   TEXT,
    appeal_status                   TEXT,
    check_number                    TEXT,
    payment_date                    TEXT
);

CREATE TABLE IF NOT EXISTS claim_lines (
    claim_line_id           TEXT PRIMARY KEY,
    claim_id                TEXT REFERENCES medical_claims(claim_id),
    line_number             INTEGER,
    procedure_code          TEXT,
    procedure_description   TEXT,
    modifier                TEXT,
    units                   INTEGER,
    diagnosis_pointer       TEXT,
    billed_amount           REAL,
    allowed_amount          REAL,
    plan_paid_amount        REAL,
    member_responsibility   REAL,
    service_date            TEXT
);

CREATE TABLE IF NOT EXISTS pharmacy_claims (
    rx_claim_id         TEXT PRIMARY KEY,
    member_id           TEXT NOT NULL,
    plan_id             TEXT REFERENCES plans(plan_id),
    fill_date           TEXT,
    medication_name     TEXT,
    ndc                 TEXT,
    medication_category TEXT,
    quantity            INTEGER,
    days_supply         INTEGER,
    refill_number       INTEGER,
    prescriber_npi      TEXT,
    pharmacy_npi        TEXT,
    pharmacy_name       TEXT,
    formulary_status    TEXT,
    prior_auth_required INTEGER,  -- boolean: 0/1
    ingredient_cost     REAL,
    dispensing_fee       REAL,
    total_cost          REAL,
    member_copay        REAL,
    plan_paid           REAL,
    claim_status        TEXT,
    daw_code            TEXT
);

-- ============================================================
-- Operational
-- ============================================================

CREATE TABLE IF NOT EXISTS authorizations (
    auth_id             TEXT PRIMARY KEY,
    member_id           TEXT NOT NULL,
    plan_id             TEXT REFERENCES plans(plan_id),
    provider_id         TEXT REFERENCES providers(provider_id),
    auth_type           TEXT,
    service_description TEXT,
    procedure_code      TEXT,
    service_category    TEXT,
    status              TEXT,
    request_date        TEXT,
    decision_date       TEXT,
    effective_date      TEXT,
    expiration_date     TEXT,
    approved_units      INTEGER,
    requested_units     INTEGER,
    denial_reason       TEXT,
    clinical_notes      TEXT,
    urgency             TEXT,
    reviewer            TEXT
);

CREATE TABLE IF NOT EXISTS call_logs (
    call_id                 TEXT PRIMARY KEY,
    member_id               TEXT NOT NULL,
    agent_id                TEXT REFERENCES agents(agent_id),
    call_date               TEXT,
    call_time               TEXT,
    duration_seconds        INTEGER,
    call_type               TEXT,
    call_reason             TEXT,
    disposition             TEXT,
    related_claim_id        TEXT REFERENCES medical_claims(claim_id),
    related_auth_id         TEXT REFERENCES authorizations(auth_id),
    sentiment               TEXT,
    notes                   TEXT,
    queue_wait_seconds      INTEGER,
    first_call_resolution   INTEGER,  -- boolean: 0/1
    ivr_path                TEXT
);

CREATE TABLE IF NOT EXISTS case_notes (
    note_id             TEXT PRIMARY KEY,
    member_id           TEXT NOT NULL,
    case_id             TEXT,
    author              TEXT,
    created_date        TEXT,
    category            TEXT,
    note_type           TEXT,
    content             TEXT,
    related_claim_id    TEXT REFERENCES medical_claims(claim_id),
    related_auth_id     TEXT REFERENCES authorizations(auth_id),
    follow_up_required  INTEGER,  -- boolean: 0/1
    follow_up_date      TEXT,
    status              TEXT
);

CREATE TABLE IF NOT EXISTS secure_messages (
    message_id          TEXT PRIMARY KEY,
    thread_id           TEXT,
    member_id           TEXT NOT NULL,
    direction           TEXT,
    sent_date           TEXT,
    subject             TEXT,
    body                TEXT,
    category            TEXT,
    status              TEXT,
    related_claim_id    TEXT REFERENCES medical_claims(claim_id),
    priority            TEXT,
    response_time_hours REAL
);

-- ============================================================
-- Junction tables (normalized arrays)
-- ============================================================

CREATE TABLE IF NOT EXISTS member_chronic_conditions (
    member_id           TEXT REFERENCES members(member_id),
    condition_name      TEXT NOT NULL,
    PRIMARY KEY (member_id, condition_name)
);

CREATE TABLE IF NOT EXISTS provider_languages (
    provider_id         TEXT REFERENCES providers(provider_id),
    language            TEXT NOT NULL,
    PRIMARY KEY (provider_id, language)
);

CREATE TABLE IF NOT EXISTS agent_languages (
    agent_id            TEXT REFERENCES agents(agent_id),
    language            TEXT NOT NULL,
    PRIMARY KEY (agent_id, language)
);

-- ============================================================
-- Indexes on foreign keys and common query columns
-- ============================================================

-- Plans
CREATE INDEX IF NOT EXISTS idx_plans_employer ON plans(employer_id);
CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);

-- Members
CREATE INDEX IF NOT EXISTS idx_members_employer ON members(employer_id);
CREATE INDEX IF NOT EXISTS idx_members_plan ON members(plan_id);
CREATE INDEX IF NOT EXISTS idx_members_pcp ON members(pcp_provider_id);
CREATE INDEX IF NOT EXISTS idx_members_status ON members(status);
CREATE INDEX IF NOT EXISTS idx_members_name ON members(last_name, first_name);

-- Dependents
CREATE INDEX IF NOT EXISTS idx_dependents_subscriber ON dependents(subscriber_member_id);
CREATE INDEX IF NOT EXISTS idx_dependents_employer ON dependents(employer_id);
CREATE INDEX IF NOT EXISTS idx_dependents_plan ON dependents(plan_id);

-- Benefits
CREATE INDEX IF NOT EXISTS idx_benefits_plan ON benefits(plan_id);
CREATE INDEX IF NOT EXISTS idx_benefits_category ON benefits(category);

-- Eligibility
CREATE INDEX IF NOT EXISTS idx_eligibility_member ON eligibility(member_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_plan ON eligibility(plan_id);

-- Accumulators
CREATE INDEX IF NOT EXISTS idx_accumulators_member ON accumulators(member_id);
CREATE INDEX IF NOT EXISTS idx_accumulators_plan ON accumulators(plan_id);

-- Medical claims
CREATE INDEX IF NOT EXISTS idx_claims_member ON medical_claims(member_id);
CREATE INDEX IF NOT EXISTS idx_claims_plan ON medical_claims(plan_id);
CREATE INDEX IF NOT EXISTS idx_claims_provider ON medical_claims(provider_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON medical_claims(claim_status);
CREATE INDEX IF NOT EXISTS idx_claims_service_date ON medical_claims(service_date);

-- Claim lines
CREATE INDEX IF NOT EXISTS idx_claim_lines_claim ON claim_lines(claim_id);

-- Pharmacy claims
CREATE INDEX IF NOT EXISTS idx_rx_claims_member ON pharmacy_claims(member_id);
CREATE INDEX IF NOT EXISTS idx_rx_claims_plan ON pharmacy_claims(plan_id);
CREATE INDEX IF NOT EXISTS idx_rx_claims_fill_date ON pharmacy_claims(fill_date);

-- Authorizations
CREATE INDEX IF NOT EXISTS idx_auth_member ON authorizations(member_id);
CREATE INDEX IF NOT EXISTS idx_auth_plan ON authorizations(plan_id);
CREATE INDEX IF NOT EXISTS idx_auth_provider ON authorizations(provider_id);
CREATE INDEX IF NOT EXISTS idx_auth_status ON authorizations(status);

-- Call logs
CREATE INDEX IF NOT EXISTS idx_calls_member ON call_logs(member_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent ON call_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_date ON call_logs(call_date);

-- Case notes
CREATE INDEX IF NOT EXISTS idx_notes_member ON case_notes(member_id);
CREATE INDEX IF NOT EXISTS idx_notes_case ON case_notes(case_id);

-- Secure messages
CREATE INDEX IF NOT EXISTS idx_messages_member ON secure_messages(member_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON secure_messages(thread_id);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(filename: str) -> list:
    """Load a JSON array from data/json/."""
    path = JSON_DIR / filename
    if not path.exists():
        print(f"  ⚠  {filename} not found, skipping")
        return []
    with open(path, "r") as f:
        return json.load(f)


def flatten_address(row: dict) -> dict:
    """Extract nested address object into flat address_* columns."""
    addr = row.pop("address", None) or {}
    row["address_line1"] = addr.get("line1")
    row["address_line2"] = addr.get("line2")
    row["address_city"] = addr.get("city")
    row["address_state"] = addr.get("state")
    row["address_zip"] = addr.get("zip")
    return row


def bool_to_int(val):
    """Convert Python bool/None to SQLite integer."""
    if val is None:
        return None
    return 1 if val else 0


def insert_rows(cur: sqlite3.Cursor, table: str, rows: list, columns: list):
    """Bulk insert rows into a table."""
    if not rows:
        return 0
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join(columns)
    sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"
    values = []
    for row in rows:
        values.append(tuple(row.get(col) for col in columns))
    cur.executemany(sql, values)
    return len(values)


# ---------------------------------------------------------------------------
# Entity loaders
# ---------------------------------------------------------------------------

def load_reference_tables(cur):
    """Load all 4 reference/lookup tables."""
    for filename, table, cols in [
        ("reference_diagnosis_codes.json", "reference_diagnosis_codes", ["code", "description", "category"]),
        ("reference_procedure_codes.json", "reference_procedure_codes", ["code", "description", "category", "avg_cost"]),
        ("reference_place_of_service.json", "reference_place_of_service", ["code", "description"]),
        ("reference_medications.json", "reference_medications", ["name", "ndc", "category", "avg_cost", "days_supply"]),
    ]:
        data = load_json(filename)
        n = insert_rows(cur, table, data, cols)
        print(f"  {table}: {n} rows")


def load_employers(cur):
    data = load_json("employers.json")
    for row in data:
        flatten_address(row)
        row.pop("account_manager", None)  # not in schema — lightweight field
    cols = ["employer_id", "name", "tax_id", "industry", "size_category",
            "employee_count", "address_line1", "address_line2", "address_city",
            "address_state", "address_zip", "phone", "effective_date", "status"]
    n = insert_rows(cur, "employers", data, cols)
    print(f"  employers: {n} rows")


def load_plans(cur):
    data = load_json("plans.json")
    cols = ["plan_id", "employer_id", "plan_name", "plan_type", "tier",
            "effective_date", "termination_date", "status",
            "deductible_individual", "deductible_family",
            "out_of_pocket_max_individual", "out_of_pocket_max_family",
            "monthly_premium_individual", "monthly_premium_family",
            "coinsurance_in_network", "coinsurance_out_of_network",
            "copay_pcp", "copay_specialist", "copay_er", "copay_urgent_care",
            "copay_rx_generic", "copay_rx_preferred_brand",
            "copay_rx_non_preferred", "copay_rx_specialty",
            "network_name", "pharmacy_benefit_manager"]
    n = insert_rows(cur, "plans", data, cols)
    print(f"  plans: {n} rows")


def load_providers(cur):
    data = load_json("providers.json")
    languages_rows = []
    for row in data:
        flatten_address(row)
        row["accepting_new_patients"] = bool_to_int(row.get("accepting_new_patients"))
        langs = row.pop("languages", []) or []
        for lang in langs:
            languages_rows.append({"provider_id": row["provider_id"], "language": lang})
    cols = ["provider_id", "npi", "name", "type", "specialty", "tax_id",
            "address_line1", "address_line2", "address_city", "address_state",
            "address_zip", "phone", "accepting_new_patients", "network_status",
            "rating", "effective_date"]
    n = insert_rows(cur, "providers", data, cols)
    print(f"  providers: {n} rows")
    n2 = insert_rows(cur, "provider_languages", languages_rows, ["provider_id", "language"])
    print(f"  provider_languages: {n2} rows")


def load_agents(cur):
    data = load_json("agents.json")
    languages_rows = []
    for row in data:
        langs = row.pop("languages", []) or []
        for lang in langs:
            languages_rows.append({"agent_id": row["agent_id"], "language": lang})
    cols = ["agent_id", "name", "department", "role", "hire_date",
            "avg_handle_time_seconds", "satisfaction_score"]
    n = insert_rows(cur, "agents", data, cols)
    print(f"  agents: {n} rows")
    n2 = insert_rows(cur, "agent_languages", languages_rows, ["agent_id", "language"])
    print(f"  agent_languages: {n2} rows")


def load_members(cur):
    data = load_json("members.json")
    conditions_rows = []
    for row in data:
        flatten_address(row)
        conditions = row.pop("chronic_conditions", []) or []
        for cond in conditions:
            conditions_rows.append({"member_id": row["member_id"], "condition_name": cond})
    cols = ["member_id", "subscriber_id", "employer_id", "plan_id",
            "first_name", "last_name", "date_of_birth", "age", "gender",
            "ssn_last4", "email", "phone", "address_line1", "address_line2",
            "address_city", "address_state", "address_zip", "coverage_type",
            "relationship", "pcp_provider_id", "status", "enrollment_date",
            "termination_date"]
    n = insert_rows(cur, "members", data, cols)
    print(f"  members: {n} rows")
    n2 = insert_rows(cur, "member_chronic_conditions", conditions_rows, ["member_id", "condition_name"])
    print(f"  member_chronic_conditions: {n2} rows")


def load_dependents(cur):
    data = load_json("dependents.json")
    cols = ["member_id", "subscriber_id", "subscriber_member_id", "employer_id",
            "plan_id", "first_name", "last_name", "date_of_birth", "gender",
            "relationship", "status", "enrollment_date"]
    n = insert_rows(cur, "dependents", data, cols)
    print(f"  dependents: {n} rows")


def load_benefits(cur):
    data = load_json("benefits.json")
    for row in data:
        row["requires_auth"] = bool_to_int(row.get("requires_auth"))
        row["requires_referral"] = bool_to_int(row.get("requires_referral"))
    cols = ["benefit_id", "plan_id", "category", "network_tier",
            "cost_sharing_type", "deductible_applies", "description",
            "annual_limit", "requires_auth", "requires_referral"]
    n = insert_rows(cur, "benefits", data, cols)
    print(f"  benefits: {n} rows")


def load_eligibility(cur):
    data = load_json("eligibility.json")
    for row in data:
        row["cobra_flag"] = bool_to_int(row.get("cobra_flag"))
    cols = ["eligibility_id", "member_id", "plan_id", "coverage_type",
            "effective_date", "termination_date", "status", "cobra_flag"]
    n = insert_rows(cur, "eligibility", data, cols)
    print(f"  eligibility: {n} rows")


def load_accumulators(cur):
    data = load_json("accumulators.json")
    cols = ["accumulator_id", "member_id", "plan_id", "plan_year",
            "deductible_limit", "deductible_used", "deductible_remaining",
            "oop_max_limit", "oop_used", "oop_remaining", "last_updated"]
    n = insert_rows(cur, "accumulators", data, cols)
    print(f"  accumulators: {n} rows")


def load_medical_claims(cur):
    data = load_json("medical_claims.json")
    cols = ["claim_id", "member_id", "plan_id", "provider_id", "claim_type",
            "claim_status", "service_date", "received_date", "processed_date",
            "primary_diagnosis", "primary_diagnosis_description",
            "secondary_diagnosis", "place_of_service",
            "place_of_service_description", "total_billed", "total_allowed",
            "total_plan_paid", "total_member_responsibility", "denial_reason",
            "appeal_status", "check_number", "payment_date"]
    n = insert_rows(cur, "medical_claims", data, cols)
    print(f"  medical_claims: {n} rows")


def load_claim_lines(cur):
    data = load_json("claim_lines.json")
    cols = ["claim_line_id", "claim_id", "line_number", "procedure_code",
            "procedure_description", "modifier", "units", "diagnosis_pointer",
            "billed_amount", "allowed_amount", "plan_paid_amount",
            "member_responsibility", "service_date"]
    n = insert_rows(cur, "claim_lines", data, cols)
    print(f"  claim_lines: {n} rows")


def load_pharmacy_claims(cur):
    data = load_json("pharmacy_claims.json")
    for row in data:
        row["prior_auth_required"] = bool_to_int(row.get("prior_auth_required"))
    cols = ["rx_claim_id", "member_id", "plan_id", "fill_date",
            "medication_name", "ndc", "medication_category", "quantity",
            "days_supply", "refill_number", "prescriber_npi", "pharmacy_npi",
            "pharmacy_name", "formulary_status", "prior_auth_required",
            "ingredient_cost", "dispensing_fee", "total_cost", "member_copay",
            "plan_paid", "claim_status", "daw_code"]
    n = insert_rows(cur, "pharmacy_claims", data, cols)
    print(f"  pharmacy_claims: {n} rows")


def load_authorizations(cur):
    data = load_json("authorizations.json")
    cols = ["auth_id", "member_id", "plan_id", "provider_id", "auth_type",
            "service_description", "procedure_code", "service_category",
            "status", "request_date", "decision_date", "effective_date",
            "expiration_date", "approved_units", "requested_units",
            "denial_reason", "clinical_notes", "urgency", "reviewer"]
    n = insert_rows(cur, "authorizations", data, cols)
    print(f"  authorizations: {n} rows")


def load_call_logs(cur):
    data = load_json("call_logs.json")
    for row in data:
        row["first_call_resolution"] = bool_to_int(row.get("first_call_resolution"))
    cols = ["call_id", "member_id", "agent_id", "call_date", "call_time",
            "duration_seconds", "call_type", "call_reason", "disposition",
            "related_claim_id", "related_auth_id", "sentiment", "notes",
            "queue_wait_seconds", "first_call_resolution", "ivr_path"]
    n = insert_rows(cur, "call_logs", data, cols)
    print(f"  call_logs: {n} rows")


def load_case_notes(cur):
    data = load_json("case_notes.json")
    for row in data:
        row["follow_up_required"] = bool_to_int(row.get("follow_up_required"))
    cols = ["note_id", "member_id", "case_id", "author", "created_date",
            "category", "note_type", "content", "related_claim_id",
            "related_auth_id", "follow_up_required", "follow_up_date", "status"]
    n = insert_rows(cur, "case_notes", data, cols)
    print(f"  case_notes: {n} rows")


def load_secure_messages(cur):
    data = load_json("secure_messages.json")
    cols = ["message_id", "thread_id", "member_id", "direction", "sent_date",
            "subject", "body", "category", "status", "related_claim_id",
            "priority", "response_time_hours"]
    n = insert_rows(cur, "secure_messages", data, cols)
    print(f"  secure_messages: {n} rows")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build():
    force = "--force" in sys.argv

    if DB_PATH.exists():
        if force:
            DB_PATH.unlink()
            print(f"Removed existing {DB_PATH.name}")
        else:
            print(f"ERROR: {DB_PATH} already exists. Use --force to overwrite.")
            sys.exit(1)

    print(f"Building {DB_PATH.name} from {JSON_DIR}/...")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Create schema
    print("\n[1/3] Creating schema...")
    cur.executescript(SCHEMA)

    # Load data (order matters for foreign keys)
    print("\n[2/3] Loading data...")
    load_reference_tables(cur)
    load_employers(cur)
    load_plans(cur)
    load_providers(cur)
    load_agents(cur)
    load_members(cur)
    load_dependents(cur)
    load_benefits(cur)
    load_eligibility(cur)
    load_accumulators(cur)
    load_medical_claims(cur)
    load_claim_lines(cur)
    load_pharmacy_claims(cur)
    load_authorizations(cur)
    load_call_logs(cur)
    load_case_notes(cur)
    load_secure_messages(cur)

    conn.commit()

    # Verify
    print("\n[3/3] Verifying...")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  Tables created: {len(tables)}")

    total_rows = 0
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        total_rows += count

    print(f"  Total rows: {total_rows:,}")

    # FK integrity check
    cur.execute("PRAGMA foreign_key_check")
    fk_errors = cur.fetchall()
    if fk_errors:
        print(f"\n  ⚠  {len(fk_errors)} foreign key violations found!")
        for err in fk_errors[:10]:
            print(f"     {err}")
    else:
        print("  Foreign key check: PASSED ✓")

    db_size = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\n  Database size: {db_size:.1f} MB")
    print(f"  Location: {DB_PATH}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    build()
