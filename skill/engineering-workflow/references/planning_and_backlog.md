# Planning And Backlog

Use this reference when creating or updating `PLANS.md` and `docs/codex/TASKS_BACKLOG.md`.

## Planning Depth

- Use `PLANS.md` for every task that changes repository state.
- Use a full active plan for every task that changes repository state while it is active, blocked, pending validation, or handoff-relevant.
- Preserve the user's requested scope, inputs and sources, constraints, locked decisions, current work queue, validation plan, latest validation result, and resume point.
- Do not compress active work into a single queue item or final-summary line.
- If a task must be narrowed, ask the user or record the explicit assumption and reason before implementation.
- Do not leave durable decisions only in chat.

## Active Plan Contract

An active plan must include enough state for a future agent to continue without reconstructing the work from chat:

- goal and requested scope
- constraints and explicit non-goals
- inputs, source files, references, issues, or prior artifacts
- completed baseline facts that should not be rechecked
- ordered current work queue with checked progress
- locked decisions with reasons
- verification commands or manual checks
- latest validation results
- handoff notes or the exact resume point

Conservative planning means preserving existing owners and avoiding unrelated expansion. It does not mean reducing the user's requested outcome because the work is large or inconvenient.

## Decomposition Rules

Good work-queue items are:

- ordered in the sequence they should be executed
- independently checkable
- scoped to one outcome or subsystem
- clear about validation or documentation follow-up
- small enough that a future agent can resume without re-planning the whole task

Avoid vague items such as "finish implementation" or "clean up docs". Replace them with the next concrete state change.

## Backlog Rules

- Use `docs/codex/TASKS_BACKLOG.md` only for future or inactive work.
- A backlog item needs an activation trigger, next safe action, and exit criteria.
- Keep detailed execution checklists out of the backlog until work starts.
- When work starts, mark the backlog item `promoted` and link or name the matching active plan in `PLANS.md`.
- If a backlog item has no activation trigger or next safe action, remove it or fold the durable lesson into `project_principles.md`.

## Completed Work Lifecycle

- Keep a full active plan in `PLANS.md` while there is active work, blocked work, pending validation, unresolved handoff, or imminent dependent work.
- When work is complete, move durable decisions into their canonical owner such as `AGENTS.md`, `docs/engineering/project_principles.md`, or project-specific docs.
- Collapse the completed active plan into one `Recently Completed` entry only after validation results, follow-up links, and handoff state are recorded.
- Keep at most 10 `Recently Completed` entries by default.
- Archive a full completed plan under `docs/archive/plans/YYYY-MM-DD-<slug>.md` only when it preserves future-useful rationale, migration decisions, validation matrices, or an explicit retention requirement.
- Delete stale completed detail instead of archiving it when the information is already captured in canonical docs, tests, backlog items, or issue trackers.

## Backlog Cleanup

- `planned`, `parked`, and `blocked` items stay only while their activation trigger and next safe action remain useful.
- `promoted` items should link to the active plan and should not duplicate that plan.
- After promoted work closes, mark the backlog item `done` only when the record itself remains useful.
- Remove completed backlog items when all useful information already lives in `PLANS.md`, an archive note, an issue tracker, or canonical docs.
- The backlog is not a journal of completed work.
