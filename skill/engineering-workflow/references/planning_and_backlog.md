# Planning And Backlog

Use this canonical reference whenever work creates or updates `PLANS.md` or `docs/codex/TASKS_BACKLOG.md`.

Stable contract markers:

- `plan_schema_version: 1`
- `repo_change_plan: full_required`
- `plan_mode_exit_materialization: required`
- `direct_execution_materialization: required`
- `compressed_active_plan: forbidden`

## Contents

1. Planning Boundary
2. Materialization Gates
3. Plan Origin
4. Requirement Traceability
5. Full Active Plan Schema
6. Plan Fidelity Check
7. Work Queue And Resume Point
8. Resume And Milestone Reconciliation
9. Pre-Commit Closure Gate
10. Backlog Lifecycle
11. Completed Work Lifecycle

## Planning Boundary

Any task that changes repository state requires a full active plan in `PLANS.md` before the first implementation, configuration, test, template, generated-artifact, local-configuration, repository-metadata, or workflow-documentation change.

Repository state includes tracked files, untracked files, repository metadata, generated artifacts, local configuration, and repository runtime state. A short chat plan, private todo list, Plan Mode UI, or final summary does not replace `PLANS.md`.

The only exception is a fully read-only action that changes none of those states. Read-only inspection may use `read_only_verify` without creating a plan.

Do not introduce a lightweight or small-task bypass. Conservative execution protects existing ownership and avoids unrelated expansion; it does not reduce the user's requested outcome because the task is large or inconvenient.

## Materialization Gates

### Plan Mode Exit Materialization Gate

When Plan Mode produced an approved plan:

1. Treat the Plan Mode plan as ephemeral until it is stored in `PLANS.md`.
2. Make creation or complete update of the active plan the first repository write after leaving Plan Mode.
3. Preserve every approved outcome, requirement, constraint, non-goal, source URL, user answer, locked decision, rejected alternative, ordered step, validation requirement, recovery requirement, unresolved risk, and exact resume point.
4. Do not replace the approved structure with a few summary bullets.
5. Run the Plan Fidelity Check.
6. Begin implementation only after fidelity passes.

### Direct Execution Materialization Gate

When Plan Mode was not used:

1. Analyze the user request and available repository evidence.
2. Create or fully update the active plan before any other repository write.
3. Preserve the complete requested scope and every explicit source or constraint.
4. For a large structured prompt, assign stable requirement IDs and map them to work and validation.
5. Run the Plan Fidelity Check before implementation.

Plan Mode is one possible plan source, not a prerequisite for this skill. The same full-plan contract applies in CLI, IDE, app, direct execution, resume, and external handoff flows.

## Plan Origin

Record exactly one `Plan Origin` value:

- `plan_mode_approved`
- `direct_execution`
- `resumed`
- `backlog_promotion`
- `external_handoff`

Do not infer `plan_mode_approved` merely because a plan exists. Use the origin that describes how the active plan entered the repository.

## Requirement Traceability

Assign a stable ID such as `REQ-001` to every explicitly requested outcome. Keep every requirement in the active plan until closure, including completed requirements.

For each ID record:

- complete requirement summary
- source: user prompt, approved Plan Mode decision, external specification, or repository rule
- owning work-queue item or items
- acceptance or validation criteria
- current status: `pending`, `in_progress`, `blocked`, `done`, `superseded`, or `out_of_scope`

Use `superseded` or `out_of_scope` only with the user decision or higher-priority reason that changed the requirement. Never remove a requirement merely because it is done.

Every requirement ID must appear in the work queue, and every acceptance criterion must map to verification. If the task declares external sources, retain their URLs under `Inputs And Sources`.

## Full Active Plan Schema

Every active repo-changing plan contains at least:

- `Goal`
- `Plan Origin`
- `Requested Scope`
- `Requirement Traceability`
- `Explicit Non-Goals`
- `Constraints`
- `Inputs And Sources`
- `User Decisions And Answers`
- `Completed Baseline State`
- `Current Work Queue`
- `Locked Decisions`
- `Verification`
- `Latest Validation Results`
- `Risks And Recovery`
- `Resume Point`
- `Plan Fidelity Check`
- `Reconciliation Check`
- `Pre-Commit Closure`
- `Handoff Notes`

