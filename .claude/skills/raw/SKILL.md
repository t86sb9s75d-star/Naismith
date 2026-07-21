---
name: raw
description: >-
  Produce a COMPLETE, UNEDITED, lossless RAW HANDOFF of the current session — a
  full top-to-bottom memory/context dump so a fresh session or another agent can
  resume with total continuity. Captures the mission, every decision and its
  reasoning, every user instruction and preference, all files changed and
  commands run, current git/PR/CI state, open threads, gotchas, and explicitly
  flagged uncertainties. Use this whenever the user asks to "hand this off,"
  wants a handoff / memory dump / context dump / brain dump / brief for the next
  session or another agent, wants to capture everything before compacting,
  clearing, or ending, is running low on context, or types /raw — even if they
  never say the word "skill." Prefer this over writing a short summary: a raw
  handoff is lossless and faithful, not a summary.
---

# Raw Handoff

## What this is

A **raw handoff** is a complete, faithful dump of everything that matters in the
current session, written so that a recipient with **zero** shared context can
pick up exactly where this session left off and lose nothing.

**Three kinds of recipient, one hard rule.** The handoff may go to a fresh
session of yourself, to a **different agent**, or to a **subagent** you spawn
for a scoped slice of the work. None of them can see this conversation. So the
handoff must be **self-contained**: everything the recipient needs is written
down explicitly. No "the file we edited," no "as discussed," no pronouns
pointing back at a conversation they never saw — name the actual path, restate
the actual decision. If a claim depends on context that isn't in the document,
it isn't really in the handoff. (Subagents are the strictest test of this — see
"Handing off to a subagent" below.)

It is the opposite of a summary. A summary decides what to drop; a raw handoff
decides nothing away. The guiding instinct is **"when in doubt, keep it in."**

The user's mental model (their words): *"a complete unedited raw handoff of a
top-to-bottom memory of literally everything you can pull."* Honor that. The
failure mode to avoid is a tidy, lossy recap that reads well but silently drops
the decision, the reason, or the piece of state the next agent actually needed.

## The three principles

1. **Lossless over brief.** Include every load-bearing fact, decision, reason,
   and piece of state. Length is fine. What is *not* fine is omitting something
   the next agent would have to re-derive or re-ask. "Lossless" means no
   important information is lost — not that you transcribe every token of small
   talk. Preserve **exact wording** wherever paraphrase could mislead: the
   user's explicit instructions, names, identifiers, file paths, error text,
   commands, and numbers.

2. **Faithful — grounded in reality, never fabricated.** Your memory of the
   session can be stale or wrong. Do not report state from memory when you can
   *check* it. Pull the real git branch, the real commits, the real file list,
   the real PR/CI status using tools, and report what the tools actually say. If
   you cannot verify something, say so — never invent a commit hash, a test
   result, a file path, or a status.

3. **Flag uncertainty, don't paper over it.** Anything you're unsure about gets
   an explicit `⚠️ UNCERTAIN:` marker with what you'd need to confirm it. A
   handoff that admits its gaps is far more useful than one that hides them.

## Method — how to actually pull "everything"

Work in this order. Don't shortcut it.

1. **Re-read the whole session, top to bottom.** Start from the first message,
   not the last few turns. Reconstruct the full arc: what the user originally
   wanted, how it evolved, every course-correction and reversal. The reasoning
   *behind* decisions is the first thing lost to compaction and the most
   valuable thing to preserve — capture the "why," not just the "what."

