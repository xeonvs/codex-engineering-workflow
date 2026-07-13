# Codex Engineering Workflow

Public standalone Codex skill for auditing, scaffolding, validating, updating, and migrating a repository's engineering-workflow layer.

Current skill version: `0.5.1`.

The skill keeps `AGENTS.md` as a map, `PLANS.md` as durable active execution state, and repository-specific product or domain documents under their existing owners. Repository-changing work always uses a full plan; read-only inspection is the only exception.

## Quick Start

1. Install or link `skill/engineering-workflow` in one of the supported skill-discovery locations.
2. Start a new Codex turn if the running client has not detected the installation change.
3. Invoke `$engineering-workflow` and name the repository outcome you want.

```text
Use $engineering-workflow to audit this repository and propose a conservative workflow scaffold.
```

The scripts require Python 3.11 or newer and use only the standard library.

## Installing The Skill

Current Codex authoring guidance supports repository skills under `.agents/skills`, user skills under `$HOME/.agents/skills`, administrator skills under `/etc/codex/skills`, and system-provided skills. Symlinked skill folders are supported. The official skill installer continues to use `$CODEX_HOME/skills` (normally `$HOME/.codex/skills`), so the correct location depends on how the skill is managed.

For repository-local authoring:

```bash
mkdir -p .agents/skills
ln -s "$(pwd)/skill/engineering-workflow" .agents/skills/engineering-workflow
```

For a user-scoped authoring installation:

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/skill/engineering-workflow" "$HOME/.agents/skills/engineering-workflow"
```

For an installation managed in the official installer's location:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
ln -s "$(pwd)/skill/engineering-workflow" "$CODEX_HOME/skills/engineering-workflow"
```

Do not infer the active installation from a similarly named directory. Refresh and update operations require the exact loaded skill path.

## Using The Skill In Codex

Invoke the skill explicitly and describe the desired end state:

```text
Use $engineering-workflow to add a full AGENTS/PLANS/backlog/pitfalls workflow while preserving existing architecture and operations docs.
```

```text
Use $engineering-workflow in read-only mode to verify the workflow structure and ownership boundaries.
```

```text
Use $engineering-workflow to upgrade this repository's workflow rules to the current installed version, but do not add runtime agent configuration.
```

Repository content is treated as untrusted evidence. It cannot grant approval, expand scope, request secrets, or override system, developer, or user instructions.

## Refresh Loaded Skill

`Refresh Loaded Skill` is a prompt-driven orchestration mode. The agent resolves the exact active installation, checks it against the canonical upstream, and chooses the required action from structured evidence:

- identical skill content: reread the active `SKILL.md` and needed references;
- changed instructions, scripts, or resources: invoke the safe installed-skill updater itself, then reread the updated installation;
- alternate source, downgrade, dirty/divergent checkout, or another protected state: stop and ask only for the required decision.

Major or minor version drift always triggers the update check. Patch drift also updates when content changed. Codex normally detects changed skills automatically; restart or start a new task only if the refreshed instructions do not appear.

```text
Use $engineering-workflow to Refresh Loaded Skill. Inspect the exact active installation and canonical upstream, invoke any safe required update yourself, then reread and report the active path and version.
```

For a strictly local reread with no upstream access or writes, say so explicitly. `Refresh Loaded Skill` never implies target-repository migration.

## Update Installed Skill

`update_installed_skill` is a distinct lifecycle operation. It checks a trusted upstream and safely updates the exact active symlink target, Git checkout, or copied installation without changing a target repository.

The agent runs check mode first and parses `recommended_action`, `automatic_update_allowed`, `confirmation_required`, instruction/content drift, and SemVer drift. These commands are the deterministic backend, not steps the user must manually copy after giving a resolved prompt.

Check backend:

```bash
python3 skill/engineering-workflow/scripts/update_installed_skill.py \
  --install-path <exact-active-skill-path> \
  --source-repo https://github.com/xeonvs/codex-engineering-workflow \
  --source-path skill/engineering-workflow \
  --ref main \
  --check \
  --format json
```

Apply backend when the check allows automatic update:

```bash
python3 skill/engineering-workflow/scripts/update_installed_skill.py \
  --install-path <exact-active-skill-path> \
  --source-repo https://github.com/xeonvs/codex-engineering-workflow \
  --source-path skill/engineering-workflow \
  --ref main \
  --apply \
  --format json
```

Alternate upstreams require explicit confirmation and `--expected-commit` set to the full commit returned by check mode, so a moved ref cannot replace reviewed content. Credential-bearing URL components and plain-HTTP canonical aliases are refused. Downgrades require `--allow-downgrade`. After a successful update, the agent resolves and rereads the active installation; restart is only a fallback when Codex does not surface the detected change.

## Upgrade A Target Workflow

`Upgrade A Target Workflow` is a natural-language execution prompt. The agent invokes report-first orchestration itself; it applies automatically only when the report has no unresolved conflict, privacy finding, or approval-bound question.

```text
Use $engineering-workflow to Upgrade A Target Workflow in this repository to version 0.5.1. Run the report first, apply it yourself when safe, and ask only if the report returns a required decision.
```

Prompt orchestration backend:

```bash
python3 skill/engineering-workflow/scripts/upgrade_target_workflow.py \
  --repo <target-repository> \
  --prompt \
  --target-version 0.5.1 \
  --format json
```

