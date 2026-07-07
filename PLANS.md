# Execution Plans

Use this file for active, blocked, or recently completed execution work.

For any task that changes repository state, update this file before implementation and again before handoff.
Use a full active plan for active repo-changing work. Compact only completed work after validation and handoff are recorded.

## Active Plan: Engineering Workflow Skill 0.3.1

Status: done
Owner: Codex
Last Updated: 2026-07-07

### Goal
Release `engineering-workflow` version `0.3.1` with a stricter planning contract: active repo-changing work must stay fully resumable from `PLANS.md`, preserve sources and resume state through context compaction, and avoid silently narrowing the user's requested scope.

### Requested Scope
- Bump the skill to `0.3.1` from the previous patch release.
- Make full active `PLANS.md` entries the default for any repo-changing task.
- Remove active-work compacting language from skill docs, templates, README, and tests.
- Add anti-simplification guidance so "conservative" does not mean downscoping the task.
- Run validation, perform a full manual second review, commit the changes, and sync the installed local skill target.

### Constraints
- Keep `metadata.version` and `agents/openai.yaml` structurally unchanged.
- Do not migrate installation docs away from the working `~/.codex/skills` path in this patch.
- Keep completed-work compaction allowed only after validation and handoff are recorded.
- Stage and commit only intended changes.
- Keep the local skill symlink pointed at `$HOME/src_build/codex-engineering-workflow/skill/engineering-workflow`.

### Inputs
- User-approved implementation plan in chat on 2026-07-07.
- `skill/engineering-workflow/SKILL.md`
- `skill/engineering-workflow/references/planning_and_backlog.md`
- `skill/engineering-workflow/references/canonical_target.md`
- `skill/engineering-workflow/assets/templates/PLANS.md.tmpl`
- `skill/engineering-workflow/assets/templates/AGENTS.md.tmpl`
- `skill/engineering-workflow/assets/templates/AGENT_EXECUTION_PITFALLS.md.tmpl`
- `skill/engineering-workflow/assets/templates/project_principles.md.tmpl`
- `README.md`
- `tests/test_skill_repo_validation.py`

### Completed Baseline State
- [x] Confirmed pre-edit validation passed: `validate_skill_repo`, 21 unit tests, and `git diff --check`.
- [x] Confirmed current installed local skill is a symlink to `$HOME/src_build/codex-engineering-workflow/skill/engineering-workflow`.
- [x] Confirmed local installed skill target currently reads the previous patch version.
- [x] Confirmed Codex manual supports `SKILL.md`, optional `agents/openai.yaml`, and symlinked skill folders.

### Current Work Queue
1. [x] Record this full active plan before editing skill files.
2. [x] Update version references and planning contract text across skill docs, templates, README, and tests.
3. [x] Add or update validation tests for stale versions and the full-active-plan contract.
4. [x] Run required validation commands and targeted stale-language search.
5. [x] Perform a full second review of the diff and consistency before commit.
6. [x] Commit with message `Bump engineering workflow skill to 0.3.1`.
7. [x] Sync the installed symlink target and verify local install reads `metadata.version: 0.3.1`.

### Locked Decisions
- 2026-07-07: Full active plans are the default for all active repo-changing work; compacting is only for completed work after validation and handoff.
- 2026-07-07: The local installation will be synchronized by updating the current symlink target, not by repointing the symlink.
- 2026-07-07: `0.3.1` is a patch release because the canonical layout is unchanged.

