# Execution Plans

Use this file for active, blocked, or recently completed execution work.

For any task that changes repository state, update this file before implementation and again before handoff.
Use a full active plan for active repo-changing work. Compact only completed work after validation and handoff are recorded.

## Active Plan: Engineering Workflow Skill 0.5.0

Status: in_progress
Owner: Codex root agent
Last Updated: 2026-07-13
plan_schema_version: 1

### Goal

Upgrade `engineering-workflow` from `0.4.1` to `0.5.0` while preserving the verified `0.4.1` reconciliation contract, making the runtime skill a lean router with single canonical owners for detailed policy, adding safe self-update and target-workflow migration modes, strengthening validation and privacy guarantees, reviewing the completed diff, removing public leaks from both the current tree and Git history, and publishing the sanitized rewritten history to GitHub with a guarded force-push.

### Plan Origin

`direct_execution`

### Requested Scope

- Preserve the full structured user specification instead of reducing it to a smaller convenience patch.
- Materialize a complete active plan before changing implementation, configuration, tests, templates, or workflow documentation.
- Verify the named official OpenAI sources and record material documentation drift before implementation.
- Refactor the skill and its references, templates, scripts, validator, tests, and public documentation to the `0.5.0` contracts.
- Preserve all compatible baseline behavior and the `0.4.1` post-compaction, interruption, resume, milestone-closure, and stale-completed-state safeguards.
- Run the required validation, privacy checks, duplicate-owner checks, format parsing, version checks, and a complete manual diff/code review.
- Scan the tracked public tree and every reachable commit for workstation paths, credential-like material, secrets, private URLs, and related privacy leaks.
- Remove confirmed leaks from the current content, rewrite every affected commit, verify the rewritten history, and update GitHub `main` with a guarded force-push.

### Requirement Traceability

