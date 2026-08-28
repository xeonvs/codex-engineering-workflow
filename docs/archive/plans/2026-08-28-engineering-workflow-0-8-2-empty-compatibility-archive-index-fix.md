# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix

Status: done
Owner: root
Last Updated: 2026-08-28

### Goal

Release and install `engineering-workflow` 0.8.2 with a narrow, fail-closed correction for GitHub issue #5: empty canonical compatibility archive directories must not require managed indexes, while non-empty archives, existing unmanaged indexes, symbolic paths, and repository-owned custom archives retain their current protections.

### Plan Origin

plan_mode_approved

### Requested Scope

- Fix false `index_missing` findings for empty `docs/archive`, `docs/archive/plans`, and `docs/archive/backlog` compatibility directories.
- Preserve complete index enforcement for non-empty canonical archives and all existing README/symlink safety checks.
- Preserve repository-owned custom archive paths without inferring a migration or changing generic `close --archive` ownership behavior.
- Publish the fix as `engineering-workflow` 0.8.2 through one reviewed release commit, non-draft PR, merge commit, annotated tag, GitHub Release, issue closure, and public-tag readback.
- Update the installed `engineering-workflow@xeonvs-engineering` plugin to 0.8.2 through the configured marketplace and verify the active cached skill bytes/version.
- Run privacy and Gitleaks checks without exposing candidate secret values to the agent; rewrite published history only if a real secret is validated under the user's explicit conditional authorization.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | `check_archive_indexes()` omits an empty canonical compatibility archive directory from `required` and emits no `index_missing` only when it has no indexable targets and no README path or symlink. | Approved plan; GitHub issue #5 | WQ-01, WQ-02 | Exact synthetic regression passes and structured output excludes the empty archive indexes. | done |
| REQ-002 | Non-empty canonical archives and existing managed, unmanaged, valid symbolic, or broken-symbolic README paths remain fail-closed under the current index and path-safety rules. | Approved plan self-review correction | WQ-01, WQ-02 | Negative lifecycle tests retain missing/unmanaged/unsafe failures and archive closure tests remain green. | done |
| REQ-003 | Repository-owned custom archive content remains byte-identical and generic archive closure/destination ownership behavior is unchanged. | GitHub issue #5; approved non-goal | WQ-01, WQ-02 | Synthetic target snapshot proves no mutation or migration of custom archive paths. | done |
| REQ-004 | Active version owners, current upgrade defaults/examples, regression constants, and deterministic Codex/Claude plugin manifests consistently identify 0.8.2 without changing plan, instruction, orchestration, platform, or privacy contract versions. | Approved release scope | WQ-03, WQ-04 | Active-version review, repository validator, package byte-parity check, and plugin validators pass. | done |
| REQ-005 | Focused tests, full repository gate, semantic self-review, public-tree privacy scan, and fully redacted Gitleaks tree/history scans pass on final content. | Repository contract; approved plan | WQ-02, WQ-04, WQ-05 | Final validation evidence is recorded with no unreviewed finding or generated residue. | done |
| REQ-006 | Authorized delivery preserves the release commit through PR merge, closes issue #5, publishes annotated `v0.8.2` and a GitHub Release, validates all remote CI runs and a fresh public tag clone, and leaves clean synchronized `main`. | User-approved release plan | WQ-06 | GitHub and public-clone readback cover PR/main/tag jobs, merge parents, tag, Release, issue, manifests, and package. | out_of_scope |
| REQ-007 | The configured `xeonvs-engineering` marketplace and installed `engineering-workflow` plugin are updated to 0.8.2 without direct cache-directory replacement. | User follow-up request | WQ-06 | Marketplace update/reinstall succeeds; `codex plugin list` and active cached `SKILL.md` both report 0.8.2. | out_of_scope |

### Explicit Non-Goals

- Do not redesign generic `close --archive` to write a repository-owned custom archive.
- Do not change archive destination inference, ownership classification, planned index creation, or target migration semantics beyond the check-side false positive in issue #5.
- Do not change plan schema version 2, instruction contract version 2, orchestration contract version 3, platform compatibility version 1, or privacy review contract version 1.
- Do not create the Claude-specific dry-run tag `engineering-workflow--v0.8.2`.
- Do not hand-edit generated marketplace package files or directly replace a plugin cache directory.
- Do not delete the remote feature branch after merge.

### Constraints

- Preserve unrelated user work and stage only reviewed 0.8.2 files.
- The first repository file write is this full plan; implementation begins only after its fidelity and current-tree reconciliation are verified.
- The empty-directory skip must not bypass an existing README, a symlink to a README, or a broken README symlink.
- Generated marketplace contents come only from `scripts/build_marketplace_package.py`.
- Use `PYTHONDONTWRITEBYTECODE=1` for repository Python checks and leave no caches, scanner reports, backups, or temporary artifacts in the repository.
- Keep raw Gitleaks findings fully redacted and outside the repository; never print or ingest candidate values.
- Direct model judgment owns implementation, semantic review, destructive recovery, release decisions, and external writes. Programmatic orchestration, when available, is limited to bounded independent validation/result aggregation with declared evidence and stopping conditions.

