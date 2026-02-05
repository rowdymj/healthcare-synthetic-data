# Healthcare Synthetic Dataset - Data Specification

**Version:** 1.0
**Last Updated:** 2025
**Audience:** Engineering Teams
**Purpose:** Technical Reference for Development, Testing, and Demonstrations

---

## 1. Overview

### Dataset Purpose

The Healthcare Synthetic Dataset is a realistic, production-like dataset of health insurance claims and eligibility data. It is designed for:

- **Prototype development** - Building claim processing, eligibility, and authorization systems
- **Demonstration environments** - Showcasing healthcare platform capabilities to stakeholders
- **Development and testing** - Safe environment for testing without PII exposure
- **Performance testing** - Realistic data volumes for benchmarking and load testing

### Key Statistics

| Metric | Count | Value |
|--------|-------|-------|
| **Members** | | |
| Primary Subscribers | 2,000 | |
| Dependents (Spouses/Children) | 2,297 | |
| Total Covered Lives | 4,297 | |
| **Organizations & Plans** | | |
| Employers | 25 | Across 6 industries |
| Benefit Plans | 50 | HMO, PPO, EPO, HDHP, POS with Bronze-Platinum tiers |
| Benefit Records | 900 | ~18 per plan |
| **Providers** | | |
| Total Providers | 300 | 225 individual (75%), 75 facilities (25%) |
| **Claims Activity** | | |
| Medical Claims | 13,841 | Professional and institutional |
| Claim Lines | 24,206 | Service-level detail |
| Pharmacy Claims | 7,055 | Prescription fills |
| Prior Authorizations | 567 | Pending/Approved/Denied |
| Accumulators | 2,000 | Deductible and OOP tracking |
| **Financial** | | |
| Total Billed Amount | | $63.3M |
| Plan Paid Amount | | $34.0M |
| Member Cost Share | | $13.2M |
| Denied/Adjusted | | $16.1M |

---

## 2. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SYNTHETIC HEALTHCARE                          │
│                          DATA MODEL                                  │
└─────────────────────────────────────────────────────────────────────┘

                           ┌──────────────┐
                           │  EMPLOYERS   │
                           │   (25)       │
                           └──────┬───────┘
                                  │ 1:M
                                  │
                    ┌─────────────────────────────┐
                    │         PLANS              │
                    │  (50)  HMO/PPO/EPO/HDHP   │
                    └──────┬────────────┬────────┘
                           │ 1:M        │ 1:M
                    ┌──────▼──┐    ┌────▼────────┐
                    │ BENEFITS│    │ MEMBERS    │
                    │  (900)  │    │ (2000)     │
                    └─────────┘    └────┬────────┘
                                        │ 1:M
                                   ┌────▼──────────┐
                                   │ DEPENDENTS   │
                                   │  (2297)      │
                                   └──────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              ┌─────▼──────┐     ┌──────▼────────┐  ┌───────▼──────┐
              │ELIGIBILITY │     │  ACCUMULATORS│  │AUTHORIZATIONS│
              │  (4297)    │     │    (2000)    │  │    (567)     │
              └────────────┘     └──────────────┘  └───────┬──────┘
                                                           │
                    ┌──────────────────────────────┬───────┴────────────┐
                    │                              │                    │
              ┌─────▼────────────┐      ┌──────────▼────────┐   ┌───────▼────────┐
              │  MEDICAL CLAIMS  │      │  PHARMACY CLAIMS │   │   PROVIDERS    │
              │    (13,841)      │      │     (7,055)      │   │     (300)      │
              └────┬────────────┬┘      └────┬────┬────────┘   └────────────────┘
                   │            │            │    │
                   │ 1:M        │ 1:1        │    └─ M:1 (provider_id)
              ┌────▼────┐   ┌───▼──────┐    │
              │CLAIM    │   │MEMBERS   │    │
              │LINES    │   │(foreign) │    │
              │(24,206) │   └──────────┘    │
              └─────────┘                   │
                                       ┌────▼──────┐
                                       │MEMBERS    │
                                       │(foreign)  │
                                       └───────────┘