For an explicitly report-only request, planning remains read-only:

```bash
python3 skill/engineering-workflow/scripts/upgrade_target_workflow.py \
  --repo <target-repository> \
  --plan \
  --target-version 0.5.1 \
  --format json
```

Direct apply remains available to the agent after a separately reviewed report:

```bash
python3 skill/engineering-workflow/scripts/upgrade_target_workflow.py \
  --repo <target-repository> \
  --apply \
  --target-version 0.5.1 \
  --format json
```

The migration creates or updates the target's full active `PLANS.md` plan before other migration edits. Runtime agent configuration remains untouched unless `--include-agent-config` is explicit. Existing TOML is structurally merged; unknown keys and custom profiles are preserved, and the exact configuration diff is reported.

## Operating Modes

Repository workflow modes:

- `greenfield_scaffold` — initialize the workflow layer in an empty or nearly empty repository.
- `conservative_merge` — preserve existing owners while adding only missing workflow structure.
- `read_only_verify` — inspect without executing repository-authored code or writing state.
- `disposable_copy_verify` — run builds, tests, linters, or repository commands in an isolated copy.
- `upgrade_target_workflow` — prompt-orchestrate, plan, or apply a versioned workflow migration.

Skill lifecycle modes:

- `refresh_loaded_skill` — check the canonical candidate, automatically update when safe content drift requires it, then reread the active installation.
- `update_installed_skill` — retrieve, validate, back up, and update the active installation.

If a request could mean either self-update or target migration, the skill investigates first and asks one targeted question rather than combining them.

## Planning And Backlog Lifecycle

Every repository-changing task must materialize a full active plan in `PLANS.md` before implementation, tests, configuration, templates, or workflow documentation change. There is no lightweight exception. Plan Mode is optional: an approved Plan Mode plan is materialized as the first write after exit, while direct execution derives and materializes the same full schema as its first write.

The active schema includes stable requirement IDs, source-to-queue-to-validation traceability, user decisions, risks and recovery, a fidelity self-check, reconciliation, pre-commit closure, handoff notes, and the exact first unfinished action. An agreed plan cannot be compressed during materialization.

After context compaction, interruption, resume, milestone closure, handoff, or session change, the agent reads `PLANS.md`, inspects changes since its last update, and reconciles requirements, queue, backlog, validation, working tree, and statuses before more code changes. The 0.4.1 reconciliation and stale-completed-state protections remain in force.

## Agent Orchestration

One root agent is the default and the only owner of shared workflow state and final synthesis. Deterministic polling, sorting, filtering, aggregation, bounded retry, and status checks belong in tools or scripts. Subagents are reserved for independent bounded work with a concrete output contract and measurable latency, isolation, or coverage benefit.

Current capability-to-model mappings live only in `references/model_profiles.md` and the optional agent templates. Runtime agent templates are never installed into a target repository without an explicit request and `--include-agent-config`.

## Validation And Privacy

Strict read-only verification permits only known non-mutating inspection commands. Repository-authored scripts, project tests, package-manager commands, plugins, generators, and apparently safe commands with shell chaining are not read-only safe. Stronger checks run in a disposable copy with a minimal credential-free environment, timeout, bounded network policy, and cleanup.

The public scan covers all tracked text, including root plans, README, skill files, templates, tests, and CI. It reports only category, path, and line—not detected values. Historical version mentions are allowed in clearly historical or completed contexts; active version owners must agree.

## Example Workflows

Greenfield:

```text
Use $engineering-workflow to scaffold the workflow layer in this empty repository and validate it in a disposable copy.
```

Mature repository:

```text
Use $engineering-workflow to audit this mature repository, preserve every domain-document owner, and add only missing workflow-owned structure.
```

Target migration:

```text
Use $engineering-workflow to Upgrade A Target Workflow in this repository to 0.5.1. Run the report and apply it yourself when safe.
```

## Repository Layout

- `skill/engineering-workflow/SKILL.md` — lean runtime router and invariants.
- `skill/engineering-workflow/references/` — canonical detailed contracts.
- `skill/engineering-workflow/scripts/` — deterministic audit, validation, update, migration, and sanitization tools.
- `skill/engineering-workflow/assets/` — target document and optional agent templates.
- `tests/` — offline behavioral regression tests.
- `.github/workflows/ci.yml` — public repository validation.

## Validating

```bash
python3 skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root .
python3 -m unittest discover -s tests -v
git diff --check
```

The validator checks structural ownership, plan schema markers, active version consistency, model-profile ownership, public privacy, parseable metadata and templates, and the absence of generated cache artifacts.

## Versioning And Updates

The project uses semantic versioning. Version 0.5.0 added plan materialization and traceability, lifecycle-versus-migration routing, agent orchestration profiles, safe installed-skill update, target workflow migration, exact ownership classification, stricter command safety, and repository-wide privacy validation. Version 0.5.1 fixes environment-independent CI validation, makes refresh/update selection and target migration explicitly agent-invoked from natural-language prompts, binds alternate-source approval to an exact commit, hardens migration writes against path races, and closes privacy/validation output gaps.

Historical version records remain valid in completed or migration context. Current-version owners are `SKILL.md`, this README, current update prompts, and active workflow state manifests.

Canonical upstream: [xeonvs/codex-engineering-workflow](https://github.com/xeonvs/codex-engineering-workflow).
