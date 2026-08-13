# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is `skill/engineering-workflow/references/planning_and_backlog.md`.

## Active Plan: Engineering Workflow 0.6.0

Status: done
Owner: root
Last Updated: 2026-08-13

### Goal

Release the source-tree implementation of `engineering-workflow` 0.6.0 with one canonical owner per active invariant, a non-normative incident catalog, executable instruction routing and guards, deterministic plan closure/archive/index handling, and safe diagnostic command classification.

### Plan Origin

plan_mode_approved

### Requested Scope

- Add a repo-local root `AGENTS.md` for agents developing this repository, with no runtime or distribution dependency from the skill.
- Replace the second-manual pitfalls pattern with a cause/owner/route/guard/retirement incident catalog.
- Add executable instruction-contract validation and block false workflow version stamps.
- Introduce planning schema v2 with checked close/archive operations and generated navigation indexes.
- Upgrade public skill/state contracts and all active version sources to 0.6.0.
- Preserve safe diagnostics while blocking mutation, repository-code execution, network use, and sensitive output at the correct boundary.
- Cover prior incidents and representative target changes with behavioral tests.
- Perform complete validation, review, reconciliation, and future-useful plan archival without installing, publishing, or mutating other repositories.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Root `AGENTS.md` is a complete local development map and cannot become a runtime skill dependency. | Approved plan section 1 | WQ-01, WQ-05 | Content review and negative dependency test. | done |
| REQ-002 | One instruction-lifecycle owner defines cause codes, invariant identity, routes, guards, and retirement. | Approved plan section 2 | WQ-02, WQ-05 | Contract parser and valid/invalid graph tests. | done |
| REQ-003 | Pitfalls is a compact non-normative incident catalog with no `Better default` rule body. | Approved plan section 2 | WQ-02, WQ-05 | Template/schema and imperative/duplicate tests. | done |
| REQ-004 | Audit, target validation, and migration consume an executable instruction graph and refuse unresolved conflicts or fake version stamps. | Approved plan section 3 | WQ-03, WQ-05 | CLI/JSON integration and migration regression tests. | done |
| REQ-005 | Planning schema v2 and `plan_lifecycle.py` enforce truthful closure, compact/archive dispositions, atomic rollback, and legacy-v1 preservation. | Approved plan section 4 | WQ-02, WQ-03, WQ-05 | Lifecycle command and state-transition tests. | done |
| REQ-006 | Every skill-created documentation directory receives a managed navigation README; archives are indexed exactly once without overwriting user prose. | Approved plan section 5 | WQ-02, WQ-03, WQ-05 | Index link/orphan/atomicity tests and source-repo backfill. | done |
| REQ-007 | Public version/state/audit interfaces are synchronized at 0.6.0, state schema 2, instruction contract 1, planning contract 2, orchestration contract 1. | Approved plan section 6 | WQ-02, WQ-03, WQ-06 | Structural validator, version search, YAML/JSON checks. | done |
| REQ-008 | Command safety exposes multi-axis risks while keeping the legacy string API and allowing safe diagnostics. | Approved plan section 6 | WQ-03, WQ-05 | Safe `sed -n`/normal reads pass; write/execute/network/sensitive-output cases fail. | done |
| REQ-009 | Finviz, compact-plan conflict, provider-boundary duplication, UI QA, stale archive, and safe-diagnostic scenarios are replayed. | Approved incident matrix | WQ-05 | Dedicated behavioral fixtures/tests. | done |
| REQ-010 | Full skill validation, tests, repeat validation, diff review, privacy/residue checks, reconciliation, and archive/index closure pass. | Approved acceptance criteria | WQ-06, WQ-07 | Exact final results recorded before closure. | done |
| REQ-011 | No local installed-skill update, target-repository mutation, commit, push, or release occurs without separate authorization. | Approved constraints | WQ-01, WQ-07 | Final git/install/remote state readback. | done |

### Explicit Non-Goals

- Do not update the active user-scoped installation or any other installed copy.
- Do not modify sampled downstream repositories or rewrite their historical instruction documents.
- Do not commit, push, publish, tag, or create a release.
- Do not make the root `AGENTS.md` an asset, template, state-manifest entry, or runtime input.

### Constraints

- Preserve existing repository-owned text unless this repository owns the contract being changed.
- Use report-first, fail-closed migration for customized target instruction documents.
- Keep historical schema-v1 archives immutable; index and label them as legacy.
- Avoid phrase gates that require the same normative prose in multiple owners.
- All repository edits use `apply_patch`; validation must not leave tracked or cache artifacts.

### Inputs And Sources

- User-approved implementation plan in this task, 2026-08-13.
- Current repository at baseline commit `bf5193a` on clean `main` tracking `origin/main`.
- Official Codex guidance: `https://learn.chatgpt.com/docs/agent-configuration/agents-md` and `https://learn.chatgpt.com/docs/build-skills`.
- Skill-authoring guidance: the system `skill-creator` instructions loaded for this run.
- Historical incident evidence from the existing 0.5.1 archive and prior repository workflow records.

### User Decisions And Answers

- 2026-08-13: the user selected implementation of the approved plan and delegated the skill version choice.
- 2026-08-13: version selected as 0.6.0 because public contracts and schemas change.
- 2026-08-13: the root `AGENTS.md` is only for developing this repository and must not participate in skill runtime.
- 2026-08-13: archive/closure policy and all index README creation are explicitly in scope.

### Completed Baseline State

