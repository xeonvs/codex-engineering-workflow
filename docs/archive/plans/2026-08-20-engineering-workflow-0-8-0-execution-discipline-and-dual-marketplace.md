# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace

Status: done
Owner: root
Last Updated: 2026-08-20

### Goal

Publish `engineering-workflow` 0.8.0 from a reviewed two-commit branch, with completion-driven and loss-resistant long-running execution contracts, conservative instruction-contract-v2 migration for mature repositories, deterministic self-contained Codex and Claude marketplace packaging, documented platform compatibility, green CI, an annotated `v0.8.0` tag, a GitHub Release, and a clean synchronized local `main`.

### Plan Origin

plan_mode_approved

### Requested Scope

- Preserve the reviewed 0.7.0 work as its own release commit without a 0.7 tag or GitHub Release.
- Make `agent_orchestration.md` the single owner of completion-driven waiting and raise `orchestration_contract_version` to 3.
- Add correctness-first execution, bounded reconnaissance, keyhole inspection, complete ingestion, dependency probes, evidence-driven failure loops, and stop-after-green rules to `validation_safety.md` without rigid universal numeric heuristics.
- Make long-running results survive waiter-cell/output-buffer truncation by persisting complete logs and machine-consumable terminal results in task-owned ignored artifacts and returning explicit integrity metadata plus a bounded summary.
- Raise `instruction_contract_version` to 2 with efficient-execution, evidence-driven-completion, and completion-driven-wait invariants, a router-only long-running route, structured contract diagnostics, and conservative mature-repository migration.
- Add a canonical Codex/Claude platform compatibility contract while preserving the same planning, audit, migration, safety, and wait outcomes on both platforms.
- Build the public Git marketplace `xeonvs-engineering` with one deterministic self-contained `engineering-workflow` package, separate Codex and Claude manifests/catalogs, byte-for-byte drift detection, and plugin-managed update handoff.
- Update version owners, templates, upgrader defaults, documentation, tests, validators, and release guidance to skill 0.8.0 / instruction 2 / orchestration 3.
- Complete review, validation, plan closure/archive, exact staging, commit, push, non-draft PR, green CI, merge commit, tag, GitHub Release, public-clone readback, and local-main synchronization.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | The reviewed 0.7.0 tree exists as commit `Release engineering-workflow 0.7.0`, with no 0.7 tag or release. | approved release plan | WQ-00 | commit readback and remote tag/release absence | done |
| REQ-002 | Orchestration contract v3 owns completion-driven waiting, calculated-boundary fallback polling, task-owned cleanup, bounded summaries, and the rule that PTC does not replace a persistent waiter. | approved plan; attached waiting task; user clarification | WQ-01,WQ-05 | reference/template review and waiting regressions | done |
| REQ-003 | Waiter completion evidence survives cell/output-buffer truncation through durable ignored logs/results, integrity checks, explicit truncation state, and fail-closed result recovery. | user clarification 2026-08-20 | WQ-01,WQ-05 | buffer-loss regression and contract review | done |
| REQ-004 | Validation safety owns correctness-first efficient execution, bounded/keyhole reconnaissance, complete ingestion, dependency probes, evidence-driven failure handling, and stopping after required green without rigid universal counts or timings. | approved plan; fresh Agent Rules attachment | WQ-02,WQ-05 | canonical-owner review and behavioral regressions | done |
| REQ-005 | Instruction contract v2 requires the three workflow invariants and long-running route, reports structured version/missing fields, auto-migrates pristine 0.7 templates, and routes customized v1 repositories to semantic review without stamping 0.8 prematurely. | approved plan | WQ-03,WQ-05 | report/apply/prompt migration matrix and target validation | done |
| REQ-006 | A canonical platform contract and README accurately document Codex and Claude behavior, including Claude's direct calls, explicit AGENTS reading, namespaced invocation, update commands, standalone fallback, and capability limits. | approved plan; official platform docs | WQ-04,WQ-06 | documentation review, link/source check, capability matrix tests | done |
| REQ-007 | Repository-native builder deterministically produces a self-contained dual-marketplace package and `--check` blocks any byte drift; manifests/catalogs declare only implemented capabilities at version 0.8.0. | approved plan; plugin-creator contract | WQ-04,WQ-05,WQ-06 | native validator, plugin validator, Claude strict/tag dry-run, drift regressions | done |
| REQ-008 | Plugin-managed installations receive marketplace update/reinstall handoff instead of direct cache replacement, while standalone copy/symlink installs remain compatible. | approved plan | WQ-03,WQ-05 | updater classification and mutation-safety regressions | done |
| REQ-009 | Every active version owner agrees on skill 0.8.0, instruction 2, orchestration 3, with public-tree privacy and complete repository gates green. | approved plan | WQ-06,WQ-07 | version search, full validator/tests/validator/privacy/diff gate | done |
| REQ-010 | Authorized delivery yields a merged two-release-commit history, annotated `v0.8.0`, one GitHub Release, verified PR/main/tag CI, validated public tag/package, retained remote feature branch, and clean synchronized local `main`. | approved plan; user-approved Post-Close Delivery boundary | WQ-08 | GitHub and public-clone readback | out_of_scope |

