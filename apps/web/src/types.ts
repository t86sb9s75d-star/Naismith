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
  // Model-call provenance (handoff §11): provider + per-turn usage/cost and the
  // running session total. Zero for the free mock provider.
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  session_cost_usd: number;
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
  prompt_version: string | null;
  tool_name: string | null;
  authorization_ref: string | null;
  input_digest: string | null;
  result_digest: string | null;
  status: string;
  error_code: string | null;
  correlation_id: string;
}