```

---

## 3. Entity Specifications

### 3.1 EMPLOYERS

Organizations offering health benefits to employees.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| employer_id | string | Yes | Unique identifier (UUID) | `emp_550e8400-e29b-41d4-a716-446655440000` | Primary Key |
| name | string | Yes | Legal company name | `Acme Corporation` | 1-100 characters |
| industry | string | Yes | NAICS industry classification | `Manufacturing`, `Healthcare`, `Finance`, `Technology`, `Retail`, `Government` | Enum |
| employee_count | integer | Yes | Headcount range | `500` | Typically 50-5000 |
| address | string | Yes | Street address | `123 Main St, Suite 400` | |
| city | string | Yes | City name | `Springfield` | |
| state | string | Yes | Two-letter state code | `IL` | |
| zip_code | string | Yes | Five-digit ZIP code | `62701` | |
| phone | string | No | Contact phone number | `217-555-0123` | |
| email | string | No | Contact email | `benefits@acmecorp.com` | |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 25
**Industries Represented:** Manufacturing (6), Healthcare (5), Finance (4), Technology (5), Retail (3), Government (2)

---

### 3.2 PLANS

Benefit plans offered by employers with cost-sharing terms.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| plan_id | string | Yes | Unique identifier (UUID) | `plan_659e8400-e29b-41d4-a716-446655440001` | Primary Key |
| employer_id | string | Yes | Reference to employer | `emp_550e8400...` | Foreign Key → EMPLOYERS |
| plan_name | string | Yes | Display name | `Premium PPO 80/20` | |
| plan_type | string | Yes | Network type | `PPO`, `HMO`, `EPO`, `HDHP`, `POS` | Enum |
| metal_tier | string | Yes | ACA metal level | `Gold`, `Silver`, `Bronze`, `Platinum` | Enum |
| effective_date | date | Yes | Start of coverage | `2024-01-01` | |
| termination_date | date | No | End of coverage (if terminated) | `2024-12-31` | Optional |
| annual_deductible | decimal | Yes | Per-member deductible | `1500.00` | USD |
| family_deductible | decimal | Yes | Family aggregate deductible | `3000.00` | USD |
| in_network_oop_max | decimal | Yes | Out-of-pocket maximum | `5000.00` | USD |
| out_of_network_oop_max | decimal | Yes | Out-of-network OOP max | `10000.00` | USD |
| copay_primary_care | decimal | Yes | PCP office visit copay | `25.00` | USD |
| copay_specialist | decimal | Yes | Specialist office visit copay | `50.00` | USD |
| copay_urgent_care | decimal | Yes | Urgent care copay | `100.00` | USD |
| copay_emergency_room | decimal | Yes | Emergency room copay | `500.00` | Waived if admitted |
| coinsurance_in_network | decimal | Yes | In-network coinsurance % after deductible | `0.20` | 0.0-1.0 (0-100%) |
| coinsurance_out_of_network | decimal | Yes | Out-of-network coinsurance % | `0.40` | 0.0-1.0 (0-100%) |
| pharmacy_tier1_copay | decimal | Yes | Generic drug copay | `10.00` | USD |
| pharmacy_tier2_copay | decimal | Yes | Preferred brand copay | `30.00` | USD |
| pharmacy_tier3_copay | decimal | Yes | Non-preferred brand copay | `60.00` | USD |
| pharmacy_deductible | decimal | Yes | Pharmacy deductible | `100.00` | USD |
| monthly_premium | decimal | Yes | Employee monthly premium | `350.00` | USD |
| employer_contribution_pct | decimal | Yes | Employer cost share % | `0.75` | 0.0-1.0 (0-100%) |
| active | boolean | Yes | Current plan status | `true` | |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 50
**Plan Type Distribution:** PPO (18), HMO (14), HDHP (9), POS (6), EPO (3)
**Metal Tier Distribution:** Gold (15), Silver (15), Bronze (12), Platinum (8)

---

### 3.3 BENEFITS

Detailed benefit schedule for each plan covering specific services.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| benefit_id | string | Yes | Unique identifier (UUID) | `ben_759e8400-e29b-41d4-a716-446655440002` | Primary Key |
| plan_id | string | Yes | Reference to plan | `plan_659e8400...` | Foreign Key → PLANS |
| service_category | string | Yes | Type of service | `Office Visits`, `Diagnostic Lab`, `Imaging`, `Surgery`, `Mental Health`, `Pharmacy`, `Preventive`, `Rehabilitation`, `Inpatient`, `Emergency`, `Maternity`, `Durable Equipment`, `Home Health`, `Skilled Nursing`, `Hospice`, `Urgent Care`, `Telehealth`, `Vaccines` | Enum |
| is_preventive | boolean | Yes | Preventive services status | `true` | Covered at 100% |
| copay | decimal | No | Copay amount if applicable | `25.00` | USD |
| coinsurance | decimal | No | Coinsurance % after deductible | `0.20` | 0.0-1.0 |
| deductible_applies | boolean | Yes | Whether deductible applies | `true` | |
| oop_max_applies | boolean | Yes | Whether OOP max applies | `true` | |
| coverage_limit | decimal | No | Maximum benefit per service period | `5000.00` | Optional limit |
| requires_auth | boolean | Yes | Prior authorization required | `false` | |
| in_network_coverage_pct | decimal | Yes | In-network coverage % | `0.80` | 0.0-1.0 |
| out_of_network_coverage_pct | decimal | Yes | Out-of-network coverage % | `0.60` | 0.0-1.0 |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 900 (~18 per plan)
**Service Categories:** 18 distinct categories
**Key Patterns:** Preventive services = 100% coverage, Emergency = copay waived if admitted

---

### 3.4 PROVIDERS

Healthcare providers (physicians, hospitals, clinics, etc.).

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| provider_id | string | Yes | Unique identifier (UUID) | `prov_859e8400-e29b-41d4-a716-446655440003` | Primary Key |
| npi | string | Yes | National Provider Identifier | `1234567890` | 10 digits, unique in healthcare |
| provider_type | string | Yes | Individual or facility | `Individual`, `Facility` | Enum |
| first_name | string | No | First name (if individual) | `John` | |
| last_name | string | No | Last name (if individual) | `Smith` | |
| facility_name | string | No | Facility name | `Springfield General Hospital` | If facility_type |
| specialty | string | Yes | Medical specialty | `Internal Medicine`, `Cardiology`, `Surgery`, `Psychiatry`, `Orthopedics`, `Pediatrics`, `OB/GYN`, `Dentistry` | Enum |
| address | string | Yes | Office/facility address | `456 Medical Center Dr` | |
| city | string | Yes | City | `Springfield` | |
| state | string | Yes | State code | `IL` | |
| zip_code | string | Yes | ZIP code | `62701` | |
| phone | string | No | Contact phone | `217-555-0456` | |
| fax | string | No | Fax number | `217-555-0457` | |
| email | string | No | Email address | `jsmith@medicalcenter.com` | |
| accept_medicare | boolean | Yes | Medicare participation status | `true` | |
| accept_medicaid | boolean | Yes | Medicaid participation status | `true` | |
| network_status | string | Yes | Network inclusion status | `In-Network`, `Out-of-Network`, `Contracted` | Enum |
| is_primary_care | boolean | Yes | PCP eligible | `true` | Can be assigned as primary care physician |
| board_certified | boolean | Yes | Board certification status | `true` | |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 300
**Provider Type Distribution:** Individual (225 / 75%), Facility (75 / 25%)
**Network Status:** In-Network (240 / 80%), Out-of-Network (45 / 15%), Contracted (15 / 5%)
**Specialties:** 8 major specialties with varying distribution

---

### 3.5 MEMBERS

Primary subscribers (policy holders).

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| member_id | string | Yes | Unique identifier (UUID) | `mem_959e8400-e29b-41d4-a716-446655440004` | Primary Key |
| employer_id | string | Yes | Sponsoring employer | `emp_550e8400...` | Foreign Key → EMPLOYERS |
| plan_id | string | Yes | Enrolled plan | `plan_659e8400...` | Foreign Key → PLANS |
| first_name | string | Yes | Given name | `Alice` | |
| last_name | string | Yes | Family name | `Johnson` | |
| date_of_birth | date | Yes | Birth date | `1980-05-15` | Age range: 18-70 |
| gender | string | Yes | Gender | `Female`, `Male`, `Non-Binary` | Enum |
| ssn_last_four | string | Yes | Last 4 of SSN | `1234` | For matching purposes |
| email | string | No | Email address | `alice.johnson@email.com` | |
| phone | string | No | Phone number | `217-555-0789` | |
| address | string | Yes | Residential address | `789 Oak Lane` | |
| city | string | Yes | City | `Springfield` | |
| state | string | Yes | State code | `IL` | |
| zip_code | string | Yes | ZIP code | `62701` | |
| primary_care_physician_id | string | No | Assigned PCP | `prov_859e8400...` | Foreign Key → PROVIDERS (HMO requirement) |
| chronic_conditions | array | No | ICD-10 diagnosis codes | `["E11.9", "I10", "E78.5"]` | Array of codes |
| has_hypertension | boolean | Yes | Hypertension flag | `true` | ~15% of members |
| has_diabetes | boolean | Yes | Diabetes flag | `false` | ~10% of members |
| has_hyperlipidemia | boolean | Yes | High cholesterol flag | `true` | ~8% of members |
| has_asthma | boolean | Yes | Asthma flag | `false` | ~7% of members |
| has_mental_health | boolean | Yes | Mental health condition flag | `false` | ~6% of members |
| has_gerd | boolean | Yes | GERD flag | `true` | ~5% of members |
| has_back_pain | boolean | Yes | Chronic back pain flag | `false` | ~4% of members |
| smoker | boolean | Yes | Smoking status | `false` | |
| coverage_type | string | Yes | Coverage tier | `Individual`, `Individual+Spouse`, `Individual+Children`, `Family` | Enum |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 2,000
**Age Distribution:** 18-30 (15%), 30-40 (25%), 40-50 (30%), 50-60 (25%), 60-70 (5%)
**Coverage Type:** Individual (40%), Individual+Spouse (25%), Individual+Children (15%), Family (20%)
**Chronic Condition Prevalence:** ~60% have ≥1 chronic condition

---

### 3.6 DEPENDENTS

Spouses and children covered under member accounts.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| dependent_id | string | Yes | Unique identifier (UUID) | `dep_a59e8400-e29b-41d4-a716-446655440005` | Primary Key |
| member_id | string | Yes | Primary subscriber | `mem_959e8400...` | Foreign Key → MEMBERS |
| relationship | string | Yes | Relationship to member | `Spouse`, `Child` | Enum |
| first_name | string | Yes | Given name | `Robert` | |
| last_name | string | Yes | Family name | `Johnson` | |
| date_of_birth | date | Yes | Birth date | `1982-08-22` | |
| gender | string | Yes | Gender | `Male`, `Female`, `Non-Binary` | Enum |
| ssn_last_four | string | Yes | Last 4 of SSN | `5678` | For matching purposes |
| chronic_conditions | array | No | ICD-10 codes | `["J45.9"]` | Array of codes |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 2,297
**Relationship Distribution:** Spouse (1,150 / 50%), Child (1,147 / 50%)
**Age Range:** 0-85 (children range 0-18, spouses typically 20-70)

---

### 3.7 ELIGIBILITY

Coverage periods and enrollment status for each covered life.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| eligibility_id | string | Yes | Unique identifier (UUID) | `elig_b59e8400-e29b-41d4-a716-446655440006` | Primary Key |
| member_id | string | Yes | Covered member | `mem_959e8400...` | Foreign Key → MEMBERS or derived from DEPENDENTS |
| plan_id | string | Yes | Enrolled plan | `plan_659e8400...` | Foreign Key → PLANS |
| enrollment_date | date | Yes | Coverage start date | `2024-01-01` | |
| termination_date | date | No | Coverage end date | `2024-12-31` | Optional; null = active |
| termination_reason | string | No | Reason for termination | `Voluntary Termination`, `End of Contract`, `Failure to Pay Premium`, `Disenrollment` | Enum |
| coverage_status | string | Yes | Current status | `Active`, `Terminated`, `Suspended`, `COBRA Eligible` | Enum |
| is_cobra | boolean | Yes | COBRA election status | `false` | |
| cobra_start_date | date | No | COBRA coverage start | `2024-09-01` | If applicable |
| cobra_end_date | date | No | COBRA coverage end | `2025-09-01` | 18 months max |
| subscriber_indicator | boolean | Yes | Primary or dependent indicator | `true` | true = subscriber, false = dependent |
| relationship_code | string | No | Relationship if dependent | `01`, `19`, `20`, `21` | HIPAA code; blank if subscriber |
| created_at | date | Yes | Record creation date | `2023-01-15` | |
| updated_at | date | Yes | Last modification date | `2024-06-20` | |

**Total Records:** 4,297 (2,000 members + 2,297 dependents)
**Coverage Status:** Active (3,847 / 89%), Terminated (350 / 8%), COBRA Eligible (100 / 2%), Suspended (0 / 0%)
**COBRA Records:** 150 members have COBRA history

---

### 3.8 MEDICAL CLAIMS

Professional and institutional healthcare claims.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| claim_id | string | Yes | Unique identifier (UUID) | `clm_c59e8400-e29b-41d4-a716-446655440007` | Primary Key |
| member_id | string | Yes | Claiming member | `mem_959e8400...` | Foreign Key → MEMBERS/DEPENDENTS |
| claim_number | string | Yes | External claim reference | `CLM-2024-001234` | Unique per payer |
| provider_id | string | Yes | Rendering provider | `prov_859e8400...` | Foreign Key → PROVIDERS |
| servicing_provider_id | string | No | Facility provider | `prov_859e8400...` | Foreign Key → PROVIDERS |
| plan_id | string | Yes | Member's plan at time of service | `plan_659e8400...` | Foreign Key → PLANS |
| claim_type | string | Yes | Claim type | `Professional`, `Institutional` | Enum |
| service_type | string | Yes | Type of service | `Office Visit`, `Hospital Inpatient`, `ER`, `Diagnostic`, `Surgery`, `Therapy`, `Other` | Enum |
| place_of_service | string | Yes | Location code | `11`, `21`, `23`, `24`, `25`, `26`, `81` | HIPAA POS codes |
| admission_date | date | No | Hospital admission date | `2024-03-15` | For inpatient claims |
| discharge_date | date | No | Hospital discharge date | `2024-03-18` | For inpatient claims |
| service_from_date | date | Yes | Service period start | `2024-03-15` | |
| service_to_date | date | Yes | Service period end | `2024-03-15` | Same as from_date for single visits |
| received_date | date | Yes | Claim receipt date | `2024-03-22` | |
| processed_date | date | Yes | Date claim was processed | `2024-04-05` | |
| primary_diagnosis | string | Yes | Primary ICD-10 code | `I10` | Foreign Key → ICD-10 Reference |
| secondary_diagnoses | array | No | Other ICD-10 codes | `["E78.5", "E11.9"]` | Array of codes |
| procedure_codes | array | Yes | CPT codes | `["99213", "93000"]` | Array of codes |
| total_billed | decimal | Yes | Provider's billed amount | `750.00` | USD |
| allowed_amount | decimal | Yes | Plan's allowed amount | `500.00` | USD |
| plan_paid | decimal | Yes | Amount plan paid | `400.00` | USD |
| member_cost_share | decimal | Yes | Member responsibility | `100.00` | Copay + coinsurance |
| member_deductible | decimal | Yes | Applied deductible | `0.00` | USD |
| member_coinsurance | decimal | Yes | Applied coinsurance | `100.00` | USD |
| claim_status | string | Yes | Processing status | `Paid`, `Denied`, `Pending`, `Adjusted`, `Appealed` | Enum |
| denial_reason | string | No | Reason for denial | `Not Medically Necessary`, `Out of Network`, `Exceeds Frequency Limit` | If denied |
| adjustment_reason | string | No | Reason for adjustment | `Duplicate Claim`, `Coordination of Benefits` | If adjusted |
| appeal_status | string | No | Appeal status | `Pending`, `Approved`, `Denied`, `Withdrawn` | If appealed |
| requires_authorization | boolean | Yes | Prior auth needed | `false` | |
| authorization_id | string | No | Related auth record | `auth_d59e8400...` | Foreign Key → AUTHORIZATIONS |
| created_at | date | Yes | Record creation date | `2024-03-22` | |
| updated_at | date | Yes | Last modification date | `2024-04-05` | |

**Total Records:** 13,841
**Claim Status Distribution:** Paid (9,688 / 70%), Denied (1,107 / 8%), Pending (1,661 / 12%), Adjusted (969 / 7%), Appealed (416 / 3%)
**Average Billed:** $4,575
**Average Allowed:** $3,100
**Average Plan Paid:** $2,170

---

### 3.9 CLAIM LINES

Individual service lines within claims.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| claim_line_id | string | Yes | Unique identifier (UUID) | `cln_d59e8400-e29b-41d4-a716-446655440008` | Primary Key |
| claim_id | string | Yes | Parent claim | `clm_c59e8400...` | Foreign Key → MEDICAL_CLAIMS |
| line_number | integer | Yes | Sequence within claim | `1` | 1-based |
| procedure_code | string | Yes | CPT code | `99213` | Foreign Key → CPT Reference |
| modifier | string | No | CPT modifier | `25`, `59`, `76` | Optional CPT modifier |
| units | decimal | Yes | Quantity of service | `1.0` | |
| unit_price | decimal | Yes | Price per unit | `150.00` | USD |
| billed_amount | decimal | Yes | Line billed amount | `150.00` | USD |
| allowed_amount | decimal | Yes | Line allowed amount | `100.00` | USD |
| plan_paid | decimal | Yes | Plan payment | `80.00` | USD |
| member_deductible | decimal | Yes | Applied deductible | `0.00` | USD |
| member_coinsurance | decimal | Yes | Applied coinsurance | `20.00` | USD |
| line_status | string | Yes | Processing status | `Paid`, `Denied`, `Pending`, `Adjusted` | Enum |
| denial_reason | string | No | Reason for denial | `Exceeds Frequency Limit`, `Bundled with Primary` | If denied |
| service_from_date | date | Yes | Service date | `2024-03-15` | |
| service_to_date | date | Yes | Service date end | `2024-03-15` | |
| created_at | date | Yes | Record creation date | `2024-03-22` | |
| updated_at | date | Yes | Last modification date | `2024-04-05` | |

**Total Records:** 24,206 (average 1.75 lines per claim)
**Line Status:** Paid (16,944 / 70%), Denied (1,936 / 8%), Pending (2,929 / 12%), Adjusted (1,397 / 6%)

---

### 3.10 PHARMACY CLAIMS

Prescription drug fills and refills.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| pharmacy_claim_id | string | Yes | Unique identifier (UUID) | `phrm_e59e8400-e29b-41d4-a716-446655440009` | Primary Key |
| member_id | string | Yes | Claiming member | `mem_959e8400...` | Foreign Key → MEMBERS/DEPENDENTS |
| plan_id | string | Yes | Member's plan | `plan_659e8400...` | Foreign Key → PLANS |
| ndc | string | Yes | National Drug Code | `00002003201` | 11-digit code |
| medication_name | string | Yes | Drug name | `Lisinopril 10mg tablet` | |
| therapy_class | string | Yes | Drug category | `ACE Inhibitor`, `Statin`, `Beta Blocker`, `SSRI`, `Antibiotic`, `Analgesic`, `Other` | Enum |
| prescription_date | date | Yes | Date drug prescribed | `2024-03-10` | |
| fill_date | date | Yes | Date prescription filled | `2024-03-11` | |
| days_supply | integer | Yes | Days of medication provided | `30` | Typical: 30, 90 |
| quantity | integer | Yes | Number of units | `30` | Tablets, capsules, etc. |
| dispensing_pharmacy_id | string | No | Pharmacy identifier | `phar_f59e8400...` | Optional for tracking |
| formulary_status | string | Yes | Formulary tier | `Tier 1 (Generic)`, `Tier 2 (Preferred Brand)`, `Tier 3 (Non-Preferred)`, `Not Covered` | Enum |
| requires_authorization | boolean | Yes | Prior auth required | `false` | |
| authorization_id | string | No | Related auth | `auth_d59e8400...` | Foreign Key → AUTHORIZATIONS |
| ingredient_cost | decimal | Yes | AWP or ingredient cost | `5.00` | USD |
| dispensing_fee | decimal | Yes | Pharmacy dispensing fee | `2.50` | USD |
| total_billed | decimal | Yes | Total billed | `7.50` | USD |
| plan_paid | decimal | Yes | Plan payment | `5.00` | USD |
| member_cost_share | decimal | Yes | Member responsibility | `2.50` | Copay or coinsurance |
| claim_status | string | Yes | Processing status | `Paid`, `Denied`, `Pending`, `Reversed` | Enum |
| denial_reason | string | No | Reason for denial | `Prior Authorization Required`, `Quantity Limit Exceeded`, `Non-Formulary` | If denied |
| created_at | date | Yes | Record creation date | `2024-03-11` | |
| updated_at | date | Yes | Last modification date | `2024-03-12` | |

**Total Records:** 7,055
**Claim Status:** Paid (6,279 / 89%), Denied (423 / 6%), Pending (353 / 5%)
**Formulary Distribution:** Tier 1 (60%), Tier 2 (25%), Tier 3 (10%), Not Covered (5%)
**Average Cost:** $8.75 total billed, $6.20 plan paid

---

### 3.11 AUTHORIZATIONS

Prior authorization and precertification records.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| authorization_id | string | Yes | Unique identifier (UUID) | `auth_d59e8400-e29b-41d4-a716-446655440010` | Primary Key |
| member_id | string | Yes | Requesting member | `mem_959e8400...` | Foreign Key → MEMBERS/DEPENDENTS |
| plan_id | string | Yes | Member's plan | `plan_659e8400...` | Foreign Key → PLANS |
| provider_id | string | Yes | Requesting provider | `prov_859e8400...` | Foreign Key → PROVIDERS |
| request_type | string | Yes | Auth type | `Prior Authorization`, `Precertification`, `Referral Approval` | Enum |
| service_type | string | Yes | Service requiring auth | `Advanced Imaging`, `Surgery`, `Specialty Medication`, `Physical Therapy`, `Durable Equipment`, `Inpatient Admission` | Enum |
| procedure_code | string | No | CPT code if applicable | `70450` | Optional |
| diagnosis_code | string | Yes | ICD-10 diagnosis code | `M79.3` | Foreign Key → ICD-10 Reference |
| request_date | date | Yes | Auth request submitted date | `2024-03-10` | |
| authorization_number | string | No | Auth approval number | `AUTH-2024-12345` | Generated if approved |
| authorization_date | date | No | Date approved | `2024-03-12` | |
| expiration_date | date | No | When auth expires | `2024-06-12` | |
| units_approved | integer | No | Number of units approved | `5` | For therapies |
| authorization_status | string | Yes | Current status | `Approved`, `Denied`, `Pending`, `Partially Approved`, `Withdrawn` | Enum |
| denial_reason | string | No | Reason if denied | `Not Medically Necessary`, `Investigational Treatment`, `No Prior Conservative Tx` | |
| notes | string | No | Additional comments | `Requires concurrent mental health treatment` | |
| reviewed_by | string | No | Reviewer identifier | `reviewer_user_123` | Internal reference |
| created_at | date | Yes | Record creation date | `2024-03-10` | |
| updated_at | date | Yes | Last modification date | `2024-03-12` | |

**Total Records:** 567
**Authorization Status:** Approved (312 / 55%), Denied (85 / 15%), Pending (85 / 15%), Partially Approved (57 / 10%), Withdrawn (28 / 5%)
**Common Request Types:** Prior Authorization (65%), Precertification (25%), Referral (10%)

---

### 3.12 ACCUMULATORS

Member deductible and out-of-pocket tracking per benefit year.

| Field | Data Type | Required | Description | Example | Notes |
|-------|-----------|----------|-------------|---------|-------|
| accumulator_id | string | Yes | Unique identifier (UUID) | `acc_e59e8400-e29b-41d4-a716-446655440011` | Primary Key |
| member_id | string | Yes | Tracked member | `mem_959e8400...` | Foreign Key → MEMBERS |
| plan_id | string | Yes | Member's plan | `plan_659e8400...` | Foreign Key → PLANS |
| benefit_year | integer | Yes | Calendar year | `2024` | YYYY format |
| deductible_individual | decimal | Yes | Plan deductible amount | `1500.00` | USD |
| deductible_met | decimal | Yes | Amount toward deductible | `1250.00` | USD |
| deductible_remaining | decimal | Yes | Remaining deductible | `250.00` | USD |
| oop_max_individual | decimal | Yes | Out-of-pocket maximum | `5000.00` | USD |
| oop_met | decimal | Yes | Amount toward OOP max | `3800.00` | USD |
| oop_remaining | decimal | Yes | Remaining OOP | `1200.00` | USD |
| pharmacy_deductible | decimal | Yes | Pharmacy deductible | `100.00` | USD |
| pharmacy_deductible_met | decimal | Yes | Amount toward pharmacy ded | `100.00` | USD |
| pharmacy_deductible_remaining | decimal | Yes | Remaining pharmacy ded | `0.00` | USD |
| family_deductible | decimal | Yes | Family aggregate deductible | `3000.00` | USD |
| family_deductible_met | decimal | Yes | Family amount toward ded | `1800.00` | USD |
| family_deductible_remaining | decimal | Yes | Remaining family ded | `1200.00` | USD |
| calculation_date | date | Yes | Last calculation date | `2024-04-30` | |
| created_at | date | Yes | Record creation date | `2024-01-01` | |
| updated_at | date | Yes | Last modification date | `2024-04-30` | |

**Total Records:** 2,000 (one per primary member per benefit year)
**Deductible Status:** Not Met (400 / 20%), Partially Met (1,000 / 50%), Fully Met (600 / 30%)
**OOP Status:** Not Met (600 / 30%), Partially Met (1,100 / 55%), Fully Met (300 / 15%)

---

## 4. Reference Data

### 4.1 ICD-10 Diagnosis Codes

| Code | Description | Category | Prevalence |
|------|-------------|----------|------------|
| I10 | Essential hypertension | Circulatory | 15% |
| E11.9 | Type 2 diabetes without complications | Metabolic | 10% |
| E78.5 | Hyperlipidemia, unspecified | Metabolic | 8% |
| J45.9 | Asthma, unspecified | Respiratory | 7% |
| F41.1 | Generalized anxiety disorder | Mental Health | 6% |
| K21.9 | Unspecified GERD | GI | 5% |
| M54.5 | Low back pain | Musculoskeletal | 4% |
| F32.9 | Major depressive disorder, single episode, unspecified | Mental Health | 4% |
| E66.9 | Obesity, unspecified | Metabolic | 3% |
| M79.3 | Panniculitis, unspecified | Musculoskeletal | 2% |
| J44.9 | Chronic obstructive pulmonary disease, unspecified | Respiratory | 2% |
| E10.9 | Type 1 diabetes without complications | Metabolic | 1% |
| C34.90 | Unspecified part of unspecified lobe of right lung | Neoplasm | 1% |
| I50.9 | Heart failure, unspecified | Circulatory | 1% |
| F90.9 | Attention-deficit/hyperactivity disorder, unspecified | Mental Health | 1% |
| N18.3 | Chronic kidney disease, stage 3 | Renal | 1% |
| E89.0 | Postprocedural hypothyroidism | Endocrine | 0.5% |
| L89.90 | Pressure ulcer of unspecified site, unspecified stage | Dermatological | 0.5% |
| I21.9 | ST elevation myocardial infarction of unspecified site | Circulatory | 0.5% |
| M19.90 | Unspecified osteoarthritis of unspecified site | Musculoskeletal | 0.5% |
| S72.001 | Closed fracture of right femoral neck | Traumatic | 0.5% |
| I63.9 | Cerebral infarction, unspecified | Circulatory | 0.3% |
| D64.9 | Anemia, unspecified | Hematological | 0.3% |
| G89.29 | Other chronic pain | Pain | 0.3% |
| H25.9 | Unspecified age-related cataract | Ophthalmological | 0.2% |
| B20 | HIV disease | Infectious | 0.1% |
| C92.10 | Chronic myeloid leukemia in remission | Neoplasm | 0.1% |

**Total Codes:** 27
**Categories:** 10 major clinical categories
**Notes:** Prevalence rates are approximate across the synthetic population

---

### 4.2 CPT Procedure Codes

| Code | Description | Category | Frequency |
|------|-------------|----------|-----------|
| 99213 | Office visit, established patient, moderate complexity | Office Visit | 18% |
| 99214 | Office visit, established patient, high complexity | Office Visit | 12% |
| 99203 | Office visit, new patient, low-moderate complexity | Office Visit | 8% |
| 99204 | Office visit, new patient, moderate-high complexity | Office Visit | 5% |
| 99285 | Emergency dept visit, high complexity | Emergency | 4% |
| 93000 | Electrocardiogram | Diagnostic | 3% |
| 70450 | Head or brain CT, without contrast | Imaging | 3% |
| 71046 | Chest X-ray, 2 views | Imaging | 2% |
| 80053 | Comprehensive metabolic panel | Lab | 2% |
| 85025 | Complete blood count with differential | Lab | 2% |
| 99232 | Inpatient hospital visit, subsequent, low complexity | Hospital | 2% |
| 99233 | Inpatient hospital visit, subsequent, high complexity | Hospital | 2% |
| 27447 | Total knee replacement, unilateral | Surgery | 1.5% |
| 47562 | Laparoscopic cholecystectomy | Surgery | 1.5% |
| 43235 | Upper endoscopy with biopsy | Endoscopy | 1.5% |
| 90834 | Psychotherapy, 45 minutes | Mental Health | 1.5% |
| 97110 | Therapeutic exercises | Physical Therapy | 1.5% |
| 64413 | Injection, anesthetic; median, ulnar, or radial nerve | Injection | 1% |
| 20610 | Arthrocentesis, major joint | Procedure | 1% |
| 99232 | Subsequent hospital inpatient visit, low complexity | Hospital | 1% |
| 71020 | Chest X-ray, 1 view | Imaging | 1% |
| 36415 | Venipuncture, collection of blood specimen | Lab | 1% |
| 99341 | Home visit, new patient, low complexity | Home Health | 0.5% |
| 99347 | Home visit, established patient, moderate complexity | Home Health | 0.5% |
| 96401 | Chemotherapy injection | Oncology | 0.3% |
| 92004 | Comprehensive eye exam | Ophthalmology | 0.5% |
| 97161 | Physical therapy evaluation, low complexity | Physical Therapy | 0.5% |
| 99291 | Critical care, first hour | Critical Care | 0.2% |

**Total Codes:** 28
**Categories:** 8 major service categories
**Notes:** Frequency reflects relative prevalence in medical claims data

---

### 4.3 NDC Medications

| NDC | Generic Name | Brand Name | Strength | Form | Therapy Class | Frequency |
|-----|--------------|-----------|--------|------|---------------|-----------|
| 00002003201 | Lisinopril | Prinivil | 10mg | Tablet | ACE Inhibitor | 8% |
| 00378132945 | Metformin | Glucophage | 500mg | Tablet | Antidiabetic | 7% |
| 00054451100 | Atorvastatin | Lipitor | 20mg | Tablet | Statin | 6% |
| 00069078090 | Sertraline | Zoloft | 50mg | Tablet | SSRI | 4% |
| 65862078205 | Omeprazole | Prilosec | 20mg | Capsule | PPI | 3% |
| 00093710520 | Levothyroxine | Synthroid | 75mcg | Tablet | Thyroid | 2% |
| 00378100190 | Amlodipine | Norvasc | 5mg | Tablet | Calcium Channel Blocker | 2% |
| 00069050585 | Clopidogrel | Plavix | 75mg | Tablet | Antiplatelet | 1.5% |
| 00055105345 | Metoprolol | Lopressor | 50mg | Tablet | Beta Blocker | 1.5% |
| 00173069412 | Albuterol | Proventil | 90mcg | Inhaler | Bronchodilator | 1% |
| 00006751502 | Ibuprofen | Advil | 200mg | Tablet | NSAID | 2% |
| 00182197330 | Amoxicillin | Amoxil | 500mg | Capsule | Antibiotic | 1% |
| 00002046690 | Azithromycin | Zithromax | 250mg | Tablet | Antibiotic | 0.8% |
| 00054192230 | Fluoxetine | Prozac | 20mg | Capsule | SSRI | 0.8% |
| 00172477200 | Escitalopram | Lexapro | 10mg | Tablet | SSRI | 0.8% |
| 00006751610 | Cetirizine | Zyrtec | 10mg | Tablet | Antihistamine | 0.6% |
| 00046470055 | Gabapentin | Neurontin | 300mg | Capsule | Anticonvulsant | 0.5% |
| 00009508552 | Vitamin D3 | Various | 2000IU | Tablet | Supplement | 0.5% |
| 00023441635 | Pravastatin | Pravachol | 20mg | Tablet | Statin | 0.5% |
| 00069660520 | Simvastatin | Zocor | 20mg | Tablet | Statin | 0.4% |
| 00003160220 | Folic Acid | Various | 1mg | Tablet | Supplement | 0.3% |
| 00068516490 | Valsartan | Diovan | 80mg | Tablet | ARB | 0.3% |
| 00172493820 | Lorazepam | Ativan | 1mg | Tablet | Benzodiazepine | 0.2% |
| 00172591210 | Alprazolam | Xanax | 0.5mg | Tablet | Benzodiazepine | 0.2% |

**Total Medications:** 24
**Categories:** 10 major therapy classes
**Notes:** Top 5 medications account for ~30% of all fills

---

### 4.4 Place of Service Codes

| Code | Description | Type |
|------|-------------|------|
| 11 | Office | Outpatient |
| 21 | Inpatient Hospital | Inpatient |
| 23 | Emergency Room | Emergency |
| 24 | Ambulatory Surgical Center | Outpatient |
| 25 | Patient's Home | Outpatient |
| 26 | Psychiatric Facility | Inpatient |
| 81 | Independent Lab | Outpatient |

---

## 5. Data Relationships & Join Patterns

### 5.1 Core Join Patterns

#### Pattern 1: Member Claims History
```sql
SELECT
  m.member_id,
  m.first_name,
  m.last_name,
  mc.claim_id,
  mc.claim_number,
  mc.service_from_date,
  mc.claim_status,
  mc.total_billed,
  mc.plan_paid
