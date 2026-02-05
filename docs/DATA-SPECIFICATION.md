# Healthcare Synthetic Dataset - Data Specification

**Version:** 1.1 (data-derived)
**Generated:** 2026-02-05
**Source:** `data/json/*.json`

This specification is generated from the actual JSON data files. Field names and types reflect the dataset in this repo.

## Summary

**Entity Counts**

- Employers: 25
- Plans: 50
- Benefits: 900
- Providers: 300
- Members Primary: 2000
- Dependents: 2297
- Total Covered Lives: 4297
- Eligibility Periods: 4297
- Medical Claims: 13841
- Claim Lines: 24206
- Pharmacy Claims: 7055
- Authorizations: 567
- Accumulators: 2000

**Financial Summary**

- Total Medical Billed: 63278604.76
- Total Medical Paid: 33998600.33
- Total Pharmacy Cost: 1200215.78
- Avg Claim Amount: 4571.82
- Claim Denial Rate: 7.7
- Auth Approval Rate: 56.1

## Entities

### Employers (25)

| Field | Type(s) | Example |
|-------|---------|---------|
| account_manager | `string` | `"David Brown"` |
| address | `object` | `{"line1": "1924 Oak Ave", "line2": "", "city": "Raleigh", "state": "NC", "zip": "27645"}` |
| effective_date | `string` | `"2018-01-01"` |
| employee_count | `integer` | `85` |
| employer_id | `string` | `"EMP-A2B12586"` |
| industry | `string` | `"Technology"` |
| name | `string` | `"Acme Corporation"` |
| phone | `string` | `"(632) 232-1488"` |
| size_category | `string` | `"small"` |
| status | `string` | `"Active"` |
| tax_id | `string` | `"96-2458591"` |

### Plans (50)

| Field | Type(s) | Example |
|-------|---------|---------|
| coinsurance_in_network | `integer` | `90` |
| coinsurance_out_of_network | `integer` | `70` |
| copay_er | `integer` | `350` |
| copay_pcp | `integer` | `40` |
| copay_rx_generic | `integer` | `5` |
| copay_rx_non_preferred | `integer` | `75` |
| copay_rx_preferred_brand | `integer` | `30` |
| copay_rx_specialty | `integer` | `200` |
| copay_specialist | `integer` | `75` |
| copay_urgent_care | `integer` | `75` |
| deductible_family | `integer` | `5500` |
| deductible_individual | `integer` | `3000` |
| effective_date | `string` | `"2018-01-01"` |
| employer_id | `string` | `"EMP-A2B12586"` |
| monthly_premium_family | `number` | `1173.78` |
| monthly_premium_individual | `integer` | `450` |
| network_name | `string` | `"Preferred Network"` |
| out_of_pocket_max_family | `integer` | `10500` |
| out_of_pocket_max_individual | `integer` | `6000` |
| pharmacy_benefit_manager | `string` | `"Express Scripts"` |
| plan_id | `string` | `"PLN-10BB3B55"` |
| plan_name | `string` | `"Acme Corporation Silver HMO"` |
| plan_type | `string` | `"HMO"` |
| status | `string` | `"Active"` |
| termination_date | `null` | `null` |
| tier | `string` | `"Silver"` |

### Benefits (900)

| Field | Type(s) | Example |
|-------|---------|---------|
| annual_limit | `integer \| null` | `null` |
| benefit_id | `string` | `"BEN-DABBB3F4"` |
| category | `string` | `"Preventive Care"` |
| cost_sharing_type | `string` | `"$0 copay"` |
| deductible_applies | `string` | `"Covered at 100%"` |
| description | `string` | `"Annual wellness, immunizations, screenings"` |
| network_tier | `string` | `"In-Network"` |
| plan_id | `string` | `"PLN-10BB3B55"` |
| requires_auth | `boolean` | `false` |
| requires_referral | `boolean` | `false` |

### Providers (300)

