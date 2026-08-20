# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Programmatic Tool Calling Runtime Contract 0.7.0

Status: done
Owner: root
Last Updated: 2026-08-16

### Goal

Release a reviewed `engineering-workflow` 0.7.0 repository state in which the installed skill can identify bounded Programmatic Tool Calling stages, render complete runtime instructions, preserve direct model judgment and target-repository ownership boundaries, and fall back safely when PTC is unavailable or unsuitable.

### Plan Origin

plan_mode_approved

### Requested Scope

- Add a canonical PTC decision and execution contract for repositories processed by the skill, with special care for mature repositories and their existing scripts, harnesses, instructions, and owners.
- Add a deterministic stage-assessment and instruction-rendering helper plus an installed runtime template; do not persist generic PTC rules into target-repository templates.
- Keep Responses API request handling and target application code out of scope; the model uses PTC only when the user launches the skill and the runtime exposes it.
- Re-audit the existing GPT-5.6 mapping, select the release version, update every active version/contract owner, and perform complete review and validation.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Canonical orchestration policy routes predictable, schema-known, reducible stages to PTC and semantic, approval, mutation, citation, artifact, or unknown-shape stages to direct work or a targeted question. | approved plan; official PTC guide | WQ-01, WQ-03 | focused decision-matrix tests and canonical-reference review | done |
| REQ-002 | A deterministic helper validates a model-supplied stage descriptor and returns `programmatic`, `direct`, or `ask`, rendering bounded instructions only for `programmatic`. | approved plan | WQ-02, WQ-03 | CLI/module tests cover eligible, disqualified, ambiguous, invalid, and unavailable-runtime cases | done |
| REQ-003 | Runtime instructions contain allowed tools, reduced schema/evidence, concurrency, retry, stop, structured failure, and direct handoff without changing Responses API or target application code. | user clarification; official PTC guide | WQ-01, WQ-02, WQ-03 | template/renderer tests and diff review show no API integration changes | done |
| REQ-004 | Mature repositories preserve local owners and prefer an adequate native script or harness; generic normative PTC prose is not copied into target `AGENTS.md`, principles, or plan templates. | user clarification; repository ownership contract | WQ-01, WQ-03 | mature-repository and template-boundary regressions | done |
| REQ-005 | Active skill version becomes `0.7.0`, orchestration contract becomes `2`, all active version owners agree, and existing GPT-5.6 role mappings remain unchanged after current review. | approved plan; official GPT-5.6 guidance | WQ-04 | validator and active-version search | done |
| REQ-006 | Entire change receives two review passes, privacy/hygiene checks, focused tests, and the complete repository gate with truthful lifecycle closure. | user request; repository working contract | WQ-05, WQ-06 | review log, full gate, lifecycle check/close | done |

### Explicit Non-Goals

- Do not add or modify Responses API request fields, callers, continuation loops, or target application integrations.
- Do not put API-only fields into Codex TOML or invent a Codex configuration key for PTC.
- Do not copy a universal PTC invariant into target `AGENTS.md`, project-principles, or `PLANS.md` templates.
- Do not change the current GPT-5.6 model-role mapping without measured evidence of a regression or unsupported model.
- Do not install/update the local loaded skill, commit, push, tag, publish, deploy, or rewrite history without separate authorization.

### Constraints

- The canonical policy owns semantics once; routers, templates, tests, and README may link or enforce but must not duplicate normative prose.
- Candidate discovery and semantic routing remain direct model judgment. The helper may validate supplied facts and render instructions, not choose repository architecture.
- Programmatic execution is restricted to bounded non-side-effecting stages with known result schemas; retries are at most one and concurrency is explicitly capped.
- Existing user-owned files and unrelated worktree changes must be preserved.
- Repository-changing work follows planning schema 2 and closes only through `plan_lifecycle.py`.

### Inputs And Sources

- User request: assess and adopt Programmatic Tool Calling in the workflow, then clarified that the skill should form instructions and request model use at suitable points without changing Responses API.
- Approved implementation plan from 2026-08-16: runtime decision gate, installed instruction template, deterministic helper, mature-repository precedence, version `0.7.0`, orchestration contract `2`, full review.
- Official OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
- Official Programmatic Tool Calling guide: https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling
- Repository owners: `skill/engineering-workflow/SKILL.md`, `references/agent_orchestration.md`, `references/model_profiles.md`, planning/version validators and tests.

### User Decisions And Answers

- 2026-08-16: PTC applies while the skill processes target repositories; applicability must be decided per repository, especially for mature repositories.
- 2026-08-16: Do not change Responses API or target application code; form only the runtime instructions and request model use in suitable stages.
- 2026-08-16: Use templates where appropriate, but design the ownership boundary carefully.
- 2026-08-16: If candidate facts remain materially ambiguous after read-only investigation, ask one targeted question rather than guessing.
- 2026-08-16: Model and release-version selection is delegated to the implementer; selected release is `0.7.0`, while the already-current GPT-5.6 role mapping remains unchanged.

### Completed Baseline State

- [x] WQ-00 — Reconciled `main` with `origin/main`, confirmed a clean starting worktree, reviewed history/blame for the existing orchestration/model mapping, fetched current official GPT-5.6/PTC guidance, and established a green baseline: validator passed, 171 tests passed, 1 platform-dependent test skipped, final validator and `git diff --check` passed.

### Current Work Queue

