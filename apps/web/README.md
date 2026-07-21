# naismith-web

The voice-first Naismith client — **text conversation slice** for Phase 0/1.
Vite + React + TypeScript (strict). It renders a transcript-first conversation
screen and a live governance panel: the active Constitution version, the
session's policy version, and the append-only audit trail for the session.

Voice, memory, and interview UIs arrive in later phases; this slice proves the
text path end to end against the API.

## Develop

```bash
npm install
npm run dev        # http://localhost:5173, expects the API on :8000
```

Point the app at a non-default API with `VITE_API_BASE_URL` (see the repo-root
`.env.example`).

## Check

```bash
npm run build      # tsc --noEmit && vite build
```
