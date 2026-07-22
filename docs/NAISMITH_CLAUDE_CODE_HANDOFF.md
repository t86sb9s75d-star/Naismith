---
project: Naismith
artifact_type: Claude Code master handoff and governing product specification
status: Draft v2.0 — product-definition correction
supersedes: Draft v1.1 product framing
last_updated: 2026-07-21
repository: t86sb9s75d-star/Naismith
repository_visibility: Public
---

# NAISMITH — CLAUDE CODE MASTER HANDOFF v2.0

> **Read this before changing the repository.**
>
> The previous handoff incorrectly allowed one future workflow—interviews—to
> become the identity of the entire product. That framing is superseded.
>
> **Naismith is not a basketball product. The name is basketball-inspired only.**
>
> **Naismith is not primarily an interview agent.**
>
> Naismith is the user's general-purpose personal AI operating system: one
> persistent, governed interface that remembers, reasons, coordinates tools,
> delegates work to outside AI agents, and helps the user operate across
> business, research, planning, coding, projects, learning, decisions, and
> personal operations.

---

## 0. Immediate instruction to Claude

Before writing code:

1. Inspect the repository and current branch.
2. Read this file, `README.md`, and the Constitution.
3. Treat the definition in this handoff as authoritative over the older
   interview-centered product language.
4. Do not delete working governance code merely because the product framing
   changed.
5. Do not begin voice, interviews, simulations, or broad autonomous tooling yet.
6. First preserve and merge the correctness fixes already on the current Claude
   branch.
7. Build the smallest general-purpose vertical slice that proves the new product
   definition.
8. Keep every change reviewable, tested, reversible, and free of secrets or
   private user data.

For every major change, report:

- what changed;
- why it is required by this handoff;
- tests run and actual results;
- what remains unbuilt;
- risks, assumptions, and decisions requiring the owner.

---

# PART I — CORRECT PRODUCT DEFINITION

## 1. What Naismith is

### 1.1 One-sentence definition

**Naismith is a constitutionally bounded personal AI operating system that gives
the user one continuous interface, one governed memory, and one control layer
for using the best available AI models, agents, tools, and applications.**

### 1.2 The product hierarchy

Naismith itself is the continuity and control system. It is not merely one model.

The hierarchy is:

1. **The user** — the final authority.
2. **The Naismith Constitution and policy kernel** — the rules governing every
   model, agent, tool, memory operation, and external action.
3. **Naismith identity and continuity** — the stable interface, preferences,
   permissions, context, and operating history presented to the user.
4. **Legend Vault** — the user's raw-first, portable, auditable long-term record
   and knowledge system.
5. **The Naismith runtime** — plans, routes, delegates, retrieves, combines, and
   returns work.
6. **External AI agents and models** — specialists Naismith may use when
   authorized.
7. **Tools and connected applications** — systems that provide data or perform
   approved actions.
8. **Skills and workflows** — reusable procedures for business, research,
   planning, coding, interviews, learning, and other domains.

### 1.3 What the name does and does not mean

The name references James Naismith and may inspire language such as "floor
general," but the application is **not basketball-focused**. Basketball must
not shape the feature set, information architecture, market positioning, or
default workflows unless the user explicitly chooses a basketball task.

### 1.4 Naismith is broader than a chatbot

Naismith should eventually:

- hold continuous text and voice conversations;
- preserve accessible source material and reasoning through Legend Vault;
- retrieve relevant context with visible provenance;
- maintain governed memory and user-correctable preferences;
- coordinate outside AI agents and models;
- compare multiple agents on the same task;
- run specialist-agent teams under one plan;
- use connected tools with explicit permissions;
- organize projects, decisions, tasks, files, and ongoing work;
- simulate options and evaluate proposed changes;
- support reusable domain workflows;
- explain what it knows, where it came from, which agent produced it, what it
  did, and what remains uncertain.

### 1.5 Interviews are one optional workflow

Interview preparation, mock interviews, structured interviews, scoring, and
simulation remain possible future modules. They are not the core product and
must not dominate the architecture.

Interview-specific rules apply only when an interview or evaluation workflow is
active. The same is true for any future vertical module.

