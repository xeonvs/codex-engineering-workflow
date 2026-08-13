# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Complete Engineering Workflow 0.6.0 Publication

Status: active
Owner: root
Last Updated: 2026-08-13

### Goal

Move the fully validated 0.6.0 pull request into `main`, verify the resulting main-branch checks, close durable lifecycle state, and remove the merged feature branch.

### Plan Origin

direct_execution

### Requested Scope

- Confirm there are no unresolved review threads or failing checks.
- Mark PR #1 ready, merge it into `main`, validate the resulting remote and local main state, close this plan, and clean the merged branch.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | PR #1 is review-complete, ready, and merged into `main`. | Current user request | WQ-01 | PR state and merged SHA readback. | in_progress |
| REQ-002 | Final `main` checks and repository gates pass. | Current user request | WQ-02 | GitHub Actions and local validator readback. | pending |
| REQ-003 | Lifecycle is closed and merged feature refs are cleaned. | Current user request | WQ-03 | Compact plan, clean worktree, and ref readback. | pending |

### Explicit Non-Goals

- Do not create an unprecedented tag/GitHub Release or update the separately managed installed skill without an explicit request.

### Constraints

- Preserve the reviewed implementation commits and archived 0.6.0 implementation plan.
- Do not merge while any review thread or check is unresolved.

### Inputs And Sources

- User request on 2026-08-13 to drive the work to full completion.
- PR #1: `https://github.com/xeonvs/codex-engineering-workflow/pull/1`.

### User Decisions And Answers

- 2026-08-13: full repository publication completion is authorized.
- Installed-skill update remains a distinct operation requiring explicit authorization under local `AGENTS.md`.

### Completed Baseline State

- [x] WQ-00 — PR #1 has no comments, reviews, or unresolved threads; final head `c670fbe` is mergeable and has two successful checks.
- [x] WQ-00A — Repository history has no release tags or GitHub Releases; publication truth is the main branch and CI.

### Current Work Queue

- [ ] WQ-01 — Mark PR #1 ready and merge it. Covers REQ-001. `in_progress`
- [ ] WQ-02 — Verify remote/main CI and local gates. Covers REQ-002. `pending`
- [ ] WQ-03 — Compact lifecycle state and clean merged refs. Covers REQ-003. `pending`

### Locked Decisions

- Merge only after the plan-materialization commit is green.
- Keep installation and target-repository mutation outside this repository publication.

### Verification

- REQ-001: thread-aware review read, PR metadata, merge result.
- REQ-002: GitHub Actions conclusions, validator, lifecycle check, `git diff --check`.
- REQ-003: compact closure, final main/upstream equality, no feature refs, clean worktree.

### Latest Validation Results

- 2026-08-13: no review threads or comments; PR head `c670fbe` is mergeable with two successful `validate` checks.

### Risks And Recovery

- Risk: merge races a new review or failing check. Recovery: reread PR immediately before merge and stop on drift.
- Risk: lifecycle closure leaves a follow-up commit. Recovery: make one bounded main-branch closure commit, rerun CI, and verify exact refs.

### Resume Point

- Continue WQ-01 by committing this plan, waiting for green checks, marking the PR ready, and merging it.

### Plan Fidelity Check

- [x] Every agreed outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point names the first unfinished queue item.
- [x] This plan is not a compressed rewrite of a more detailed approved plan.

### Reconciliation Check

- [x] PR, branch, remote, checks, review threads, and current lifecycle state agree.
- [x] Completed publication records contain no stale unfinished state.

### Closure Gate

- [ ] Every in-scope requirement and queue item is terminal.
- [ ] Applicable validation is current for final `main`.
- [ ] Review, omission, and ref cleanup state are reconciled.
- [ ] Resume Point contains no future in-scope work.
- [ ] Compact disposition can be applied atomically.

### Post-Close Delivery

- The bounded lifecycle closure commit and its main-branch CI readback remain in scope; installation, tag, and GitHub Release remain out of scope.

### Handoff Notes

- Continue only from the first unfinished queue item and report exact PR, merge SHA, main SHA, checks, and refs.

## Recently Completed

- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
- [x] 2026-08-13: Completed Engineering Workflow 0.6.0; [full archived plan](docs/archive/plans/2026-08-13-engineering-workflow-0-6-0.md).
- [x] 2026-07-13: Completed implementation, review, security/privacy remediation, and validation for `engineering-workflow` 0.5.1; the [legacy schema-v1 plan](docs/archive/plans/2026-07-13-engineering-workflow-0.5.1.md) preserves its historical record.
