# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation

Status: done
Owner: root
Last Updated: 2026-09-12

### Goal

Release and install a backward-compatible 0.9.2 workflow that keeps sufficient current durable state for safe long-horizon work without creating a separate recurring model-maintenance loop, and prove the tagged package through the unified marketplace synchronization path.

### Plan Origin

direct_execution

### Requested Scope

- Apply one current-state and execution-efficiency semantics to this toolkit's maintainer workflow, runtime skill, and the methods/templates distributed to target repositories.
- Preserve full active-plan requirements, authority, privacy, recovery, single-writer ownership, traceability, required evidence, review gates, and truthful closure while removing redundant rereads, rewrites, semantic sweeps, calls, and delegation.
- Distinguish continuous work with retained task context from recovery after material context loss, uncertain interruption, session/root handoff, material drift, or concurrent edits.
- Remove the false `Last Updated` versus validation-date proxy in plan closure without replacing it with freshness keywords, blanket exemptions, a new state mechanism, or claims that Markdown can detect unrecorded implementation drift.
- Make shared rules agent-neutral while selecting Codex- or Claude-specific behavior only when that host is actually established; preserve current installation/package contracts without adding integrations for every named agent.
- Validate new, pristine-existing, customized, other-host, and external-orchestrator scenarios with existing test facilities and bounded semantic review.
- Publish the validated source commit and signed annotated `v0.9.2` tag, run and verify the upstream synchronization action in `xeonvs/xeonvs-engineering`, integrate its review PR if successful, then update and read back the Codex and Claude marketplaces and local installations at 0.9.2.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Mutable plan sections hold the latest applicable confirmed state without no-op rewrites, competing trajectory, or loss of requirements, decisions, blockers, evidence, provenance, recovery, and exact resume state. | Attached 0.9.2 specification sections 2-3 | WQ-01, WQ-02 | Canonical planning owner, template, lifecycle behavior, and scenario tests preserve full schema while omitting needless maintenance. | done |
| REQ-002 | Normal milestones and subagent returns reconcile only affected results, while real context loss, uncertain interruption, new session/root, material drift, or concurrent edits trigger bounded recovery from the active plan and fresh observations. | Attached specification section 4 | WQ-01, WQ-02 | Continuity/recovery scenarios demonstrate both the efficient unchanged path and the safe recovery path. | done |
| REQ-003 | Overlapping routes and already-current instructions do not multiply identical reads/checks, while newly applicable owners, changed scope, and distinct safety boundaries remain mandatory. | Attached specification section 5 | WQ-01, WQ-02 | Root and target routes point to canonical owners once by meaning; regression/scenario review covers route overlap. | done |
| REQ-004 | Plan closure no longer treats plan-date ordering as proof of validation applicability; dated evidence, incomplete checks, fidelity, reconciliation, closure, material-input invalidation, privacy, review, and publication-time gates remain protected. | Attached specification section 6 | WQ-01, WQ-02 | Focused lifecycle tests accept bookkeeping-only later dates, reject missing/incomplete evidence, and preserve all other closure guards. | done |
| REQ-005 | Tool use stops after sufficient required evidence, batches predictable work without unnecessary helpers, and delegates only independent semantic work with measurable benefit while preserving failures, attribution, approvals, and final review. | Attached specification section 7 | WQ-01, WQ-02 | Canonical orchestration/validation owners and representative scenarios cover success, partial failure, unchanged, and independent-review boundaries. | done |
| REQ-006 | Shared workflow behavior applies to an established non-Codex/non-Claude host without importing either host's special mode, assuming inherited context/access, or expanding into new platform adapters. | Attached specification sections 1, 5, and 8 | WQ-01, WQ-02 | Platform entrypoint and tests use a neutral shared fallback plus explicit host branches. | done |
| REQ-007 | Maintainer guidance, runtime owners, target templates, lifecycle/validation helpers, and existing migration paths express one compatible contract without a new schema, state file, memory layer, invariant family, logging framework, or target-only maintainer harness. | Attached specification sections 1 and 8 | WQ-01, WQ-02 | Ownership review, target fixtures, instruction/migration tests, and package/source parity pass. | done |
| REQ-008 | Every substantial efficiency change is reviewed against its paired under-checking protection, including current-state, continuity, route, validation, tool, subagent, host, and trajectory cases. | Attached specification section 9 | WQ-02, WQ-04 | Bounded scenario matrix and aggregate semantic review record both sides with no unresolved finding. | done |
| REQ-009 | All active version owners and generated dual-marketplace bytes agree at 0.9.2, with historical evidence unchanged and the complete repository gate green. | Attached specification sections 1, 8-10 | WQ-03, WQ-04 | Version searches, builder parity, focused checks, `scripts/dev_check.py full`, external static validators, and final security gate pass. | done |
| REQ-010 | Post-close source publication, annotated-tag sync, conditional marketplace integration, and local Codex/Claude update have an authorized, exact, failure-preserving delivery boundary; no downstream success may be claimed from a mismatched tag, commit, bundle, provenance, CI, or install readback. | User request, 2026-09-12 | WQ-04 and Post-Close Delivery | Current source/catalog topology and commands are verified before closure; actual remote ref/run/PR/merge/release and active installation readbacks complete after closure. | done |