FROM members m
INNER JOIN medical_claims mc ON m.member_id = mc.member_id
WHERE m.member_id = 'mem_959e8400...'
ORDER BY mc.service_from_date DESC;
```

#### Pattern 2: Member Coverage & Eligibility
```sql
SELECT
  m.member_id,
  m.first_name,
  m.plan_id,
  p.plan_name,
  p.plan_type,
  e.enrollment_date,
  e.termination_date,
  e.coverage_status
FROM members m
INNER JOIN plans p ON m.plan_id = p.plan_id
INNER JOIN eligibility e ON m.member_id = e.member_id
WHERE e.coverage_status = 'Active'
ORDER BY m.member_id;
```

#### Pattern 3: Claim Details with Line Items
```sql
SELECT
  mc.claim_id,
  mc.claim_number,
  mc.service_from_date,
  cln.line_number,
  cln.procedure_code,
  cln.billed_amount,
  cln.allowed_amount,
  cln.plan_paid,
  cln.line_status
FROM medical_claims mc
INNER JOIN claim_lines cln ON mc.claim_id = cln.claim_id
WHERE mc.claim_id = 'clm_c59e8400...'
ORDER BY cln.line_number;
```

#### Pattern 4: Plan Benefits & Copays
```sql
SELECT
  p.plan_id,
  p.plan_name,
  b.service_category,
  b.copay,
  b.coinsurance,
  b.deductible_applies,
  b.requires_auth
