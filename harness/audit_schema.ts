// TypeScript interface contract for client teams integrating with Shippy HC.
// Source of truth: harness/audit.py — keep these in sync.

export type AuditEventType =
  | 'tool_call'
  | 'tool_result'
  | 'escalation'
  | 'human_review'
  | 'determination'
  | 'error'
  | 'recovery';

export interface AuditEntry {
  sessionId: string;
  workflowId: string;
  timestamp: string; // ISO8601
  eventType: AuditEventType;
  toolName?: string;
  toolParams?: Record<string, unknown>;
  toolResult?: unknown;
  escalationReason?: string;
  humanReviewerId?: string;
  humanDecision?: string;
  confidence?: number;
  model: string;
  promptVersion: string;
}

export interface AuditVerifyResult {
  complete: boolean;
  missing: string[];
}
