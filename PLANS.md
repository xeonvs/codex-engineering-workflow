# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Privacy Preflight Exact Review V2 And Release

Status: active
Owner: root
Last Updated: 2026-09-23

### Goal

Fix issue #8 by allowing an explicitly user-approved, exact-snapshot review of any privacy finding for target workflow migration only; preserve the independent public-tree and pre-push secret gates, then release and install the update through xeonvs-engineering.

### Plan Origin

plan_mode_approved

### Requested Scope

- Implement the approved issue #8 plan in the canonical engineering-workflow repository, publish a patch release, import exact released bytes into xeonvs-engineering, release the marketplace, and update local managed installations.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Preflight offers value-free exact-snapshot approval for every privacy category; no target write occurs before explicit approval. | User-approved plan; issue #8 and comments | WQ-01 | Mixed-category, self-match, fixture, no-write, stale-token tests | done |
| REQ-002 | Review contract v2 rejects v1 tokens and binds category, path, line, exact decoded line including its ending, multiplicity, and version pair; changed/new findings fail or roll back. | User-approved plan; privacy contract | WQ-01 | Token/version/mutation and rollback regression matrix | done |
| REQ-003 | Shared public-tree detection and Gitleaks/publication gates remain unchanged; approval authorizes migration only. | User-approved plan | WQ-01 | Scanner parity test, source full/security gate and diff review | done |
| REQ-004 | Runtime instructions, canonical references, README, package bytes, and version owners describe the new risk and behavior consistently. | User-approved plan; release contract | WQ-02 | Structural/contract tests, package parity and plugin validators | done |
| REQ-005 | Source patch release and exact marketplace import/release are published, with tgrep-search unchanged. | User-approved plan; marketplace release contract | WQ-03,WQ-04 | PR/CI readback, annotated tags, provenance, release assets | pending |
| REQ-006 | Codex/Claude local managed installations resolve the released workflow version; plans close truthfully. | User-approved plan; prior installation preference | WQ-05 | Native CLI readback and lifecycle check/closure | pending |

### Explicit Non-Goals

- Do not silence or narrow the shared scanner, approve publication of real secrets, edit target repositories to test migration, add a persistent allowlist, alter tgrep-search, or rewrite published history.

### Constraints

- Preserve whole-repository scan coverage and value-free candidate reporting. The agent must not read flagged values; a user must independently inspect locally before approving high-risk candidates.
- Approval is limited to target workflow migration on one exact finding snapshot and version pair. Independent public-tree and pre-push Gitleaks gates remain separate.
- Review each logical commit and the aggregate release diff; run final full and immediate pre-push security checks.

### Inputs And Sources

- https://github.com/xeonvs/codex-engineering-workflow/issues/8 and its two owner comments, current 0.9.8 privacy implementation and tests, canonical privacy/target-upgrade references, and the approved plan in this task.
- Current read-only repository audit summary at `/tmp/engineering-privacy-issue8-audit.json` reports mature Git discovery with no inventory truncation; generic self-repository instruction graph findings are outside this issue's migration change.

### User Decisions And Answers

- 2026-09-23: Implement the proposed plan and publish source plus marketplace patch releases with local updates.
- 2026-09-23: Choose approval for findings of any formerly hard category rather than only low-risk or provenance-classified findings. Preserve explicit confirmation, exact snapshot binding, and separate publication gates.

### Completed Baseline State

- [x] Source `main` starts clean; latest remote stable annotated tag is `v0.9.8`; issue #8 remains open and describes 0.9.8 reproduction.

### Current Work Queue

- [x] WQ-01 — Implement privacy review v2 and behavior/regression tests for REQ-001/REQ-002/REQ-003. `done`
- [x] WQ-02 — Update canonical guidance, version owners, generated package and validate/review for REQ-004. `done`
- [ ] WQ-03 — Publish source PR, annotated patch tag and release for REQ-005. `in_progress`
- [ ] WQ-04 — Import into xeonvs-engineering, validate, PR/merge, tag and release for REQ-005. `pending`
- [ ] WQ-05 — Refresh installations, reconcile, and close both plans for REQ-006. `pending`

### Locked Decisions

- Use `privacy_review` contract v2 with `privacy-review-v2` tokens. All scanner categories become review candidates in migration preflight, never automatic exceptions; `hard_block` is no longer returned solely because of a finding category.
- Keep candidate output limited to category/path/line and aggregate token. Explain high-risk manual inspection and that migration approval does not certify public content.
- Provisional patch versions are engineering-workflow 0.9.9 and xeonvs-engineering 1.0.9, subject to fresh remote tag inspection at publication.

### Verification

- Focused privacy/migration tests, contract tests, source full/release/security gates, package parity, Codex/Claude plugin validators, marketplace tests/provenance/public scans, CI and release asset readback, native installed-version readback.

### Latest Validation Results

- 2026-09-23: Read-only issue and repository audit completed. Privacy v2 implementation and tests cover all detector categories, mixed findings, self-match, value-free output, v1 rejection, snapshot drift, and rollback. Source release gate passed 12/12 (full checks plus public-tree and redacted Gitleaks). Source/package skill quick validators, Codex plugin validator, and strict Claude plugin/marketplace validators passed. Aggregate review found and removed a stale hard-block rule in the target-upgrade reference; final package was regenerated and release gate rerun on the corrected bytes.
- 2026-09-23: Aggregate review also identified non-UTF-8 Git path handling in v2 token serialization; switched to ASCII-escaped canonical JSON and added a regression. Final release gate passed 12/12 and source/package quick validators plus Codex/Claude plugin validators passed on those bytes.

### Risks And Recovery

- High-risk candidates may represent real secrets. Require explicit user review of local values, and do not treat migration approval as release clearance; independent scans remain blocking before push.
- Remote refs or package APIs may move during publication. Reinspect exact heads/tags, stop on drift, and do not repeat uncertain side effects.
- A new finding during apply must roll back non-plan writes and retain a truthful failure plan for recovery.

### Resume Point

- WQ-03: commit the reviewed source slice, run Claude tag dry-run and immediate pre-push security gate, then publish and merge the source PR.

### Plan Fidelity Check

- [x] Every requested source, marketplace, local-installation, security, and closure outcome is mapped to ordered work and validation.
- [x] User-selected review breadth, non-goals, canonical sources, risks, recovery, and exact first action are recorded.

### Reconciliation Check

- [ ] Final code, package, releases, installations, and plan states agree.

### Closure Gate

- [ ] All requirements and queue items are terminal with final review and validation evidence.

### Post-Close Delivery

- Publication and local refresh remain active in WQ-03 through WQ-05.

### Handoff Notes

- None.

## Recently Completed

- [x] 2026-09-23: Completed GPT-6 Model Profiles And Marketplace Release; [full archived plan](docs/archive/plans/2026-09-23-gpt-6-model-profiles-and-marketplace-release.md).
- [x] 2026-09-20: Completed Publish Repository Audit Fix 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-publish-repository-audit-fix-0-9-7.md).
- [x] 2026-09-20: Completed Bounded Git-Aware Repository Audit 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-bounded-git-aware-repository-audit-0-9-7.md).
- [x] 2026-09-15: Completed Context Discipline And Bounded Delegation 0.9.6; [full archived plan](docs/archive/plans/2026-09-15-context-discipline-and-bounded-delegation-0-9-6.md).
- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](docs/archive/plans/2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