FROM plans p
INNER JOIN benefits b ON p.plan_id = b.plan_id
WHERE p.plan_id = 'plan_659e8400...'
ORDER BY b.service_category;
```

#### Pattern 5: Member Accumulators (Deductible/OOP)
```sql
SELECT
  m.member_id,
  m.first_name,
  a.benefit_year,
  a.deductible_individual,
  a.deductible_met,
  a.deductible_remaining,
  a.oop_max_individual,
  a.oop_met,
  a.oop_remaining
FROM members m
INNER JOIN accumulators a ON m.member_id = a.member_id
WHERE a.benefit_year = 2024
ORDER BY m.member_id;
```

#### Pattern 6: Authorization Status
```sql
SELECT
  a.authorization_id,
  a.authorization_number,
  m.first_name,
  m.last_name,
  p.npi,
  a.service_type,
  a.request_date,
  a.authorization_status,
  a.units_approved
FROM authorizations a
INNER JOIN members m ON a.member_id = m.member_id
INNER JOIN providers p ON a.provider_id = p.provider_id
WHERE a.authorization_status IN ('Pending', 'Approved')
ORDER BY a.request_date DESC;
```

#### Pattern 7: Pharmacy Claims
```sql
SELECT
  pc.pharmacy_claim_id,
  m.first_name,
  m.last_name,
  pc.medication_name,
  pc.therapy_class,
  pc.fill_date,
  pc.days_supply,
  pc.formulary_status,
  pc.plan_paid,
  pc.member_cost_share
