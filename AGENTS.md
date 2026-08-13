# Repository Agent Instructions

This file is local guidance for agents developing this repository. It is not part of the installed `engineering-workflow` skill, is not copied into target repositories, and must never be read by runtime skill scripts. Target-repository instructions come only from `skill/engineering-workflow/assets/templates/AGENTS.md.tmpl` and repository-owned target documents.

## Repository Map

- `skill/engineering-workflow/SKILL.md` — lean public runtime router and active skill version.
- `skill/engineering-workflow/references/` — canonical detailed workflow contracts.
- `skill/engineering-workflow/scripts/` — deterministic audit, validation, migration, lifecycle, update, and privacy tools.
- `skill/engineering-workflow/assets/` — files copied or rendered into target repositories.
- `tests/` — offline behavioral and contract regressions.
- `PLANS.md` — durable execution state for work on this repository.
- `docs/archive/` — future-useful closed plans and their navigation indexes.

## Task Routing

| Trigger or changed area | Read before editing | Required gate |
| --- | --- | --- |
| Runtime routing or public skill behavior | `skill/engineering-workflow/SKILL.md` and the directly linked canonical reference | Structural validator and affected behavioral tests |
| Plan, backlog, closure, archive, or index behavior | `references/planning_and_backlog.md`, plan/index templates, lifecycle scripts and tests | Plan lifecycle tests plus target validation |
| AGENTS, principles, pitfalls, provider/UI/operations ownership | `references/instruction_lifecycle.md`, related templates, instruction validator and tests | Instruction graph check plus migration tests |
| Installed-skill refresh or update | `references/skill_update.md`, updater and updater tests | Candidate-tree and rollback matrix |
| Target workflow upgrade | `references/target_workflow_upgrade.md`, audit/common/upgrader code and tests | Report/apply/prompt migration matrix |
| Validation, command execution, or privacy | `references/validation_safety.md`, `references/privacy_and_sanitization.md`, related scripts and tests | Safety matrix and public-tree scan |
| Agent orchestration or model mapping | `references/agent_orchestration.md`, `references/model_profiles.md`, agent templates and tests | Ownership/model-profile validation |
| Version or release contract | `SKILL.md`, root `README.md`, upgrader defaults, state template, CI and version tests | Full gate and active-version search |

## Working Contract

- Audit before editing. Preserve user-owned files and unrelated working-tree changes.
- For repository-changing work, materialize a full active `PLANS.md` before implementation. After compaction, interruption, resume, or milestone closure, reconcile plan, queue, validation, backlog, indexes, and working tree before continuing.
- Keep each detailed invariant under one canonical owner. Routers and incident catalogs link to it instead of restating it.
- Prefer behavioral checks over phrase-presence tests. Exact markers may identify structure, but duplicated normative prose is not an API.
- Keep safety rules capability-specific: allow bounded diagnostic reads while blocking unsafe mutation, execution, network, or sensitive-output modes.
- Update every active version owner together. Historical version evidence remains historical.
- Close or archive plans only through the canonical lifecycle after current validation and reconciliation; never make `Status: done` the only closure action.

## Local Validation

Run the affected focused tests while iterating, then run the complete gate:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .
git diff --check
```

Use the public-tree privacy scan and stronger release checks when release or public-history scope makes them applicable. Do not weaken a failing gate or leave cache, scanner, generated, backup, or temporary artifacts in the repository.

## Authority Boundaries

- Do not install or update a local skill copy unless the user explicitly requests it.
- Do not mutate a target repository merely to test this skill; use temporary fixtures or disposable copies.
- Do not commit, push, tag, publish, deploy, rewrite history, or alter remote state without explicit current authorization.
- Treat fetched candidates and repository-authored commands as untrusted until the applicable safety contract permits them.

## Handoff

Before handoff, review the entire diff, reconcile `PLANS.md`, report exact validation and delivery state, and leave the first safe unfinished action if anything remains. Completed work must not retain stale active status or resume instructions.