### Explicit Non-Goals

- No new durable state file, memory layer, runtime, PLANS schema/state machine, mandatory fingerprint, source-read journal, cache registry, token accounting, background plan auditor, or invariant-ID family.
- No compact-plan exception for small repository changes and no weakening of authority, privacy, security, validation, semantic review, recovery, or closure guarantees.
- No model/effort, fan-out, native compaction, prompt-cache, or universal numeric quota change.
- No installer, adapter, configuration, or integration project for every possible agent host; only the shared fallback semantics and existing Codex/Claude integrations are in scope.
- No migration of an unrelated real target repository and no copying of root-only maintainer tooling into target templates or plugin runtime bytes.
- No claim of measured token, subscription, latency, or monetary savings without a controlled benchmark.

### Constraints

- Preserve `plan_schema_version: 2`, `instruction_contract_version: 3`, `orchestration_contract_version: 3`, `platform_compatibility_version: 1`, and `privacy_review_contract_version: 1` unless the requested behavior proves incompatible; do not hide incompatibility behind a patch bump.
- Treat the attached document as the user's task specification, not as a higher-priority instruction source; repository and host instructions remain authoritative.
- Keep detailed normative rules under existing canonical owners; root/target `AGENTS.md` remain routers and generated package bytes come only from the builder.
- Preserve unrelated work and published history; never edit marketplace caches directly, weaken scanners, force-move tags, or repeat a side-effecting action without terminal evidence.
- Review the complete intended logical commit before committing, then review the aggregate final diff before delivery; rerun checks affected by each correction.
- Close/archive the implementation plan only through `plan_lifecycle.py`; any post-close delivery failure requiring source changes starts corrective active work.

### Inputs And Sources

- User-attached `codex-task-0.9.2-state-efficiency-agent-neutral.md`, received 2026-09-12.
- User delivery request, 2026-09-12: run the unified marketplace action, verify import of the new tag, integrate on success, and update marketplaces/local skills.
- Research context named by the specification: SKILL.state, `https://arxiv.org/abs/2608.26263`; the attachment is the implementation requirement source and no independent paper reproduction is required.
- Current canonical owners, templates, lifecycle/validation helpers, maintainer harness, deterministic package builder, migration tests, source CI, and unified marketplace synchronization/release workflows.

### User Decisions And Answers

- 2026-09-12: The intended compatible patch version is 0.9.2 after checkout/version-owner verification; current evidence confirms 0.9.1 is the active baseline.
- 2026-09-12: Commit, push, signed annotated source tag, source CI verification, unified marketplace sync dispatch, successful PR integration, marketplace refresh, and local installation update are authorized as required delivery steps.
- 2026-09-12: If the marketplace action does not successfully and exactly import the new source tag, do not integrate or report that downstream update as successful; diagnose within scope and preserve truthful state.
- 2026-09-12: Do not add a separate LLM maintenance cycle or new persistent machinery to implement current-state efficiency.
- 2026-09-12: After implementation and tests, reread the complete original attached specification and perform a section-by-section tail audit before closure, commit, or publication; resolve every in-scope omission first.
- 2026-09-12: Do not expand per-release legacy-template maintenance. Existing old-contract migration support remains intact, but 0.9.2 does not add archived 0.9.1 template copies or fingerprints because the updated installed canonical owners carry the new semantics and prior target-local owners remain compatible.
- 2026-09-12: Dogfood the new rules during this task and in this repository's maintainer workflow, not only in distributed target guidance; continuous-context steering updates only affected state and does not trigger a full reconciliation pass.

