-- Healthcare Sandbox — SQLite Schema
-- ====================================
-- Generated from scripts/build_database.py
-- Rebuild the database: python3 scripts/build_database.py
--
-- 23 tables | ~65,837 rows | 15.7 MB
-- Foreign keys enforced via PRAGMA foreign_keys = ON
--
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