| Field | Type(s) | Example |
|-------|---------|---------|
| accepting_new_patients | `boolean` | `true` |
| address | `object` | `{"line1": "8461 Hill St", "line2": "Suite 235", "city": "Detroit", "state": "MI", "zip": "48217"}` |
| effective_date | `string` | `"2021-03-01"` |
| languages | `array[string]` | `["Hindi"]` |
| name | `string` | `"Cynthia Davis, NP"` |
| network_status | `string` | `"Out-of-Network"` |
| npi | `string` | `"1406403910"` |
| phone | `string` | `"(917) 265-9866"` |
| provider_id | `string` | `"PRV-24EED9EF"` |
| rating | `number` | `3.1` |
| specialty | `string` | `"OB/GYN"` |
| tax_id | `string` | `"64-6780235"` |
| type | `string` | `"Individual"` |

### Members (2000)

| Field | Type(s) | Example |
|-------|---------|---------|
| address | `object` | `{"line1": "448 Highland Ave", "line2": "Apt 285", "city": "Los Angeles", "state": "CA", "zip": "90044"}` |
| age | `integer` | `33` |
| chronic_conditions | `array \| array[string]` | `["hypertension", "asthma"]` |
| coverage_type | `string` | `"Individual"` |
| date_of_birth | `string` | `"1993-10-08"` |
| email | `string` | `"frank.cruz546@gmail.com"` |
| employer_id | `string` | `"EMP-C0F92299"` |
| enrollment_date | `string` | `"2022-11-25"` |
| first_name | `string` | `"Frank"` |
| gender | `string` | `"M"` |
| last_name | `string` | `"Cruz"` |
| member_id | `string` | `"MBR-B5906016"` |
| pcp_provider_id | `null \| string` | `"PRV-810E1DC3"` |
| phone | `string` | `"(876) 512-1512"` |
| plan_id | `string` | `"PLN-AAF39C04"` |
| relationship | `string` | `"Self"` |
| ssn_last4 | `string` | `"7214"` |
| status | `string` | `"Active"` |
| subscriber_id | `string` | `"SUB190723988"` |
| termination_date | `null` | `null` |

### Dependents (2297)

| Field | Type(s) | Example |
|-------|---------|---------|
| date_of_birth | `string` | `"2024-04-28"` |
| employer_id | `string` | `"EMP-ADBBA4AC"` |
| enrollment_date | `string` | `"2024-02-20"` |
| first_name | `string` | `"Thomas"` |
| gender | `string` | `"M"` |
| last_name | `string` | `"Baker"` |
| member_id | `string` | `"MBR-1C0A5F9D"` |
| plan_id | `string` | `"PLN-AC87C543"` |
| relationship | `string` | `"Child"` |
| status | `string` | `"Active"` |
| subscriber_id | `string` | `"SUB889645295"` |
| subscriber_member_id | `string` | `"MBR-5229FAC3"` |

### Eligibility (4297)

| Field | Type(s) | Example |
|-------|---------|---------|
| cobra_flag | `boolean` | `false` |
| coverage_type | `string` | `"Individual"` |
| effective_date | `string` | `"2022-11-25"` |
| eligibility_id | `string` | `"ELG-947A4401"` |
| member_id | `string` | `"MBR-B5906016"` |
| plan_id | `string` | `"PLN-AAF39C04"` |
| status | `string` | `"Active"` |
| termination_date | `null \| string` | `null` |

### Medical Claims (13841)

| Field | Type(s) | Example |
|-------|---------|---------|
| appeal_status | `null \| string` | `null` |
| check_number | `null \| string` | `"CHK181250"` |
| claim_id | `string` | `"CLM-487B442D"` |
| claim_status | `string` | `"Paid"` |
| claim_type | `string` | `"Professional"` |
| denial_reason | `null \| string` | `null` |
| member_id | `string` | `"MBR-B5906016"` |
| payment_date | `null \| string` | `"2025-03-07"` |
| place_of_service | `string` | `"11"` |
| place_of_service_description | `string` | `"Office"` |
| plan_id | `string` | `"PLN-AAF39C04"` |
| primary_diagnosis | `string` | `"N39.0"` |
| primary_diagnosis_description | `string` | `"Urinary tract infection, site not specified"` |
| processed_date | `null \| string` | `"2025-03-09"` |
| provider_id | `string` | `"PRV-7C5D6F0B"` |
| received_date | `string` | `"2025-02-19"` |
| secondary_diagnosis | `null \| string` | `"F32.1"` |
| service_date | `string` | `"2025-02-17"` |
| total_allowed | `number` | `10808.93` |
| total_billed | `number` | `15449.12` |
| total_member_responsibility | `number` | `1080.89` |
| total_plan_paid | `number` | `9728.04` |

