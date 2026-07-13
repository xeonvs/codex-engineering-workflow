# Canonical Target

The workflow layer uses one clear owner per concern and does not absorb repository-specific domain documentation.

## Canonical Files

- `AGENTS.md`: short repository map and source-of-truth index
- `PLANS.md`: full active plans, traceability, reconciliation, validation, recovery, and truthful recently completed state
- `docs/engineering/project_principles.md`: durable cross-cutting engineering rules and ownership boundaries
- `docs/codex/TASKS_BACKLOG.md`: future or inactive work with activation and exit criteria
- `docs/codex/AGENT_EXECUTION_PITFALLS.md`: generalized recurring execution failure patterns
- `docs/codex/ENGINEERING_WORKFLOW_STATE.yaml`: explicit migration/version/ownership state for listed paths only

## Optional Files

- `docs/codex/agent_practices_adoption.md`: one-time adoption note for a mature repository
- `docs/codex/exec_plan_migration_note.md`: mapping when old plan topology remains historical
- `.codex/agents/*.toml`: optional runtime profiles installed only after explicit authorization

## Ownership

- `managed`: state manifest, manifest-listed path, or explicit managed section
- `shared`: exact canonical workflow/config path that may contain repository-owned content
- `protected`: domain, product, architecture, QA, security, release, or operational documentation
- `external_source_of_truth`: repository overview or external tracker/document owner
- `historical`: explicitly supported plan/backlog archive path
- `unknown`: ownership is not proven and remains protected

Do not infer ownership from broad directory prefixes. A file under `docs/codex/` or `docs/engineering/` is not managed merely because of its directory.

## Outside The Workflow Layer

- domain semantics and product policy
- architecture manuals
- release, launch, operational, QA, and security runbooks or policy
- benchmark artifacts
- external tracker records
- unrelated archived research

Index those sources from `AGENTS.md` when useful; do not rewrite or absorb them without explicit authorization.
