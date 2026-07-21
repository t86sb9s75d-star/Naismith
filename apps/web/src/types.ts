// Mirrors packages/contracts/*.schema.json and the API's Pydantic models.
// Keep these in sync when the shared contracts change.

export type Speaker = "user" | "assistant";

export interface Turn {
  id: string;
  session_id: string;
  sequence_number: number;
  speaker: Speaker;
  text: string;
  created_at: string;
  safety_labels: string[];
}

export interface Session {
  id: string;
  workspace_id: string | null;
  mode: "text";
  status: "active" | "ended";
  created_at: string;
  policy_version: string;
  model_route: string;
}

export type PolicyDecisionType = "allow" | "allow_with_confirmation" | "deny";

export interface PolicyDecision {
  decision: PolicyDecisionType;
  policy_version: string;
  reason: string;
  rules_evaluated: string[];
  required_actions: string[];
}

export interface MessageResponse {
  session_id: string;
  user_turn: Turn;
  assistant_turn: Turn;
  policy_decision: PolicyDecision;
  model_version: string;
  audit_event_id: string;
}

export interface ConstitutionInfo {
  version: string;
  sha256: string;
  article_count: number;
  source_path: string;
  text: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  session_id: string | null;
  actor_type: string;
  actor_id: string;
  event_type: string;
  policy_version: string | null;
  model_version: string | null;
  status: string;
  correlation_id: string;
}