| ID | Requirement | Source | Work Queue | Acceptance / Validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Require a full durable active `PLANS.md` for every repo-changing task, with no lightweight exception, and materialize Plan Mode or direct-execution plans before implementation writes. | User specification sections 1.1-1.3 | WQ-01, WQ-05 | Planning reference, router invariant, template, validator, and tests cover both Plan Mode exit and direct execution. | done |
| REQ-002 | Add stable requirement IDs, traceability, the complete plan schema, fidelity checks, exact resume-point rules, and protection against compressed active plans. | User specification sections 1.4-1.6 | WQ-01, WQ-05, WQ-09 | Template/schema validation and behavioral tests cover every required section and declared source. | done |
| REQ-003 | Preserve or strengthen all `0.4.1` reconciliation semantics across compaction, interruption, resume, milestone closure, handoff, and session changes; completed state must not look active. | User specification sections 1.7-1.8; baseline contract | WQ-01, WQ-05, WQ-09 | Existing regression coverage remains or is replaced by stronger behavioral tests. | done |
| REQ-004 | Verify all named official OpenAI sources, prefer current documentation, and record material differences from the specification. | User specification section 2 | WQ-02 | Source notes are recorded below and reflected in canonical references without inventing unsupported Codex fields. | done |
| REQ-005 | Make `SKILL.md` a concise runtime router while keeping the listed hard invariants explicit and assigning one canonical owner to each detailed contract. | User specification sections 3.1-3.2 | WQ-03, WQ-05 | Router is shorter; required links/invariants exist; duplicate-contract scan is clean. | done |
| REQ-006 | Replace long exact-prose validator coupling with headings, links, structured markers, parseable metadata, plan-schema fields, semantic ownership checks, duplicate-owner checks, and behavioral tests. | User specification section 3.3 | WQ-05, WQ-09 | Validator no longer treats long prose as public API; old reconciliation coverage is retained. | done |
| REQ-007 | Document repository workflow modes and distinct skill lifecycle modes with unambiguous invocation semantics and one targeted question only when evidence cannot resolve ambiguity. | User specification section 4 | WQ-03, WQ-05 | Canonical references and tests cover all named modes and phrases. | done |
| REQ-008 | Add a universal deterministic-first agent orchestration policy with root ownership, bounded independent fan-out, single-writer shared state, explicit subagent contracts, depth `1`, and no model-based sleep/poll loops. | User specification sections 5.1-5.2 and 5.8 | WQ-04, WQ-05 | Canonical policy and behavioral checks cover routing, ownership, fan-out, nesting, and monitoring. | done |
| REQ-009 | Add one canonical current model mapping and optional utility/explorer/reviewer templates using supported model/reasoning guidance without API-only or invented Codex settings. | User specification sections 5.3-5.7 and 5.9 | WQ-02, WQ-04, WQ-09 | Mapping has one owner; utility has no expensive reasoning; no invented pro model slug; YAML/TOML parse. | done |
| REQ-010 | Separate `refresh_loaded_skill` from `update_installed_skill`; refresh must be local/read-only and update must change only the active installed skill. | User specification sections 6.1-6.2 and 6.7 | WQ-04, WQ-06 | Reference, README prompts, and tests distinguish refresh, update, and target migration. | done |
| REQ-011 | Implement `update_installed_skill.py` with the full CLI, symlink/git/copy handling, canonical trust boundary, validation, backup, atomic replacement, rollback, downgrade rules, and structured results. | User specification sections 6.3-6.6 | WQ-06, WQ-09 | Offline temporary-git tests cover all listed success/refusal/rollback cases. | done |
| REQ-012 | Implement `upgrade_target_workflow` as a separate audited plan/apply migration with discovery, ownership classification, conflict report, mutation boundaries, structural TOML merge, and state manifest. | User specification section 7 | WQ-07, WQ-09 | Dry-run/apply tests cover missing/existing plans and manifests, protected/unknown content, config preservation, and exact diff. | done |
| REQ-013 | Replace broad workflow ownership prefixes with exact canonical paths, manifest-managed paths, archive paths, and explicit section markers; unknown docs remain protected. | User specification section 8 | WQ-07, WQ-09 | Regression fixtures cover unknown files under `docs/codex/` and `docs/engineering/`. | done |
| REQ-014 | Enforce conservative read-only command parsing with token-aware rejection and route repo-authored tests/builds/linters to a credential-free disposable copy with timeout and cleanup. | User specification section 9 | WQ-08, WQ-09 | Safety tests cover allowed Git inspection and all listed shell/package/repo-code hazards. | done |
| REQ-015 | Expand privacy sanitization and public scanning to all tracked public text, including root `PLANS.md`, for macOS/Linux/Windows paths, file URLs, SSH material, internal hosts, credentials, tokens, passwords, and unintended private repository URLs. | User specification sections 10 and 10.1 | WQ-01, WQ-08, WQ-10 | Current-tree privacy scan and unit tests cover every listed pattern without scanning excluded binary/cache/vendor content. | done |
| REQ-016 | Allow legitimate historical versions while enforcing active version consistency in the skill, README, prompts, manifests, and installation checks. | User specification section 10.2 | WQ-05, WQ-09 | Tests distinguish historical context from active stale-version mismatches. | done |
| REQ-017 | Convert the completed `0.4.1` plan to history, create this full `0.5.0` active plan first, remove workstation paths, and pass the fidelity gate before other edits. | User specification section 11 | WQ-01 | This file contains the complete schema, no workstation path, and a passing fidelity/reconciliation record. | done |
| REQ-018 | Bump every active version source from `0.4.1` to `0.5.0`, preserve legitimate history, and keep `agents/openai.yaml` aligned with the revised skill. | User specification sections 12-13; skill-creator guidance | WQ-03, WQ-05, WQ-09 | Validator, version search, metadata readback, and OpenAI YAML validation pass. | done |
| REQ-019 | Add or update all behavioral tests listed for planning, orchestration, self-update, target upgrade, ownership, validation safety, and privacy. | User specification section 14 | WQ-09 | Full unittest suite passes and retains equivalent `0.4.1` coverage. | done |
| REQ-020 | Run all required repository gates plus YAML, TOML, JSON, version, prompt, privacy, model, ownership, planning, reconciliation, and duplicate-contract checks. | User specification section 15 | WQ-10 | Every named check has an exact recorded result. | done |
| REQ-021 | Perform a complete code review of the final change set, including correctness, security, privacy, rollback, scope, and contract consistency, and fix all confirmed findings. | Direct user request; user specification sections 15 and 17 | WQ-11 | Two-pass full-diff review records findings and resolutions; no unresolved actionable issue remains. | done |
| REQ-022 | Scan all reachable Git history for privacy/secret leaks, remediate confirmed findings, rewrite all affected commits, rescan, and force-update GitHub safely. | Direct user request, overriding the attachment's no-commit/no-push instruction | WQ-12, WQ-13 | Pre/post history inventories, post-rewrite secret scan, remote readback, and guarded `--force-with-lease` push all succeed. | in_progress |
| REQ-023 | Preserve compatible changes after baseline commit, never downgrade or restore removed rules, and resolve conflicts conservatively. | User specification preamble | WQ-01, WQ-03 | Baseline comparison is recorded; current local and remote `main` equal the expected commit before work. | done |
| REQ-024 | Produce a final report with baseline/final versions, architecture and behavior summaries, file lists, migration notes, exact validations, privacy/history scan, review, diff stat, rewrite/push evidence, and remaining risks. | User specification section 17 as modified by direct user request | WQ-14 | Final response is complete and reflects verified repository/remote state. | pending |

