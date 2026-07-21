# Naismith

Naismith is a **voice-first, memory-enabled, constitutionally bounded AI agent**
that runs and improves interviews, conducts structured simulations, learns only
through controlled and reviewable evaluation loops, and uses a user-controlled
Legend Vault (Obsidian-compatible Markdown) as its knowledge base.

It is built around a strict, testable [Constitution](constitution/NAISMITH_CONSTITUTION.md)
that outranks prompts, tools, memories, and optimization targets. The full
product spec, architecture, and delivery plan live in
[`docs/NAISMITH_CLAUDE_CODE_HANDOFF.md`](docs/NAISMITH_CLAUDE_CODE_HANDOFF.md) —
**read it before changing the repository.**

## Core principles

- Human authority remains primary.
- Autonomy is scoped, granted, and revocable — default authority is zero.
- Memory has provenance and deletion controls.
- Interview scoring is evidence-linked and reviewable.
- Simulations cannot promote themselves to production.
- Private data and secrets never belong in this public repository.

## Status — Phase 0/1 vertical slice

This repository currently implements the **thin text-first slice** from the
handoff (§14): it proves the governance skeleton before any autonomy, memory,
voice, or external tools are introduced.

What runs today:

- A **FastAPI service** (`services/api/`) that surfaces the active Constitution,
  runs a **deterministic policy engine outside the model** (deny-by-default),
  drives a **mock model adapter**, and writes an **append-only audit trail**.
- A **React web app** (`apps/web/`) — a transcript-first conversation screen
  with a live governance panel.
- An **executable constitutional test suite** that runs the code-enforceable
  articles as live assertions and skips capabilities not yet built.
- Docker Compose (API + Postgres + Redis) and CI (lint, type-check, tests,
  secret scanning).

Deliberately absent this phase: real model/voice providers, durable memory,
external tools, and persistence.

## Layout

```
constitution/        The Constitution + its machine-loadable test registry
docs/                The governing handoff / specification
services/api/        FastAPI API + session gateway (Python)
apps/web/            Voice-first client — text slice (TypeScript/React)
packages/contracts/  Shared JSON Schemas (source of truth for boundary types)
scripts/             run-tests.sh (mirrors CI)
```

## Run locally

Requires Python 3.11+ and Node 22+.

```bash
# API
python -m venv .venv && source .venv/bin/activate
pip install -e "services/api[dev]"
naismith-api                      # http://127.0.0.1:8000

# Web (in another shell)
cd apps/web && npm install && npm run dev   # http://localhost:5173
```

Then open the web app, start a text session, send a message, and watch the
Constitution version and audit events update. Or use Docker:

```bash
docker compose up --build         # API on :8000, Postgres, Redis
```

## Test

```bash
./scripts/run-tests.sh            # API lint + types + tests, web build
```

## Privacy

Do not commit private exports, transcripts, recordings, generated records, real
credentials, or personal artifacts. `.gitignore` excludes common runtime paths,
and CI runs secret scanning — but review every commit before pushing.