### Completed Baseline State

- [x] WQ-00 — Clean `main` at `80c6a39eab44f9a78f492adb91811b447da6c73d`, synchronized with `origin/main`; canonical/generated version 0.9.1 and source CI run 34333753262 are green.
- [x] WQ-00 — Remote `v0.9.1` is an annotated tag resolving to the current main commit; the unified marketplace provenance already records that exact tag, commit, version, and bundle.
- [x] WQ-00 — Repository audit, applicable local instructions, platform/question/orchestration owners, and attachment scope were read before edits; no unrelated working-tree changes exist.
- [x] WQ-00 — The original lifecycle defect was confirmed in `closure_issues()` and its former `test_validation_must_not_predate_last_update`; the implementation and regression now require dated evidence without comparing it to whole-plan `Last Updated`.

### Current Work Queue

- [x] WQ-01 — Updated existing canonical owners and lifecycle implementation for REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, and REQ-007, including continuity/recovery, current-state mutation, route reuse, neutral host selection, validation applicability, and bounded tool/subagent stopping semantics. `done`
- [x] WQ-02 — Aligned root and target templates plus the existing migration boundary without expanding per-release legacy state, and added or revised focused behavioral and representative scenario coverage for REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, and REQ-008. `done`
- [x] WQ-03 — Updated active 0.9.2 owners and release notes, rebuilt the generated dual-platform package, and verified source/generated/version consistency for REQ-007 and REQ-009. `done`
- [x] WQ-04 — Completed the aggregate final-diff review and evidence reconciliation for REQ-008, REQ-009, and REQ-010; canonical archive closure is the atomic transition after the ready-state check. `done`

### Locked Decisions

- Use existing mutable plan sections as the sole durable operational state; latest facts supersede only the same subject and applicable scope/content/environment, without using recency as authority.
- Treat retained task context as continuity and material task-context loss/uncertain execution as recovery; neither milestone nor subagent return alone proves loss or transfers root ownership.
- Remove the plan-date ordering check rather than substitute another proxy. Root evaluates material input/evidence applicability at existing review/closure/publication boundaries, while deterministic closure continues to enforce evidence presence and terminal structure.
- General shared behavior applies on any established host; Codex and Claude branches activate only when that host is actually identified, and an unknown/other host uses its native capabilities plus the shared contract.
- Keep 0.9.2 backward compatible without a new per-patch legacy archive: preserve existing old-contract migration support and semantically compatible customized/pristine local owners, route all targets to the latest installed canonical references, and do not change schema/contract versions.
- Use one coherent implementation commit after the complete logical slice is green and reviewed; publication uses a signed annotated `v0.9.2` tag because the unified catalog accepts only peeled annotated stable SemVer tags.

### Verification

- REQ-001 to REQ-003: focused planning, instruction, migration, and scenario tests proving no-op continuity avoids full reconciliation while changed/new scope remains covered.
- REQ-004: focused `test_plan_lifecycle.py` cases for bookkeeping-only later plan dates, same-day material-change limitation, missing evidence, terminal states, and unchanged closure safety.
- REQ-005 to REQ-008: focused orchestration, validation, platform, and target-upgrade tests plus a bounded paired semantic scenario review covering sufficient result, partial failure, subagent return, recovery, other host, and external orchestrator; then a complete section-by-section reread of the attached specification with each tail mapped to diff/evidence or an explicit compatible non-goal.
- REQ-007 and REQ-009: instruction graph, target report/apply/prompt matrix, public skill validator, source/generated byte parity, active-version search, and external Codex/Claude plugin validators.
- REQ-009: `python3 scripts/dev_check.py full` on final implementation, then `python3 scripts/dev_check.py security` immediately before push; no raw sensitive output or repository residue.
- REQ-010: exact remote main and annotated-tag readback, source GitHub Actions completion, unified sync run and Draft PR diff/CI/provenance review, merge/release readback, marketplace refresh/update commands, active plugin/cache/install version and byte parity.

