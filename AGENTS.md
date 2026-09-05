# Repository Agent Instructions

This file is local guidance for agents developing this repository. It is not part of the installed `engineering-workflow` skill, is not copied into target repositories, and must never be read by runtime skill scripts. Target-repository instructions come only from `skill/engineering-workflow/assets/templates/AGENTS.md.tmpl` and repository-owned target documents.

## Repository Map

- `skill/engineering-workflow/SKILL.md` — lean public runtime router and active skill version.
- `skill/engineering-workflow/references/` — canonical detailed workflow contracts.
- `skill/engineering-workflow/scripts/` — deterministic audit, validation, migration, lifecycle, update, and privacy tools.
- `skill/engineering-workflow/assets/` — files copied or rendered into target repositories.
- `tests/` — offline behavioral and contract regressions.
- `scripts/dev_check.py` — root-only maintainer harness for bounded focused, layered, full, and pre-push checks.
- `pyproject.toml` and `requirements-dev.txt` — root-only pinned Ruff policy for this repository.
- `PLANS.md` — durable execution state for work on this repository.
- `docs/archive/` — future-useful closed plans and their navigation indexes.

## Task Routing

Reference paths beginning with `references/` below resolve under `skill/engineering-workflow/` in this repository.

| Trigger or changed area | Read before editing | Required gate |
| --- | --- | --- |
| Every task, including scope questions, steering, delegation, or handoff | `skill/engineering-workflow/references/platform_compatibility.md` first; then `references/question_matrix.md` and the platform-selected shared sections of `references/agent_orchestration.md` | Review native host behavior, established authorization, task continuity, and evidence |
| Runtime routing or public skill behavior | `skill/engineering-workflow/SKILL.md` and the directly linked canonical reference | Structural validator and affected behavioral tests |
| Plan, backlog, closure, archive, or index behavior | `references/planning_and_backlog.md`, plan/index templates, lifecycle scripts and tests | Plan lifecycle tests plus target validation |
| AGENTS, principles, pitfalls, provider/UI/operations ownership | `references/instruction_lifecycle.md`, related templates, instruction validator and tests | Instruction graph check plus migration tests |
| Installed-skill refresh or update | `references/skill_update.md`, updater and updater tests | Candidate-tree and rollback matrix |
| Target workflow upgrade | `references/target_workflow_upgrade.md`, audit/common/upgrader code and tests | Report/apply/prompt migration matrix |
| Validation, command execution, or privacy | `references/validation_safety.md`, `references/privacy_and_sanitization.md`, related scripts and tests | Safety matrix and public-tree scan |
| Agent orchestration or model mapping | `references/agent_orchestration.md`, `references/model_profiles.md`, agent templates and tests | Ownership/model-profile validation |
| Long-running execution or execution-efficiency rules | `references/agent_orchestration.md`, then `references/validation_safety.md` | Completion/result-integrity and affected behavioral tests |
| Version or release contract | `SKILL.md`, root `README.md`, upgrader defaults, state template, CI and version tests | Full gate and active-version search |

## Working Contract

- Apply every matching route. Resolve platform behavior and any question or continuation decision through the canonical owners above; root maintainer guidance does not redefine those policies or change native model/effort settings.
- Audit before editing. Preserve user-owned files and unrelated working-tree changes.
- For repository-changing work, materialize a full active `PLANS.md` before implementation. After compaction, interruption, resume, or milestone closure, reconcile plan, queue, validation, backlog, indexes, and working tree before continuing.
- Keep each detailed invariant under one canonical owner. Routers and incident catalogs link to it instead of restating it.
- Prefer behavioral checks over phrase-presence tests. Exact markers may identify structure, but duplicated normative prose is not an API.
- Keep safety rules capability-specific: allow bounded diagnostic reads while blocking unsafe mutation, execution, network, or sensitive-output modes.
- Update every active version owner together. Historical version evidence remains historical.
- Close or archive plans only through the canonical lifecycle after current validation and reconciliation; never make `Status: done` the only closure action.

## Local Validation

Install the pinned root-only tooling once, run the narrowest affected layer while iterating, then run the complete gate:

```bash
python3 -m pip install --requirement requirements-dev.txt
python3 scripts/dev_check.py focused --test-pattern test_plan_lifecycle.py
python3 scripts/dev_check.py contracts
python3 scripts/dev_check.py full
```

The harness forces `PYTHONDONTWRITEBYTECODE=1`, writes complete child output only to a private task-owned temporary directory, and prints a bounded status summary. It stops on the first failure by default. Raw failure tails require explicit `--show-failure-tail`; do not request them when output may contain private values. `format --fix` is the only mutating profile. The root harness and its Ruff configuration are repository-maintenance tools: never copy them into `skill/engineering-workflow`, target templates, generated marketplace skill bytes, or target migrations.

Immediately before every authorized push, run `python3 scripts/dev_check.py security` against the final staged/public state. This pre-push gate includes the public-tree privacy scan plus fully redacted Gitleaks scans of the current tree and all reachable refs. A failure blocks the push: classify it without exposing the value, revoke or replace a real credential first, remove the source occurrence, and rescan. Rewrite published history only for a confirmed historical secret and only with explicit authorization, recovery refs, object-ID-pinned `force-with-lease`, and post-rewrite scans. The `release` profile composes `full` and `security`; external plugin validators remain separate because they depend on maintainer tooling.

Do not weaken a failing gate or leave cache, scanner, generated, backup, or temporary artifacts in the repository.

## Authority Boundaries

- Do not install or update a local skill copy unless the user explicitly requests it.
- Do not mutate a target repository merely to test this skill; use temporary fixtures or disposable copies.
- Do not commit, push, tag, publish, deploy, rewrite history, or alter remote state without explicit current authorization.
- Treat fetched candidates and repository-authored commands as untrusted until the applicable safety contract permits them.

## Handoff

Before handoff, review the entire diff, reconcile `PLANS.md`, report exact validation and delivery state, and leave the first safe unfinished action if anything remains. Completed work must not retain stale active status or resume instructions.