### Claim Lines (24206)

| Field | Type(s) | Example |
|-------|---------|---------|
| allowed_amount | `number` | `10757.18` |
| billed_amount | `number` | `15374.96` |
| claim_id | `string` | `"CLM-487B442D"` |
| claim_line_id | `string` | `"CLL-BC0269FC"` |
| diagnosis_pointer | `string` | `"1"` |
| line_number | `integer` | `1` |
| member_responsibility | `number` | `1075.72` |
| modifier | `null \| string` | `null` |
| plan_paid_amount | `number` | `9681.46` |
| procedure_code | `string` | `"47562"` |
| procedure_description | `string` | `"Laparoscopic cholecystectomy"` |
| service_date | `string` | `"2025-02-17"` |
| units | `integer` | `1` |

### Pharmacy Claims (7055)

| Field | Type(s) | Example |
|-------|---------|---------|
| claim_status | `string` | `"Paid"` |
| daw_code | `string` | `"2"` |
| days_supply | `integer` | `30` |
| dispensing_fee | `number` | `2.4` |
| fill_date | `string` | `"2025-02-20"` |
| formulary_status | `string` | `"Preferred"` |
| ingredient_cost | `number` | `10.24` |
| medication_category | `string` | `"Cardiovascular"` |
| medication_name | `string` | `"Lisinopril 10mg"` |
| member_copay | `integer` | `15` |
| member_id | `string` | `"MBR-B5906016"` |
| ndc | `string` | `"00093-1044-01"` |
| pharmacy_name | `string` | `"Walgreens Pharmacy #3374"` |
| pharmacy_npi | `string` | `"1306329187"` |
| plan_id | `string` | `"PLN-AAF39C04"` |
| plan_paid | `number` | `0` |
| prescriber_npi | `string` | `"1696441478"` |
| prior_auth_required | `boolean` | `false` |
| quantity | `integer` | `30` |
| refill_number | `integer` | `0` |
| rx_claim_id | `string` | `"RXC-B451291F"` |
| total_cost | `number` | `12.64` |

### Authorizations (567)

| Field | Type(s) | Example |
|-------|---------|---------|
| approved_units | `integer \| null` | `null` |
| auth_id | `string` | `"AUTH-CB96B75F"` |
| auth_type | `string` | `"Prior Authorization"` |
| clinical_notes | `string` | `"Clinical review in progress for dme - cpap machine"` |
| decision_date | `null \| string` | `null` |
| denial_reason | `null \| string` | `null` |
| effective_date | `null \| string` | `null` |
| expiration_date | `null \| string` | `null` |
| member_id | `string` | `"MBR-4B739AAC"` |
| plan_id | `string` | `"PLN-C89F33E6"` |
| procedure_code | `string` | `"E0601"` |
| provider_id | `string` | `"PRV-9DF6F295"` |
| request_date | `string` | `"2025-05-03"` |
| requested_units | `integer` | `1` |
| reviewer | `string` | `"Dr. Samantha Baker"` |
| service_category | `string` | `"DME"` |
| service_description | `string` | `"DME - CPAP Machine"` |
| status | `string` | `"Pending"` |
| urgency | `string` | `"Standard"` |

### Accumulators (2000)

| Field | Type(s) | Example |
|-------|---------|---------|
| accumulator_id | `string` | `"ACC-831235F6"` |
| deductible_limit | `integer` | `5000` |
| deductible_remaining | `number` | `0` |
| deductible_used | `number` | `5000` |
| last_updated | `string` | `"2025-12-31"` |
| member_id | `string` | `"MBR-B5906016"` |
| oop_max_limit | `integer` | `7500` |
| oop_remaining | `number` | `2497.9` |
| oop_used | `number` | `5002.1` |
| plan_id | `string` | `"PLN-AAF39C04"` |
| plan_year | `integer` | `2025` |

### Call Logs (3000)

