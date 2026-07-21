import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { AuditEvent, ConstitutionInfo, Session, Turn } from "./types";

export default function App(): JSX.Element {
  const [constitution, setConstitution] = useState<ConstitutionInfo | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const transcriptEnd = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [info, s] = await Promise.all([
          api.getConstitution(),
          api.createSession(),
        ]);
        setConstitution(info);
        setSession(s);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, []);

  useEffect(() => {
    transcriptEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  const send = useCallback(async () => {
    const text = draft.trim();
    if (!text || !session || sending) return;
    setSending(true);
    setError(null);
    setDraft("");
    try {
      const res = await api.sendMessage(session.id, text);
      setTurns((prev) => [...prev, res.user_turn, res.assistant_turn]);
      setAudit(await api.getAuditEvents(session.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }, [draft, session, sending]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="dot" /> Naismith
        </div>
        <div className="status-chips">
          <span className="chip">mode: text</span>
          <span className="chip">recording: off</span>
          <span className="chip">memory: none</span>
          {session && <span className="chip">model: {session.model_route}</span>}
        </div>
      </header>

      <main className="layout">
        <section className="conversation">
          <div className="transcript" role="log" aria-live="polite">
            {turns.length === 0 && (
              <p className="hint">
                Start a text session below. Naismith runs on a mock adapter in this
                slice — replies are deterministic placeholders, and every exchange
                is policy-checked and audited.
              </p>
            )}
            {turns.map((t) => (
              <div key={t.id} className={`bubble ${t.speaker}`}>
                <div className="speaker">{t.speaker}</div>
                <div className="text">{t.text}</div>
              </div>
            ))}
            {sending && <div className="bubble assistant thinking">thinking…</div>}
            <div ref={transcriptEnd} />
          </div>

          {error && <div className="error">{error}</div>}

          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <input
              type="text"
              value={draft}
              placeholder="Type a message…"
              onChange={(e) => setDraft(e.target.value)}
              disabled={!session}
              aria-label="Message"
            />
            <button type="submit" disabled={!session || sending || !draft.trim()}>
              Send
            </button>
          </form>
        </section>

        <aside className="governance">
          <h2>Governance</h2>
          <div className="panel">
            <h3>Active Constitution</h3>
            {constitution ? (
              <dl>
                <dt>version</dt>
                <dd>{constitution.version}</dd>
                <dt>articles</dt>
                <dd>{constitution.article_count}</dd>
                <dt>sha-256</dt>
                <dd className="mono">{constitution.sha256.slice(0, 16)}…</dd>
              </dl>
            ) : (
              <p className="hint">loading…</p>
            )}
          </div>

          <div className="panel">
            <h3>Session</h3>
            {session ? (
              <dl>
                <dt>id</dt>
                <dd className="mono">{session.id.slice(0, 8)}…</dd>
                <dt>policy</dt>
                <dd>{session.policy_version}</dd>
                <dt>workspace</dt>
                <dd>{session.workspace_id ?? "local"}</dd>
              </dl>
            ) : (
              <p className="hint">creating…</p>
            )}
          </div>

          <div className="panel">
            <h3>Audit trail ({audit.length})</h3>
            <ul className="audit">
              {audit.map((e) => (
                <li key={e.id}>
                  <span className="event-type">{e.event_type}</span>
                  <span className="mono">{e.status}</span>
                </li>
              ))}
              {audit.length === 0 && <li className="hint">no events yet</li>}
            </ul>
          </div>
        </aside>
      </main>
    </div>
  );
}