---

## 2. Core product pillars

### 2.1 Constitution and policy kernel

The existing Constitution remains the highest authority.

All external agents are subordinate to Naismith's policy boundary. An outside
agent may suggest a plan, but it cannot grant itself permissions, write memory,
perform consequential actions, or alter Naismith's governing rules.

The Constitution must be reviewed later for language that accidentally implies
Naismith is primarily an interview system. Do not silently rewrite it. Prepare
a versioned amendment proposal and constitutional tests for owner review.

### 2.2 Legend Vault — the memory brain

Legend Vault is a permanent core requirement.

It must remain:

- raw-first;
- immutable at the source-record layer;
- portable and model-agnostic;
- user-controlled;
- permission-based;
- auditable;
- inspectable in ordinary files;
- separated into raw records and derived intelligence.

The raw record may include authorized text, visible voice transcripts, links,
images, files, screenshots, tool outputs, and other accessible source material.
Derived summaries, memories, entities, embeddings, and recommendations sit on
top and never replace or silently rewrite the source.

Naismith's intelligence layer may retrieve from and reason over Legend Vault,
but no model or agent may mutate the authoritative raw archive.

The separate `Legend-Vault` repository remains a related component. It may act
as an upstream capture/import and integrity layer. Do not replace it with a
generic memory database.

### 2.3 General-purpose runtime

The runtime is Naismith's execution body. It should:

- understand the user's objective;
- break work into bounded tasks;
- select the right model, agent, skill, or tool;
- request permission where required;
- track state and budgets;
- preserve provenance;
- stop on uncertainty, policy conflict, or exhaustion;
- combine results without hiding disagreement;
- return control to the user.

OpenClaw may be evaluated as a possible shell or body. It is not automatically
adopted and must not replace Legend Vault or the Constitution.

Anima may be evaluated as a continuity or internal-state component. Any adopted
state must remain inspectable, bounded, and subordinate to governed memory.

### 2.4 Agent Access Fabric

**This is a core platform requirement.**

Inside the Naismith app, the user should be able to access and coordinate any
AI model or agent that is technically compatible, officially accessible, and
authorized by the user.

The product aspiration is broad market access. The engineering contract is:

> Naismith supports any provider or agent for which a lawful, supported,
> permissioned connection can be implemented. It does not bypass provider
> restrictions or pretend unsupported access exists.

Naismith must not hard-code itself around one model provider.

---

# PART II — UNIVERSAL AI AGENT ACCESS

## 3. Access methods

Naismith should support the following connection classes.

### 3.1 Native model API

For providers exposing an official inference API.

Examples of capabilities:

- text generation;
- image understanding;
- audio;
- structured output;
- tool calling;
- embeddings;
- batch jobs.

### 3.2 Native agent API

For products exposing a persistent agent, coding agent, research agent, or job
API rather than only raw model inference.

Naismith should preserve the difference between a model and an agent. An agent
may have its own tools, files, state, job lifecycle, and permissions.

### 3.3 OAuth or official application connector

For services that authorize Naismith through OAuth, a GitHub App, an installed
application, or another official consent mechanism.

### 3.4 MCP connector

Model Context Protocol servers may expose tools, resources, or prompts.
Every MCP capability still passes through Naismith's schema validation,
authorization, data-minimization, audit, and confirmation layers.

### 3.5 Local agent or command-line bridge

For user-installed agents and local models that can be invoked through a
controlled local process.

Requirements:

- explicit installation and registration;
- fixed executable or service identity;
- scoped filesystem and network access;
- bounded runtime;
- captured stdout/stderr or normalized events;
- visible cancellation;
- no hidden persistence.

### 3.6 Provider-native job handoff

Some agents operate inside another platform rather than through a general API.
GitHub coding agents are an example of work that may occur through repository
issues, pull requests, jobs, or platform-native controls.

Naismith may create and monitor such work only through supported permissions and
with clear attribution.

### 3.7 User-mediated handoff

When a provider offers no supported programmatic integration, Naismith may:

