# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure

Status: done
Owner: root
Last Updated: 2026-09-12

### Goal

Correct 0.9.2 plan closure so compact and archive transitions preserve every non-active top-level section in customized repositories, then publish the immutable corrective release before resuming marketplace synchronization.

### Plan Origin

direct_execution

### Requested Scope

- Preserve unknown, repository-owned, and legacy sibling sections when closing a valid active plan; update or insert only the managed `Recently Completed` section and remove only the active plan section.
- Add a regression based on the observed `xeonvs-engineering` `## Completed Work` loss and verify both compact/archive callers retain existing lifecycle behavior.
- Update active version owners and generated package to 0.9.3, run focused/full/external/security gates, review and close this corrective plan, then publish immutable `v0.9.3` and make it the latest GitHub release/badge source.
- Resume the authorized downstream marketplace action and integration only after source/tag/CI readbacks are exact.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | `_compact_root()` preserves every level-2 sibling section outside `Active Plan` and `Recently Completed`, including exact customized historical content and order. | Observed marketplace closure failure, 2026-09-12 | WQ-01 | Behavioral compact regression compares retained section bytes/content and lifecycle readback. | done |
| REQ-002 | Canonical recent-entry bounding, archive links, atomic closure, schemas, indexes, and active-plan removal remain correct for compact and archive dispositions. | Existing lifecycle contract | WQ-01, WQ-02 | Focused lifecycle suite and complete repository gate pass. | done |
| REQ-003 | Active source/package/version owners agree at 0.9.3 with no rewrite of 0.9.2 history and all release/static/privacy checks green. | Immutable-release recovery boundary | WQ-02 | Version/package parity, full/external validators, final review, security, tag/release/CI readbacks. | done |
| REQ-004 | Downstream sync consumes the corrected latest stable tag and no 0.9.2 catalog integration is claimed after the closure defect was discovered. | User marketplace/local-update request | WQ-02 and Post-Close Delivery | Marketplace auth fix, rerun, Draft PR provenance/digest/CI, merge/release, and local install readbacks use 0.9.3. | done |

### Explicit Non-Goals

- Do not move, delete, or rewrite `v0.9.2`, its GitHub release, commit, archive, or CI evidence.
- Do not introduce a new plan schema, section registry, migration state, legacy template archive, or semantic parser for arbitrary Markdown bodies.
- Do not change plan closure gates, archive ownership/index rules, status vocabulary, unrelated runtime behavior, model profiles, or marketplace bundle content by hand.

### Constraints

- The corrective release remains backward compatible and changes only closure composition, its tests/version owners, generated package, and truthful release documentation/state.
- Preserve the exact prefix and all non-managed top-level sections; only the active plan and canonical recent-entry list are lifecycle-managed by this transition.
- Use the canonical builder, full gate, external skill/plugin/Claude validators, aggregate review, canonical closure, signed annotated tag, pre-push security gate, and exact hosted CI readback.

### Inputs And Sources

- Reproduction: compact closure in the temporary `xeonvs/xeonvs-engineering` checkout removed its existing `## Completed Work` section while reporting success; the deletion was detected before commit/push and restored from Git.
- Current implementation: `skill/engineering-workflow/scripts/plan_lifecycle.py::_compact_root` rebuilds a fixed canonical root and reads `Recently Completed` through EOF.
- Existing lifecycle/template/validator/package tests and immutable source release `v0.9.2` at `e1e143ae7e8fb6d66b1ba1fde0fdf9b39a125d82`: `https://github.com/xeonvs/codex-engineering-workflow/releases/tag/v0.9.2`.

### User Decisions And Answers

- 2026-09-12: The repositories must dogfood the new current-state rules and preserve useful state while removing unnecessary maintenance.
- 2026-09-12: Update and fully integrate the `xeonvs-engineering` marketplace, then update Codex/Claude marketplaces and local skills.
- 2026-09-12: Because published tags are immutable, use 0.9.3 for the corrective release rather than moving or rewriting 0.9.2.

### Completed Baseline State

- [x] WQ-00 — Source `main`, remote main, annotated `v0.9.2`, latest GitHub release/badge source, and both source CI runs agree at `e1e143ae...`; the working tree was clean before this plan.
- [x] WQ-00 — The failure is reproduced and isolated to `_compact_root`; marketplace history was restored before any external write, and its auth-fix branch remains local.
- [x] WQ-00 — Existing lifecycle validation accepts the customized sibling section before closure, proving the deletion occurs in transition composition rather than plan eligibility.

