# Naismith

Naismith is a **general-purpose, constitutionally bounded personal AI operating
system**. It gives the user one continuous interface, one governed memory, and
one control layer for coordinating AI models, agents, tools, files, projects,
and applications.

The name is basketball-inspired. **The product is not basketball-focused.**

Naismith is also **not primarily an interview agent**. Interviews may become one
optional workflow beside business, research, planning, coding, learning, and
other personal operations.

Read the authoritative handoff before changing the repository:

- [`docs/NAISMITH_CLAUDE_CODE_HANDOFF.md`](docs/NAISMITH_CLAUDE_CODE_HANDOFF.md)
- [`docs/CLAUDE_START_HERE.md`](docs/CLAUDE_START_HERE.md)
- [`constitution/NAISMITH_CONSTITUTION.md`](constitution/NAISMITH_CONSTITUTION.md)

## Core architecture

1. **User authority** — the user remains in control.
2. **Constitution and policy kernel** — every model, agent, memory operation, and
   tool call is bounded outside the language model.
3. **Legend Vault** — raw-first, portable, inspectable long-term records and
   knowledge.
4. **General-purpose runtime** — plans, retrieves, delegates, combines, and
   reports work.
5. **Agent Access Fabric** — connects supported outside models and agents through
   official APIs, OAuth, MCP, local bridges, provider-native jobs, or
   user-mediated handoffs.
6. **Skills and workflows** — reusable procedures for many domains.

External agents are specialists under Naismith. They do not replace Naismith,
broaden their own permissions, or bypass its policy layer.

## Subscription and API note

Consumer subscriptions and developer API access are not automatically the same.

The user may connect ChatGPT/OpenAI, Claude/Anthropic, GitHub, and other
ecosystems only through supported, permissioned methods. Naismith must track the
actual entitlement, scopes, rate limits, cost, and data restrictions for each
connection. It must never scrape consumer sessions or store real credentials in
this public repository.

## Current status

This repository currently implements a **governance-first text prototype**, not
the complete product.

What runs today:

- FastAPI service;
- active Constitution endpoints;
- deterministic deny-by-default policy layer;
- a bounded, policy-checked agent runtime (Hermes-style state machine);
- a model gateway with a provider registry, explicit selection, timeouts,
  retries, normalized errors, and per-turn cost/usage — backed by a
  deterministic mock provider (a real Anthropic provider is scaffolded but
  inert: no network call, no paid usage);
- durable persistence for sessions, turns, audit events, and model-call cost
  (SQLAlchemy + Alembic migrations; SQLite locally, Postgres-ready);
- text sessions with an append-only audit trail;
- React transcript UI with governance information;
- shared JSON Schema contracts;
- constitutional tests;
- CI, secret scanning, and a bounded stress harness.

Not yet implemented:

- live model providers (the real gateway exists; no provider is activated yet);
- Agent Access Fabric;
- authentication and workspace isolation;
- Legend Vault retrieval;
- governed memory;
- external tools;
- voice;
- workflow modules;
- simulations.

## Corrected delivery order

1. Stabilize the current branch and correct documentation.
2. Build a persistent general-purpose text workspace with one real provider.
3. Add Agent Access Fabric v1 for OpenAI, Anthropic, and supported GitHub agent
   workflows.
4. Add Legend Vault read-only retrieval with citations.
5. Add governed memory.
6. Add approved tool execution.
7. Add voice and multimodal input.
8. Add reusable workflows, including interviews.
9. Add controlled simulation and evaluation.

Build one narrow, tested vertical slice at a time.

## Layout

```text
constitution/        Constitution and constitutional-test registry
docs/                Governing handoff and development instructions
services/api/        FastAPI service and runtime foundation
apps/web/            React/TypeScript client
packages/contracts/  Shared boundary schemas
scripts/             Local test and bounded stress tooling
```

## Run locally

Requires Python 3.11+ and Node 22+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e "services/api[dev]"
naismith-api
```

In another shell:

```bash
cd apps/web
npm install
npm run dev
```

Or:

```bash
docker compose up --build
```

## Test

```bash
./scripts/run-tests.sh
python scripts/stress_test.py
```

Do not claim test or CI success unless it was actually executed and observed.

## Privacy

Never commit real credentials, private exports, raw handoffs, personal
transcripts, recordings, private Legend Vault data, or generated user records.