- prepare a complete prompt or task package;
- open or deep-link to the provider where supported;
- export the necessary files;
- let the user submit the task;
- re-import the result with provenance.

This is a valid fallback. Naismith must not scrape private sessions, steal
cookies, automate around access controls, or violate a provider's terms.

### 3.8 Unsupported or unavailable

If no lawful supported connection exists, Naismith must say the agent is not
currently callable inside the app. It may still prepare a manual handoff.

---

## 4. Subscription, entitlement, and billing reality

The user currently has ChatGPT, Claude, and GitHub subscriptions. These are
valuable access entitlements, but consumer subscriptions do not automatically
become API credentials inside Naismith.

Official provider documentation confirms:

- ChatGPT and the OpenAI API are billed and managed separately.
- Claude paid plans and the Anthropic API Console are separate products.
- GitHub Copilot access and GitHub API or coding-agent permissions depend on the
  specific plan, repository, organization, token, app, and enabled capability.

Therefore Naismith needs an **Entitlement Registry**, not a simple "subscription
exists" checkbox.

Each connection record should track:

- provider;
- product or agent;
- access method;
- account identity;
- subscription or seat status where discoverable;
- API or OAuth credential reference;
- permitted scopes;
- available capabilities;
- data-use restrictions;
- workspace or repository restrictions;
- rate limits;
- cost model;
- user budget;
- credential expiry;
- last successful capability check;
- disabled or revoked status.

Secrets never enter source control, Legend Vault notes, ordinary logs, model
prompts, or handoff documents.

---

## 5. Provider and agent architecture

### 5.1 Required interfaces

Use separate interfaces rather than one vague provider class.

```python
class ModelProvider:
    async def generate(self, request: ModelRequest) -> ModelResponse: ...

class AgentProvider:
    async def submit(self, task: AgentTask) -> AgentJob: ...
    async def status(self, job_id: str) -> AgentJobStatus: ...
    async def cancel(self, job_id: str) -> None: ...
    async def collect(self, job_id: str) -> AgentResult: ...

class ToolConnector:
    async def list_capabilities(self) -> list[Capability]: ...
    async def invoke(self, call: ToolCall) -> ToolResult: ...

class ContextProvider:
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult: ...
```

The exact names may change, but model inference, persistent agents, tools, and
context retrieval must not be collapsed into one untyped adapter.

### 5.2 Agent manifest

Every model or agent should publish a normalized manifest containing:

- stable ID and provider;
- display name;
- kind: model, agent, tool, local runtime, or user-mediated;
- supported modalities;
- capability tags;
- context and file limits;
- available tools;
- whether it can create side effects;
- authentication method;
- data classifications it may receive;
- retention or training restrictions when known;
- price and rate-limit metadata;
- latency and reliability observations;
- current health;
- version;
- terms or connection notes;
- provenance requirements.

### 5.3 Capability router

The router chooses among approved agents based on:

1. explicit user choice;
2. task capability requirements;
3. data sensitivity;
4. permission scope;
5. quality evidence;
6. cost budget;
7. latency;
8. reliability;
9. context or file limits;
10. provider availability.

The user must always be able to pin a specific agent.

Automatic routing must disclose which provider was selected and why.

### 5.4 Collaboration modes

Naismith should eventually support:

- **Direct mode** — one chosen model or agent.
- **Best-fit mode** — Naismith selects one approved provider.
- **Compare mode** — multiple agents answer independently.
- **Council mode** — specialists analyze different parts, then a synthesis step
  combines results.
- **Challenge mode** — one agent critiques another.
- **Handoff mode** — one agent produces a structured package for another.
- **Coding mode** — coordinate Claude Code, OpenAI/Codex-class coding tools,
  GitHub-native agents, tests, review, and repository actions.
- **Fallback mode** — move to an approved alternate provider after a failure.

No agent may secretly spawn additional agents outside the registered runtime.

### 5.5 Provenance

Every delegated result records:

- task ID;
- requesting user and workspace;
- sending Naismith component;
- provider and agent/model ID;
- version;
- prompt or task-package version;
- context sources shared;
- tools authorized;
- start and end time;
- cost or usage;
- result digest;
- errors;
- human approvals;
- downstream synthesis lineage.

