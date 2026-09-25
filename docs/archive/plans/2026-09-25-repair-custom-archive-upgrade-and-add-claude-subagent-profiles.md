# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Repair Custom Archive Upgrade And Add Claude Subagent Profiles

Status: done
Owner: root
Last Updated: 2026-09-25

### Goal

Fix issues #19 and #20 without losing custom archive navigation or wrapped completed-plan pointers; offer native, opt-in Claude Code subagent model profiles without changing existing Codex opt-ins or user settings; publish and verify patch releases in the source and unified marketplaces and refresh local installations.

### Plan Origin

plan_mode_approved

### Requested Scope

- Repair the declared custom archive index graph during target workflow upgrades.
- Preserve existing multiline Recently Completed entries when closing a plan.
- Add separately opted-in Claude Code subagent model profiles and preserve native/user configuration.
- Verify implementation, review the aggregate diff, create and merge the source PR, publish source and unified-marketplace patch releases, and verify local installations.
- Divide independent, bounded implementation and review work among subagents while root owns integration and durable state.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Target upgrade preserves a valid explicitly declared custom archive chain, including parent links and unmanaged prose | issue #19 and approved plan | WQ-01, WQ-03 | Disposable target upgrade succeeds; graph validates; negative cases roll back | done |
| REQ-002 | Claude Code receives native model/effort selection only through separate opt-in profiles, without altering Codex opt-in or user settings | user bonus and approved choice | WQ-02, WQ-03 | Opt-in, no-opt-in, idempotence, preservation, unsafe path, and rollback tests pass | done |
| REQ-003 | Source skill and generated dual-platform package remain coherent and fully validated | approved plan | WQ-03, WQ-04 | Full, security, plugin, package, and aggregate review checks pass | done |
| REQ-004 | Source and unified marketplace releases and local installations are updated and verified | approved delivery choice | WQ-05, WQ-06 | PR/CI, release tag, byte-exact import, marketplace release, and active local version readback | done |
| REQ-005 | Independent work is bounded and integrated by root | explicit user instruction | WQ-01, WQ-02, WQ-04 | Disjoint file ownership, compact findings, root acceptance and final review | done |
| REQ-006 | Plan closure preserves complete existing multiline archive pointers | issue #20 and user follow-up | WQ-07 | Archive and compact close retain wrapped entries and links; lifecycle validates | done |

### Explicit Non-Goals

- No global Claude model or effort override, plugin-wide agent installation, recursive delegation, or changes to unrelated skills and repositories.
- No weakening of privacy, secret, instruction, or lifecycle validation.
- No migration of customized user agent definitions or settings without a separate decision.

### Constraints

- Materialize this full plan before any other repository write; root alone changes PLANS.md and final state.
- `--include-agent-config` and its prior state remain Codex-only. Claude configuration requires a distinct flag and state marker; default upgrade leaves `.claude/**` unchanged.
- Generate package bytes from canonical skill sources; do not edit generated package or plugin caches directly.
- Public/security gates run on final content immediately before each authorized push. Remote writes and local installation refresh follow the user's approved delivery choice; no history rewrite or scanner weakening.

### Inputs And Sources

- User request: implement the approved plan, including delegation, PR, patch releases, marketplaces, and local refresh.
- Issue: https://github.com/xeonvs/codex-engineering-workflow/issues/19
- Issue: https://github.com/xeonvs/codex-engineering-workflow/issues/20
- Claude Code subagent documentation: https://code.claude.com/docs/en/sub-agents
- Claude Code model and effort documentation: https://code.claude.com/docs/en/model-config
- Codex subagent documentation: https://learn.chatgpt.com/docs/agent-configuration/subagents

### User Decisions And Answers

- 2026-09-25: choose opt-in project Claude subagent profiles, not guidance alone.
- 2026-09-25: deliver PR and patch releases, update unified marketplace and local installations.
- 2026-09-25: split independent bounded work among subagents; root orchestrates and integrates.
- 2026-09-25: include newly opened issue #20 and review findings before publication.

### Completed Baseline State

- [x] WQ-00 — Main working tree was clean before implementation; issue #19 was the only open source issue then. Issue #20 opened during work. Published source and marketplace tags were v0.9.9 and v1.0.9; recheck before publication.
- [x] WQ-00A — Existing `planned_explicit_index_writes` preserves custom parent links; bare interim generic index check would reject the restored link. Existing final lifecycle check validates both graphs.
- [x] WQ-00B — Claude Code supports native per-agent `model` and `effort`; definition/invocation precedence and provider restrictions are documented. Existing target opt-in applies only to Codex.

### Current Work Queue