FROM pharmacy_claims pc
INNER JOIN members m ON pc.member_id = m.member_id
WHERE pc.fill_date >= '2024-01-01'
ORDER BY pc.fill_date DESC;
```

#### Pattern 8: Provider Claims Volume
```sql
SELECT
  p.provider_id,
  p.npi,
  p.last_name,
  p.first_name,
  p.specialty,
  COUNT(mc.claim_id) AS claim_count,
  SUM(mc.total_billed) AS total_billed,
  SUM(mc.plan_paid) AS total_paid,
  AVG(mc.plan_paid) AS avg_paid
FROM providers p
LEFT JOIN medical_claims mc ON p.provider_id = mc.provider_id
GROUP BY p.provider_id, p.npi, p.last_name, p.first_name, p.specialty
ORDER BY claim_count DESC;
```

### 5.2 Common Filter Criteria

- **Date Range:** Filter claims by `service_from_date` or `fill_date`
- **Member Status:** Filter by `eligibility.coverage_status = 'Active'`
- **Claim Status:** Filter by `claim_status IN ('Paid', 'Denied', 'Pending')`
- **Network Status:** Filter by `provider.network_status = 'In-Network'`
- **Chronic Conditions:** Filter by member boolean flags or `chronic_conditions` array
- **Benefit Year:** Filter accumulators by calendar year
- **Plan Type:** Filter by `plan.plan_type` or `metal_tier`

---

## 6. Realistic Data Distribution Notes

### 6.1 Chronic Condition Prevalence

Based on realistic population health data:

| Condition | Flag Field | Prevalence | ICD-10 Code |
|-----------|------------|-----------|------------|
| Hypertension | `has_hypertension` | 15% | I10 |
| Type 2 Diabetes | `has_diabetes` | 10% | E11.9 |
| Hyperlipidemia | `has_hyperlipidemia` | 8% | E78.5 |
| Asthma | `has_asthma` | 7% | J45.9 |
| Mental Health | `has_mental_health` | 6% | F32.9, F41.1 |
| GERD | `has_gerd` | 5% | K21.9 |
| Chronic Back Pain | `has_back_pain` | 4% | M54.5 |

**Key Notes:**
- Conditions are not mutually exclusive; many members have multiple conditions
- ~60% of member population has at least one chronic condition
- Age correlates with condition prevalence (older members have higher rates)
- Chronic condition flags drive claim patterns and authorization requirements

### 6.2 Claim Status Distribution

| Status | Percentage | Interpretation |
|--------|-----------|-----------------|
| Paid | 70% | Claim approved and benefits paid |
| Denied | 8% | Claim rejected; member may appeal |
| Pending | 12% | Under review; may require additional info |
| Adjusted | 7% | Claim modified (duplicate removal, COB, etc.) |
| Appealed | 3% | Member appealed a denial |

**Financial Impact:**
- Paid claims average $2,170 plan paid per claim
- Denied claims represent revenue leakage (~$13.2M in test data)
- Pending claims indicate processing delays
- Appeals often result in partial or full reversal of denials

### 6.3 Authorization Status Distribution

| Status | Percentage | Typical Timeline |
|--------|-----------|-----------------|
| Approved | 55% | 1-3 business days |
| Denied | 15% | 2-5 business days |
| Pending | 15% | Awaiting information |
| Partially Approved | 10% | Approved with limitations |
| Withdrawn | 5% | Request cancelled by provider |

**Service Types Requiring Auth:**
- Advanced imaging (MRI, CT, PET): ~35% of auths
- Surgery: ~30% of auths
- Specialty medications: ~20% of auths
- Physical therapy: ~10% of auths
- Inpatient admission: ~5% of auths

### 6.4 Coverage Type Distribution

| Type | Percentage | Members | Dependents |
|------|-----------|---------|-----------|
| Individual | 40% | 800 | 0 |
| Individual + Spouse | 25% | 500 | 500 |
| Individual + Children | 15% | 300 | 300 |
| Family | 20% | 400 | 697 |

### 6.5 Plan Selection Distribution

| Plan Type | Percentage | Enrollment Trend |
|-----------|-----------|------------------|
| PPO | 40% | Most popular; highest costs |
| HMO | 28% | Growing; lower costs |
| HDHP | 18% | Growing; younger members |
| POS | 12% | Declining; fewer enrollees |
| EPO | 2% | Niche; specialty markets |

**Metal Tier Selection:**
- Bronze: 24% (lower premium, higher deductibles)
- Silver: 30% (balanced; most popular)
- Gold: 30% (higher premium, lower deductibles)
- Platinum: 16% (highest premium, lowest deductibles)

### 6.6 Pharmacy Distribution

| Characteristic | Distribution |
|---------------|--------------|
| Generic (Tier 1) | 60% of claims |
| Preferred Brand (Tier 2) | 25% of claims |
| Non-Preferred (Tier 3) | 10% of claims |
| Not Covered | 5% of claims |
| Requiring Auth | 8% of claims |

**Top Drug Categories:**
1. Hypertension meds (ACE-I, ARB, BB, CCB): 20%
2. Hyperlipidemia meds (Statins): 15%
3. Antidiabetics: 12%
4. Mental health meds (SSRI, SNRIs): 10%
5. GI meds (PPI): 8%

### 6.7 Provider Network

| Metric | Value |
|--------|-------|
| Individual Providers | 225 (75%) |
| Facility Providers | 75 (25%) |
| In-Network | 240 (80%) |
| Out-of-Network | 45 (15%) |
| Contracted | 15 (5%) |
| Primary Care Physicians | ~80 |
| Specialists | ~220 |

**Specialty Distribution:**
- Internal Medicine/Family Practice: 30%
- Cardiology: 15%
- Orthopedics: 12%
- Psychiatry/Behavioral: 10%
- OB/GYN: 8%
- Pediatrics: 8%
- Dentistry: 10%
- Other: 7%

---

## 7. File Manifest

All data files are provided in multiple formats for flexibility.

### 7.1 Core Entity Files

| File | Format | Records | Size | Description |
|------|--------|---------|------|-------------|
| employers.csv / .json | CSV / JSON | 25 | ~8 KB | Employer organizations |
| plans.csv / .json | CSV / JSON | 50 | ~35 KB | Benefit plans |
| benefits.csv / .json | CSV / JSON | 900 | ~245 KB | Benefit schedules |
| providers.csv / .json | CSV / JSON | 300 | ~120 KB | Healthcare providers |
| members.csv / .json | CSV / JSON | 2,000 | ~680 KB | Primary subscribers |
| dependents.csv / .json | CSV / JSON | 2,297 | ~580 KB | Family members |
| eligibility.csv / .json | CSV / JSON | 4,297 | ~420 KB | Coverage records |

### 7.2 Claims Files

| File | Format | Records | Size | Description |
|------|--------|---------|------|-------------|
| medical_claims.csv / .json | CSV / JSON | 13,841 | ~4.2 MB | Professional & institutional claims |
| claim_lines.csv / .json | CSV / JSON | 24,206 | ~5.8 MB | Service line details |
| pharmacy_claims.csv / .json | CSV / JSON | 7,055 | ~1.8 MB | Prescription fills |

### 7.3 Administrative Files

| File | Format | Records | Size | Description |
|------|--------|---------|------|-------------|
| authorizations.csv / .json | CSV / JSON | 567 | ~240 KB | Prior auth records |
| accumulators.csv / .json | CSV / JSON | 2,000 | ~380 KB | Deductible/OOP tracking |

### 7.4 Reference Data Files

| File | Format | Records | Size | Description |
|------|--------|---------|------|-------------|
| icd10_codes.csv / .json | CSV / JSON | 27 | ~5 KB | Diagnosis codes |
| cpt_codes.csv / .json | CSV / JSON | 28 | ~6 KB | Procedure codes |
| ndc_medications.csv / .json | CSV / JSON | 24 | ~8 KB | Medications |
| place_of_service.csv / .json | CSV / JSON | 7 | ~2 KB | POS codes |

### 7.5 Database Schemas

| File | Format | Description |
|------|--------|-------------|
| schema.sql | SQL | Complete DDL for all tables |
| schema.json | JSON Schema | JSON schema definitions |
| relationships.json | JSON | Foreign key relationships |

### 7.6 Summary & Validation

| File | Format | Description |
|------|--------|-------------|
| data_summary.json | JSON | Record counts and statistics |
| data_validation.txt | Text | Data quality checks and notes |
| README.md | Markdown | Quick start guide |

---

## 8. Quick Start Guide

### 8.1 Loading Data in Python

#### Using Pandas

```python
import pandas as pd
import json
from datetime import datetime

