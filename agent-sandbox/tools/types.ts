/**
 * Healthcare Sandbox Tool Type Definitions
 *
 * Auto-generated from tool_schemas.json and api_server.py return shapes.
 * Re-generate by reading the schema and tracing API return types.
 *
 * All tools may also return `{ error: string }` on failure.
 */

// ── Shared Entity Types ─────────────────────────────────────────────

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  zip: string;
}

export interface Member {
  member_id: string;
  subscriber_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  plan_id: string;
  employer_id: string;
  pcp_provider_id: string;
  address: Address;
  phone: string;
  email: string;
  relationship: string;
  chronic_conditions: string[];
  risk_score: number;
  preferred_language: string;
  communication_preference: string;
}

export interface Dependent {
  member_id: string;
  subscriber_member_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  relationship: string;
}

export interface Plan {
  plan_id: string;
  plan_name: string;
  plan_type: string;
  tier: string;
  network_name: string;
  deductible_individual: number;
  deductible_family: number;
  out_of_pocket_max_individual: number;
  out_of_pocket_max_family: number;
  copay_pcp: number;
  copay_specialist: number;
  copay_er: number;
  copay_urgent_care: number;
  copay_rx_generic: number;
  copay_rx_preferred_brand: number;
  copay_rx_non_preferred: number;
  copay_rx_specialty: number;
  coinsurance_in_network: number;
  coinsurance_out_of_network: number;
}

export interface Benefit {
  benefit_id: string;
  plan_id: string;
  category: string;
  service: string;
  in_network_cost_share: string;
  out_of_network_cost_share: string;
  prior_auth_required: boolean;
  annual_limit: string | null;
  notes: string;
}

export interface Provider {
  provider_id: string;
  name: string;
  specialty: string;
  credential: string;
  npi: string;
  network_status: string;
  accepting_new_patients: boolean;
  address: Address;
  phone: string;
  languages: string[];
  facility_type: string;
}

export interface MedicalClaim {
  claim_id: string;
  member_id: string;
  provider_id: string;
  service_date: string;
  claim_status: 'Paid' | 'Denied' | 'Pending' | 'Adjusted' | 'Appealed';
  primary_diagnosis: string;
  primary_diagnosis_description: string;
  total_billed: number;
  total_allowed: number;
  total_plan_paid: number;
  total_member_responsibility: number;
  denial_reason: string | null;
  place_of_service: string;
  claim_type: string;
  payment_date: string | null;
  check_number: string | null;
}

export interface ClaimLine {
  claim_line_id: string;
  claim_id: string;
  line_number: number;
  procedure_code: string;
  procedure_description: string;
  diagnosis_pointer: string;
  units: number;
  billed_amount: number;
  allowed_amount: number;
  plan_paid: number;
  member_responsibility: number;
  denial_reason: string | null;
}

export interface PharmacyClaim {
  rx_claim_id: string;
  member_id: string;
  medication_name: string;
  medication_category: string;
  ndc: string;
  fill_date: string;
  days_supply: number;
  quantity: number;
  pharmacy_name: string;
  prescriber_id: string;
  formulary_status: 'Preferred' | 'Non-Preferred' | 'Specialty';
  total_cost: number;
  plan_paid: number;
  member_paid: number;
  copay_applied: number;
}

export interface Accumulator {
  accumulator_id: string;
  member_id: string;
  plan_year: string;
  deductible_individual_limit: number;
  deductible_individual_met: number;
  deductible_family_limit: number;
  deductible_family_met: number;
  oop_individual_limit: number;
  oop_individual_met: number;
  oop_family_limit: number;
  oop_family_met: number;
  last_updated: string;
}

export interface EligibilityPeriod {
  eligibility_id: string;
  member_id: string;
  plan_id: string;
  effective_date: string;
  termination_date: string | null;
  status: string;
  coverage_type: string;
}

export interface Authorization {
  auth_id: string;
  member_id: string;
  plan_id: string;
  provider_id: string;
  auth_type: string;
  service_description: string;
  procedure_code: string;
  service_category: string;
  status: string;
  request_date: string;
  decision_date: string | null;
  effective_date: string | null;
  expiration_date: string | null;
  approved_units: number | null;
  requested_units: number;
  denial_reason: string | null;
  urgency: string;
  clinical_notes: string;
  reviewer: string | null;
  message?: string;
}

export interface Appeal {
  appeal_id: string;
  member_id: string;
  claim_id: string | null;
  auth_id: string | null;
  appeal_reason: string;
  supporting_documentation: string | null;
  expedited: boolean;
  status: string;
  submitted_date: string;
  received_date: string;
  expected_decision_date: string;
  message: string;
}

export interface CallLog {
  call_id: string;
  member_id: string;
  call_date: string;
  call_type: string;
  duration_minutes: number;
  agent_id: string;
  reason: string;
  resolution: string;
  satisfaction_score: number | null;
}