- [x] WQ-01 — Implement custom archive index reconciliation and focused disposable-target regressions for REQ-001 and REQ-005. `done`
- [x] WQ-02 — Implement separate Claude opt-in templates, policy, migrator behavior, and focused regressions for REQ-002 and REQ-005. `done`
- [x] WQ-03 — Integrate both slices, update active version owners to next patch version, rebuild generated package, run affected checks for REQ-001/002/003. `done`
- [x] WQ-07 — Fix issue #20's wrapped pointer truncation and the review-identified empty Claude-agent overwrite, with disposable regressions; rebuild package and rerun affected checks for REQ-002, REQ-003, and REQ-006. `done`
- [x] WQ-04 — Run full and security gates, review each logical slice and aggregate diff, fix findings, and reconcile source plan for REQ-003/005. `done`
- [x] WQ-05 — Create/merge source PR after checks and publish source patch release for REQ-004. `done`
- [x] WQ-06 — Import exact released bytes into xeonvs-engineering, verify, create/merge PR, publish marketplace patch release, refresh active local Codex/Claude installations, and read back versions for REQ-004. `done`

### Locked Decisions

- 2026-09-25: Reuse the explicit index planner after generic writes and rely on unified lifecycle validation rather than duplicating custom-link allowance logic.
- 2026-09-25: Add a separate Claude opt-in flag and state marker; retain the existing Codex flag's meaning.
- 2026-09-25: Use Claude aliases Haiku for small semantic utility work and Sonnet/medium for explorer/reviewer; no fixed Haiku effort. Ordinary bounded implementation uses Sonnet/medium through native selection. Opus escalation requires user selection or confirmation.
- 2026-09-25: Preserve customized target agents and native Claude settings; refresh only exact prior generated template bytes. Do not set `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`.
- 2026-09-25: If live tags remain unchanged, target source v0.9.10 and marketplace v1.0.10; otherwise recalculate next patch versions.

### Verification

- REQ-001 / WQ-01: disposable custom-chain upgrade, explicit and generic index graph checks, prose preservation, default archive absence, malformed/unmanaged/symlink rollback.
- REQ-002 / WQ-02: optional Claude config creation, non-opt-in byte stability, rerun idempotence, custom model preservation, prior-template refresh, unsafe-path and rollback tests, frontmatter validation.
- REQ-003 / WQ-03/04: focused tests, `python3 scripts/dev_check.py full`, package byte parity, external Claude/plugin validators, `python3 scripts/dev_check.py security`, aggregate semantic review.
- REQ-004 / WQ-05/06: CI success, annotated stable source tag, GitHub import result, identical source/import package bytes, marketplace CI/tag, native local installation and enabled/version readback.
- REQ-005 / WQ-01/02/04: bounded handoffs and root-reviewed integration without overlapping plan or version-owner writes.
- REQ-006 / WQ-07: disposable archive/compact closure retains multiline archive links and checks lifecycle success.

### Latest Validation Results

- 2026-09-25: issue #19, Claude opt-in (including empty file), and issue #20 focused tests passed; full gate 9/9, security gate 3/3, and external plugin/skill validators passed. Independent final review found no remaining issues.
- 2026-09-25: source PR #21 and marketplace PR #23 merged after CI. Source annotated tag/release `v0.9.10` and marketplace annotated tag/release `v1.0.10` published. Marketplace provenance and bundle bytes match the released source; catalog tests, validator, upstream verification, release workflow, and archive SHA256 passed. Codex and Claude read back enabled `engineering-workflow 0.9.10` with byte-identical local skill trees; `tgrep-search 1.0.3` remained unchanged.

### Risks And Recovery

- Custom index regression and final lifecycle validation passed; migration rollback remains covered.
- Claude opt-in preservation, unsafe paths, and rollback are covered by disposable regressions.
- Released source, imported package, published marketplace, and both local installations were verified against one another.

### Resume Point

- No unfinished in-scope work remains.

### Plan Fidelity Check

- [x] Every agreed outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point names the first unfinished queue item.
- [x] This plan is not a compressed rewrite of a more detailed approved plan.

### Reconciliation Check

- [x] Affected work state, repository state, and applicable validation agree.
- [x] Plan and requirement statuses, queue, resume point, indexes, and related docs agree.
- [x] Completed sections contain no stale next-work or blocker wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Compact or archive disposition can be applied atomically.

### Post-Close Delivery

- Requested source and marketplace delivery completed. The archival documentation PR changes no released artifact.

### Handoff Notes

- No in-scope work remains; no handoff is required.

## Recently Completed

- [x] 2026-09-23: Completed Privacy Preflight Exact Review V2 And Release; [full archived plan](docs/archive/plans/2026-09-23-privacy-preflight-exact-review-v2-and-release.md).
- [x] 2026-09-23: Completed GPT-6 Model Profiles And Marketplace Release; [full archived plan](docs/archive/plans/2026-09-23-gpt-6-model-profiles-and-marketplace-release.md).
- [x] 2026-09-20: Completed Publish Repository Audit Fix 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-publish-repository-audit-fix-0-9-7.md).
- [x] 2026-09-20: Completed Bounded Git-Aware Repository Audit 0.9.7; [full archived plan](docs/archive/plans/2026-09-20-bounded-git-aware-repository-audit-0-9-7.md).
- [x] 2026-09-15: Completed Context Discipline And Bounded Delegation 0.9.6; [full archived plan](docs/archive/plans/2026-09-15-context-discipline-and-bounded-delegation-0-9-6.md).
- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](docs/archive/plans/2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