# Load CSV files
employers = pd.read_csv('data/employers.csv')
plans = pd.read_csv('data/plans.csv')
members = pd.read_csv('data/members.csv')
medical_claims = pd.read_csv('data/medical_claims.csv')
claim_lines = pd.read_csv('data/claim_lines.csv')
pharmacy_claims = pd.read_csv('data/pharmacy_claims.csv')

# Convert date columns
date_columns = ['date_of_birth', 'created_at', 'updated_at', 'service_from_date']
for col in date_columns:
    if col in medical_claims.columns:
        medical_claims[col] = pd.to_datetime(medical_claims[col])

# Display basic info
print(f"Total members: {len(members)}")
print(f"Total medical claims: {len(medical_claims)}")
print(f"Total billed: ${medical_claims['total_billed'].sum():,.2f}")
print(f"Plan paid: ${medical_claims['plan_paid'].sum():,.2f}")
```

#### Using JSON

```python
import json

# Load JSON files
with open('data/members.json', 'r') as f:
    members = json.load(f)

with open('data/medical_claims.json', 'r') as f:
    claims = json.load(f)

# Access individual records
first_member = members[0]
print(f"{first_member['first_name']} {first_member['last_name']}")
```

### 8.2 Loading Data in JavaScript

#### Using Node.js & Pandas (via csv-parser)

```javascript
const fs = require('fs');
const csv = require('csv-parser');

// Load CSV
fs.createReadStream('data/members.csv')
  .pipe(csv())
  .on('data', (row) => {
    console.log(row);
  })
  .on('end', () => {
    console.log('CSV loaded');
  });

// Load JSON
const members = JSON.parse(fs.readFileSync('data/members.json', 'utf8'));
console.log(`Total members: ${members.length}`);
```

#### Using Browser & Fetch API

```javascript
// Load JSON data
fetch('data/members.json')
  .then(response => response.json())
  .then(members => {
    console.log(`Loaded ${members.length} members`);

    // Filter by employer
    const acmeMembers = members.filter(m => m.employer_id === 'emp_...');
    console.log(`Acme members: ${acmeMembers.length}`);
  });

// Load CSV (using a CSV parser library)
import Papa from 'papaparse';

fetch('data/medical_claims.csv')
  .then(response => response.text())
  .then(data => {
    const claims = Papa.parse(data, { header: true });
    console.log(`Loaded ${claims.data.length} claims`);
  });