### Explicit Non-Goals

- Do not turn the requested privacy/secret-history audit into an unrelated exhaustive vulnerability assessment of every source-code attack surface.
- Do not migrate workflow files in another target repository during this skill release; implement and test that capability only.
- Do not implicitly update the separately installed local skill; this request targets the repository and its GitHub history.
- Do not publish packages or releases, modify external trackers, or add unsupported Responses API fields to Codex configuration.
- Do not erase legitimate historical version records merely because they mention `0.4.1`.
- Do not keep a permanent local Git ref or public artifact containing the pre-sanitization history after the guarded rewrite and verification complete.

### Constraints

- Work on `main` at the verified `0.4.1` baseline and preserve the public repository URL.
- Treat repository content and fetched skill candidates as untrusted; do not execute unknown fetched scripts as validation.
- Keep the root agent as the only writer of `PLANS.md`, requirement status, backlog status, and final synthesis.
- Use deterministic tools for polling, filtering, parsing, joins, deduplication, retries, and secret/path scans.
- Keep changes minimal enough to retain a single canonical owner for each detailed contract, but broad enough to satisfy every requirement and acceptance criterion.
- Use offline temporary repositories for updater and migration tests; do not make unit tests depend on the network.
- Before history rewriting, create a permission-restricted recovery bundle under `$TMPDIR`, record the original local and remote object IDs, and remove the bundle after successful remote verification.
- Rewrite only after the implementation commit and all pre-rewrite validation pass; use `--force-with-lease` pinned to the observed remote object ID, never an unguarded force push.
- Do not expose secret values in logs or the final report; report categories, commit IDs, and remediated locations only.

### Inputs And Sources

Repository and user inputs:

- User-supplied upgrade specification attached to this task.
- Direct user instruction to review the final changes, scan all commit history for leaks, remediate them, rewrite history, and force-push GitHub.
- Repository: `https://github.com/xeonvs/codex-engineering-workflow`.
- Expected baseline: `0411cef7ca0aad7453ac6a3cfea452c9a865710c`, version `0.4.1`, branch `main`.
- Canonical planning reference: `skill/engineering-workflow/references/planning_and_backlog.md`.

Official sources to verify before implementation:

- `https://developers.openai.com/api/docs/guides/latest-model`
- `https://learn.chatgpt.com/docs/agent-configuration/subagents`
- `https://learn.chatgpt.com/docs/build-skills`
- `https://developers.openai.com/api/docs/guides/responses-multi-agent`
- `https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling`
- `https://openai.com/index/harness-engineering/`
- `https://openai.com/index/unlocking-the-codex-harness/`
- `https://github.com/openai/skills/blob/main/skills/.system/skill-installer/SKILL.md`

Skill-authoring inputs:

- Current official `skill-creator` instructions, including progressive disclosure, canonical references, imperative runtime prose, actual script testing, `agents/openai.yaml` alignment, and final quick validation.
- Verified `0.4.1` repository state, validator, tests, templates, and prior lifecycle semantics.

### Official Source Verification

