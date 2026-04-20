# Canonical Target

The skill aims for a layered workflow structure with one clear owner per concern.

## Canonical Files

- `AGENTS.md`
  - short repo map
  - source-of-truth index
  - high-signal invariants and default validation commands
- `PLANS.md`
  - only active or blocked execution work
- `docs/engineering/project_principles.md`
  - durable cross-cutting engineering rules
  - doc ownership boundaries
  - context-hygiene defaults
- `docs/codex/TASKS_BACKLOG.md`
  - tracked future work that is not active
- `docs/codex/AGENT_EXECUTION_PITFALLS.md`
  - recurring execution mistakes

## Optional Files

- `docs/codex/agent_practices_adoption.md`
  - one-time adoption/adaptation note for mature repos
- `docs/codex/exec_plan_migration_note.md`
  - one-time mapping note when old plan topology is retained as historical detail

## What Stays Outside The Workflow Layer

- domain semantics
- product policy
- architecture manuals
- release or launch runbooks
- benchmark artifacts
- archived historical notes

The workflow layer should point to those docs, not absorb them.
