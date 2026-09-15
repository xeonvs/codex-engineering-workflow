# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Context Discipline And Bounded Delegation 0.9.6

Status: active
Owner: root
Last Updated: 2026-09-15

### Goal

Make root context, durable repository knowledge, compact worker handoffs, and bounded tool-heavy execution explicit in this repository and in workflow-generated target instructions, then publish engineering-workflow 0.9.6 and synchronize xeonvs-engineering 1.0.6.

### Plan Origin

plan_mode_approved

### Requested Scope

- Apply the approved context-discipline plan to the engineering skill and xeonvs-engineering, including their own project instructions and the target templates they distribute.
- Use razor-ai/codex-orchestration only as a critically reviewed source of general principles; do not copy it or depend on its APIs.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Root retains intent, plan, integration, and current working state while bounded workers receive self-contained context and return compact evidence. | User requirements and approved plan | WQ-01 | Orchestration scenarios and template review. | done |
| REQ-002 | Transient evidence and durable knowledge are distinguished, and recovery uses PLANS.md, current repository state, and relevant durable artifacts. | User requirements, approved plan, and current-session audit | WQ-02 | Planning scenarios, bounded-output behavior, and generated target inspection. | done |
| REQ-003 | Predictable tool-heavy stages use existing bounded execution mechanisms without a new orchestration framework or API dependency. | User requirements and approved plan | WQ-03 | Orchestration policy tests and semantic review. | done |
| REQ-004 | Versioned source and generated plugin bytes reach 0.9.6 with safe migration of prior pristine target instructions. | Approved delivery plan | WQ-04 | Migration matrix, package parity, full and security gates. | done |
| REQ-005 | xeonvs-engineering imports 0.9.6, publishes 1.0.6, and managed Codex/Claude installations update. | Approved delivery plan | WQ-05 | Provenance/byte validation, release and installation readback. | pending |

### Explicit Non-Goals

- Add codex-orchestration, a scheduler, mandatory advisor, fixed worker count, required PTC, Responses-only APIs, or changes to tgrep-search 1.0.3.
- Change model profiles, permissions, plan/instruction schema versions, or safety boundaries.

### Constraints

- Keep detailed invariants under one canonical owner and keep AGENTS files route-oriented.
- Preserve customized target instructions; migrate only known pristine local templates automatically.
- Do not monitor CI; use local release evidence and one bounded remote readback where required.

### Inputs And Sources

- User-approved plan in the current task.
- https://github.com/razor-ai/codex-orchestration/blob/a1d9c546665c3253cdcaa8fe5c0c060199a6126c/plugins/codex-orchestration/skills/codex-orchestration/SKILL.md
- Current engineering-workflow 0.9.5 and xeonvs-engineering 1.0.5 releases.

### User Decisions And Answers

- 2026-09-15: The referenced skill is comparative material, not an authority or dependency.
- 2026-09-15: Apply the behavior both to the projects themselves and to principles configured through templates.
- 2026-09-15: Execute the approved plan immediately according to the new principles.

### Completed Baseline State

- [x] WQ-00 — Current references, templates, tests, versions, repository state, and external comparison skill inspected; no overlapping active plan or dirty worktree exists.

### Current Work Queue

- [x] WQ-01 — Implement and review REQ-001 orchestration and handoff rules. `done`
- [x] WQ-02 — Implement and review REQ-002 state, recovery, and bounded-output rules. `done`
- [x] WQ-03 — Implement and review REQ-003 bounded execution rules. `done`
- [x] WQ-04 — Implement version/migration/package changes and validate REQ-001 through REQ-004. `done`
- [ ] WQ-05 — Deliver source and marketplace releases and verify REQ-005. `in_progress`

### Locked Decisions

- Canonical detailed owners remain agent_orchestration.md and planning_and_backlog.md.
- Target project principles receive concise operational rules; AGENTS routes make those owners reachable; optional worker templates receive only role-specific handoff behavior.
- Context isolation is outcome-based and host-neutral; no fork/session field is required.

### Verification

- Behavioral tests for root/worker boundaries, self-contained packets, compact returns, transient/durable state, recovery sources, and host-neutral fallback.
- Prior-pristine migration and customized-owner preservation scenarios; generated source/package parity.
- Full maintainer gate, aggregate diff review, external plugin/Claude validation, and pre-push security gate.
- Marketplace tests, catalog/provenance verification, artifact and installed-version readback.

### Latest Validation Results

- 2026-09-15: Focused orchestration and planning tests passed. Upgrade migration tests passed after correcting their expected post-migration template and route ownership.
- 2026-09-15: Session audit found two avoidable context spikes: a 15,549-token aggregate diff result and a 6,605-token direct unittest result were truncated. Subsequent review uses selected hunks and the repository harness; the planning owner now requires bounded model-facing output and focused recovery after truncation.
- 2026-09-15: Direct root execution remains appropriate for the coupled edit/migration sequence; one independent semantic review received a self-contained read-only packet.
- 2026-09-15: Independent review found no material semantic defect. Its residual coverage concern was addressed by expanding the prior-pristine migration test across all four rendered AGENTS layouts plus a customized-owner case.
- 2026-09-15: Final full maintainer gate passed 9/9 stages, including all tests, structural validation, package parity, and whitespace checks. Codex plugin/skill validation and Claude plugin/marketplace validation passed.

### Risks And Recovery

- Risk: added prose creates bureaucracy for already-bounded work. Recovery: keep delegation conditional and make no new mandatory artifact for simple tasks.
- Risk: duplicated rules conflict across references and templates. Recovery: references own detail; templates carry only local operational behavior and links.
- Risk: customized targets are overwritten. Recovery: exact pristine fingerprints only; semantic review for customized owners.

### Resume Point

- Continue WQ-05 with source commit, security gate, PR merge, annotated 0.9.6 release, and downstream marketplace synchronization.

### Plan Fidelity Check

- [x] Both repositories, project instructions, distributed templates, releases, installation update, explicit exclusions, sources, and validation are preserved.
- [x] Every requested outcome maps to an ordered work item and acceptance evidence.

### Reconciliation Check

- [ ] Changed results and plan entries agree.

### Closure Gate

- [ ] Requirements and queue are terminal; applicable validation and delivery evidence are recorded.

### Post-Close Delivery

- Source PR/merge/tag/release and downstream marketplace import/PR/merge/tag/release are authorized by the approved plan. CI monitoring is excluded.

### Handoff Notes

- None.


## Recently Completed

- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](docs/archive/plans/2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
