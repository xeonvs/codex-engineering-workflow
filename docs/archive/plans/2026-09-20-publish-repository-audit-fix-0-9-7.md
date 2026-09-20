# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Publish Repository Audit Fix 0.9.7

Status: done
Owner: root
Last Updated: 2026-09-20

### Goal

Publish the completed repository-audit fix as engineering-workflow 0.9.7, import its immutable release into xeonvs-engineering 1.0.7, and refresh the managed Codex and Claude marketplace installations.

### Plan Origin

direct_execution

### Requested Scope

- Complete every remaining delivery step for issue #12, including source and marketplace publication and local marketplace/plugin updates.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | The reviewed 0.9.7 source/package change is committed through a PR and merged without unrelated changes. | User authorization | WQ-01 | Aggregate diff review, release/security gate, exact-head PR merge readback. | done |
| REQ-002 | Annotated `v0.9.7` and a public GitHub release point at the merged source commit. | User authorization | WQ-02 | Tag object/peeled commit and release readback. | done |
| REQ-003 | xeonvs-engineering imports exact 0.9.7 bytes/provenance while retaining tgrep-search 1.0.3 and publishes marketplace 1.0.7. | User authorization | WQ-03 | Synchronizer, catalog tests, recorded-byte verification, PR/merge/tag/release artifact readback. | done |
| REQ-004 | Managed Codex and Claude installations resolve engineering-workflow 0.9.7 and tgrep-search 1.0.3 from the refreshed marketplace. | User authorization | WQ-04 | Native CLI update and installed-version readback. | done |
| REQ-005 | Source and downstream plans close with durable release evidence and no stale resume state. | Workflow contract | WQ-05 | Lifecycle checks and closure PRs after delivery. | done |

### Explicit Non-Goals

- Change tgrep-search, alter the source/marketplace ownership decision, rewrite history, force-move tags, or edit managed plugin caches directly.

### Constraints

- Publish only reviewed bytes that passed the required full and security gates.
- Marketplace synchronization accepts only the stable annotated upstream tag and must preserve exact source bytes and provenance.
- Use native marketplace/plugin update commands; do not hand-edit configured caches or marketplace snapshots.

### Inputs And Sources

- https://github.com/xeonvs/codex-engineering-workflow/issues/12
- Completed archived implementation plan `docs/archive/plans/2026-09-20-bounded-git-aware-repository-audit-0-9-7.md`.
- Current source worktree, generated plugin package, and xeonvs-engineering synchronization/release contracts.

### User Decisions And Answers

- 2026-09-20: Complete the work end-to-end, including marketplace updates.

### Completed Baseline State

- [x] WQ-00 — Source main matches remote at `fc89f51`; 0.9.7 implementation is locally reviewed, full/security validated, package-aligned, and not yet committed or tagged. Remote 0.9.7 and marketplace 1.0.7 tags do not exist.

### Current Work Queue

- [x] WQ-01 — Revalidate the final source tree, commit, push a release branch, open and merge the exact-head source PR for REQ-001. `done`
- [x] WQ-02 — Create and publish annotated source tag/release for REQ-002. `done`
- [x] WQ-03 — Import, validate, review, and publish xeonvs-engineering 1.0.7 for REQ-003. `done`
- [x] WQ-04 — Refresh and verify managed installations for REQ-004. `done`
- [x] WQ-05 — Reconcile and close both durable plans for REQ-005. `done`

### Locked Decisions

- `codex-engineering-workflow` remains canonical source; `xeonvs-engineering` remains the generated distribution catalog.
- Use patch releases 0.9.7 and 1.0.7.
- CI polling is unnecessary when local release gates, exact remote object readback, and published artifacts provide sufficient terminal evidence.

### Verification

- Source `scripts/dev_check.py release`, external skill/plugin validation where supported, exact current-version search, source/package parity, and aggregate review.
- Marketplace catalog validation, all tests, exact recorded-upstream verification, Codex/Claude manifest validation where supported, and redacted Gitleaks tree/history scans.
- One bounded readback of each merge, annotated tag, release, release assets, and local installed versions.

### Latest Validation Results

- 2026-09-20: Implementation full gate passed 9/9 with all 263 tests; final public-tree and redacted Gitleaks checks passed 3/3 before the delivery request.
- 2026-09-20: Final release profile passed 12/12 on the delivery tree. Plugin-creator validation, source/package `quick_validate`, and Claude plugin validation passed; Claude tag dry-run correctly requires the release bytes to be committed first.
- 2026-09-20: Source PR #13 merged at `2ceeba7e92497040b99a3bc1d302e4e26bf2a853`; annotated `v0.9.7` and its public GitHub release were published after a fresh post-merge security gate.
- 2026-09-20: Marketplace PR #17 merged at `b89e70fadbf81a3a8d24e86eb98541b2e981e748`; annotated `v1.0.7` imported exact 0.9.7 bytes while retaining tgrep-search 1.0.3. Release run `35505523852` published the checksummed archive with digest `sha256:c98cabfe13b1af6b4731e8a4130a241dc3d0c40416007e9addfe61fabaac3d0d`.
- 2026-09-20: Codex and Claude read back engineering-workflow 0.9.7 and tgrep-search 1.0.3 as enabled managed plugins; Claude requires restart to apply the updated plugin. Marketplace closure PR #18 merged at `83d984297ec2e8986b9da64f2a23344a893e1bf4`.

### Risks And Recovery

- Risk: remote main changes before merge. Recovery: use a branch PR and exact head-object merge guard; refresh and revalidate if the base introduces a conflict.
- Risk: marketplace imports stale or non-annotated source. Recovery: synchronizer rejects the candidate and publication stops before tag creation.
- Risk: local installation observes a stale snapshot. Recovery: refresh through native marketplace commands, reinstall by validated marketplace name, and read back active versions.

### Resume Point

- None; source and marketplace releases, artifact readback, managed installation refresh, and downstream plan closure are complete.

### Plan Fidelity Check

- [x] Source release, downstream import/release, managed installations, durable closure, exclusions, authorization, and validation are represented.
- [x] Requirements map to ordered work and concrete terminal evidence.

### Reconciliation Check

- [x] Changed results and plan entries agree.

### Closure Gate

- [x] Requirements and queue are terminal; final release and installation evidence are recorded.

### Post-Close Delivery

- None; all authorized source and marketplace delivery and managed installation work is complete.

### Handoff Notes

- None.


## Recently Completed

- [x] 2026-09-20: Completed Bounded Git-Aware Repository Audit 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-bounded-git-aware-repository-audit-0-9-7.md).
- [x] 2026-09-15: Completed Context Discipline And Bounded Delegation 0.9.6; [full archived plan](docs/archive/plans/2026-09-15-context-discipline-and-bounded-delegation-0-9-6.md).
- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](docs/archive/plans/2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