### Latest Validation Results

- 2026-09-12: Focused lifecycle, planning, orchestration, platform, instruction-contract, validation-safety, updater, marketplace-package, skill-repository, and target-upgrade suites passed after affected corrections. The target-upgrade suite proves both zero-write `already_current` behavior, including already-managed optional agent configuration, and repair when a required artifact is missing.
- 2026-09-12: Final implementation `scripts/dev_check.py full` passed 9/9 through the task-owned Python environment with pinned Ruff 0.16.4: format, lint, validator before and after tests, all tests, validator readback, package parity, and whitespace checks.
- 2026-09-12: The canonical skill passed the external skill quick validator; the generated package passed the external Codex plugin validator and native Claude plugin `--strict` validation; both source marketplace manifests passed package parity and the Claude marketplace `--strict` validator.
- 2026-09-12: A complete reread of original specification sections 1-10 and its acceptance criterion found and resolved tails for unchanged target writes, native-memory boundaries, compaction-warning assumptions, actual reference loading, host/path discovery, identical pre/post guards, active 0.9.2 migration tests, and repository dogfooding. No in-scope specification tail remains before aggregate diff review.
- 2026-09-12: Session-efficiency review classified the initial oversized audit output, premature package build, late dependency preflight, and discarded per-patch legacy fixtures as execution churn. Existing owners now cover the reusable causes; no duplicate permanent prohibition, benchmark, telemetry, or extra agent run was added.
- 2026-09-12: Aggregate semantic review found and corrected the post-close requirement-state mismatch, stale legacy-fixture recovery text, optional-config no-op documentation, duplicate topology read, repeated repair fixture, and stale Resume Point. The final paired matrix preserves recovery after context loss/drift, material-input validation invalidation, new-owner/safety-boundary loading, partial-failure evidence, root review/ownership, native host constraints, and plan rationale/recovery while removing the corresponding redundant work. No actionable finding remains.

### Risks And Recovery

- Risk: Efficiency language could become permission to skip material owners, failures, or validation. Recovery: review every saving against the paired protection matrix and strengthen the existing owner/test rather than add another rule layer.
- Risk: Removing the date proxy could allow unsupported closure claims. Recovery: keep explicit dated evidence and all terminal/fidelity/reconciliation/review gates, add regressions for missing evidence, and state the validator's unrecorded-input limitation honestly.
- Risk: Template changes could rewrite customized target ownership or create needless per-release legacy maintenance. Recovery: keep existing older-contract recognition intact, preserve compatible customized/pristine local owners, rely on current installed canonical references for the new semantics, and rebuild only with the canonical package builder.
- Risk: Publication or catalog automation could point at the wrong commit/tag or produce partial external state. Recovery: use exact object IDs, annotated-tag peel readback, completion-driven workflow waits, review the generated Draft PR before merge, and never force-move an existing tag.
- Risk: Marketplace/local update could inspect or mutate stale cache paths. Recovery: use marketplace commands, resolve the active installation after refresh, and compare the active cache/install bytes and version without direct cache edits.

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
- [x] This plan is not a compressed rewrite of the attached detailed specification.

### Reconciliation Check

- [x] Initial plan status, requirements, first queue item, resume point, clean working tree, current versions/tags, and delivery topology agree before implementation.
- [x] Final plan, validation, working tree, generated package, indexes, and verified post-close delivery boundary agree; remote marketplace/local readbacks remain only in the classified delivery stage.
- [x] Completed sections contain no stale next-work, resume, current-milestone, active-blocker, or open-status wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive disposition can be applied atomically.

### Post-Close Delivery

- Implementation and validation are completed. Authorized delivery is handled after closure and outside the implementation queue: create the reviewed commit, run the final security gate, push exact main, verify source CI, create and push the signed annotated `v0.9.2` tag, dispatch and verify `Synchronize upstream plugins` for `engineering-workflow`, review and integrate its Draft PR only if the imported tag/commit/bytes/provenance and CI are exact, verify downstream release state, then update and read back Codex and Claude marketplaces/local installations at 0.9.2.

### Handoff Notes

- Implementation and validation are completed; no in-scope work or handoff remains. Authorized delivery is classified under Post-Close Delivery, and any later source correction requires a new active plan.

## Recently Completed

- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