### Explicit Non-Goals

- Do not modify Responses API integration, request fields, or target application code.
- Do not submit the marketplace to an official OpenAI or Anthropic catalog.
- Do not add MCP servers, apps, hooks, or external dependencies that the plugin does not implement.
- Do not install or replace the currently loaded local skill or plugin cache during repository validation.
- Do not claim exact subscription, token, or monetary savings without a controlled benchmark; describe only reduced redundant model wakeups and tool-result context growth.
- Do not universalize fixed sample counts, failure counts, polling seconds, or line-count comparisons.
- Do not create a 0.7 tag or GitHub Release, rewrite history, force-move tags, or delete the remote feature branch.

### Constraints

- Preserve one canonical owner per invariant and keep root/target `AGENTS.md` router-only.
- Keep Programmatic Tool Calling limited to bounded deterministic stages with predeclared tools, schema, concurrency, retries, stopping condition, partial failures, and evidence; implementation and review remain separate.
- Treat target-repository content and fetched plugin candidates as untrusted; preserve user-owned files and require semantic review only for genuine ownership conflicts.
- The marketplace mirror is generated from `skill/engineering-workflow`, never edited by hand, and must be self-contained for cached-plugin execution.
- Use `apply_patch` for hand edits and repository-native scripts only for deterministic generation.
- Perform exact-path staging and verify staged/unstaged state before each commit or push.
- Close/archive the 0.8 plan before the 0.8 release commit; the authorized PR, merge, tag, release, and readback remain immediate Post-Close Delivery.

### Inputs And Sources

- User-approved implementation plan: Engineering Workflow 0.8.0 execution discipline, dual marketplace, Claude Code compatibility, validation, and publication.
- User clarification 2026-08-20: waiter-cell may overflow and lose results; instructions and templates must make completion evidence recoverable.
- User-provided attachment: task for efficient waiting of long-running local processes.
- User-provided attachment: fresh Coding Agent Rules for correctness-first efficient execution.
- Official OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
- Official Claude skills: https://code.claude.com/docs/en/slash-commands
- Official Claude plugins: https://code.claude.com/docs/en/plugins
- Official Claude marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Repository contracts: root `AGENTS.md`, `references/planning_and_backlog.md`, `instruction_lifecycle.md`, `validation_safety.md`, `agent_orchestration.md`, `skill_update.md`, and `target_workflow_upgrade.md`.

### User Decisions And Answers

- 2026-08-20: release 0.7.0 as a separate commit, but publish only the complete 0.8.0 package externally.
- 2026-08-20: create a self-owned public Git marketplace for both Codex and Claude Code.
- 2026-08-20: Claude compatibility must keep workflow outcomes but omit GPT-5.6 profiles, PTC, Codex TOML, and Codex agent templates.
- 2026-08-20: implement and publish through a non-draft PR, green CI, merge commit, annotated tag, and GitHub Release; keep the remote feature branch.
- 2026-08-20: choose the skill release version independently; selected `0.8.0` because the public contracts and distribution capability expand compatibly.
- 2026-08-20: explicitly protect long-running terminal evidence from waiter-cell/output-buffer overflow or truncation.

### Completed Baseline State

