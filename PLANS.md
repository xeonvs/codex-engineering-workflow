# Execution Plans

Use this file for active, blocked, or recently completed execution work.

For any task that changes repository state, update this file before implementation and again before handoff.
Use a full active plan for active repo-changing work. Compact only completed work after validation and handoff are recorded.

## Active Plan: Engineering Workflow Skill 0.4.1

Status: done
Owner: Codex
Last Updated: 2026-07-08

### Goal
Release `engineering-workflow` version `0.4.1` with explicit reconciliation rules for context compaction, interruption, resume, and milestone closure so `PLANS.md`, `docs/codex/TASKS_BACKLOG.md`, and related workflow docs agree before code changes resume.

### Requested Scope
- Check whether templates already contain the requested reconciliation and stale completed-section guidance.
- Add explicit rules when missing.
- Prevent stale "next work", resume, or milestone status text from remaining in completed sections where it can be mistaken for current state.
- Update version references, templates, references, validator guardrails, tests, local install, and commit the change.

### Constraints
- Keep this a patch release because it clarifies the existing 0.4 lifecycle policy without changing canonical file paths or status vocabulary.
- Keep active-work plans full and resumable until genuinely closed.
- Do not leave completed milestone sections with stale next-action language.
- Stage and commit only intended changes.
- Keep the local skill symlink pointed at `$HOME/src_build/codex-engineering-workflow/skill/engineering-workflow`.

### Inputs
- User request on 2026-07-08 about compaction/resume reconciliation and stale completed-section text.
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
- [x] Working tree was clean before this task.
- [x] Existing templates have resume/pre-commit closure rules, but not explicit post-compaction or post-interruption reconciliation across plan/backlog/status sources.
- [x] Closed 0.3.1 and 0.4.0 detailed active plans were compacted into `Recently Completed` entries before this task's code changes.

### Current Work Queue
1. [x] Record this full active plan and compact stale completed active-plan detail before editing skill files.
2. [x] Update reconciliation and stale completed-section policy across skill docs and templates.
3. [x] Add validator and tests for the new 0.4.1 contract.
4. [x] Run validation and targeted searches.
5. [x] Review the complete diff and close this active plan before final commit.
6. [x] Commit the 0.4.1 change.
7. [x] Sync the installed symlink target and verify local install reads `metadata.version: 0.4.1`.

### Locked Decisions
- 2026-07-08: `0.4.1` is a patch release because it clarifies 0.4 lifecycle behavior without changing canonical layout or status vocabulary.
- 2026-07-08: After context compaction, interruption, resume, or milestone closure, reconcile `PLANS.md`, backlog, current milestone, next safe action, validation state, and status fields before code changes.
- 2026-07-08: Completed sections must not retain stale "next work", resume, or milestone status text that can be mistaken for current state.

### Verification
- `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- Targeted search for stale versions and stale completed-section wording.
- Manual review of diff consistency before commit.
- Local install version readback through `$HOME/.codex/skills/engineering-workflow/SKILL.md`.

### Latest Validation Results
- 2026-07-08: `python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .` passed with no errors or warnings.
- 2026-07-08: `python3 -m unittest discover -s tests -v` passed, 28 tests.
- 2026-07-08: `git diff --check` passed.
- 2026-07-08: Targeted public stale-version and legacy-planning-language search returned no matches.
- 2026-07-08: Manual diff review confirmed the templates now include reconciliation after compaction/interruption/resume/milestone closure and forbid stale next-work or milestone text in completed sections.
- 2026-07-08: Local installed skill readback through `$HOME/.codex/skills/engineering-workflow/SKILL.md` returned `metadata.version: 0.4.1`.

### Resume Point
- Work is complete; this plan is closed before final commit by the pre-commit closure rule.

### Handoff Notes
- The final commit includes this closed plan state, and the existing local skill symlink target has been synchronized.

## Recently Completed

- [x] 2026-07-07: Released `engineering-workflow` 0.4.0 with pre-commit plan closure, active-plan archive policy, backlog remove-by-default cleanup, validator guardrails, and 26 passing tests.
- [x] 2026-07-07: Released `engineering-workflow` 0.3.1 with full active plans by default, anti-simplification guidance, validator guardrails, and 24 passing tests.
- [x] 2026-05-21: Updated `engineering-workflow` to the previous patch release with forced skill refresh guidance, planning/backlog lifecycle rules, completed-work cleanup policy, template updates, and validator coverage. Validation passed: `validate_skill_repo`, 21 unit tests, and `git diff --check`.