```

### 8.3 Common Queries to Try

#### Query 1: Member Summary with Active Coverage

```python
active_members = (
    members[members['member_id'].isin(eligibility[eligibility['coverage_status'] == 'Active']['member_id'])]
    .groupby('employer_id')
    .size()
)
print(active_members)
```

#### Query 2: Total Claims by Status

```python
claims_summary = medical_claims.groupby('claim_status').agg({
    'claim_id': 'count',
    'total_billed': 'sum',
    'plan_paid': 'sum'
}).rename(columns={'claim_id': 'count'})
print(claims_summary)
```

#### Query 3: Member Cost Share Analysis

```python
member_cost = medical_claims.groupby('member_id').agg({
    'member_cost_share': 'sum',
    'claim_id': 'count'
}).rename(columns={'claim_id': 'claim_count'})
print(member_cost.sort_values('member_cost_share', ascending=False).head(10))
```

#### Query 4: Top Medications by Fill Count

```python
top_meds = pharmacy_claims['medication_name'].value_counts().head(10)
print(top_meds)
```

#### Query 5: Authorization Approval Rate

```python
auth_stats = authorizations.groupby('authorization_status').size()
approval_rate = (auth_stats.get('Approved', 0) / len(authorizations)) * 100
print(f"Approval rate: {approval_rate:.1f}%")
```

#### Query 6: Provider Claims Volume

```python
provider_claims = medical_claims.merge(providers, on='provider_id')
provider_volume = provider_claims.groupby(['npi', 'last_name']).agg({
    'claim_id': 'count',
    'plan_paid': 'sum'
}).rename(columns={'claim_id': 'claim_count'}).sort_values('claim_count', ascending=False).head(20)
print(provider_volume)
```

#### Query 7: Deductible & OOP Analysis

```python
deductible_status = accumulators.groupby('benefit_year').agg({
    'deductible_remaining': ['min', 'max', 'mean'],
    'oop_remaining': ['min', 'max', 'mean']
})
print(deductible_status)
```

### 8.4 How to Regenerate with Different Parameters

The synthetic dataset can be regenerated with different parameters for testing and prototyping.

#### Regeneration Parameters

```python
# Configuration for data generation
config = {
    "seed": 42,  # For reproducibility
    "member_count": 2000,  # Primary subscribers
    "employer_count": 25,
    "plan_count": 50,
    "provider_count": 300,
    "benefit_year": 2024,
    "claims_per_member_annual": 6.9,  # ~13,841 total / 2,000 members
    "pharmacy_claims_per_member_annual": 3.5,  # ~7,055 total / 2,000 members
    "chronic_condition_prevalence": {
        "hypertension": 0.15,
        "diabetes": 0.10,
        "hyperlipidemia": 0.08,
        "asthma": 0.07,
        "mental_health": 0.06,
        "gerd": 0.05,
        "back_pain": 0.04
    },
    "claim_status_distribution": {
        "paid": 0.70,
        "denied": 0.08,
        "pending": 0.12,
        "adjusted": 0.07,
        "appealed": 0.03
    }
}

# Generate new dataset
from synthetic_data_generator import HealthcareDataGenerator