export interface SecureMessage {
  message_id: string;
  member_id: string;
  direction: string;
  subject: string;
  body: string;
  sent_date: string;
  read_date: string | null;
  category: string;
  status: string;
}

export interface CaseNote {
  note_id: string;
  member_id: string;
  case_id: string;
  author: string;
  category: string;
  note_type: string;
  content: string;
  created_date: string;
  related_claim_id: string | null;
  related_auth_id: string | null;
  follow_up_required: boolean;
  follow_up_date: string | null;
  status: string;
  message?: string;
}

export interface KnowledgeBaseEntry {
  section: string;
  [key: string]: unknown;
}

export interface FormularyEntry {
  medication: {
    name: string;
    ndc: string;
    category: string;
    avg_cost: number;
  };
  tier: 'Generic' | 'Preferred Brand' | 'Non-Preferred' | 'Specialty';
  copay: number | null;
  prior_auth_required: boolean;
  step_therapy_required: boolean;
}

export interface ToolError {
  error: string;
}

// ── Tool Params Types ───────────────────────────────────────────────

/** Look up a member by ID, name, or subscriber ID. Returns demographics, plan enrollment, PCP, and chronic conditions. */
export interface LookupMemberParams {
  /** Member ID (e.g. MBR-A1B2C3D4) */
  member_id?: string;
  /** Subscriber ID (e.g. SUB123456789) */
  subscriber_id?: string;
  /** First name for search */
  first_name?: string;
  /** Last name for search */
  last_name?: string;
  /** DOB in YYYY-MM-DD format */
  date_of_birth?: string;
}

/** Get a member's current coverage details including plan, benefits, deductible status, and out-of-pocket accumulator. */
export interface GetMemberCoverageParams {
  /** Member ID */
  member_id: string;
}

/** List all dependents (spouse, children) enrolled under a subscriber. */
export interface GetMemberDependentsParams {
  /** Primary subscriber member ID */
  member_id: string;
}

/** Search medical claims by member, date range, status, provider, or diagnosis. Returns claim summaries with billed/paid amounts. */
export interface SearchClaimsParams {
  /** Filter by member ID */
  member_id?: string;
  /** Filter by claim status */
  claim_status?: 'Paid' | 'Denied' | 'Pending' | 'Adjusted' | 'Appealed';
  /** Service date start (YYYY-MM-DD) */
  date_from?: string;
  /** Service date end (YYYY-MM-DD) */
  date_to?: string;
  /** Filter by provider ID */
  provider_id?: string;
  /** Filter by ICD-10 code */
  diagnosis_code?: string;
  /** Minimum billed amount */
  min_amount?: number;
  /** Max results to return (default 20) */
  limit?: number;
}

/** Get full claim detail including all claim lines, diagnosis, procedure codes, billed/allowed/paid amounts, and denial reason if applicable. */
export interface GetClaimDetailParams {
  /** Claim ID (e.g. CLM-A1B2C3D4) */
  claim_id: string;
}

/** Search pharmacy/prescription claims by member, medication, date range, or formulary status. */
export interface SearchPharmacyClaimsParams {
  /** Filter by member ID */
  member_id?: string;
  /** Medication name (partial match) */
  medication_name?: string;
  /** Drug category (e.g. Diabetes, Cardiovascular) */
  medication_category?: string;
  /** Fill date start (YYYY-MM-DD) */
  date_from?: string;
  /** Fill date end (YYYY-MM-DD) */
  date_to?: string;
  /** Formulary tier */
  formulary_status?: 'Preferred' | 'Non-Preferred' | 'Specialty';
  /** Max results (default 20) */
  limit?: number;
}

/** Check what benefits a member's plan covers for a specific service category. Returns copay, coinsurance, auth requirements, and limits. */
export interface CheckBenefitsParams {
  /** Plan ID */
  plan_id: string;
  /** Service category (e.g. 'Primary Care Visit', 'Emergency Room', 'Physical Therapy', 'Prescription Drugs - Generic') */
  service_category: string;
}

/** Get a member's current deductible and out-of-pocket accumulator status for the plan year. */
export interface GetAccumulatorParams {
  /** Member ID */
  member_id: string;
}

/** Search for healthcare providers by specialty, name, network status, or location. */
export interface SearchProvidersParams {
  /** Provider specialty (e.g. Cardiology, Family Medicine) */
  specialty?: string;
  /** Provider name (partial match) */
  name?: string;
  /** Network status filter */
  network_status?: 'In-Network' | 'Out-of-Network';
  /** Only show providers accepting new patients */
  accepting_new_patients?: boolean;
  /** City filter */
  city?: string;
  /** State code filter */
  state?: string;
  /** Max results (default 20) */
  limit?: number;
}