When results conflict, preserve the conflict. Do not flatten disagreement into a
false single answer.

---

# PART III — DATA, SECURITY, AND AUTHORITY

## 6. Data-sharing boundary

Before sending data to an outside agent, Naismith should determine:

- what minimum data the task requires;
- whether the provider is approved for that data class;
- whether the user granted the required scope;
- whether raw Legend Vault records are necessary;
- whether redaction or summarization can reduce exposure;
- whether the provider retains or trains on submitted data;
- whether the task can run locally instead.

For sensitive delegations, the app should show a preview of the provider, data
categories, files, permissions, expected cost, and external actions.

### 6.1 Default rules

- No outside agent receives the whole Legend Vault by default.
- Retrieval is scoped to the minimum relevant blocks.
- Read and write authority are separate.
- Model output is not authorization.
- Provider credentials are stored in a secret manager or operating-system
  credential store.
- Consequential actions require explicit approval.
- A provider failure must not weaken policy.
- Removing a connection revokes future use immediately.

## 7. Cost and observability

Naismith must track cost, token usage, latency, failures, and routing decisions
per provider, agent, task, user, workspace, and project.

Promptrace may be evaluated as an observability and token/cost package. Adoption
must not make the core dependent on a proprietary telemetry service.

Required controls:

- per-request estimate when available;
- per-agent and per-provider limits;
- per-workflow budget;
- daily and monthly caps;
- alert before a hard cap;
- cancellation;
- no silent paid upgrade or purchase;
- cost shown in the final task record.

Docguard may be evaluated as an intake-security layer for documents and
retrieval. It does not replace Naismith's policy kernel.

---

# PART IV — USER EXPERIENCE

## 8. Main application surfaces

Naismith should eventually provide:

### 8.1 Home / command center

- ask anything;
- continue ongoing work;
- view active projects and jobs;
- choose or inspect the agent route;
- see pending approvals;
- see important memory or source context;
- resume previous decisions.

### 8.2 Agent directory

- connected agents and models;
- capabilities;
- account and entitlement status;
- cost;
- data permissions;
- health;
- connect, disable, or revoke controls.

### 8.3 Task workspace

- objective;
- plan;
- subtasks;
- assigned agents;
- shared context;
- tool calls;
- costs;
- results;
- conflicts;
- approvals;
- final synthesis;
- export to Legend Vault.

### 8.4 Legend Vault

- raw records;
- derived notes;
- provenance;
- search and retrieval;
- corrections;
- memory proposals;
- deletion and export;
- connection to projects and decisions.

### 8.5 Projects and decisions

- goals;
- constraints;
- evidence;
- alternatives;
- decisions and reasons;
- next actions;
- agents involved;
- source history;
- reversals and updates.

### 8.6 Skills and workflows

Reusable skills may cover business research, planning, coding, analytics,
learning, document work, interviews, simulations, and other areas. A skill is a
bounded procedure, not the identity of Naismith.

---

# PART V — CORRECTED DELIVERY PLAN

## 9. Current repository state

Verified through GitHub on July 21, 2026:

- Repository: `t86sb9s75d-star/Naismith`.
- `main` contains merged PR #1 at merge commit `db72769`.
- The existing Claude development branch contains two additional commits:
  - `404ee5e` — four Copilot correctness fixes plus regression tests.
  - `a816f53` — `/raw` skill and repository-state collector.
- Those two commits are ahead of `main`.
- No follow-up pull request was open when this handoff was prepared.
- CI for the follow-up branch was not independently confirmed through the
  available connector and must be checked before merge.

What runs today:

- FastAPI service;
- deterministic external policy check;
- mock model adapter;
- in-memory sessions and turns;
- append-only JSONL audit events;
- basic React text conversation UI;
- shared JSON Schemas;
- constitutional tests;
- CI and bounded stress harness.

What does not run today:

- a real model;
- an Agent Access Fabric;
- provider account connections;
- durable application persistence;
- Legend Vault retrieval;
- governed memory;
- general-purpose projects or task planning;
- external tools;
- voice;
- interview workflow;
- simulation lab.