### Inputs And Sources

- User-approved implementation plan: Engineering Workflow 0.8.2 — issue #5.
- User follow-up: install the updated skill locally after publication.
- GitHub issue: https://github.com/xeonvs/codex-engineering-workflow/issues/5
- Canonical planning and archive index contract: `skill/engineering-workflow/references/planning_and_backlog.md`.
- Lifecycle implementation and regressions: `skill/engineering-workflow/scripts/plan_lifecycle.py` and `tests/test_plan_lifecycle.py`.
- Deterministic package builder: `scripts/build_marketplace_package.py`.
- Installed marketplace evidence: `engineering-workflow@xeonvs-engineering` currently reports 0.8.1.

### User Decisions And Answers

- 2026-08-28: release the fix as version 0.8.2 rather than a local-only patch or unreleased PR.
- 2026-08-28: use a non-draft PR, merge commit, annotated `v0.8.2`, GitHub Release, public clone readback, and synchronized local `main`.
- 2026-08-28: harden the issue's probable one-line fix so an existing or symbolic README cannot be skipped.
- 2026-08-28: keep custom archive closure ownership redesign outside this issue.
- 2026-08-28: update the locally installed marketplace plugin to 0.8.2 after the public release and verify the active cached skill.
- 2026-08-28: if a real secret is validated, perform the previously authorized exact local/GitHub history cleanup and rescan; fixtures and false positives do not authorize rewriting.

### Completed Baseline State

- [x] WQ-00 — Confirmed clean synchronized `main` at `411147c`, open issue #5 assigned to `xeonvs`, current release/tag/plugin version 0.8.1, one configured plugin-managed installation, deterministic marketplace topology, canonical archive contract, exact false-positive reproduction, validator/package/privacy baseline, and 212 passing tests with one platform-dependent skip.

### Current Work Queue

- [x] WQ-01 — Implemented the narrow check-side empty compatibility archive predicate for REQ-001, REQ-002, and REQ-003. `done`
- [x] WQ-02 — Added the synthetic positive and fail-closed negative lifecycle regression matrix for REQ-001, REQ-002, and REQ-003. `done`
- [x] WQ-03 — Updated active 0.8.2 version owners and rebuilt the deterministic dual-marketplace package for REQ-004. `done`
- [x] WQ-04 — Ran focused checks, skill/plugin validators, version/package review, and implementation self-review for REQ-001, REQ-002, REQ-003, REQ-004, and REQ-005. `done`
- [x] WQ-05 — Ran the complete final repository/privacy/Gitleaks gate and reconciled lifecycle state for atomic plan archival under REQ-005. `done`
- [x] WQ-06 — Commit, push, PR, CI, merge, tag, Release, issue/public-clone readback, marketplace update/reinstall, installed-version verification, and final synchronization for REQ-006 and REQ-007 are outside the closable repository lifecycle under the authorized Post-Close Delivery boundary. `out_of_scope`

### Locked Decisions

- The skip predicate applies only to the three canonical compatibility archive directories in `INDEX_SPECS`.
- A directory is skippable only before it is appended to `required`, when `_index_targets()` is empty and `README.md` neither exists nor is a symlink; `is_symlink()` explicitly protects broken symlinks whose `exists()` result is false.
- Existing empty managed indexes are still validated and preserved rather than silently removed.
- `check_archive_indexes()` keeps its current JSON shape; only the membership of `required` and absence of false `index_missing` entries change for the exact empty case.
- Existing canonical planning prose already owns lazy archive creation, so no new duplicated normative rule is added.
- Historical 0.8.1 references remain historical; current upgrade defaults, examples, version constants, skill metadata, and generated manifests move to 0.8.2.
- The installed plugin is updated only after public release readback via configured marketplace refresh and `codex plugin add engineering-workflow@xeonvs-engineering`, followed by active cache readback.

### Verification

- REQ-001 / WQ-01, WQ-02: exact issue #5 synthetic target passes lifecycle check, excludes the two empty archive README paths from `required`, and remains byte-identical.
- REQ-002 / WQ-01, WQ-02: non-empty archive, unmanaged README, symlink-to-file README, and broken README symlink all remain blocking; normal archive closure and legacy archive indexing remain green.
- REQ-003 / WQ-02: repository-owned `docs/product` archive paths and state-manifest ownership entries remain unchanged.
- REQ-004 / WQ-03, WQ-04: active-version search, README/current prompt review, upgrader default checks, deterministic package rebuild and `--check`, manifest validation, skill-creator quick validation, plugin-creator validation, Claude strict plugin/marketplace validation, and Claude tag dry-run.
- REQ-005 / WQ-04, WQ-05: validator → full unittest suite → validator → package check → public-tree privacy scan → `git diff --check`, plus fully redacted Gitleaks tree/all-public-ref scans and complete diff/self-review.
- REQ-006 / WQ-06: inspect every GitHub Actions job/step for branch, PR, main, and tag runs; verify expected-head merge, merge parents, annotated tag, Release, issue state, and fresh public tag clone.
- REQ-007 / WQ-06: update configured marketplace, reinstall the namespaced plugin, verify `codex plugin list`, locate the active 0.8.2 cache path, and read back its `SKILL.md` metadata and changed lifecycle implementation.