/** Look up a prior authorization by ID or search by member. Returns status, approved units, expiration, and denial reason if applicable. */
export interface GetAuthorizationParams {
  /** Authorization ID */
  auth_id?: string;
  /** Search by member ID */
  member_id?: string;
}

/** Submit a new prior authorization request for a service. */
export interface SubmitAuthorizationRequestParams {
  /** Member ID */
  member_id: string;
  /** Requesting provider ID */
  provider_id: string;
  /** Description of the requested service */
  service_description: string;
  /** CPT/HCPCS code */
  procedure_code: string;
  /** Supporting ICD-10 diagnosis code */
  diagnosis_code: string;
  /** Request urgency */
  urgency?: 'Standard' | 'Urgent' | 'Emergency';
  /** Supporting clinical rationale */
  clinical_notes?: string;
}

/** Get a member's interaction history including call logs, secure messages, and case notes. */
export interface GetInteractionHistoryParams {
  /** Member ID */
  member_id: string;
  /** Type of interactions to retrieve (default: all) */
  interaction_type?: 'calls' | 'messages' | 'case_notes' | 'all';
  /** Start date (YYYY-MM-DD) */
  date_from?: string;
  /** End date (YYYY-MM-DD) */
  date_to?: string;
  /** Max results (default 20) */
  limit?: number;
}

/** Create a new case note for a member interaction. */
export interface CreateCaseNoteParams {
  /** Member ID */
  member_id: string;
  /** Note category */
  category: 'Clinical Review' | 'Billing' | 'Enrollment' | 'Grievance' | 'Appeal' | 'Care Coordination' | 'Utilization Management';
  /** Note content */
  content: string;
  /** Related claim ID if applicable */
  related_claim_id?: string;
  /** Related auth ID if applicable */
  related_auth_id?: string;
  /** Whether follow-up is needed */
  follow_up_required?: boolean;
  /** Follow-up date if required (YYYY-MM-DD) */
  follow_up_date?: string;
}

/** Search policies, FAQs, business rules, and reference data. Use this when answering member questions about how their plan works. */
export interface SearchKnowledgeBaseParams {
  /** Natural language search query */
  query: string;
  /** Knowledge base section to search (default: all) */
  section?: 'plan_policies' | 'coverage_guidelines' | 'member_faq' | 'provider_policies' | 'formulary_guidelines' | 'appeals_and_grievances' | 'business_rules' | 'reference_data' | 'all';
  /** Keyword filters */
  keywords?: string[];
}

/** Verify a member's eligibility status for a specific date of service. */
export interface CheckEligibilityParams {
  /** Member ID */
  member_id: string;
  /** Date to check eligibility for (YYYY-MM-DD) */
  date_of_service: string;
}

/** Initiate an appeal for a denied claim or authorization. */
export interface InitiateAppealParams {
  /** Member ID */
  member_id: string;
  /** Reason for the appeal */
  appeal_reason: string;
  /** Denied claim ID (if claim appeal) */
  claim_id?: string;
  /** Denied auth ID (if auth appeal) */
  auth_id?: string;
  /** Description of supporting documents */
  supporting_documentation?: string;
  /** Request expedited review (medical urgency) */
  expedited?: boolean;
}

/** Render a member-facing document such as an EOB, denial letter, auth approval letter, or ID card. */
export interface GenerateDocumentParams {
  /** Type of document to generate */
  document_type: 'EOB' | 'denial_letter' | 'auth_approval_letter' | 'auth_denial_letter' | 'id_card' | 'welcome_letter' | 'appeal_acknowledgment';
  /** Member ID */
  member_id: string;
  /** Related claim ID (for EOB, denial letter) */
  claim_id?: string;
  /** Related auth ID (for auth letters) */
  auth_id?: string;
  /** Related appeal ID (for appeal acknowledgment) */
  appeal_id?: string;
}

/** Look up formulary status, tier, and coverage details for a specific medication under a member's plan. */
export interface GetPlanFormularyParams {
  /** Plan ID */
  plan_id: string;
  /** Medication name (partial match) */
  medication_name?: string;
  /** National Drug Code */
  ndc?: string;
}

// ── Tool Result Types ───────────────────────────────────────────────

export interface LookupMemberResult {
  results: Member[];
  total: number;
}

export interface GetMemberCoverageResult {
  member: Member;
  plan: Plan | null;
  employer: { employer_id: string; name: string } | null;
  benefits: Benefit[];
  accumulator: Accumulator | null;
  eligibility_periods: EligibilityPeriod[];
}

export interface GetMemberDependentsResult {
  member_id: string;
  dependents: Dependent[];
  count: number;
}

export interface SearchClaimsResult {
  results: MedicalClaim[];
  total: number;
}

export interface GetClaimDetailResult {
  claim: MedicalClaim;
  claim_lines: ClaimLine[];
  provider: Provider | null;
  member_name: string | null;
}