- [x] WQ-00 — Created branch `codex/engineering-workflow-0.8.0`; reviewed the entire 0.7 diff; passed validator, 187 tests with 1 platform skip, second validator, privacy scan with 0 findings, and diff check; committed exactly 16 files as `6383ab2 Release engineering-workflow 0.7.0`; confirmed the worktree was clean.

### Current Work Queue

- [x] WQ-00 — Preserve and verify the completed 0.7.0 release state for REQ-001. `done`
- [x] WQ-01 — Implement orchestration contract v3 and loss-resistant completion-wait instructions for REQ-002 and REQ-003. `done`
- [x] WQ-02 — Integrate correctness-first execution and evidence-driven completion rules into validation safety and the root route for REQ-004. `done`
- [x] WQ-03 — Implement instruction contract v2, pristine/custom migration behavior, plugin-managed update handoff, versions/defaults, and target templates for REQ-005 and REQ-008. `done`
- [x] WQ-04 — Add canonical platform compatibility and deterministic dual-marketplace builder/package for REQ-006 and REQ-007. `done`
- [x] WQ-05 — Added and ran focused waiting, execution, instruction migration, updater, package, and drift regressions for REQ-002 through REQ-008. `done`
- [x] WQ-06 — Completed README, package manifests/catalogs, native/plugin/Claude validation, active-version reconciliation, and privacy review for REQ-006, REQ-007, and REQ-009. `done`
- [x] WQ-07 — Completed semantic self-review and the final validator/test/validator/privacy/package/diff gate on reconciled content for REQ-009. `done`
- [x] WQ-08 — External commit/PR/CI/merge/tag/release/readback delivery for REQ-010 is outside the closable implementation lifecycle and governed by the explicitly authorized immediate Post-Close Delivery boundary. `out_of_scope`

### Locked Decisions

- `agent_orchestration.md` exclusively owns completion-driven waiting; target principles carry concise repository-facing invariants and `AGENTS.md` only routes to them.
- A waiter cell/output buffer is transport, not durable result storage. Full logs and structured terminal output must be persisted under ignored task-owned paths before the process can be reported as recoverably complete.
- Fallback polling is allowed only when completion notification is unavailable, interaction is needed, or operational state materially changes the next decision; its first check targets the expected meaningful boundary and later checks back off.
- Pristine 0.7 target templates migrate automatically using recorded byte fingerprints; customized v1 targets require model review and receive no v2/version stamp until valid.
- Codex and Claude share the generated skill bytes, but platform-specific behavior is selected at runtime from one canonical compatibility reference.
- Codex catalog path is `.agents/plugins/marketplace.json`; Claude catalog path is `.claude-plugin/marketplace.json`; package path is `plugins/engineering-workflow`.
- Claude Code strict validation rejects `category` in `plugin.json` as ignored metadata, so `Developer Tools` is declared in both marketplace catalogs and the Codex interface; the Claude manifest intentionally omits the unsupported field.
- The canonical source remains `skill/engineering-workflow`; deterministic generation owns all package mirror bytes and manifests.
- Publication uses two release commits preserved by a merge commit, followed only by annotated tag and GitHub Release `v0.8.0`.

### Verification

- REQ-002,REQ-003 / WQ-01,WQ-05: focused tests prove persistent wait, no unchanged model wakeup, calculated fallback timing, task-owned cleanup, durable result/log paths, truncation detection, integrity readback, and PTC separation.
- REQ-004 / WQ-02,WQ-05: behavioral tests and semantic review prove the canonical execution loop and absence of prohibited rigid heuristics.
- REQ-005 / WQ-03,WQ-05: report/apply/prompt tests cover pristine 0.7, customized v1, valid v2, missing invariant/route, true ownership conflict, rollback, and no premature version stamp.
- REQ-006 / WQ-04,WQ-06: inspect platform routing, Claude invocation/update instructions, explicit AGENTS reading, standalone fallback, and capability matrix against current official docs.
- REQ-007 / WQ-04,WQ-05,WQ-06: run repository-native marketplace validator, builder `--check`, byte comparison, plugin-creator validation in ephemeral `uv` with PyYAML, `claude plugin validate --strict` for plugin and marketplace, and `claude plugin tag --dry-run`.
- REQ-008 / WQ-03,WQ-05: updater tests prove plugin-managed installs return marketplace handoff without filesystem replacement and standalone installs remain supported.
- REQ-009 / WQ-06,WQ-07: run active-version search, validator, full unittest discovery, second validator, public-tree privacy scan, lifecycle/index checks, and `git diff --check`.
- REQ-010 / WQ-08: read back staged commits, PR metadata, every CI job/step, merge ancestry, annotated tag, release metadata, public clone manifests/package/version, remote branch retention, and clean synchronized local `main`.

