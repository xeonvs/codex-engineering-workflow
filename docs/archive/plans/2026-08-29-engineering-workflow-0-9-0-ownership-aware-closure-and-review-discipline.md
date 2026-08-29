# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline

Status: done
Owner: root
Last Updated: 2026-08-29

### Goal

Release the already-completed dynamic README badge together with an ownership-aware plan-archive closure fix and an enforceable review-before-commit target contract as `engineering-workflow` 0.9.0 directly on `main`: a declared target archive graph must receive the completed plan, index updates, and machine-state transition atomically; every logical commit must receive a bounded self-review and the complete change set must receive a final semantic self-review before staging or delivery.

### Plan Origin

direct_execution

### Requested Scope

- Preserve and deliver the validated dynamic version badge already present in the local README diff.
- Address the new owner comment on GitHub issue #5 with a synthetic, repository-independent regression.
- Resolve archive destination and index ownership from explicit workflow state rather than path-name heuristics.
- Update the target-owned archive index graph and clear the machine-readable active-plan state in the same atomic closure transaction.
- Fail closed on incomplete, conflicting, unsafe, symbolic, or unmanaged archive declarations and prove no second `docs/archive` tree is created for a custom archive graph.
- Add the missing target-template discipline for a self-review before each logical commit and one final review of the complete change set, with conservative migration for mature customized repositories.
- Add a repository-native developer harness that runs focused or layered checks with `PYTHONDONTWRITEBYTECODE=1`, standard formatting/lint/test tools, private full logs, and bounded terminal summaries so routine validation does not flood model context.
- Bump the distributed skill/plugin minor version to 0.9.0 and instruction contract to version 3, rebuild the deterministic marketplace package, commit all reviewed changes directly to `main`, push, inspect every CI job/step, and verify issue #5 closure.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | The README retains one dynamic latest-release badge with the previously validated styling and link. | User badge request and completed local diff | WQ-01, WQ-06 | Final diff contains the single badge and HTTP/SVG readback remains valid. | done |
| REQ-002 | Workflow state may explicitly declare one safe archive directory and an ordered leaf-to-root managed index graph; legacy state without archive declarations retains the canonical default. | Issue #5 owner comment | WQ-01, WQ-02 | Parser/resolver tests cover default, explicit custom, incomplete, conflicting, unsafe, and symbolic declarations. | done |
| REQ-003 | `close --disposition archive` writes the completed plan into the declared archive, updates every declared managed index, compacts root `PLANS.md`, and clears `active_plan` atomically. | Issue #5 owner comment | WQ-02, WQ-03 | Exact synthetic two-layout regression passes and byte/state snapshots prove the intended transaction. | done |
| REQ-004 | Custom archive closure never creates a second default archive root and lifecycle check validates the declared archive/state rather than silently validating only `docs/archive`. | Issue #5 post-close invariant | WQ-02, WQ-03 | Positive and negative post-close tests assert no default tree, exactly one archived plan/index entry, no active plan, and rollback on validation failure. | done |
| REQ-005 | Canonical documentation, target state template, upgrader output, and migration preservation teach agents and tools to use the explicit archive graph without overwriting a target-owned declaration. | Repository ownership and migration contracts | WQ-04 | Template/reference review and upgrader regression preserve explicit custom archive fields while new targets receive canonical defaults. | done |
| REQ-006 | Target instructions require a bounded self-review before each logical commit and a final review of the aggregate diff; pristine v2 templates migrate automatically while customized v2 owners require model-guided semantic migration before a v3 stamp. | User review-discipline question and repository practice | WQ-04, WQ-05 | Contract-v3 template, validator, pristine/customized migration, and instruction graph regressions pass. | done |
| REQ-007 | Active version owners and generated Codex/Claude marketplace package consistently identify 0.9.0; instruction contract is 3 while planning 2, orchestration 3, platform 1, and privacy 1 remain unchanged. | SemVer impact decision | WQ-05 | Version-owner review, builder parity, repository and plugin validation pass. | done |
| REQ-008 | Full validation, per-slice and aggregate semantic self-review, privacy checks, direct-main commit/push, completion-driven CI inspection, and issue readback complete without a PR, tag, GitHub Release, or unrelated mutation. | User delivery authorization | WQ-06, WQ-07 | Final local/remote SHA, clean `main`, all CI steps, package bytes, issue state, and remote refs are read back. | out_of_scope |
| REQ-009 | Maintainers can run focused, layered, full, and release-oriented repository checks through one bounded-output harness that enforces no bytecode writes, uses existing standard tools, preserves full private logs, and exposes failures without noisy successful output. | User developer-process request | WQ-08, WQ-09 | Harness contract/unit tests plus focused/layer/full self-hosting runs prove selection, environment, exit aggregation, log retention/cleanup, formatting/lint coverage, and bounded summaries. | done |

