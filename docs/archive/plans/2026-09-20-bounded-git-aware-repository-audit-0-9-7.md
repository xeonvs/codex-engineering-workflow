# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Bounded Git-Aware Repository Audit 0.9.7

Status: done
Owner: root
Last Updated: 2026-09-20

### Goal

Resolve issue #12 by making repository audit discovery Git-aware and bounded, adding compact machine-readable agent output backed by a complete report artifact, preserving security scan coverage, and preparing a coherent 0.9.7 source/package update.

### Plan Origin

direct_execution

### Requested Scope

- Apply https://github.com/xeonvs/codex-engineering-workflow/issues/12 to the engineering-workflow project.
- Evaluate whether `codex-engineering-workflow` should become read-only in favor of `xeonvs-engineering`, without changing repository archival or ownership settings unless separately authorized.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Git-backed discovery uses tracked files plus non-ignored untracked files with NUL-safe names, retaining tracked files under ignored-looking paths. | Issue #12 | WQ-01 | Synthetic tracked/ignored/untracked and unusual-name tests. | done |
| REQ-002 | Non-Git discovery is bounded, prunes ignored/generated trees before traversal, never follows external symlinks, and reports any inventory limitation. | Issue #12 | WQ-01 | Non-Git, symlink, limit, and large ignored-tree tests. | done |
| REQ-003 | The audit CLI preserves default full JSON and offers opt-in compact JSON pointing to an atomically written complete report, with status, failure categories, counts, and explicit omissions/truncation. | Issue #12 | WQ-02 | CLI and summary-contract tests. | done |
| REQ-004 | Runtime guidance routes agent consumption through bounded summary output while privacy/public-tree scanning retains its independent tracked-file coverage. | Issue #12 | WQ-02, WQ-03 | Semantic review, privacy regression, source/package parity. | done |
| REQ-005 | Repository ownership recommendation is evidence-based and does not mistake the marketplace snapshot for the full maintainer source. | User proposal | WQ-04 | Source/marketplace topology comparison and final rationale. | done |
| REQ-006 | All active 0.9.7 version owners and generated marketplace bytes agree and the completed change passes required gates. | Repository release contract | WQ-03, WQ-05 | Version search, full gate, plugin validators, security gate if publication is later authorized. | done |

### Explicit Non-Goals

- Archive, rename, or make either GitHub repository read-only; reverse the current upstream synchronization direction; publish, tag, push, or update local installed plugins without separate current authorization.
- Narrow privacy/public-tree scanning, omit tracked public files, add a new orchestration layer, or remove default full-JSON compatibility.

### Constraints

- Normal Git discovery must use repository inventory rather than filesystem-wide traversal and decode NUL-delimited path bytes with filesystem surrogate handling.
- Canonical explicitly requested paths remain visible when tracked, including under normally ignored directory names.
- Complete audit evidence must remain available outside the compact model-facing result; failure and truncation state cannot be hidden.
- Keep detailed discovery/output behavior in code and tests; keep `SKILL.md` a concise runtime router.

### Inputs And Sources

- https://github.com/xeonvs/codex-engineering-workflow/issues/12 and its synthetic reproducer/acceptance criteria.
- Current `common.py`, `repo_audit.py`, audit tests, planning/validation/instruction/privacy owners, and package build contract.
- Current remote tree shapes: source has 176 tracked files including 46 tests; `xeonvs-engineering` has a 52-file packaged workflow snapshot plus marketplace-specific synchronization tests.

### User Decisions And Answers

- 2026-09-20: Apply the new issue.
- 2026-09-20: Treat source-repository retirement as a proposal for analysis, not as authorization to archive or redirect repositories.

### Completed Baseline State

- [x] WQ-00 — Main is clean at 0.9.6; issue #12, relevant owners, implementation, tests, and source/marketplace topology were inspected before editing.

### Current Work Queue