### Latest Validation Results

- 2026-08-28: clean synchronized baseline `main` and open issue #5 confirmed; exact false-positive output reproduced with `docs/archive/README.md` and `docs/archive/plans/README.md` reported missing.
- 2026-08-28: baseline validator → 212 tests with one platform-dependent skip → validator → deterministic package check → public-tree privacy scan → `git diff --check` passed at 0.8.1.
- 2026-08-28: baseline skill quick validation, plugin-creator validation, Claude strict plugin/marketplace validation, and Claude tag dry-run passed.
- 2026-08-28: focused 0.8.2 lifecycle (16), marketplace (4), skill-repository validator (26 with one platform skip), and target-upgrader (40) test suites passed; deterministic package rebuild/check reports zero drift.
- 2026-08-28: final validator → 216 tests with one platform-dependent skip → validator → deterministic package check → public-tree privacy scan → `git diff --check` passed at 0.8.2.
- 2026-08-28: skill-creator quick validation, plugin-creator validation, and Claude strict plugin/marketplace validation passed. Claude tag dry-run correctly stopped only because the release tree is not committed and will be repeated after commit without `--force`.
- 2026-08-28: fully redacted Gitleaks scans of the final working tree and complete `--all` Git history both returned status 0; no raw report was created, no secret value entered agent context, and no history rewrite condition was met.
- 2026-08-28: full source/generated diff and semantic self-review confirmed the check-only scope, complete README/symlink guard, non-empty archive failure, preserved custom archive bytes, correctly classified version strings, and byte-identical marketplace package.

### Risks And Recovery

- Risk: broad empty-target skipping hides an unsafe or repository-owned README. Recovery: require the complete no-target/no-file/no-symlink predicate and cover unmanaged, valid-symlink, and broken-symlink cases.
- Risk: a non-empty archive passes without a complete index chain. Recovery: retain `_index_targets()` as the content criterion and rerun closure plus negative archive tests.
- Risk: the narrow issue expands into custom archive migration. Recovery: leave close/apply destination logic unchanged and assert custom archive bytes before and after the check.
- Risk: active/historical version strings are replaced indiscriminately. Recovery: classify every 0.8.1 occurrence, change only active owners/current examples, and preserve historical evidence fixtures.
- Risk: generated marketplace drift or an invalid install. Recovery: rebuild from canonical source, verify byte identity and manifests, publish first, then use marketplace update/reinstall and active-cache readback without direct cache writes.
- Risk: scanner output exposes a secret. Recovery: use complete redaction and task-owned ignored temporary reports, retain only safe aggregate evidence, and delete reports after verification.
- Risk: validated secret remediation rewrites excessive history. Recovery: enumerate exact affected public refs from redacted evidence, preserve recovery refs, use guarded force publication only under the explicit condition, and rescan every affected ref and fresh public clone.
- Risk: remote delivery partially succeeds. Recovery: read back each state transition, stop before duplicate tag/Release creation, and create a corrective active plan if post-close evidence invalidates the release.

### Resume Point

- No unfinished in-scope implementation work remains.

### Plan Fidelity Check

- [x] Every agreed outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point names the first unfinished queue item.
- [x] This plan is not a compressed rewrite of the approved plan.

### Reconciliation Check

- [x] Plan status, requirement statuses, first unfinished queue item, resume point, backlog, validation baseline, issue assignment, branch, installed plugin state, indexes, and working tree agree.
- [x] Completed sections contain no stale next-work, resume, current-milestone, active-blocker, or open-status wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive disposition can be applied atomically.

### Post-Close Delivery

- Outside the closable repository-implementation scope and explicitly authorized for immediate delivery after archive closure: exact staging and commit `Release engineering-workflow 0.8.2`, any conditionally required verified local/GitHub secret-history cleanup, push of `codex/issue-5-empty-archive-index-0.8.2`, non-draft PR with `Closes #5`, completion-driven CI inspection, expected-head merge commit, annotated `v0.8.2`, GitHub Release, issue/public-tag readback, configured marketplace update, `engineering-workflow@xeonvs-engineering` reinstall and active-cache verification, and final clean synchronized `main`. The remote feature branch remains unless separately authorized for deletion.

### Handoff Notes

- No in-scope work remains; Post-Close Delivery is the sole owner of the authorized external actions.

## Recently Completed

- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
- [x] 2026-08-13: Completed Engineering Workflow 0.6.0; [full archived plan](docs/archive/plans/2026-08-13-engineering-workflow-0-6-0.md).
- [x] 2026-07-13: Completed implementation, review, security/privacy remediation, and validation for `engineering-workflow` 0.5.1; the [legacy schema-v1 plan](docs/archive/plans/2026-07-13-engineering-workflow-0.5.1.md) preserves its historical record.