export interface SearchPharmacyClaimsResult {
  results: PharmacyClaim[];
  total: number;
}

export interface GetPlanFormularyResult {
  plan_id: string;
  plan_name: string;
  formulary_results: FormularyEntry[];
}

export interface CheckBenefitsResult {
  plan_id: string;
  plan_name: string;
  plan_type: string;
  tier: string;
  service_category: string;
  benefits: Benefit[];
  plan_copays: {
    pcp: number;
    specialist: number;
    er: number;
    urgent_care: number;
  };
}

/** Returns the raw accumulator record. */
export type GetAccumulatorResult = Accumulator;

export interface CheckEligibilityResult {
  member_id: string;
  eligible: boolean;
  period?: EligibilityPeriod;
  reason?: string;
}

export interface SearchProvidersResult {
  results: Provider[];
  total: number;
}

/** When called with auth_id, returns a single Authorization. When called with member_id, returns a list. */
export type GetAuthorizationResult = Authorization | {
  member_id: string;
  authorizations: Authorization[];
  count: number;
};

/** Returns the newly created authorization with status "Pending". */
export type SubmitAuthorizationRequestResult = Authorization;

export interface GetInteractionHistoryResult {
  member_id: string;
  calls?: CallLog[];
  messages?: SecureMessage[];
  case_notes?: CaseNote[];
}

/** Returns the newly created case note. */
export type CreateCaseNoteResult = CaseNote;

export interface SearchKnowledgeBaseResult {
  query: string;
  results: KnowledgeBaseEntry[];
  total: number;
}

/** Returns the newly created appeal with status "Received". */
export type InitiateAppealResult = Appeal;

export interface GenerateDocumentResult {
  document_type: string;
  template_id: string;
  member_id: string;
  claim_id: string | null;
  auth_id: string | null;
  appeal_id: string | null;
  status: 'generated';
  document_text: string;
  variables: string[];
}

// ── Tool Name Union ─────────────────────────────────────────────────

export type ToolName =
  | 'lookup_member'
  | 'get_member_coverage'
  | 'get_member_dependents'
  | 'search_claims'
  | 'get_claim_detail'
  | 'search_pharmacy_claims'
  | 'check_benefits'
  | 'get_accumulator'
  | 'search_providers'
  | 'get_authorization'
  | 'submit_authorization_request'
  | 'get_interaction_history'
  | 'create_case_note'
  | 'search_knowledge_base'
  | 'check_eligibility'
  | 'initiate_appeal'
  | 'generate_document'
  | 'get_plan_formulary';

// ── Mapping Types ───────────────────────────────────────────────────

export interface ToolParamsMap {
  lookup_member: LookupMemberParams;
  get_member_coverage: GetMemberCoverageParams;
  get_member_dependents: GetMemberDependentsParams;
  search_claims: SearchClaimsParams;
  get_claim_detail: GetClaimDetailParams;
  search_pharmacy_claims: SearchPharmacyClaimsParams;
  check_benefits: CheckBenefitsParams;
  get_accumulator: GetAccumulatorParams;
  search_providers: SearchProvidersParams;
  get_authorization: GetAuthorizationParams;
  submit_authorization_request: SubmitAuthorizationRequestParams;
  get_interaction_history: GetInteractionHistoryParams;
  create_case_note: CreateCaseNoteParams;
  search_knowledge_base: SearchKnowledgeBaseParams;
  check_eligibility: CheckEligibilityParams;
  initiate_appeal: InitiateAppealParams;
  generate_document: GenerateDocumentParams;
  get_plan_formulary: GetPlanFormularyParams;
}

export interface ToolResultMap {
  lookup_member: LookupMemberResult;
  get_member_coverage: GetMemberCoverageResult;
  get_member_dependents: GetMemberDependentsResult;
  search_claims: SearchClaimsResult;
  get_claim_detail: GetClaimDetailResult;
  search_pharmacy_claims: SearchPharmacyClaimsResult;
  check_benefits: CheckBenefitsResult;
  get_accumulator: GetAccumulatorResult;
  search_providers: SearchProvidersResult;
  get_authorization: GetAuthorizationResult;
  submit_authorization_request: SubmitAuthorizationRequestResult;
  get_interaction_history: GetInteractionHistoryResult;
  create_case_note: CreateCaseNoteResult;
  search_knowledge_base: SearchKnowledgeBaseResult;
  check_eligibility: CheckEligibilityResult;
  initiate_appeal: InitiateAppealResult;
  generate_document: GenerateDocumentResult;
  get_plan_formulary: GetPlanFormularyResult;
}

/** Type-safe tool execution helper. All tools may return ToolError on failure. */
export type ToolResult<T extends ToolName> = ToolResultMap[T] | ToolError;