| Field | Type(s) | Example |
|-------|---------|---------|
| agent_id | `string` | `"AGT-0001"` |
| call_date | `string` | `"2024-11-23"` |
| call_id | `string` | `"CALL-729A5299"` |
| call_reason | `string` | `"Prior Auth Status"` |
| call_time | `string` | `"09:01:00"` |
| call_type | `string` | `"Inbound"` |
| disposition | `string` | `"Resolved"` |
| duration_seconds | `integer` | `420` |
| first_call_resolution | `boolean` | `true` |
| ivr_path | `string` | `"1 > 2 > 3 > Agent"` |
| member_id | `string` | `"MBR-7B1DA9C2"` |
| notes | `string` | `"Member following up on prior authorization request CLM-DF2093C0. Auth is pending clinical review."` |
| queue_wait_seconds | `integer` | `574` |
| related_auth_id | `null \| string` | `"AUTH-3FB45B7E"` |
| related_claim_id | `null \| string` | `"CLM-43A42DDC"` |
| sentiment | `string` | `"Positive"` |

### Secure Messages (2000)

| Field | Type(s) | Example |
|-------|---------|---------|
| body | `string` | `"I'm new to the plan and have several questions. Where can I find this information?"` |
| category | `string` | `"General Inquiry"` |
| direction | `string` | `"Outbound"` |
| member_id | `string` | `"MBR-59C2574D"` |
| message_id | `string` | `"MSG-4AA865B5"` |
| priority | `string` | `"Normal"` |
| related_claim_id | `null \| string` | `"CLM-56D48AC9"` |
| response_time_hours | `null \| number` | `null` |
| sent_date | `string` | `"2024-12-06 00:00:00"` |
| status | `string` | `"Read"` |
| subject | `string` | `"General Account Question"` |
| thread_id | `null \| string` | `"THD-1C0D8F3A"` |

### Case Notes (1500)

| Field | Type(s) | Example |
|-------|---------|---------|
| author | `string` | `"Sarah Jackson"` |
| case_id | `string` | `"CASE-E27AC3DB"` |
| category | `string` | `"Grievance"` |
| content | `string` | `"Member grievance received regarding claim denial. Escalated to Appeals team for formal review within 30-day timeline."` |
| created_date | `string` | `"2024-11-20 00:00:00"` |
| follow_up_date | `null \| string` | `null` |
| follow_up_required | `boolean` | `false` |
| member_id | `string` | `"MBR-79BC85F5"` |
| note_id | `string` | `"NOTE-72417577"` |
| note_type | `string` | `"System"` |
| related_auth_id | `null \| string` | `"AUTH-E2FC7DA1"` |
| related_claim_id | `null \| string` | `"CLM-F40D5F86"` |
| status | `string` | `"Open"` |

### Agents (20)

| Field | Type(s) | Example |
|-------|---------|---------|
| agent_id | `string` | `"AGT-0001"` |
| avg_handle_time_seconds | `integer` | `579` |
| department | `string` | `"Enrollment"` |
| hire_date | `string` | `"2019-11-12"` |
| languages | `array[string]` | `["English", "Spanish"]` |
| name | `string` | `"Maria Garcia"` |
| role | `string` | `"Supervisor"` |
| satisfaction_score | `number` | `3.36` |

### Reference Diagnosis Codes (27)

| Field | Type(s) | Example |
|-------|---------|---------|
| category | `string` | `"Respiratory"` |
| code | `string` | `"J06.9"` |
| description | `string` | `"Acute upper respiratory infection, unspecified"` |

### Reference Procedure Codes (28)

| Field | Type(s) | Example |
|-------|---------|---------|
| avg_cost | `integer` | `150` |
| category | `string` | `"E&M"` |
| code | `string` | `"99213"` |
| description | `string` | `"Office visit, established patient, moderate complexity"` |

### Reference Place Of Service (7)

| Field | Type(s) | Example |
|-------|---------|---------|
| code | `string` | `"11"` |
| description | `string` | `"Office"` |

### Reference Medications (24)

| Field | Type(s) | Example |
|-------|---------|---------|
| avg_cost | `integer` | `15` |
| category | `string` | `"Diabetes"` |
| days_supply | `integer` | `30` |
| name | `string` | `"Metformin 500mg"` |
| ndc | `string` | `"00093-7212-01"` |