### Explicit Non-Goals

- Do not place the developer harness, its Ruff configuration, CI orchestration, or harness instructions inside `skill/engineering-workflow`, target templates, marketplace skill bytes, or target-repository migrations; it is repository-maintenance tooling only.
- Do not infer archive ownership from directory names, broad prefixes, arbitrary existing files, or protected-path wording.
- Do not rewrite an unmanaged repository-owned index; an explicit index graph still requires managed marker blocks or an explicitly managed new index path.
- Do not migrate historical archive bytes between roots or delete a pre-existing archive layout.
- Do not add a third-party YAML dependency or accept YAML aliases, tags, dynamic commands, or executable configuration.
- Do not change plan schema version 2, orchestration contract version 3, platform compatibility version 1, or privacy review contract version 1.
- Do not create a feature branch, pull request, annotated tag, GitHub Release, or history rewrite.
- Do not update the locally installed marketplace plugin unless separately requested after publication.

### Constraints

- Preserve the existing uncommitted README badge and compact completion entry; do not discard or overwrite prior user-authorized work.
- This full plan is the first new repository write for the reopened issue work; implementation begins only after lifecycle fidelity passes.
- Treat the state manifest as declarative data and accept only normalized repository-relative paths with no symbolic target or parent.
- The explicit archive contract is all-or-nothing: `plan_archive_path`, non-empty ordered `plan_archive_indexes`, and `active_plan` must agree before mutation.
- Existing targets without any new archive keys use the current canonical archive behavior; partial declarations fail closed.
- Prepare every archive, index, root-plan, and state byte before applying the existing atomic write/rollback mechanism.
- Generated marketplace files are updated only through `scripts/build_marketplace_package.py`.
- Use `PYTHONDONTWRITEBYTECODE=1`; keep scanner values out of agent output and leave no cache, backup, or temporary artifact in the repository.

### Inputs And Sources

- User request on 2026-08-29 to inspect the new issue comment and merge all confirmed work into the main branch.
- GitHub issue #5: `https://github.com/xeonvs/codex-engineering-workflow/issues/5`.
- New owner comment: `https://github.com/xeonvs/codex-engineering-workflow/issues/5#issuecomment-5451804402`.
- Preserved local changes: dynamic README badge and compact completion entry from the immediately preceding validated task.
- Canonical planning/index contract: `skill/engineering-workflow/references/planning_and_backlog.md`.
- Canonical target ownership contract and state template: `skill/engineering-workflow/references/canonical_target.md` and `skill/engineering-workflow/assets/templates/ENGINEERING_WORKFLOW_STATE.yaml.tmpl`.
- Lifecycle implementation and tests: `skill/engineering-workflow/scripts/plan_lifecycle.py` and `tests/test_plan_lifecycle.py`.
- Target upgrader and migration tests: `skill/engineering-workflow/scripts/upgrade_target_workflow.py` and `tests/test_upgrade_target_workflow.py`.

### User Decisions And Answers

- 2026-08-29: preserve the badge change without requiring a PR for that presentation-only edit.
- 2026-08-29: inspect the new issue #5 comment and take its finding into the current work rather than merely acknowledging it.
- 2026-08-29: all confirmed changes may be committed and pushed directly to the repository's main branch.
- 2026-08-29: no separate pull request is required for this delivery.

### Completed Baseline State