## 10. Phase 0.5 — correct and stabilize the baseline

Before expanding product scope:

1. Verify the current follow-up branch CI.
2. Review and merge the four correctness fixes.
3. Correct `/raw`:
   - conditional sections rather than mandatory empty scaffolding;
   - explicit secret, credential, private-key, and unnecessary-PII exclusions;
   - preserve load-bearing raw context without blindly reproducing every token.
4. Update README and governing documentation to the general-purpose definition.
5. Add a product-definition regression check so interview-centered language
   cannot silently return to the top-level description.
6. Do not merge private raw handoff files into the public repository.

Exit:

- baseline tests green;
- corrected product definition is prominent;
- current branch state is clean and reviewable;
- no false claim that Naismith is already a general-purpose working agent.

## 11. Phase 1 — persistent general-purpose text core

Build the smallest real Naismith experience:

- authenticated owner identity;
- workspace and project records;
- durable Postgres sessions, turns, tasks, and audit events;
- one real approved model provider;
- provider-independent request and response types;
- user can explicitly select the provider;
- basic capability and entitlement registry;
- task records with provenance and cost;
- general-purpose text UI;
- safe failure and cancellation.

Multi-tenant boundaries should be implemented correctly if the hosted app will
support multiple users, but the product experience should remain centered on
the owner's personal AI workspace. Do not let enterprise tenancy work replace
the core user experience.

Exit:

- the user holds a persistent real-model conversation;
- the selected provider is visible;
- every turn has provider, model, version, policy, and audit metadata;
- workspace isolation tests pass;
- a restart does not lose the conversation;
- no external side-effect tools.

## 12. Phase 2 — Agent Access Fabric v1

Start with the providers the user already uses:

1. OpenAI connection.
2. Anthropic connection.
3. GitHub connection and supported coding-agent workflows.

Important:

- Consumer subscriptions do not imply API access.
- Implement official API, OAuth, GitHub App, MCP, CLI, or user-mediated methods
  according to each provider's supported surface.
- Do not scrape consumer web sessions or copy browser cookies.
- Connection setup must clearly show any separate API billing.

Build:

- provider and agent manifests;
- entitlement registry;
- capability discovery;
- secret references;
- health checks;
- explicit provider selection;
- best-fit router;
- compare mode;
- cost and usage records;
- provider revocation;
- normalized errors and fallback.

Exit:

- the user can connect at least two distinct providers through official methods;
- choose either one;
- send the same task to both;
- see separate results, costs, and provenance;
- disconnect either provider cleanly.

## 13. Phase 3 — Legend Vault read-only brain

Build:

- integration contract with the existing Legend Vault system;
- read-only connector;
- raw record and derived-note distinction;
- metadata validation;
- incremental indexing;
- hybrid retrieval;
- block-level citations;
- read grants;
- prompt-injection tests;
- Docguard evaluation;
- cross-workspace isolation.

Exit:

- Naismith answers from approved Vault content with visible sources;
- retrieved text cannot change policy or grant tools;
- the raw archive remains unchanged;
- the user can see exactly what context was sent to each outside agent.

## 14. Phase 4 — governed memory

Build:

- memory proposals;
- provenance;
- confirmation policy;
- conflict and precedence handling;
- inferred-memory labeling;
- inspection and correction;
- deletion path;
- retrieval integration;
- memory audit events.

Exit:

- no durable memory without provenance;
- the user can inspect, correct, reject, and delete;
- memories never silently override current instructions.

## 15. Phase 5 — tools and external action

Build a deny-by-default tool router with:

- typed schemas;
- grants;
- read/write separation;
- previews;
- confirmation;
- idempotency;
- budgets;
- cancellation;
- audit;
- kill switches.

Start with low-risk, reversible actions. Do not allow an outside agent to call
tools directly around Naismith's policy layer.

## 16. Phase 6 — voice and multimodal interface

Add streaming speech, interruption, transcript correction, visible consent,
text fallback, and audio-minimized retention.

Voice is an interface to the general-purpose operating system, not a separate
product identity.