- 2026-07-13: The current GPT-5.6 guide confirms that `gpt-5.6` aliases the flagship `gpt-5.6-sol`, while `gpt-5.6-terra` is the balanced lower-cost choice and `gpt-5.6-luna` is the efficient high-volume choice. It recommends preserving the current reasoning baseline, testing one level lower, reserving high/xhigh/max for measured gains, and treating pro as Responses API `reasoning.mode: "pro"`, not a separate model slug.
- 2026-07-13: The same guide confirms leaner prompts, explicit hard constraints/approval boundaries/success criteria, persisted-reasoning and pro settings as API features, Programmatic Tool Calling for bounded predictable reduction, and direct calls for approvals, semantic judgment, citations, native artifacts, and final validation.
- 2026-07-13: Current Codex subagent documentation confirms demanding agents should normally start with `gpt-5.6`; faster read-heavy agents may use `gpt-5.6-terra`; reviewer/security work may use `high`; `minimal` and `none` are conditional on model support and low reasoning need. Custom-agent TOML requires `name`, `description`, and `developer_instructions`; optional `model`, `model_reasoning_effort`, and `sandbox_mode` inherit when omitted.
- 2026-07-13: Current Codex defaults are `agents.max_threads = 6` and `agents.max_depth = 1`; unset CSV worker runtime falls back to 1800 seconds. This release will preserve existing thread caps, keep depth `1`, and avoid presenting all capacity as a recommended fan-out budget.
- 2026-07-13: Current Codex guidance still favors parallel read-heavy work and warns about parallel write-heavy conflicts. Current Responses Multi-agent guidance independently supports bounded workstreams, focused contexts, root synthesis, and one agent for ordered chains, shared mutable resources, one slow operation, or fixed deterministic graphs. Responses-specific fields will not be copied into Codex TOML.
- 2026-07-13: Current Build Skills documentation confirms progressive disclosure; `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`; explicit and implicit activation; symlink support; automatic change/new-install detection with restart only if detection fails.
- 2026-07-13 material drift: current Build Skills authoring/discovery paths are repository/user `.agents/skills`, admin `/etc/codex/skills`, and bundled system skills. The official skill-installer still installs into `$CODEX_HOME/skills` (defaulting to the legacy user directory). The skill must describe both facts rather than assume one universal installation path.
- 2026-07-13: Harness Engineering supports a short `AGENTS.md` map, repository knowledge as the system of record, versioned execution plans, mechanical checks, doc gardening, and architecture invariants. Its lightweight-plan example remains intentionally overridden here by the stronger product-specific full-plan guardrail.
- 2026-07-13: The App Server article describes durable thread/turn/item lifecycles, persisted state, client/server translation, sandboxed tool execution, extensions, and approval pauses. It does not itself name a formal `control plane`/`execution plane`; any such split in this skill will be labeled as an architectural interpretation rather than quoted Codex configuration terminology.
- 2026-07-13 source-route note: the official Codex manual helper failed closed because the response lacked its required integrity header. The Developer Docs MCP was installed for future sessions but cannot become callable until restart, so this task used the same official pages through the official-domain web fallback required by `openai-docs`.

### User Decisions And Answers

- 2026-07-13: The task is direct execution, not Plan Mode; therefore `Plan Origin` is `direct_execution` and the first repository write is this complete active plan.
- 2026-07-13: The direct request to commit, rewrite history, and force-push is newer and more specific than the attachment's statements forbidding commit/push. The direct request supersedes acceptance item 31 and the matching final-report confirmations.
- 2026-07-13: The requested leak scan is a targeted public/privacy/secret scan across the tracked tree and complete Git history, not a general exhaustive vulnerability scan.
- 2026-07-13: A guarded history rewrite is explicitly authorized. Use a recovery bundle and `--force-with-lease` pinned to the pre-rewrite remote object ID.
- No other user answer is currently required; ownership and scope are resolved by repository evidence and the detailed specification.

### Completed Baseline State

- [x] Local branch is `main`, working tree is clean, and local HEAD is `0411cef7ca0aad7453ac6a3cfea452c9a865710c`.
- [x] Remote `origin/main` resolves to the same object ID; there are no post-baseline changes to preserve or describe.
- [x] Current skill version is `0.4.1`; repository topology and expected canonical planning path exist.
- [x] The previous `0.4.1` active plan was genuinely complete and has been compacted below into `Recently Completed` rather than retained as stale active work.
- [x] Baseline privacy evidence confirms the old root plan contains workstation-specific paths that must be removed from both the current tree and historical commits.
- [x] The full user specification, direct override, official source URLs, requirements, validations, recovery constraints, and exact resume point are preserved in this active plan.