### Current Work Queue

- [x] WQ-01 — Replaced fixed-root compaction with active/recent section-local composition and added the customized-sibling regression for REQ-001 and REQ-002. `done`
- [x] WQ-02 — Updated 0.9.3 owners/package, completed focused/full/external/tail/aggregate gates, and prepared exact source/downstream delivery for REQ-002, REQ-003, and REQ-004. `done`

### Locked Decisions

- Parse only level-2 section boundaries. If `Recently Completed` exists, replace its managed body in place; otherwise replace the active-plan section at its position with the new recent section. Preserve the preamble and every other section verbatim apart from bounded outer whitespace needed to join sections.
- Continue bounding recent checked entries to ten and deduplicating the new entry; do not interpret or migrate arbitrary preserved section bodies.
- The marketplace imports 0.9.3, not the superseded 0.9.2 bundle; marketplace catalog release target becomes v1.0.2 after exact integration.

### Verification

- REQ-001: focused lifecycle test closes a ready plan with a customized `## Completed Work` sibling and asserts its content/order survive compact closure.
- REQ-002: complete `test_plan_lifecycle.py`, plan validator, archive/index tests, package parity, and `scripts/dev_check.py full`.
- REQ-003: active-version search, builder check, skill quick/plugin/Claude strict validators, aggregate diff review, canonical closure readback, pre-push security, signed tag/release and hosted CI.
- REQ-004: exact upstream remote/tag/release/CI; marketplace action/PR provenance and bundle digest; marketplace v1.0.2 release; Codex/Claude marketplace and installed-version/byte readbacks.

### Latest Validation Results

- 2026-09-12: Focused lifecycle tests passed after adding compact/archive subcases that preserve customized sections before and after the active plan, retain order, remove the active section, create the archive when requested, and pass lifecycle readback.
- 2026-09-12: Final `scripts/dev_check.py full` passed 9/9 with pinned Ruff 0.16.4: format, lint, validator before/after tests, all tests, package parity, and whitespace checks.
- 2026-09-12: Canonical skill quick validation, external Codex plugin validation, native Claude plugin `--strict`, and Claude marketplace `--strict` validation passed on 0.9.3 bytes.
- 2026-09-12: Aggregate corrective diff review confirmed section-local parsing only, preservation of preamble and non-managed sibling sections, bounded/deduplicated recent entries, unchanged archive/index/atomic gates, generated/source parity, and historical-only 0.9.2 references. No finding remains.

### Risks And Recovery

- Risk: section slicing could duplicate, reorder, or lose managed recent entries. Recovery: test canonical no-recent, existing-recent, customized-sibling, compact, and archive paths before full gate.
- Risk: preserved arbitrary content could retain stale active-like text. Recovery: remove only the one validated active-plan level-2 section and keep existing stale-completed checks/closure validation unchanged.
- Risk: downstream sync could race an earlier tag or auth fix. Recovery: verify latest stable tag peel and PR provenance/digest after the source corrective release; never integrate a mismatched candidate.

### Resume Point

- No unfinished in-scope implementation work remains.

### Plan Fidelity Check

- [x] Corrective outcome, observed data-loss evidence, user delivery goal, immutable 0.9.2 boundary, validation, and recovery are preserved.
- [x] REQ-001 through REQ-004 map to the two ordered queue items and exact evidence.
- [x] Scope excludes new schemas, broad Markdown interpretation, history rewrite, and unrelated release behavior.
- [x] Resume Point identifies the first safe unfinished item and no material decision remains open.

### Reconciliation Check

- [x] Current source/tag/release state, clean baseline, reproduced defect, restored target history, queue, and resume point agree.
- [x] Final implementation, tests, package/version, review, plan/index state, and post-close delivery boundary agree.

### Closure Gate

- [x] Every requirement and queue item is terminal.
- [x] Applicable validation and aggregate review cover final content.
- [x] Resume Point contains no unfinished in-scope work and archive closure is safe.

### Post-Close Delivery

- Implementation and validation are completed. Authorized delivery is outside the implementation queue and handled after archive closure: commit, security-gated push, signed annotated `v0.9.3`, latest source release/badge and CI readback; then finish the marketplace auth PR, sync/import PR, v1.0.2 marketplace release, and local Codex/Claude updates.

### Handoff Notes

- Implementation and validation are completed; no in-scope work or handoff remains. Any later correction requires a new active plan.

## Recently Completed

- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
