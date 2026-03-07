/**
 * HealthcarePlatform — typed contract for all data adapters.
 *
 * Source of truth: agent-sandbox/tools/tool_schemas.json (19 tools).
 * SandboxAdapter (Python) implements this via execute_tool().
 * ClientAdapter implements this against real production systems.
 *
 * All param interfaces are derived from tool_schemas.json input_schema.
 */

// ---------------------------------------------------------------------------
// Base result type — all tools return a dict
// ---------------------------------------------------------------------------

export type ToolResult = Record<string, unknown>;

// ---------------------------------------------------------------------------
// Param interfaces (from tool_schemas.json input_schema)
// ---------------------------------------------------------------------------

export interface LookupMemberParams {
  member_id?: string;
  subscriber_id?: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string; // YYYY-MM-DD
}

export interface SearchClaimsParams {
  member_id?: string;
  claim_status?: 'Paid' | 'Denied' | 'Pending' | 'Adjusted' | 'Appealed';
  date_from?: string; // YYYY-MM-DD
  date_to?: string;   // YYYY-MM-DD
  provider_id?: string;
  diagnosis_code?: string;
  min_amount?: number;
  limit?: number;
}

export interface SearchPharmacyParams {
  member_id?: string;
  medication_name?: string;
  medication_category?: string;
  date_from?: string; // YYYY-MM-DD
  date_to?: string;   // YYYY-MM-DD
  formulary_status?: 'Preferred' | 'Non-Preferred' | 'Specialty';
  limit?: number;
}

export interface CheckBenefitsParams {
  plan_id: string;
  service_category: string;
}

export interface EligibilityParams {
  member_id: string;
  date_of_service: string; // YYYY-MM-DD
}

export interface FormularyParams {
  plan_id: string;
  medication_name?: string;
  ndc?: string;
}

export interface AuthParams {
  auth_id?: string;
  member_id?: string;
}

export interface SubmitAuthParams {
  member_id: string;
  provider_id: string;
  service_description: string;
  procedure_code: string;
  diagnosis_code: string;
  urgency?: 'Standard' | 'Urgent' | 'Emergency';
  clinical_notes?: string;
}

export interface AppealParams {
  member_id: string;
  claim_id?: string;
  auth_id?: string;
  appeal_reason: string;
  supporting_documentation?: string;
  expedited?: boolean;
}

export interface SearchProvidersParams {
  specialty?: string;
  name?: string;
  network_status?: 'In-Network' | 'Out-of-Network';
  accepting_new_patients?: boolean;
  city?: string;
  state?: string;
  limit?: number;
}

export interface InteractionHistoryParams {
  member_id: string;
  interaction_type?: 'calls' | 'messages' | 'case_notes' | 'all';
  date_from?: string; // YYYY-MM-DD
  date_to?: string;   // YYYY-MM-DD
  limit?: number;
}

export interface DraftCaseNoteParams {
  member_id: string;
  category: 'Clinical Review' | 'Billing' | 'Enrollment' | 'Grievance' | 'Appeal' | 'Care Coordination' | 'Utilization Management';
  content: string;
  related_claim_id?: string;
  related_auth_id?: string;
  follow_up_required?: boolean;
  follow_up_date?: string; // YYYY-MM-DD
}

export interface SubmitCaseNoteParams {
  draft_id: string;
}

export interface SearchKnowledgeBaseParams {
  query: string;
  section?: 'plan_policies' | 'coverage_guidelines' | 'member_faq' | 'provider_policies' | 'formulary_guidelines' | 'appeals_and_grievances' | 'business_rules' | 'reference_data' | 'all';
  keywords?: string[];
}

export interface GenerateDocumentParams {
  document_type: 'EOB' | 'denial_letter' | 'auth_approval_letter' | 'auth_denial_letter' | 'id_card' | 'welcome_letter' | 'appeal_acknowledgment';
  member_id: string;
  claim_id?: string;
  auth_id?: string;
  appeal_id?: string;
}

// ---------------------------------------------------------------------------
// HealthcarePlatform interface — the contract every adapter implements
// ---------------------------------------------------------------------------

export interface HealthcarePlatform {
  // tool: lookup_member
  lookupMember(params: LookupMemberParams): Promise<ToolResult>;

  // tool: get_member_coverage
  getMemberCoverage(params: { member_id: string }): Promise<ToolResult>;

  // tool: get_member_dependents
  getMemberDependents(params: { member_id: string }): Promise<ToolResult>;

  // tool: search_claims
  searchClaims(params: SearchClaimsParams): Promise<ToolResult>;

  // tool: get_claim_detail
  getClaimDetail(params: { claim_id: string }): Promise<ToolResult>;

  // tool: search_pharmacy_claims
  searchPharmacyClaims(params: SearchPharmacyParams): Promise<ToolResult>;

  // tool: check_benefits
  checkBenefits(params: CheckBenefitsParams): Promise<ToolResult>;

  // tool: get_accumulator
  getAccumulator(params: { member_id: string }): Promise<ToolResult>;

  // tool: check_eligibility
  checkEligibility(params: EligibilityParams): Promise<ToolResult>;

  // tool: get_plan_formulary
  getPlanFormulary(params: FormularyParams): Promise<ToolResult>;

  // tool: get_authorization
  getAuthorization(params: AuthParams): Promise<ToolResult>;

  // tool: submit_authorization_request
  submitAuthorizationRequest(params: SubmitAuthParams): Promise<ToolResult>;

  // tool: initiate_appeal
  initiateAppeal(params: AppealParams): Promise<ToolResult>;

  // tool: search_providers
  searchProviders(params: SearchProvidersParams): Promise<ToolResult>;

  // tool: get_interaction_history
  getInteractionHistory(params: InteractionHistoryParams): Promise<ToolResult>;

  // tool: draft_case_note
  draftCaseNote(params: DraftCaseNoteParams): Promise<ToolResult>;

  // tool: submit_case_note
  submitCaseNote(params: SubmitCaseNoteParams): Promise<ToolResult>;

  // tool: search_knowledge_base
  searchKnowledgeBase(params: SearchKnowledgeBaseParams): Promise<ToolResult>;

  // tool: generate_document
  generateDocument(params: GenerateDocumentParams): Promise<ToolResult>;
}
