import type {
  AuditEvent,
  ConstitutionInfo,
  MessageResponse,
  Session,
} from "./types";

const BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${resp.status}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  getConstitution(): Promise<ConstitutionInfo> {
    return request<ConstitutionInfo>("/v1/governance/constitution");
  },
  createSession(): Promise<Session> {
    return request<Session>("/v1/sessions", {
      method: "POST",
      body: JSON.stringify({}),
    });
  },
  sendMessage(sessionId: string, text: string): Promise<MessageResponse> {
    return request<MessageResponse>(`/v1/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  },
  getAuditEvents(sessionId: string): Promise<AuditEvent[]> {
    return request<AuditEvent[]>(
      `/v1/governance/audit-events?session_id=${encodeURIComponent(sessionId)}`,
    );
  },
};