- [x] WQ-01 — Updated the canonical runtime router and orchestration policy for REQ-001, REQ-003, and REQ-004. `done`
- [x] WQ-02 — Implemented the descriptor assessor and installed runtime instruction template for REQ-002 and REQ-003. `done`
- [x] WQ-03 — Added behavioral, rendering, mature-repository, and non-mutation regression coverage for REQ-001 through REQ-004. `done`
- [x] WQ-04 — Updated version `0.7.0`, orchestration contract `2`, model-source snapshot, README/defaults, and every active owner for REQ-005. `done`
- [x] WQ-05 — Ran focused checks and two complete diff/history/privacy review passes; remediated all findings for REQ-006. `done`
- [x] WQ-06 — Ran the full final gate, reconciled lifecycle state, completed atomic archive closure, and verified the final tree for REQ-006. `done`

### Locked Decisions

- Use an installed runtime template under the skill assets; do not alter target instruction/plan/principles templates with generic normative PTC text.
- Keep PTC selection unavailable-safe: direct calls remain the fallback and completed calls must not be repeated.
- Keep architecture selection, implementation, semantic review, approval, destructive/external writes, browser/citation work, native-artifact delivery, and final validation direct.
- Preserve `gpt-5.6-terra` for utility/explorer and `gpt-5.6` (Sol alias) for standard/review; this change is orchestration behavior, not a blind model-string migration.
- Treat the public runtime contract and manifest contract change as minor SemVer `0.7.0` with `orchestration_contract_version: 2`.

### Verification

- REQ-001 / WQ-01,WQ-03: run focused orchestration decision tests covering aggregation, deduplication, dependent predictable calls, single calls, adaptive search, semantic judgment, approvals, writes, citations, native artifacts, and unknown schemas.
- REQ-002 / WQ-02,WQ-03: validate descriptor errors, normalized decisions, rendered placeholder replacement, evidence preservation, retry/concurrency bounds, and stable JSON/CLI exit behavior.
- REQ-003 / WQ-01,WQ-02,WQ-03: search the diff for Responses API request fields and confirm only skill runtime instructions/helper code changed.
- REQ-004 / WQ-01,WQ-03: verify a mature fixture prefers an adequate repository-native path and that target `AGENTS.md`, project-principles, and plan templates do not gain duplicated PTC rules.
- REQ-005 / WQ-04: run active-version/model-owner searches and `validate_skill_repo.py` to prove version and contract agreement.
- REQ-006 / WQ-05,WQ-06: run focused tests, two review passes, public-tree privacy scan, the complete repository gate, and `git diff --check`.

### Latest Validation Results

- 2026-08-16 pre-change baseline: `validate_skill_repo.py` passed; 171 unit tests passed and 1 platform-dependent non-UTF-8 test skipped; second validator and `git diff --check` passed.
- 2026-08-16 focused final-content checks: 49 orchestration/policy/upgrader tests passed; skill validator passed for version `0.7.0`; plan lifecycle check and `git diff --check` passed.
- 2026-08-16 first semantic review: corrected README ownership summary, in-memory descriptor handling, call-bound consistency, instruction-control sanitization, failure payload guidance, and target-template enforcement.
- 2026-08-16 second semantic review: rechecked official GPT-5.6, PTC, and Codex subagent guidance; preserved the existing model mapping; added strict nested-schema validation, strict JSON parsing, descriptor/list bounds, single-line handoff fields, and explicit concurrency safety. Focused coverage now passes 78 tests with 1 platform-dependent skip, and the skill validator passes for `0.7.0`.
- 2026-08-16 pre-closure final-content gate: public-tree privacy scan passed with 0 findings; skill validator passed; 186 unit tests passed with 1 platform-dependent non-UTF-8 skip; the second skill validator and `git diff --check` passed.
- 2026-08-16 post-closure final-tree gate: lifecycle index check and public-tree privacy scan passed with 0 findings; skill validator passed; 186 unit tests passed with 1 platform-dependent non-UTF-8 skip; the second skill validator and `git diff --check` passed.

### Risks And Recovery

- Risk: generic PTC instructions leak into mature target repositories and override local ownership. Recovery: keep the template installed-only, retain target templates unchanged, and add explicit boundary tests.
- Risk: the assessor turns semantic architecture judgment into a brittle keyword classifier. Recovery: accept only explicit model-supplied stage facts, return `ask` for missing material facts, and keep candidate discovery direct.
- Risk: a correct program result loses required evidence in final synthesis. Recovery: require evidence fields in the rendered result contract and direct final validation.
- Risk: version or manifest contract owners drift. Recovery: centralize constants where practical, search every active owner, and let the validator fail closed.
- Recovery for implementation regressions: revert only task-owned edits with targeted patches while retaining this active plan and exact failing evidence.

### Resume Point

- No unfinished in-scope work remains; archive closure and final-tree validation are complete.

### Plan Fidelity Check

- [x] Every agreed outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point records that no unfinished queue item remains.
- [x] This plan is not a compressed rewrite of a more detailed approved plan.

### Reconciliation Check

- [x] Plan status, terminal requirement and queue states, no-unfinished-work resume point, backlog disposition, latest validation, working tree, indexes, and related workflow docs agree after closure.
- [x] Completed sections contain no stale next-work, resume, current-milestone, active-blocker, or open-status wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive disposition was applied atomically, required indexes pass, and the detailed contract and review record remain useful for future migrations.

### Post-Close Delivery

- Commit, push, tag, publication, CI observation, and local installed-skill refresh are out of scope without separate current authorization.

### Handoff Notes

- No external writes are authorized. Preserve the final working-tree diff and exact validation evidence for user review.

## Recently Completed

- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
- [x] 2026-08-13: Completed Engineering Workflow 0.6.0; [full archived plan](docs/archive/plans/2026-08-13-engineering-workflow-0-6-0.md).
- [x] 2026-07-13: Completed implementation, review, security/privacy remediation, and validation for `engineering-workflow` 0.5.1; the [legacy schema-v1 plan](docs/archive/plans/2026-07-13-engineering-workflow-0.5.1.md) preserves its historical record.