## 17. Phase 7 — reusable skills and workflows

Build a registry of bounded, testable workflows. Interviews may be introduced
here as one optional module beside business, coding, research, planning,
learning, and project workflows.

## 18. Phase 8 — evaluation and simulation

Use controlled simulation to evaluate routing, prompts, skills, safety, cost,
and quality.

Simulation can propose changes but cannot deploy or promote itself.

---

# PART VI — NON-GOALS AND FAILURE MODES

## 19. Naismith is not

- a basketball application;
- an interview application with unrelated features attached;
- a wrapper that simply forwards prompts to one vendor;
- a system that claims every consumer subscription is an API;
- a browser-session scraper;
- a tool for bypassing provider terms, payment, access, or permissions;
- an unbounded autonomous agent;
- a black box that hides which provider handled a task;
- a memory collector that stores everything without permission;
- a system that lets external agents write directly to the authoritative Vault;
- a system that silently spends money;
- a system that converts model output into authority;
- a product that sacrifices portability to one provider.

## 20. Major traps for Claude

1. Do not continue optimizing the repository around interviews.
2. Do not delete interview code that does not exist; simply move interviews to a
   later optional workflow.
3. Do not confuse Legend Vault with an ordinary vector database.
4. Do not treat the existing `Legend-Vault` repository as disposable.
5. Do not claim "access to any AI agent" means bypassing unsupported access.
6. Do not use consumer browser credentials as application secrets.
7. Do not put real API keys, transcripts, raw handoffs, or private files in this
   public repository.
8. Do not let an outside agent bypass Naismith policy.
9. Do not build twenty provider adapters before one end-to-end connection works.
10. Do not start voice before the text runtime, persistence, provider boundary,
    and provenance are correct.
11. Do not report tests as passed unless they were actually executed.
12. Do not start a broad rewrite when a small migration preserves working code.

---

# PART VII — OWNER-DEFINED PRODUCT TRUTHS

These are settled unless the owner changes them:

- Naismith is a broad personal AI agent/system.
- The name alone is basketball-inspired.
- Legend Vault is a permanent core requirement.
- The raw record and the intelligence layer are separate.
- Naismith should access and coordinate outside AI agents where officially and
  technically possible.
- OpenAI, Anthropic, and GitHub are first-priority connections because the user
  already uses those ecosystems.
- Naismith must remain provider-independent.
- External agents are specialists under Naismith, not replacements for it.
- Interviews are a workflow, not the product.
- Constitution, permissions, auditability, provenance, reversibility, and human
  control remain non-negotiable.
- Build narrow vertical slices before broad capability lists.
- Claims about repository state, tests, access, or completed actions must be
  verified.

---

# PART VIII — FIRST TASK FOR THE NEXT CLAUDE SESSION

The next Claude session should:

1. Verify branch, commit, PR, and CI state.
2. Read the four Copilot fixes and their tests.
3. Review `/raw` against the later conditional-section and secrets-handling
   requirements.
4. Update public documentation to the product definition in this handoff.
5. Keep the Constitution unchanged in that documentation-only correction unless
   a separate versioned amendment is proposed.
6. Produce a small PR plan for:
   - baseline fixes and corrected docs;
   - then persistent general-purpose Phase 1;
   - then Agent Access Fabric v1.
7. Stop before adding a real API key or incurring paid API usage.
8. Report exact decisions the owner must make, including:
   - initial deployment model;
   - first authentication method;
   - whether OpenAI or Anthropic is the first real provider;
   - API budget;
   - how the existing Legend Vault repository connects to Naismith;
   - which GitHub coding-agent surface is available under the user's plan.

## Definition of done for the correction

A new developer reading only the repository should understand, without asking:

- Naismith is a general-purpose personal AI operating system.
- It is not basketball-focused.
- It is not primarily an interview product.
- Legend Vault is its governed long-term knowledge foundation.
- Naismith coordinates multiple outside agents through supported connections.
- subscriptions and API entitlements are different;
- the current code is only a governance-first text prototype;
- the next build is a persistent general-purpose core, followed by the Agent
  Access Fabric.