- [x] WQ-01 — Implement and test REQ-001/REQ-002 inventory behavior. `done`
- [x] WQ-02 — Implement and test REQ-003/REQ-004 compact/full report contract and runtime guidance. `done`
- [x] WQ-03 — Update 0.9.7 version owners and generated package bytes for REQ-004/REQ-006. `done`
- [x] WQ-04 — Complete REQ-005 repository ownership analysis. `done`
- [x] WQ-05 — Perform semantic review, full validation, privacy/security checks, and closure reconciliation for REQ-006. `done`

### Locked Decisions

- Keep `codex-engineering-workflow` as the canonical development/source repository and `xeonvs-engineering` as an immutable-tag-imported distribution catalog. The marketplace package lacks the source repository's complete tests, maintainer harness, migration fixtures, and development history, so it is not an operationally complete replacement.
- Preserve `repo_audit.py <repo>` full JSON on stdout. Add bounded output only as an explicit mode with a caller-selected complete-report path.
- Reuse the existing Git-backed public inventory semantics where appropriate, but keep audit discovery and privacy scanning separate so an audit optimization cannot narrow security coverage.

### Verification

- Focused repository-audit tests for ignored untracked trees, tracked ignored-looking paths, non-ignored untracked documentation, unusual filenames, internal/external symlinks, non-Git fallback limits, and compact report fields.
- Existing privacy/public-tree tests proving tracked-file coverage remains unchanged.
- Root structural/contract checks, source/generated package parity, full maintainer gate, and aggregate semantic review.

### Latest Validation Results

- 2026-09-20: Read-only inspection confirmed the issue cause: `_iter_relevant_files` uses `Path.rglob` with filtering after traversal, while privacy scanning already has a separate Git inventory path.
- 2026-09-20: Marketplace topology inspection confirmed that its workflow directory is a packaged snapshot rather than the full maintainer repository.
- 2026-09-20: Focused repository-audit and privacy sanitizer tests passed. A live bounded summary of this repository retained failure categories and evidence metadata while the complete 42 KB JSON remained in a protected temporary report.
- 2026-09-20: Final full maintainer gate passed 9/9 stages with all 263 tests, structural validation, package parity, formatting, lint, and whitespace checks. Source and packaged skills passed `quick_validate`; Claude plugin validation passed.
- 2026-09-20: Final public-tree privacy plus redacted Gitleaks tree/history checks passed 3/3. The installed Codex CLI exposes no plugin validator and the installed Claude CLI exposes no marketplace validator; repository package validation remained the applicable catalog/manifest gate.

### Risks And Recovery

- Risk: Git inventory failure silently changes discovery scope. Recovery: record inventory source/status and use an explicitly bounded fallback with omissions surfaced in full and compact reports.
- Risk: symlink or unusual-name handling causes escape, crash, or skipped tracked evidence. Recovery: never follow links, use byte-delimited Git output and filesystem decoding, and cover both with synthetic tests.
- Risk: compact output hides actionable failures. Recovery: derive summary status/categories from the complete report and always point to the exact written evidence file.
- Risk: shared inventory refactoring narrows the privacy gate. Recovery: retain independent privacy behavior and run its existing plus targeted regression tests.

### Resume Point

- None; implementation, package preparation, semantic review, and local validation are complete. External delivery remains out of scope.

### Plan Fidelity Check

- [x] Issue acceptance, compatibility, privacy boundary, version/package work, repository-ownership proposal, exclusions, and delivery authority are represented.
- [x] Requirements map to ordered work and concrete behavioral validation.

### Reconciliation Check

- [x] Changed results and plan entries agree.

### Closure Gate

- [x] Requirements and queue are terminal; final semantic and automated evidence are recorded.

### Post-Close Delivery

- Commit, push, PR, tag, release, marketplace import, and local plugin refresh are not currently authorized and remain out of scope for this plan.

### Handoff Notes

- None.


## Recently Completed

- [x] 2026-09-15: Completed Context Discipline And Bounded Delegation 0.9.6; [full archived plan](docs/archive/plans/2026-09-15-context-discipline-and-bounded-delegation-0-9-6.md).
- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](docs/archive/plans/2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