- [x] WQ-00 — Confirmed local `main`, `origin/main`, and remote `main` at `d83fd005`; preserved only the validated README/compact-plan diff; read the reopened issue and new owner comment; reproduced the architectural cause in source: archive closure hard-codes `docs/archive/plans`, canonical state has no archive graph/active-plan keys, and lifecycle validation scans only the default archive. `done`

### Current Work Queue

- [x] WQ-01 — Specified and implemented strict state parsing/resolution for the optional archive graph and active-plan state under REQ-001 and REQ-002. `done`
- [x] WQ-02 — Refactored archive/index planning, lifecycle validation, target validation, and report-time conflict detection around a resolved default or explicit archive graph for REQ-002, REQ-003, and REQ-004. `done`
- [x] WQ-03 — Added the exact two-layout synthetic closure, ambiguity/safety, index ownership, state transition, empty-graph, validator-scope, and atomic rollback regression matrix for REQ-003 and REQ-004. `done`
- [x] WQ-04 — Updated canonical planning/ownership instructions, state and route templates, upgrader rendering/preservation, and affected tests for REQ-005. `done`
- [x] WQ-05 — Added instruction contract v3 review discipline, pristine-v2 fingerprints, customized-v2 migration behavior and regressions; moved active version owners to 0.9.0 and rebuilt the marketplace package for REQ-006 and REQ-007. `done`
- [x] WQ-06 — Completed focused suites, cross-template consistency review, per-slice and aggregate self-review, badge/package/privacy checks, full repository gate, and lifecycle closure preparation for REQ-001 through REQ-008. `done`
- [x] WQ-07 — Direct-main commit/push, exact-head CI inspection, issue closure, and remote readback are authorized immediate Post-Close Delivery outside the active implementation plan. `out_of_scope`
- [x] WQ-08 — Inventoried current CI, formatter, linter, validators, cache behavior, and observed context-noise boundaries; selected one pinned Ruff tool and a bounded sequential profile contract for REQ-009. `done`
- [x] WQ-09 — Implemented, documented, and regression-tested the root-only harness; self-hosted focused, quality, contracts, full, and security layers; repeated aggregate/template review and restored lifecycle closure readiness for REQ-009. `done`

### Locked Decisions

- Version 0.9.0 is required because the user-requested review discipline is a new mandatory target instruction contract, in addition to the archive closure fix; the earlier no-version decision applied only to the badge-only task.
- Instruction contract v3 extends the existing `workflow.evidence-driven-completion` owner: review each complete logical commit slice before committing, fix its findings, then review the aggregate final diff before staging or delivery. It does not require one commit per queue item or redundant re-review after unchanged gates.
- Known pristine v2 templates are fingerprinted and replaced automatically. Customized v2 owners remain byte-preserved and return `instruction_migration_required` with model review; no v3 stamp is written until the semantic rule and route graph validate.
- The explicit state keys are top-level `plan_archive_path`, ordered `plan_archive_indexes`, and `active_plan`. The first index owns archived plan entries; each later index owns a managed navigation link to the previous index.
- New/default state declares the canonical graph `docs/archive/plans` → `docs/archive/plans/README.md` → `docs/archive/README.md` → `docs/README.md`, with `active_plan: PLANS.md` while work is active.
- A state manifest with none of the archive keys remains backward-compatible with the current default graph. Any partial explicit graph, duplicate index path, unsafe path, symbolic component, active-plan mismatch, or unmanaged existing index blocks closure before writes.
- Explicit custom graphs may create a missing index only when that exact index path is listed in `managed_paths`; otherwise a missing or unmarked index is an ownership conflict.
- Successful closure replaces `active_plan: PLANS.md` with `active_plan: null` in the same atomic transaction. A later active plan must restore the path before closure; canonical instructions will state this responsibility.
- Existing `_render_index` remains the canonical default-index renderer. Explicit graph rendering preserves all text outside managed markers and adds only deterministic relative links inside the declared managed blocks.
- Existing default archive history is not deleted. The post-close invariant proves the transaction did not create a previously absent competing default archive tree for a custom graph.
- Delivery is one direct-main commit after plan closure; CI uses one persistent GitHub Actions watcher and remote state decisions use exact expected SHA.
- The harness is a local orchestration layer, not a new build framework: it calls repository-native commands, captures complete stdout/stderr under a mode-0700 task-owned temporary directory, emits a compact per-check status/duration summary, prints no raw failure lines unless an explicit bounded tail is requested, and returns nonzero if any selected required check fails.
- Ruff 0.16.4 is the single root-project formatter/linter and is pinned only in root developer tooling. Root configuration overrides user-global Ruff settings and excludes the generated marketplace mirror; source/package identity remains enforced by the builder.
- `PYTHONDONTWRITEBYTECODE=1` is set by the harness for every child process. Focused selection accepts one explicit safe unittest basename; named layers group related deterministic checks; `full` covers the canonical local gate; `security` is mandatory immediately before every push and runs value-safe public-tree plus fully redacted Gitleaks tree/all-ref scans; `release` composes `full` and `security` without publishing or tagging.
- Environment-dependent plugin-creator, strict Claude, and tag dry-run checks remain explicit outside the harness. A Gitleaks finding blocks push; a real credential is revoked or rotated before source remediation, and history rewrite remains separately authorized, recovery-backed, and force-with-lease guarded.

