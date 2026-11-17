# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Align Target Route Guidance And Publish Patch

Status: active
Owner: root
Last Updated: 2026-11-17

### Goal

Make the generated router and its canonical lifecycle reference describe the same route format and point to runnable validation checks. Publish the correction through the existing source and marketplace release flow.

### Plan Origin

plan_mode_approved

### Requested Scope

Complete the requested proofreading of local instructions and shipped target templates. Deliver the corrected source and marketplace snapshots and verify native local installation.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Accurate generated router and canonical route contract | target template follow-up | WQ-01 | Render target, execute both documented checks and run full source gate | done |
| REQ-002 | Workflow patch, exact catalog import and active local delivery | approved release plan | WQ-02 | Reviewed source and catalog diffs, CI, security, exact package and install parity | in_progress |

### Explicit Non-Goals

- Unrelated workflow changes, tgrep changes, and autonomous updates to target repositories.

### Constraints

- Keep existing tags immutable. Self-review each commit slice and review the aggregate diff before each push. Run applicable privacy and secret scans.
- Keep machine-readable route markers and ownership compatible. Keep the existing target upgrade ownership boundary.

### Inputs And Sources

- Requested target-template proofreading and the instruction lifecycle and planning references in [workflow v0.11.0](https://github.com/xeonvs/codex-engineering-workflow/releases/tag/v0.11.0).
- [Marketplace v1.0.13](https://github.com/xeonvs/xeonvs-engineering/releases/tag/v1.0.13) is the installation baseline.

### User Decisions And Answers

- Check templates used in target repositories and issue the corrected packages through the established marketplace flow.

### Completed Baseline State

- [x] WQ-00 — Source v0.11.0 and marketplace v1.0.13 published and active. Final cross-reference review identified inconsistent route format and guard wording.

### Current Work Queue

- [x] WQ-01 — Align the template and canonical reference, version the package and verify a disposable generated target for REQ-001. `done`
- [ ] WQ-02 — Deliver and verify workflow v0.11.1 and marketplace v1.0.14 including local native readback for REQ-002. `in_progress`

### Locked Decisions

- Keep route markers and contract version unchanged. Express the guidance correction through canonical installed owners, without forcing rewrites of existing target routers.

### Verification

- Check fresh rendered output, follow the actual documented validation commands, and verify source/package parity, CI and release provenance.

### Latest Validation Results

- Verified source and catalog baseline tags and confirmed next patch tags are available.
- Full local gate passed 9/9. A fresh target generated from the built plugin passed the instruction graph and plan lifecycle checks. Package parity passed after the command examples were made directly runnable.

### Risks And Recovery

- If integration fails, inspect actual state and preserve prior tags and installed working versions before retrying.

### Resume Point

- WQ-02: review source and publish v0.11.1 after exact-head CI, then import through the catalog workflow.

### Plan Fidelity Check

- [x] Scoped outcomes, sources, decisions, constraints, work items and acceptance checks are mapped.
- [x] Resume point names the first unfinished step and preserves the approved plan.

### Reconciliation Check

- [x] Initial plan matches repository state and user decisions.
- [ ] Reconcile final changes and delivery.

### Closure Gate

- [ ] All requirements and queue items are terminal and verified.
- [ ] Artifacts and handoff agree with observed state.

### Post-Close Delivery

- Reviewed plan closure follows verified local installation.

### Handoff Notes

- Continue from the release resume point.

## Recently Completed

- [x] 2026-11-17: Completed GPT-6.2 Profiles And Release 0.11.0. Reviewed maintainer instructions and every shipped target template, corrected generated routing and subagent guidance, and exercised opt-in model migration in a disposable target. Both Sol profiles passed the two comparison scenarios. Full checks, public-content and secret scans, package validation and exact-head CI passed. [Source PR #27](https://github.com/xeonvs/codex-engineering-workflow/pull/27), [source release](https://github.com/xeonvs/codex-engineering-workflow/releases/tag/v0.11.0), and [catalog release](https://github.com/xeonvs/xeonvs-engineering/releases/tag/v1.0.13) delivered. Enabled Codex and Claude Code installations match the catalog bytes.
- [x] 2026-10-12: Completed Documentation Navigation And Release Adoption 0.10.0; [full archived plan](docs/archive/plans/2026-10-12-documentation-navigation-and-release-adoption-0-10-0.md).
- [x] 2026-09-25: Completed Repair Custom Archive Upgrade And Add Claude Subagent Profiles; [full archived plan](docs/archive/plans/2026-09-25-repair-custom-archive-upgrade-and-add-claude-subagent-profiles.md).
- [x] 2026-09-23: Completed Privacy Preflight Exact Review V2 And Release; [full archived plan](docs/archive/plans/2026-09-23-privacy-preflight-exact-review-v2-and-release.md).
- [x] 2026-09-23: Completed GPT-6 Model Profiles And Marketplace Release; [full archived plan](docs/archive/plans/2026-09-23-gpt-6-model-profiles-and-marketplace-release.md).
- [x] 2026-09-20: Completed Publish Repository Audit Fix 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-publish-repository-audit-fix-0-9-7.md).
- [x] 2026-09-20: Completed Bounded Git-Aware Repository Audit 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-bounded-git-aware-repository-audit-0-9-7.md).
- [x] 2026-09-15: Completed Context Discipline And Bounded Delegation 0.9.6; [full archived plan](docs/archive/plans/2026-09-15-context-discipline-and-bounded-delegation-0-9-6.md).
- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](docs/archive/plans/2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