2. **Verify current state with tools, not memory.** Run the bundled collector
   for a read-only repo/environment snapshot, then fold its real output into the
   handoff:

   ```bash
   bash "$SKILL_DIR/scripts/collect_state.sh"
   ```

   (`$SKILL_DIR` is this skill's directory.) It reports the working directory,
   git branch, upstream, remotes, short status, recent commits, and unpushed
   commits — or notes cleanly if it isn't a git repo. For anything it can't
   reach — open PRs and their CI status, background jobs, deploy state — pull it
   from whatever tools are available this session (GitHub tools, `gh`, etc.). If
   a piece of state can't be verified, mark it `⚠️ UNCERTAIN`.

3. **Inventory the concrete work.** List every file created, edited, or deleted
   with its path; every command run that mattered and its outcome; tests and
   their results; commits, PRs, artifacts, and their URLs/identifiers.

4. **Surface the soft knowledge.** Capture the user's stated preferences,
   constraints, things they explicitly rejected, decisions they've already
   made (so the next agent doesn't re-litigate them), and the gotchas /
   landmines discovered along the way.

5. **Name what's unfinished.** Open threads, parked work, TODOs, blocked items,
   and the questions currently awaiting the user.

## Output structure

Write the handoff to a file: `RAW_HANDOFF_<UTC-timestamp>.md` in the current
working directory (or a path the user specifies). Then tell the user the path.
Also offer to print it inline if they want it in the conversation.

Use this structure. Keep a section even if it's empty — write `(none)` so the
next agent knows it was considered, not forgotten.

```markdown
# RAW HANDOFF — <one-line mission> — <UTC timestamp>

## 0. Orientation
- Generated: <UTC timestamp>
- Working dir / repos in scope: <paths>
- Environment notes: <model, platform, sandbox, network — anything non-obvious>
- One-paragraph "where we are": what this session is doing and its current state.

## 1. Mission & current objective
The big picture — what we are ultimately trying to accomplish, and the specific
thing in flight right now.

## 2. Decisions made (with reasoning)
Chronological or grouped. For each: the decision, WHY, and any alternatives
rejected. Include reversals and course-corrections explicitly — "we first did X,
then the user changed it to Y because Z."

## 3. User instructions, preferences & constraints
What the user asked for (exact wording where it matters), their stated
preferences, hard constraints, and things they explicitly said NOT to do.
Decisions already settled — do not re-open these.

## 4. Work completed
Files created/edited/deleted (with paths), key commands and outcomes, tests/CI
results, commits, PRs, artifacts — concrete and verifiable. Prefer real
identifiers (SHAs, PR numbers, URLs) pulled from tools.

## 5. Current state (verified)
Git branch / upstream / status / recent + unpushed commits (from the collector).
Open PRs and their CI status. What's merged vs pending. Background jobs.
Environment specifics that matter for resuming.

## 6. Open threads & next steps
Unresolved decisions, parked work, TODOs, blocked items, and the exact questions
currently waiting on the user. What the next agent should do first.

## 7. Gotchas & landmines
Things that bit us, environment quirks, non-obvious constraints, and traps to
avoid. Save the next agent from repeating our mistakes.

## 8. Key references
Important paths, URLs (PR links, artifacts, dashboards), and identifiers, in one
place for quick lookup.

## 9. Uncertainties & gaps
Everything marked ⚠️ UNCERTAIN, plus anything outside your reach that the next
agent should verify independently. Be honest about what this handoff does not
know.
```

## Handing off to a subagent (a scoped brief)

A full session handoff is for resuming *all* the work. A subagent is different:
you're delegating one bounded slice, and it starts cold with only the brief you
hand it. Two failure modes to avoid. Dumping the entire session on a subagent is
noise — it buries the one task under context it doesn't need. But trimming too
hard is worse: a subagent missing a path, a constraint, or the definition of
done will guess, and guess wrong, because it wasn't here for the parts you left
out.

So when the target is a subagent, produce a **focused, self-contained** extract
rather than the whole document:

- **The exact task and its definition of done.** What to produce, and how both
  of you will know it's correct — concrete files to touch, expected outputs,
  and the tests or checks that must pass.
- **Only the decisions and constraints that bear on this slice** — restated in
  full, not referenced. Include the ones that say what *not* to do (the traps
  already discovered), since the subagent wasn't there when you hit them.
- **Explicit, absolute paths and identifiers.** A subagent does not inherit your
  working directory, your open files, or your shorthand. Give real paths
  (`/home/user/project/src/foo.py`, not "the module we changed"), real branch
  names, real PR numbers, real commands.
- **A pointer to the full handoff file** for anything beyond the slice, so the
  subagent can escalate rather than invent.

The check is the self-containment rule applied narrowly: could a subagent that
has read *only this brief* complete the task correctly without coming back to
ask you something you already knew? If not, add what's missing.

## Quality bar — what "done" looks like

Before handing it over, check it against the one question that matters:

> If I handed this document to a competent agent who had never seen this
> session, could they resume the work correctly without asking me anything that
> we already figured out?

If the answer is no, something load-bearing is missing — find it and add it.
Then sanity-check the three principles: is every state claim **verified** (or
flagged), is the **reasoning** behind decisions captured (not just the
outcomes), and are the **gaps** named honestly?

Finally: prefer completeness. If you catch yourself trimming a detail to make it
read cleaner, that's the summary instinct — resist it. Keep it in.