### Verification

- REQ-001 / WQ-01, WQ-06: README source and live badge SVG show one dynamic version badge; final diff preserves the completed presentation change.
- REQ-002 / WQ-01, WQ-02, WQ-03: unit tests cover no-state legacy default, complete default declaration, complete custom declaration, partial/malformed/duplicate/unsafe/symbolic declarations, and active-plan mismatch.
- REQ-003 / WQ-02, WQ-03: synthetic target with custom archive path, ordered managed index graph, and `active_plan: PLANS.md` closes atomically into the custom destination, updates indexes, compacts PLANS, and writes `active_plan: null`.
- REQ-004 / WQ-02, WQ-03: custom closure leaves absent `docs/archive` absent; lifecycle check scans the custom archive; unmanaged index, second-root creation, and injected post-close validation failures preserve original bytes/directories.
- REQ-005 / WQ-04: references explain explicit ownership/fail-closed behavior; new template/upgrader emit the canonical graph; migration preserves an existing complete custom declaration byte-semantically and never silently replaces it with defaults.
- REQ-006 / WQ-04, WQ-05: target principles and canonical validation instructions own the two review boundaries; instruction contract v3 and migrations distinguish pristine from customized v2 repositories and refuse a new stamp until valid.
- REQ-007 / WQ-05: all active version owners/current examples/defaults are 0.9.0, historical 0.8.x evidence remains historical, deterministic builder reports zero drift, and both marketplace manifests/packages agree.
- REQ-008 / WQ-06, WQ-07: validator → full tests → validator → package check → public-tree privacy scan → `git diff --check`, plus per-slice and aggregate semantic diff/self-review; then exact commit/push/main-CI job/step/issue/ref readback.

### Latest Validation Results

- 2026-08-29: prior badge-only task passed validator → 216 tests with one platform-dependent skip → validator → package parity → public-tree privacy scan → `git diff --check`; live badge returned HTTP 200 SVG showing v0.8.2.
- 2026-08-29: reopened issue #5 and owner comment were read through GitHub; local/remote `main` still agree at `d83fd005`, and no external mutation has occurred in this task.
- 2026-08-29: repository audit classifies the project mature with retained history; expected scanner prompt-risk strings are repository fixtures/contracts and do not authorize instructions or secret access.
- 2026-08-29: cross-template and aggregate self-review found and corrected custom-archive route reachability, ambiguous post-commit wording, v3 consumer scope, empty explicit graph validation, full target-validator lifecycle coverage, and report-time ownership conflict detection; affected suites passed with lifecycle 23, validation 22, upgrader 45, and instruction contract 11 tests.
- 2026-08-29: final source gate passed validator → 231 tests with one platform-dependent skip → validator → deterministic package parity → zero-finding public-tree privacy scan → `git diff --check`; skill-creator, plugin-creator, and both strict Claude validations passed.
- 2026-08-29: Gitleaks 8.30.1 returned zero for the final tree and all refs with fully redacted task-owned output; the version badge endpoint returned HTTP 200 with SVG content.
- 2026-08-29: root developer-tool inventory found no repository formatter/linter configuration and showed that unbounded Ruff/test output could exceed a useful review window. Added pinned Ruff 0.16.4, root-only `quality`, `contracts`, `tests`, `package`, `full`, `security`, and `release` profiles, private complete logs, default fail-fast behavior, explicit-only raw tails, and regression coverage proving that no harness byte enters the skill or generated package.
- 2026-08-29: harness self-hosting passed focused developer tests, quality, contract layers, the nine-check full gate, and the three-check security gate. The full gate passed exact Ruff version/format/lint, validator → 240 tests with one platform-dependent skip → validator, deterministic package parity, working-tree and HEAD whitespace checks; security passed the value-safe public-tree scan and fully redacted Gitleaks 8.30.1 tree/all-ref scans.
- 2026-08-29: final template consistency review read all 15 target templates and found no contradictory owner, plan, closure, long-wait, review, privacy, or archive instructions. It added the missing reachable privacy-owner link, preserved `AGENTS.md` as a router, and kept the root harness/configuration completely outside target and marketplace skill bytes.

