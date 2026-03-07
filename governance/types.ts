// Pega integration: POST to /governance/validate with WorkflowState
// This is the only file your team needs to understand the contract.

export type GovernanceDecision = 'allow' | 'reject' | 'escalate';

export interface WorkflowState {
  sessionId: string;
  workflowId: string;
  workflowType: string;
  proposedAction: ProposedAction;
}

export interface ProposedAction {
  actionType: string;
  isAdverseDetermination: boolean;
  isAppealDecision: boolean;
  isClinicalComplexity: boolean;
  claimAmount: number;
  confidence: number;
  missingDataFraction: number;
}

export interface GovernanceResponse {
  decision: GovernanceDecision;
  mandatory: boolean;
  reason: string;
  auditId: string;
  escalationRequired: boolean;
  humanReviewId: string | null;
}

export interface GovernanceAPI {
  validate(state: WorkflowState): Promise<GovernanceResponse>;
  getAuditTrail(sessionId: string): Promise<AuditEntry[]>;
}

// Import AuditEntry from harness/audit_schema.ts
export { AuditEntry } from '../harness/audit_schema';