### Verification
- `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- Targeted stale-version and legacy-planning-language search across `README.md`, `PLANS.md`, `skill`, and `tests`.
- Manual review of the complete diff before commit.
- Local install version readback through `$HOME/.codex/skills/engineering-workflow/SKILL.md`.

### Latest Validation Results
- Pre-edit baseline: `validate_skill_repo` passed, 21 unit tests passed, and `git diff --check` passed.
- 2026-07-07: `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .` passed with no errors or warnings.
- 2026-07-07: `python3 -m unittest discover -s tests -v` passed, 24 tests.
- 2026-07-07: `git diff --check` passed.
- 2026-07-07: Targeted stale-version and legacy-planning-language search returned no matches.
- 2026-07-07: Full manual diff review found no active-work compacting language, no stale version references, and no wording that makes `conservative_merge` a scope-reduction path.
- 2026-07-07: Local installed skill readback through `$HOME/.codex/skills/engineering-workflow/SKILL.md` returned `metadata.version: 0.3.1`.

### Handoff Notes
- Work is complete. The repository commit contains the 0.3.1 update, and the existing local skill symlink target has been synchronized.

## Active Plan: Engineering Workflow Skill 0.4.0

Status: done
Owner: Codex
Last Updated: 2026-07-07

### Goal
Release `engineering-workflow` version `0.4.0` with clearer archive and closure policy for active plans and backlog items, including an explicit pre-commit rule that prevents completed work from being committed with an active plan still left open.

### Requested Scope
- Refine archival policy for active plans in `PLANS.md`.
- Refine cleanup and archive policy for `docs/codex/TASKS_BACKLOG.md`.
- Add a rule that before commit, the active plan must match post-commit truth: close completed work, or record why it remains active with a resume point.
- Update version references, docs, templates, validator guardrails, tests, local install, and commit the change.

### Constraints
- Keep the canonical layout unchanged.
- Keep active work fully resumable until it is actually complete.
- Do not force archival for completed work when a compact `Recently Completed` entry is enough.
- Stage and commit only intended changes.
- Keep the local skill symlink pointed at `$HOME/src_build/codex-engineering-workflow/skill/engineering-workflow`.

### Inputs
- User request on 2026-07-07 about active-plan/backlog archive policy and agents leaving active plans open before commit.
- `skill/engineering-workflow/references/planning_and_backlog.md`
- `skill/engineering-workflow/assets/templates/PLANS.md.tmpl`
- `skill/engineering-workflow/assets/templates/TASKS_BACKLOG.md.tmpl`
- `skill/engineering-workflow/assets/templates/AGENTS.md.tmpl`
- `skill/engineering-workflow/assets/templates/AGENT_EXECUTION_PITFALLS.md.tmpl`
- `skill/engineering-workflow/assets/templates/project_principles.md.tmpl`
- `skill/engineering-workflow/SKILL.md`
- `README.md`
- `tests/test_skill_repo_validation.py`

### Completed Baseline State
- [x] Working tree was clean before this 0.4.0 task.
- [x] Current public skill version is `0.3.1`.
- [x] Existing planning reference already requires full active plans and completed-work compaction only after validation/handoff.

### Current Work Queue
1. [x] Record this full active plan before editing skill files.
2. [x] Update archive, backlog cleanup, and pre-commit closure policy.
3. [x] Add validator and tests for the new 0.4.0 contract.
4. [x] Run validation and targeted searches.
5. [x] Review the complete diff and close this active plan before final commit.
6. [x] Commit the 0.4.0 change.
7. [x] Sync the installed symlink target and verify local install reads `metadata.version: 0.4.0`.

### Locked Decisions
- 2026-07-07: `0.4.0` is a minor release because it changes planning/backlog lifecycle conventions without changing canonical file paths.
- 2026-07-07: A final task commit must not leave completed work as `Status: in_progress`; partial commits may keep a plan active only with an explicit resume point.
- 2026-07-07: Backlog items should be removed by default after completion unless they still carry useful future context.

### Verification
- `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- Targeted search for stale version and old lifecycle language.
- Manual review of diff consistency before commit.
- Local install version readback through `$HOME/.codex/skills/engineering-workflow/SKILL.md`.

### Latest Validation Results
- 2026-07-07: `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .` passed with no errors or warnings.
- 2026-07-07: `python3 -m unittest discover -s tests -v` passed, 26 tests.
- 2026-07-07: `git diff --check` passed.
- 2026-07-07: Targeted public stale-version and legacy-planning-language search returned no matches.
- 2026-07-07: Full diff review confirmed `0.4.0` matches the repo SemVer policy for changed planning/backlog conventions.
- 2026-07-07: Local installed skill readback through `$HOME/.codex/skills/engineering-workflow/SKILL.md` returned `metadata.version: 0.4.0`.

### Resume Point
- Work is complete; this plan is closed before final commit by the new pre-commit closure rule.

### Handoff Notes
- The final commit includes this closed plan state, and the existing local skill symlink target has been synchronized.

## Recently Completed

- [x] 2026-05-21: Updated `engineering-workflow` to the previous patch release with forced skill refresh guidance, planning/backlog lifecycle rules, completed-work cleanup policy, template updates, and validator coverage. Validation passed: `validate_skill_repo`, 21 unit tests, and `git diff --check`.