The active plan must be sufficient for a future agent to continue without reconstructing requirements or decisions from chat. Keep verified baseline facts so they are not repeatedly audited, but verify drift-prone facts when cheap and relevant.

## Plan Fidelity Check

Before implementation and after any material scope change, confirm all of the following in the plan:

- every agreed outcome appears in `Requirement Traceability`
- every source URL is retained
- every user answer and locked decision is retained
- no requirement was silently shortened or dropped
- work-queue items cover every requirement ID
- validation covers every acceptance criterion
- explicit non-goals do not contradict requested scope
- the resume point names the first unfinished safe action
- the durable plan is not a compressed retelling of a more detailed approved plan

If any item fails, stop implementation and repair the plan first.

## Work Queue And Resume Point

Use ordered IDs such as `WQ-01`. Each work item must:

- own a bounded outcome or subsystem
- list the requirement IDs it covers
- be independently checkable
- state its current status
- include validation or documentation follow-up when applicable

The first non-done work item is the current work. The `Resume Point` must name that item and its exact next safe action. Avoid vague items such as "finish implementation" or "clean up docs."

Do not compress active, blocked, pending-validation, or handoff-relevant detail into a completed summary or one-line queue. If scope must change, record the reason and update traceability before implementation continues.

## Resume And Milestone Reconciliation

After context compaction, interruption, resume, milestone closure, subagent handoff, or a new Codex session:

1. Open `PLANS.md` first.
2. Use its verified baseline instead of restarting with a broad audit.
3. Inspect the working tree and changes since `Last Updated`.
4. Reconcile requirement statuses, current milestone, first unfinished queue item, resume point, backlog promotion state, latest validation result, and working tree.
5. Reconcile `done`, `in_progress`, `blocked`, `promoted`, `superseded`, and `out_of_scope` statuses across workflow files.
6. Continue only from the first safe unfinished action.

Completed sections must not retain stale current-milestone, next-work, resume, active-blocker, or open-status text. If follow-up remains real, represent it as an unfinished requirement, backlog item, external issue, or explicit follow-up link.

Do not reconstruct an existing durable plan from model memory.

## Pre-Commit Closure Gate

Before staging or committing repo-changing work:

- reconcile the active plan and any promoted backlog item with the state the commit will create
- if the task completes, set the plan to `done` or replace it with a truthful `Recently Completed` entry
- if work remains, keep the plan open with the first unfinished work item, exact resume point, latest validation, and risks
- if blocked, record the blocking condition, owner, recovery attempts, and next safe action
- do not commit completed work while its plan claims `planned` or `in_progress`
- do not close a task merely because a validation command ran; every requirement and acceptance criterion must be reconciled

## Backlog Lifecycle

Use `docs/codex/TASKS_BACKLOG.md` only for future or inactive work. A backlog item requires an activation trigger, next safe action, and exit criteria.

When work starts:

1. Mark the backlog item `promoted`.
2. Link it to a full active plan before implementation.
3. Keep execution detail in `PLANS.md`, not duplicated in the backlog.

After active work closes, remove the backlog item by default when durable information lives elsewhere. Keep a `done` item only when the record itself is a useful audit trail. Archive only for future-useful rationale, tracker mapping, repeated deferral history, or explicit retention.

## Completed Work Lifecycle

Keep full detail while work is active, blocked, pending validation, or handoff-relevant. After genuine completion:

- move durable rules and decisions to their canonical owners
- preserve required validation and follow-up evidence
- compact the active plan into one `Recently Completed` entry by default
- archive the full plan under `docs/archive/plans/YYYY-MM-DD-<slug>.md` only when its rationale or validation matrix remains useful
- remove stale completed detail when canonical docs, tests, issues, or backlog already preserve the useful information
- keep at most 10 recent entries by default

The backlog and `PLANS.md` are execution state, not journals of every completed step.