### Current Work Queue

1. <a id="wq-01"></a>**WQ-01 — Plan materialization and baseline reconciliation**: write this full plan as the first repository change; compact the closed `0.4.1` plan; remove workstation paths; verify traceability, fidelity, and the clean baseline. Covers REQ-001, REQ-002, REQ-003, REQ-015, REQ-017, REQ-023. `done`
2. <a id="wq-02"></a>**WQ-02 — Official-source verification**: fetch/read every named official source, compare current facts with the task, and record material drift and supported configuration/model guidance. Covers REQ-004, REQ-009. `done`
3. <a id="wq-03"></a>**WQ-03 — Canonical architecture and router**: map existing ownership, refactor `SKILL.md` into a lean invariant/router, bump metadata, align README and `agents/openai.yaml`, and keep lifecycle modes distinct. Covers REQ-005, REQ-007, REQ-018, REQ-023. `done`
4. <a id="wq-04"></a>**WQ-04 — Canonical policies**: add/update planning, orchestration, model, privacy, validation, skill-update, and target-upgrade references plus optional agent templates. Covers REQ-008, REQ-009, REQ-010. `done`
5. <a id="wq-05"></a>**WQ-05 — Templates and structural validator**: implement the plan schema and state manifest templates, concise pointers, semantic ownership checks, and behavioral rather than long-prose validation. Covers REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007, REQ-016, REQ-018. `done`
6. <a id="wq-06"></a>**WQ-06 — Installed-skill updater**: implement the safe updater, trust boundary, installation-type behavior, structured result, backup/rollback, and CLI contract. Covers REQ-010, REQ-011. `done`
7. <a id="wq-07"></a>**WQ-07 — Target workflow upgrade**: implement audit/plan/apply migration, exact ownership, conflict reporting, manifest handling, mutation boundaries, and structural TOML merge. Covers REQ-012, REQ-013. `done`
8. <a id="wq-08"></a>**WQ-08 — Validation and sanitization safety**: implement token-aware command classification, disposable-copy rules, expanded sanitization, and tracked-public-text scanning. Covers REQ-014, REQ-015. `done`
9. <a id="wq-09"></a>**WQ-09 — Behavioral test expansion**: add temporary-repository tests and fixtures for every planning, routing, update, migration, ownership, command-safety, privacy, and historical-version contract. Covers REQ-001 through REQ-019 where executable acceptance applies. `done`
10. <a id="wq-10"></a>**WQ-10 — Required validation**: run repository validator, full unittest suite, `git diff --check`, YAML/TOML/JSON parsing, version/prompt/model/owner/planning/reconciliation checks, current-tree privacy scan, and skill quick validation. Covers REQ-015, REQ-018, REQ-020. `done`
11. <a id="wq-11"></a>**WQ-11 — Full code and diff review**: perform two complete passes over the final change set, record severity/evidence, fix confirmed issues, rerun affected tests, and ensure no scope or contract was silently dropped. Covers REQ-021. `done`
12. <a id="wq-12"></a>**WQ-12 — Pre-rewrite history audit and implementation commit**: scan every reachable commit with available secret scanners plus deterministic path/credential rules, classify findings without printing values, create the restricted recovery bundle, and commit the validated `0.5.0` tree. Covers REQ-022. `done`
13. <a id="wq-13"></a>**WQ-13 — History rewrite and guarded GitHub update**: rewrite all affected commits, rescan the rewritten tree/history, rerun strong validation, verify remote lease, force-push sanitized `main`, read back GitHub state, and delete the recovery bundle/local legacy refs. Covers REQ-022. `in_progress`
14. <a id="wq-14"></a>**WQ-14 — Closure and handoff**: reconcile every requirement and queue status, close/compact active state only when remote verification is complete, and report exact files, gates, history rewrite, push, risks, and commit IDs. Covers REQ-024. `pending`

### Locked Decisions