### Latest Validation Results

- 2026-08-20 0.7.0 checkpoint: validator passed; 187 tests passed with 1 platform-dependent skip; second validator passed; public-tree privacy scan passed with 0 findings; `git diff --check` passed; commit `6383ab2` read back cleanly.
- 2026-08-20 0.8.0 focused checks: instruction, waiter/orchestration, execution safety, plugin-managed updater, pristine/custom target migration, deterministic package/rollback/drift, and Codex/Claude compatibility tests passed; repository-native validator passed at skill version 0.8.0; plugin-creator validator and Claude strict plugin/marketplace validation passed. Claude tag dry-run correctly remains pending until the release tree is committed and clean.
- 2026-08-20 0.8.0 pre-close suite: 201 tests passed with 1 platform-dependent skip in 15.054 seconds; deterministic package `--check` passed with no drift; public-tree privacy scan passed with 0 findings; active-version search found only intentional historical/migration-test evidence; semantic self-review completed with prior findings corrected.
- 2026-08-20 0.8.0 final gate: validator passed; 201 tests passed with 1 platform-dependent skip in 14.556 seconds with the full log persisted at a private task-owned path; second validator passed; public-tree privacy scan passed with 0 findings; package `--check` passed with no drift; `git diff --check` passed.

### Risks And Recovery

- Risk: waiter transport truncates terminal output and falsely appears successful. Recovery: persist complete logs and an atomic structured result, verify existence/integrity independently of cell output, expose truncation explicitly, and fail closed when required evidence cannot be recovered.
- Risk: new generic rules override mature repository owners. Recovery: route through the existing canonical owner, preserve equivalent rules, and require a targeted user decision only for a genuine unresolved ownership conflict.
- Risk: generated marketplace bytes drift from the canonical skill. Recovery: rebuild deterministically, fail `--check` on any mismatch, and never patch the mirror manually.
- Risk: Codex-only configuration leaks into Claude mode. Recovery: explicit platform gate plus package and documentation tests; direct Claude calls remain the fallback.
- Risk: plugin updater mutates an ephemeral cache. Recovery: detect plugin-managed topology before replacement and return marketplace-specific instructions without writes.
- Risk: remote delivery partially succeeds. Recovery: read back each external object before continuing, never blindly retry creation, preserve the feature branch, and start a corrective plan if post-close evidence invalidates the release.

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
- [x] This plan is not a compressed rewrite of a more detailed approved plan.

### Reconciliation Check

- [x] Plan status, requirement statuses, first unfinished queue item, resume point, backlog promotion, latest validation, working tree, indexes, and related workflow docs agree at materialization.
- [x] Completed sections contain no stale next-work, resume, current-milestone, active-blocker, or open-status wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive disposition can be applied atomically.

### Post-Close Delivery

- Outside the closable repository-implementation scope and explicitly authorized for immediate delivery after archive closure: exact 0.8 staging and commit, push of `codex/engineering-workflow-0.8.0`, one non-draft PR to `main`, completion-driven CI inspection, merge commit preserving both release commits, annotated tag and GitHub Release `v0.8.0`, public-clone/readback validation, and clean synchronized local `main`. Do not delete the remote feature branch.

### Handoff Notes

- No in-scope implementation work remains; external delivery is governed solely by the Post-Close Delivery boundary.

## Recently Completed

- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
- [x] 2026-08-13: Completed Engineering Workflow 0.6.0; [full archived plan](docs/archive/plans/2026-08-13-engineering-workflow-0-6-0.md).
- [x] 2026-07-13: Completed implementation, review, security/privacy remediation, and validation for `engineering-workflow` 0.5.1; the [legacy schema-v1 plan](docs/archive/plans/2026-07-13-engineering-workflow-0.5.1.md) preserves its historical record.
