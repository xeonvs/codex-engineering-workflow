# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Astra Workflow Instruction Efficiency

Status: done
Owner: root
Last Updated: 2026-09-13

### Goal

Narrow runtime and template routing, reuse native tool results, make descriptor assessment optional, clarify validation authorization and check selection, and prepare version 0.9.5 as a reviewed PR.

### Plan Origin

direct_execution

### Requested Scope

- Implement the relevant findings from the instruction-efficiency audit and deliver one reviewable PR for this repository.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Scoped instruction corrections and consistent packaged content. | User audit and PR request | WQ-01 | Focused instruction/migration tests, paired semantic scenarios, full maintainer gate and package parity. | done |
| REQ-002 | Reviewed local PR preparation and explicit authorized delivery boundary. | User PR-only boundary | WQ-02 | Local evidence and final diff review; required push and PR readback tracked under Post-Close Delivery. | done |

### Explicit Non-Goals

- Other skills, global configuration, installed caches, merges, tags, releases, and PR monitoring.

### Constraints

- Full plan schema, model settings, approval and privacy guards, lifecycle semantics, and published tags remain unchanged.
- Root owns this plan; workers edit only assigned implementation files.

### Inputs And Sources

- User-approved audit findings and PR-only request.
- https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

### User Decisions And Answers

- 2026-09-13: Create PRs in the three named repositories; the user will merge and report back.

### Completed Baseline State

- [x] WQ-00 — Current repository instructions and clean baseline inspected; no active plan overlaps this task.

### Current Work Queue

- [x] WQ-01 — Implement and validate REQ-001. `done`
- [x] WQ-02 — Review final content and prepare REQ-002 delivery. `done`

### Locked Decisions

- Keep scope at minimal audit corrections; publication is limited to a branch and PR.

### Verification

- Focused instruction/migration tests, paired semantic scenarios, full maintainer gate, package parity, and pre-push security.
- Reconcile declared scope and actual diff before publication; read back PR URL and head only.

### Latest Validation Results

- 2026-09-13: Focused migration tests and full maintainer gate passed (9/9 stages), including all tests and package parity. Final semantic review completed; customized-owner adoption finding corrected and re-reviewed.
- Redacted security checks remain a required pre-push delivery gate, not evidence already claimed.

### Risks And Recovery

- Risk: instruction changes broaden authorization or hide missing evidence. Recovery: paired semantic review and existing safety gates.
- Risk: downstream bytes precede a released source. Recovery: preserve current provenance and use normal release-first synchronization later.

### Resume Point

- None; local implementation and review are complete. Authorized delivery is listed below.

### Plan Fidelity Check

- [x] Requirements, source URL, user decision, constraints, queue, validation and recovery are preserved.
- [x] No requirement is silently narrowed or removed.

### Reconciliation Check

- [x] Changed results and plan entries agree.

### Closure Gate

- [x] Requirements and queue are terminal; applicable validation and final review are recorded.

### Post-Close Delivery

- Branch push and PR creation are authorized delivery after local closure; they remain required for the user task. CI monitoring, merge, release and installation are outside this request.

### Handoff Notes

- None.


## Recently Completed

- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