### Risks And Recovery

- Risk: heuristic archive discovery rewrites a repository-owned layout. Recovery: require explicit state keys for non-default paths and fail closed on partial or unmanaged declarations.
- Risk: arbitrary index rendering corrupts custom prose. Recovery: preserve bytes outside managed markers, require exact managed ownership, and snapshot/rollback every write.
- Risk: state says closure succeeded while an active plan or competing archive remains. Recovery: validate `active_plan: null`, archived plan/index reachability, compact root state, and pre/post default-root existence before transaction success.
- Risk: upgrader replaces custom archive ownership with canonical defaults. Recovery: parse and preserve a complete existing explicit graph; reject partial state before apply and add a migration regression.
- Risk: backward compatibility breaks targets without new fields. Recovery: retain the current default graph when all new keys are absent and rerun existing lifecycle closure/index tests unchanged.
- Risk: customized v2 repositories receive a false v3 stamp without the new rule. Recovery: make required contract version authoritative, auto-replace only preserved pristine fingerprints, and require semantic migration for customized owners before stamping.
- Risk: version strings or generated package drift. Recovery: classify active versus historical strings, update active owners together, rebuild only through the deterministic builder, and validate byte parity.
- Risk: direct-main delivery races another remote update. Recovery: fetch/read exact remote SHA immediately before commit/push, stop on divergence, and use the pushed commit SHA for CI/readback.
- Risk: a convenience harness hides evidence or creates a second source of validation truth. Recovery: commands remain declarative and repository-native, child exit codes are preserved, full logs remain available outside the tree, summaries are bounded, and CI/local documentation point to the same layer definitions.
- Risk: CI or issue automation fails after push. Recovery: do not duplicate commits or mutate tags; inspect exact failure evidence and start a corrective plan if repository bytes must change.

### Resume Point

- None. All in-scope implementation is complete; only authorized Post-Close Delivery remains.

### Plan Fidelity Check

- [x] Every agreed outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point correctly records no unfinished in-scope work.
- [x] This plan preserves the completed badge work and is not a compressed rewrite of the reopened issue scope.

### Reconciliation Check

- [x] Plan status, requirement statuses, absence of an unfinished queue item, resume point, issue state, version baseline, indexes, local diff, and local/remote `main` agree.
- [x] Completed sections contain no stale next-work, resume, current-milestone, active-blocker, or open-status wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive disposition can be applied atomically.

### Post-Close Delivery

- Direct-main commit/push, exact-head GitHub Actions inspection, issue #5 closure, and remote readback are outside the closed implementation scope and explicitly authorized for immediate Post-Close Delivery. Stage only the reviewed badge/0.9.0 ownership-and-review package and use `Fixes #5`; PR, tag, GitHub Release, installed-plugin update, and branch deletion are out of scope.

### Handoff Notes

- None. No external state changed during implementation; delivery continues under the existing authorized Post-Close Delivery boundary.

## Recently Completed

- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
- [x] 2026-08-13: Completed Engineering Workflow 0.6.0; [full archived plan](docs/archive/plans/2026-08-13-engineering-workflow-0-6-0.md).