generator = HealthcareDataGenerator(config)
generator.generate_all()
generator.export_to_csv('output_directory')
```

#### Scaling Examples

**Small Dataset (Testing)**
```python
config['member_count'] = 100
config['employer_count'] = 5
config['provider_count'] = 50
# Results in ~690 claims, ~350 pharmacy claims
```

**Medium Dataset (Dev Environment)**
```python
config['member_count'] = 500
config['employer_count'] = 10
config['provider_count'] = 150
# Results in ~3,450 claims, ~1,750 pharmacy claims
```

**Large Dataset (Performance Testing)**
```python
config['member_count'] = 10000
config['employer_count'] = 100
config['provider_count'] = 1000
# Results in ~69,000 claims, ~35,000 pharmacy claims
```

---

## 9. API Design Suggestions

Based on the data model, here are recommended REST API endpoints for engineers building systems with this data.

### 9.1 Members Endpoints

#### GET /api/v1/members
Retrieve all members with optional filtering.

**Query Parameters:**
- `employer_id` - Filter by employer
- `plan_id` - Filter by plan
- `coverage_status` - Filter by eligibility status (Active, Terminated, etc.)
- `limit` - Pagination limit (default: 100, max: 1000)
- `offset` - Pagination offset
- `sort` - Sort field (member_id, last_name, created_at)
- `order` - ASC or DESC

**Response (200 OK):**
```json
{
  "data": [
    {
      "member_id": "mem_959e8400...",
      "first_name": "Alice",
      "last_name": "Johnson",
      "date_of_birth": "1980-05-15",
      "email": "alice.johnson@email.com",
      "employer_id": "emp_550e8400...",
      "plan_id": "plan_659e8400...",
      "chronic_conditions": ["E11.9", "I10"],
      "coverage_type": "Family",
      "created_at": "2023-01-15T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 2000,
    "limit": 100,
    "offset": 0,
    "pages": 20
  }
}
```

#### GET /api/v1/members/{member_id}
Retrieve a specific member with complete profile.

**Response (200 OK):**
```json
{
  "data": {
    "member_id": "mem_959e8400...",
    "first_name": "Alice",
    "last_name": "Johnson",
    "date_of_birth": "1980-05-15",
    "ssn_last_four": "1234",
    "email": "alice.johnson@email.com",
    "phone": "217-555-0789",
    "address": "789 Oak Lane",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "employer_id": "emp_550e8400...",
    "plan_id": "plan_659e8400...",
    "plan_name": "Premium PPO 80/20",
    "primary_care_physician_id": "prov_859e8400...",
    "pcp_name": "Dr. John Smith",
    "chronic_conditions": ["E11.9", "I10"],
    "has_hypertension": true,
    "has_diabetes": true,
    "has_hyperlipidemia": false,
    "coverage_type": "Family",
    "created_at": "2023-01-15T00:00:00Z",
    "updated_at": "2024-06-20T00:00:00Z"
  }
}
```

#### GET /api/v1/members/{member_id}/coverage
Retrieve member's current coverage and eligibility.

**Response (200 OK):**
```json
{
  "data": {
    "member_id": "mem_959e8400...",
    "enrollment_date": "2024-01-01",
    "termination_date": null,
    "coverage_status": "Active",
    "is_cobra": false,
    "plan": {
      "plan_id": "plan_659e8400...",
      "plan_name": "Premium PPO 80/20",
      "plan_type": "PPO",
      "metal_tier": "Gold",
      "annual_deductible": 1500.00,
      "family_deductible": 3000.00,
      "in_network_oop_max": 5000.00
    }
  }
}
```

#### GET /api/v1/members/{member_id}/dependents
Retrieve member's dependents.

**Response (200 OK):**
```json
{
  "data": [
    {
      "dependent_id": "dep_a59e8400...",
      "relationship": "Spouse",
      "first_name": "Robert",
      "last_name": "Johnson",
      "date_of_birth": "1982-08-22",
      "chronic_conditions": ["J45.9"]
    }
  ]
}
```

### 9.2 Claims Endpoints

#### GET /api/v1/claims
Retrieve claims with extensive filtering.

**Query Parameters:**
- `member_id` - Filter by member
- `claim_status` - Filter by status (Paid, Denied, Pending, etc.)
- `date_from` - Filter by service date (ISO 8601)
- `date_to` - Filter by service date (ISO 8601)
- `provider_id` - Filter by provider
- `claim_type` - Professional, Institutional
- `limit` - Pagination limit
- `offset` - Pagination offset

**Response (200 OK):**
```json
{
  "data": [
    {
      "claim_id": "clm_c59e8400...",
      "claim_number": "CLM-2024-001234",
      "member_id": "mem_959e8400...",
      "provider_id": "prov_859e8400...",
      "provider_name": "Dr. John Smith",
      "claim_type": "Professional",
      "service_from_date": "2024-03-15",
      "service_to_date": "2024-03-15",
      "claim_status": "Paid",
      "total_billed": 750.00,
      "allowed_amount": 500.00,
      "plan_paid": 400.00,
      "member_cost_share": 100.00,
      "created_at": "2024-03-22T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 13841,
    "limit": 100,
    "offset": 0
  }
}
```

#### GET /api/v1/claims/{claim_id}
Retrieve claim details with line items.

**Response (200 OK):**
```json
{
  "data": {
    "claim_id": "clm_c59e8400...",
    "claim_number": "CLM-2024-001234",
    "member": {
      "member_id": "mem_959e8400...",
      "name": "Alice Johnson"
    },
    "provider": {
      "provider_id": "prov_859e8400...",
      "npi": "1234567890",
      "name": "Dr. John Smith",
      "specialty": "Internal Medicine"
    },
    "claim_type": "Professional",
    "service_from_date": "2024-03-15",
    "service_to_date": "2024-03-15",
    "claim_status": "Paid",
    "primary_diagnosis": "I10",
    "secondary_diagnoses": ["E78.5"],
    "total_billed": 750.00,
    "allowed_amount": 500.00,
    "plan_paid": 400.00,
    "member_cost_share": 100.00,
    "lines": [
      {
        "line_number": 1,
        "procedure_code": "99213",
        "description": "Office visit, established patient",
        "billed_amount": 150.00,
        "allowed_amount": 100.00,
        "plan_paid": 80.00,
        "member_coinsurance": 20.00,
        "status": "Paid"
      }
    ]
  }
}
```

#### POST /api/v1/claims
Submit a new claim (simulated for testing).

**Request Body:**
```json
{
  "member_id": "mem_959e8400...",
  "provider_id": "prov_859e8400...",
  "claim_type": "Professional",
  "service_from_date": "2024-04-01",
  "service_to_date": "2024-04-01",
  "total_billed": 500.00,
  "procedure_codes": ["99213"]
}
```

**Response (201 Created):**
```json
{
  "data": {
    "claim_id": "clm_new123...",
    "claim_number": "CLM-2024-009999",
    "status": "Pending",
    "created_at": "2024-04-01T10:00:00Z"
  }
}
```

### 9.3 Pharmacy Claims Endpoints

#### GET /api/v1/pharmacy-claims
Retrieve pharmacy claims.

**Query Parameters:**
- `member_id` - Filter by member
- `date_from` - Filter by fill date
- `date_to` - Filter by fill date
- `formulary_status` - Tier 1, Tier 2, Tier 3, Not Covered
- `claim_status` - Paid, Denied, Pending
- `limit` - Pagination limit
- `offset` - Pagination offset

**Response (200 OK):**
```json
{
  "data": [
    {
      "pharmacy_claim_id": "phrm_e59e8400...",
      "member_id": "mem_959e8400...",
      "medication_name": "Lisinopril 10mg tablet",
      "ndc": "00002003201",
      "therapy_class": "ACE Inhibitor",
      "fill_date": "2024-03-11",
      "days_supply": 30,
      "quantity": 30,
      "formulary_status": "Tier 1 (Generic)",
      "total_billed": 7.50,
      "plan_paid": 5.00,
      "member_cost_share": 2.50,
      "claim_status": "Paid"
    }
  ],
  "pagination": {
    "total": 7055,
    "limit": 100,
    "offset": 0
  }
}
```

### 9.4 Authorization Endpoints

#### GET /api/v1/authorizations
Retrieve authorization records.

**Query Parameters:**
- `member_id` - Filter by member
- `authorization_status` - Approved, Denied, Pending, etc.
- `request_type` - Prior Authorization, Precertification, Referral
- `date_from` - Filter by request date
- `limit` - Pagination limit
- `offset` - Pagination offset

**Response (200 OK):**
```json
{
  "data": [
    {
      "authorization_id": "auth_d59e8400...",
      "authorization_number": "AUTH-2024-12345",
      "member_id": "mem_959e8400...",
      "member_name": "Alice Johnson",
      "provider_id": "prov_859e8400...",
      "provider_name": "Dr. Jane Doe",
      "request_type": "Prior Authorization",
      "service_type": "Advanced Imaging",
      "procedure_code": "70450",
      "diagnosis_code": "M79.3",
      "request_date": "2024-03-10",
      "authorization_date": "2024-03-12",
      "expiration_date": "2024-06-12",
      "authorization_status": "Approved",
      "units_approved": 1
    }
  ]
}
```

#### POST /api/v1/authorizations
Submit an authorization request.

**Request Body:**
```json
{
  "member_id": "mem_959e8400...",
  "provider_id": "prov_859e8400...",
  "request_type": "Prior Authorization",
  "service_type": "Advanced Imaging",
  "procedure_code": "70450",
  "diagnosis_code": "M79.3"
}
```

**Response (201 Created):**
```json
{
  "data": {
    "authorization_id": "auth_new456...",
    "request_date": "2024-04-01T10:00:00Z",
    "authorization_status": "Pending"
  }
}
```

### 9.5 Plans & Benefits Endpoints

#### GET /api/v1/plans
Retrieve benefit plans.

**Query Parameters:**
- `employer_id` - Filter by employer
- `plan_type` - PPO, HMO, HDHP, POS, EPO
- `metal_tier` - Bronze, Silver, Gold, Platinum
- `active` - true/false

**Response (200 OK):**
```json
{
  "data": [
    {
      "plan_id": "plan_659e8400...",
      "plan_name": "Premium PPO 80/20",
      "plan_type": "PPO",
      "metal_tier": "Gold",
      "annual_deductible": 1500.00,
      "family_deductible": 3000.00,
      "in_network_oop_max": 5000.00,
      "copay_primary_care": 25.00,
      "copay_specialist": 50.00,
      "monthly_premium": 350.00,
      "active": true
    }
  ]
}
```

#### GET /api/v1/plans/{plan_id}/benefits
Retrieve benefit details for a plan.

**Response (200 OK):**
```json
{
  "data": [
    {
      "benefit_id": "ben_759e8400...",
      "service_category": "Office Visits",
      "is_preventive": true,
      "copay": 25.00,
      "coinsurance": 0.20,
      "deductible_applies": false,
      "oop_max_applies": true,
      "requires_auth": false,
      "in_network_coverage_pct": 0.80
    }
  ]
}
```

### 9.6 Accumulators Endpoints

#### GET /api/v1/members/{member_id}/accumulators
Retrieve member's deductible and OOP accumulation.

**Query Parameters:**
- `benefit_year` - Filter by year (default: current year)

**Response (200 OK):**
```json
{
  "data": {
    "accumulator_id": "acc_e59e8400...",
    "member_id": "mem_959e8400...",
    "benefit_year": 2024,
    "deductible_individual": 1500.00,
    "deductible_met": 1250.00,
    "deductible_remaining": 250.00,
    "oop_max_individual": 5000.00,
    "oop_met": 3800.00,
    "oop_remaining": 1200.00,
    "pharmacy_deductible": 100.00,
    "pharmacy_deductible_met": 100.00,
    "pharmacy_deductible_remaining": 0.00,
    "calculation_date": "2024-04-30"
  }
}
```

### 9.7 Provider Endpoints

#### GET /api/v1/providers
Retrieve healthcare providers.

**Query Parameters:**
- `specialty` - Filter by specialty
- `network_status` - In-Network, Out-of-Network, Contracted
- `is_primary_care` - true/false
- `limit` - Pagination limit

**Response (200 OK):**
```json
{
  "data": [
    {
      "provider_id": "prov_859e8400...",
      "npi": "1234567890",
      "provider_type": "Individual",
      "name": "Dr. John Smith",
      "specialty": "Internal Medicine",
      "city": "Springfield",
      "state": "IL",
      "network_status": "In-Network",
      "is_primary_care": true,
      "board_certified": true
    }
  ]
}
```

#### GET /api/v1/providers/{provider_id}/claims-summary
Retrieve provider's claims statistics.

**Response (200 OK):**
```json
{
  "data": {
    "provider_id": "prov_859e8400...",
    "npi": "1234567890",
    "name": "Dr. John Smith",
    "claim_count": 156,
    "total_billed": 98400.00,
    "total_plan_paid": 68900.00,
    "average_allowed": 650.00,
    "approval_rate": 0.94
  }
}
```

### 9.8 Error Responses

All endpoints use consistent error response format.

**400 Bad Request:**
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid query parameter: date_from must be ISO 8601 format",
    "details": {
      "parameter": "date_from",
      "value": "03/15/2024"
    }
  }
}
```

**404 Not Found:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Member not found",
    "details": {
      "member_id": "mem_invalid..."
    }
  }
}
```

**500 Internal Server Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "request_id": "req_abc123..."
  }
}
```

---

## 10. Data Quality & Validation Notes

### 10.1 Validation Rules

- **Date Logic:** `service_from_date <= service_to_date` for all claim records
- **Financial Logic:** `member_cost_share + plan_paid + write_off = allowed_amount`
- **Deductible Logic:** `deductible_remaining = deductible_individual - deductible_met`
- **Referential Integrity:** All foreign key references are valid within the dataset
- **Chronic Conditions:** Boolean flags align with ICD-10 codes in chronic_conditions array
- **Eligibility:** Dependent eligibility records must have corresponding member records

### 10.2 Known Characteristics

- **Completeness:** All required fields are populated; optional fields are ~40-70% populated
- **Realistic Distributions:** Chronic conditions, claim statuses, and authorization results reflect real-world patterns
- **Temporal Consistency:** All data is dated within the 2024 calendar year
- **Privacy:** All data is fully synthetic; no real PII is contained in this dataset

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025 | Initial comprehensive specification document |

---

**For technical support or questions about the data specification, refer to the README.md in the data directory.**
