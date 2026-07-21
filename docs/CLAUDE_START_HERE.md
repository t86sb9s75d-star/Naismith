# CLAUDE — START HERE FOR NAISMITH

The old product framing is wrong.

## Correct definition

Naismith is a **general-purpose personal AI operating system and agent command
center**. It gives the user one continuous interface, one governed memory, one
permissions system, and one audit trail while coordinating outside AI models,
agents, tools, and applications.

- It is not basketball-focused; the name is only basketball-inspired.
- It is not primarily an interview agent.
- Interviews are one optional future workflow.
- Legend Vault is the permanent raw-first, portable memory and knowledge core.
- External agents are specialists under Naismith, not replacements for it.

## Mandatory new requirement

Inside the Naismith app, the user should be able to access and coordinate any AI
agent that is officially accessible, technically compatible, and authorized.

Support, in order of preference:

1. official model or agent APIs;
2. OAuth or application connectors;
3. MCP;
4. controlled local/CLI agents;
5. provider-native jobs such as GitHub issue/PR workflows;
6. user-mediated handoffs where no supported API exists.

Never scrape consumer sessions, steal cookies, bypass a provider's limits, or
pretend unsupported access exists.

The user has ChatGPT, Claude, and GitHub subscriptions. Do not assume those
subscriptions include API usage. Build an entitlement registry that records the
actual supported connection, scopes, billing, limits, and permissions.

## Read next

1. `docs/NAISMITH_CLAUDE_CODE_HANDOFF.md`
2. `constitution/NAISMITH_CONSTITUTION.md`
3. repository README
4. current branch history, tests, PR state, and CI

## Current implementation

The repository currently contains only a governance-first text prototype:
FastAPI, mock model, policy stub, sessions, audit log, React transcript UI,
contracts, tests, and CI.

The current Claude branch also contains four Copilot correctness fixes and the
`/raw` skill. Verify them and verify CI before merge.

## Next build sequence

1. Stabilize and correct documentation.
2. Persistent general-purpose text workspace with one real model.
3. Agent Access Fabric for OpenAI, Anthropic, and GitHub-supported workflows.
4. Legend Vault read-only retrieval.
5. Governed memory.
6. Tools and approved actions.
7. Voice and multimodal interface.
8. Reusable workflows, including interviews.
9. Controlled simulation and evaluation.

Do not build the whole roadmap at once. Propose small, tested, reviewable PRs.