- `references/planning_and_backlog.md` owns detailed planning, fidelity, traceability, and reconciliation policy.
- `references/agent_orchestration.md` owns agent routing; `references/model_profiles.md` alone owns current concrete model mappings.
- `references/skill_update.md` owns installed-skill refresh/update behavior; `references/target_workflow_upgrade.md` separately owns target migration.
- `references/validation_safety.md` owns command/disposable-copy safety; `references/privacy_and_sanitization.md` owns public privacy policy.
- `SKILL.md` retains only the mandatory invariant and routing criterion for each detailed owner.
- Root remains the only writer for shared workflow state; deterministic checks remain outside LLM subagents.
- The release version is `0.5.0`, because the planning schema, lifecycle modes, orchestration, self-update, migration, ownership, and validation boundaries all change.
- The GitHub rewrite will use an explicit lease against the verified pre-rewrite `origin/main` object ID.

### Verification

Required repository gates:

- `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- Parse every tracked YAML, TOML, and JSON fixture with safe parsers.
- Run the official skill quick validator against `skill/engineering-workflow`.

Targeted contract checks:

- Version consistency across active metadata, README, update prompts, and manifests.
- Absence of an invented pro model slug and API-only pro configuration fields.
- Exactly one canonical concrete model mapping owner.
- No high/expensive default in utility templates.
- Full plan required for every repo-changing path, while read-only and direct execution behave correctly without Plan Mode.
- `0.4.1` reconciliation and stale-completed-state semantics retained.
- Duplicate detailed-contract scan and manual owner/link review.
- Current tracked-public-tree privacy scan with binary/cache/vendor exclusions.
- Full reachable-history privacy and secret scan before and after rewrite.
- Two-pass complete diff/code review and rerun of all affected gates.
- Remote object-ID readback after guarded force-push; no legacy local ref or recovery bundle remains.

### Latest Validation Results

- 2026-07-13 baseline: `git status --short --branch` showed clean `main` tracking `origin/main`.
- 2026-07-13 baseline: local HEAD and remote `main` both resolved to `0411cef7ca0aad7453ac6a3cfea452c9a865710c`.
- 2026-07-13 baseline: diff from expected baseline to HEAD is empty.
- 2026-07-13 plan gate: complete; all required sections are present, 24 requirements map to 14 queue items, the fidelity/reconciliation checks pass, and the only current tracked change is this sanitized `PLANS.md`.
- 2026-07-13 official-source gate: complete through current official web pages after the integrity-checking manual helper failed closed; material discovery-path, custom-agent-schema, model/reasoning, multi-agent, PTC, harness, and installer facts are recorded above.
- 2026-07-13 implementation checkpoint: structural validator passes with zero findings; all 86 offline behavioral tests pass, including copied/symlink/Git updates, rollback, target migration, planning, ownership, command safety, orchestration, and privacy.
- 2026-07-13 release gate: validator passed; 103 tests passed; Ruff reported no issues; `git diff --check` passed; tracked/untracked public privacy scan returned zero findings; target read-only validation passed with expected synthetic prompt-injection warnings; CLI help smokes passed; official skill quick validator passed; PyYAML parsed 4 files, TOML parsed 3 templates, and no JSON fixtures were present.
- 2026-07-13 two-pass review: fixed symlink traversal and canonical-symlink mutation boundaries, disposable-copy network/write/home-read isolation, candidate checkout-filter exposure, credential-bearing source URLs, backup containment, symlink-aware update diffs, multi-plan parsing, protected-file verification, vendor/cache exclusions, TOML inline/header edge cases, and stale-completed multiline parsing. Every confirmed finding has regression coverage and no actionable review finding remains.
- 2026-07-13 pre-rewrite deterministic history audit: scanned all 5 reachable commits and 106 unique blobs without printing candidate values. Confirmed workstation-specific macOS paths in historical `PLANS.md`; the remaining rule matches were purpose-built privacy test fixtures. Commit messages and already-public GitHub noreply metadata contained no private finding.
- 2026-07-13 independent secret scan: checksum-verified Gitleaks 8.30.1 reported zero findings in the current working tree and one historical generic-key match in the initial synthetic sanitizer test fixture. The history rewrite will fragment that fixture without changing its runtime value and replace historical workstation paths with portable placeholders, then both scanners will rerun over every rewritten commit.
- 2026-07-13 pre-rewrite checkpoint: committed the validated implementation, verified that GitHub `main` still matches the recorded baseline lease, and created a verified `0600` recovery bundle outside the repository before rewriting any object.
- 2026-07-13 rewrite dry-run follow-up: the all-history email rule exposed that `sanitize_output.py --public-tree` did not apply the direct-input email rule. The public-tree path now uses the same scanner without following symlinks, synthetic email literals are fragmented while preserving runtime values, and regression coverage verifies root-level email detection.

### Risks And Recovery

- History rewriting changes every affected commit ID and can disrupt downstream clones. Record the old-to-new map and call out required rebase/reclone behavior in the final report.
- A remote change between scan and push could be lost by an unguarded force push. Prevent this with an object-ID-specific `--force-with-lease`; stop rather than overwrite a changed remote.
- A recovery artifact itself contains the old history. Keep it permission-restricted under `$TMPDIR`, never publish it, and delete it only after verified remote success.
- Secret scanners can miss custom/private patterns or produce false positives. Combine available scanners with deterministic repository-specific rules and manually classify candidate categories without exposing values.
- New updater/migration scripts manipulate paths and Git repositories. Use temporary offline fixtures, path-containment checks, refusal defaults, backups, rollback tests, and never execute fetched candidate code.
- Canonical-owner refactoring can accidentally weaken `0.4.1`. Preserve behavioral tests before removing duplicate prose and perform a second complete diff review.

### Resume Point

Continue WQ-13 by amending this reconciled lifecycle state into the implementation commit, refreshing the restricted recovery bundle, and rewriting `main` with the classified sanitizer before the post-rewrite scans.

### Plan Fidelity Check

- [x] Every outcome in the user specification and the direct history-rewrite instruction maps to REQ-001 through REQ-024.
- [x] Every official source URL is preserved under `Inputs And Sources`.
- [x] The direct-execution origin, commit/push override, targeted scan scope, guarded force-push, and recovery decision are preserved under `User Decisions And Answers`.
- [x] No requirement was silently reduced to a smaller implementation subset.
- [x] WQ-01 through WQ-14 collectively cover every requirement ID and every requested lifecycle phase.
- [x] `Verification` covers all acceptance criteria, required commands, privacy/history scans, review, rewrite, and remote readback.
- [x] Explicit non-goals do not remove any requested outcome.
- [x] `Resume Point` identifies the first incomplete safe action.
- [x] This plan preserves the structure and detail of the supplied specification and is not a compressed chat summary.

### Reconciliation Check

- [x] Active plan, completed implementation/review gates, first unfinished queue item WQ-12, resume point, validation state, working tree, and remote baseline agree.
- [x] There is no separate active backlog or milestone state requiring reconciliation in this repository.
- [x] The previous `0.4.1` work is historical below and contains no stale active blocker, current milestone, resume instruction, or next-work status.
- [x] No implementation change preceded this plan; the only working-tree change at this gate is `PLANS.md`.

### Pre-Commit Closure

- Before the implementation commit, rerun all required validation, complete two review passes, record the exact results, and mark only genuinely completed requirements/queue items done.
- Before history rewrite and push, ensure this active plan no longer contains stale next-work state, but retain enough closed evidence for the rewritten commit.
- Do not commit or rewrite while any acceptance criterion is unresolved, except a clearly documented external risk that does not invalidate the release.

### Handoff Notes

- The attachment's no-commit/no-push statements are intentionally superseded by the direct user request; final reporting must describe the actual sanitized commit, history rewrite, and GitHub push rather than repeat those obsolete confirmations.
- If interrupted, reopen this file first, inspect changes since `Last Updated`, reconcile statuses and the first unchecked queue item, and resume from the `Resume Point` rather than reconstructing scope from memory.

## Recently Completed

- [x] 2026-07-08: Released `engineering-workflow` 0.4.1 with explicit post-compaction/interruption/resume/milestone reconciliation, stale completed-state guards, 28 passing tests, and verified local installation synchronization.
- [x] 2026-07-07: Released `engineering-workflow` 0.4.0 with pre-commit plan closure, active-plan archive policy, backlog cleanup rules, validator guardrails, and 26 passing tests.
- [x] 2026-07-07: Released `engineering-workflow` 0.3.1 with full active plans by default, anti-simplification guidance, validator guardrails, and 24 passing tests.
- [x] 2026-05-21: Updated `engineering-workflow` to the previous patch release with forced skill refresh guidance, planning/backlog lifecycle rules, completed-work cleanup policy, template updates, and validator coverage.