- [x] WQ-00 — Clean baseline `main...origin/main` at `bf5193a` confirmed; 0.5.1 has 143 passing tests in the prior validated baseline.
- [x] WQ-00A — Existing contracts, templates, scripts, fixtures, archive state, and historical failure examples audited read-only.

### Current Work Queue

- [x] WQ-01 — Materialize this plan and add the strictly repo-local root `AGENTS.md`. Covers REQ-001, REQ-011. `done`
- [x] WQ-02 — Added canonical instruction/plan lifecycle contracts, v2 templates, index templates, and 0.6.0 metadata. Covers REQ-002, REQ-003, REQ-005, REQ-006, REQ-007. `done`
- [x] WQ-03 — Implemented instruction graph, plan lifecycle, archive indexes, multi-axis safety, and integrations into audit/validation/upgrade. Covers REQ-004 through REQ-008. `done`
- [x] WQ-04 — Hardened conservative migration and state stamping for customized instruction owners. Covers REQ-004, REQ-007. `done`
- [x] WQ-05 — Added fixtures and behavioral regression coverage, including the incident replay matrix. Covers REQ-001 through REQ-009. `done`
- [x] WQ-06 — Synchronized README/SKILL/UI metadata and completed targeted validation and two-pass review. Covers REQ-007, REQ-010. `done`
- [x] WQ-07 — Reconciled all requirements, selected full archive disposition, prepared atomic index transition, and verified no unauthorized delivery occurred. Covers REQ-010, REQ-011. `done`

### Locked Decisions

- `references/instruction_lifecycle.md` owns the instruction meta-contract; it is linked directly from `SKILL.md`.
- `references/planning_and_backlog.md` remains the only owner of planning, closure, archive, and backlog lifecycle.
- Invariant IDs live beside their canonical normative blocks; no separate rule-registry file becomes another owner.
- Target `AGENTS.md` is a route table, not a rule manual. Pitfalls entries refer to rules but never restate them.
- Generated indexes contain navigation only and use managed marker blocks; pre-existing unmarked README content is protected.
- Automatic instruction-document replacement is limited to missing or known pristine template content.
- The public string safety classifier remains compatible and is derived from a structured risk result.

### Verification

- REQ-001: root instruction review plus source-tree search proving no runtime dependency.
- REQ-002–REQ-004: instruction-contract CLI, target audit/validator/migration unit tests, and JSON schema assertions.
- REQ-005–REQ-006: plan-lifecycle close/check tests with temporary repositories, rollback injection, index link/orphan validation, and legacy v1 fixture.
- REQ-007: metadata/readme/default/state synchronization and safe YAML parsing.
- REQ-008: command safety matrix for benign reads, write modes, repo execution, network, shell control, and secret-bearing paths.
- REQ-009: named incident replay tests and a representative `frontend/**` routing fixture.
- REQ-010: repository validator, full unittest discovery, repeat validator, `git diff --check`, skill quick validator, privacy scan, residue scan, and manual diff/code review.
- REQ-011: final status and remote/install readback without mutation.

### Latest Validation Results

- 2026-08-13: repository validator passed before and after the full test suite with skill version 0.6.0 and no errors or warnings.
- 2026-08-13: full unittest discovery passed 170 tests in 10.294 seconds; one non-UTF-8 filesystem test was skipped by platform capability.
- 2026-08-13: mature replay fixture passed instruction graph validation with four guarded incidents and passed target validation with zero errors; one expected legacy `docs/exec-plans` migration-note warning remains informational.
- 2026-08-13: plan lifecycle check, source archive indexes, privacy/public-tree scan, residue scan, version synchronization review, and `git diff --check` passed.
- 2026-08-13: `skill-creator` quick validator could not start because both available Python runtimes lack its external `PyYAML` dependency; no package was installed, and the repository validator independently parsed and checked all supported public formats.

### Risks And Recovery

- Risk: broad migration changes overwrite customized target instructions. Recovery: template fingerprints, report-first conflicts, no version stamp, and rollback tests.
- Risk: fuzzy duplicate detection creates false hard failures. Recovery: exact normalized duplicates are errors; similarity remains a review warning.
- Risk: closure mutates several files partially. Recovery: stage all intended bytes, validate paths/content, then apply atomically with byte-for-byte rollback.
- Risk: new safety parsing blocks useful diagnostics or misses secret output. Recovery: preserve the legacy API and test risk axes independently.
- Risk: v2 rejects historical documents. Recovery: validate strict closure only for schema v2 and index schema-v1 archives as legacy.

### Resume Point

- No unfinished in-scope work remains; the checked full-archive transition is ready.

### Plan Fidelity Check

- [x] Every approved outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point names the first unfinished queue item.
- [x] This plan is not a compressed rewrite of the approved plan.

### Reconciliation Check

- [x] Plan status, requirements, queue, final validation, working tree, replay fixtures, and index state agree.
- [x] The prior 0.5.1 work remains immutable legacy schema-v1 evidence; the new archive will use schema v2.

### Closure Gate

- [x] All in-scope requirements and queue items are terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and generated indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Full archive disposition is selected and can be applied atomically with rollback.

### Post-Close Delivery

- Local source-tree implementation only. Installation, commit, push, tag, release, and remote CI are outside the authorized scope.

### Handoff Notes

- None. Implementation and pre-closure validation are complete; durable evidence is recorded above.

## Recently Completed

- [x] 2026-07-13: Completed implementation, review, security/privacy remediation, and validation for `engineering-workflow` 0.5.1; the [legacy schema-v1 plan](docs/archive/plans/2026-07-13-engineering-workflow-0.5.1.md) preserves its historical record.
