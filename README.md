# Codex Engineering Workflow

Public standalone Codex skill for auditing, scaffolding, validating, updating, and migrating a repository's engineering-workflow layer.

Current skill version: `0.5.0`.

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

`refresh_loaded_skill` rereads the exact active `SKILL.md`, reports `metadata.version`, and opens only the references needed for the request. It performs no network access, installation write, or target-repository change.

```text
Use $engineering-workflow in refresh_loaded_skill mode. Reread the exact active SKILL.md, report its path and version, and do not update anything.
```

After a refresh, use only the reread instructions for that turn.

## Update Installed Skill

`update_installed_skill` is a distinct lifecycle operation. It checks a trusted upstream and safely updates the exact active symlink target, Git checkout, or copied installation without changing a target repository.

Check first:

```bash
python3 skill/engineering-workflow/scripts/update_installed_skill.py \
  --install-path <exact-active-skill-path> \
  --source-repo https://github.com/xeonvs/codex-engineering-workflow \
  --source-path skill/engineering-workflow \
  --ref main \
  --check \
  --format json
```

Apply after reviewing the structured result:

```bash
python3 skill/engineering-workflow/scripts/update_installed_skill.py \
  --install-path <exact-active-skill-path> \
  --source-repo https://github.com/xeonvs/codex-engineering-workflow \
  --source-path skill/engineering-workflow \
  --ref main \
  --apply \
  --format json
```

Alternate upstreams require explicit confirmation. Downgrades require `--allow-downgrade`. A successful update ends the current operation; use a new turn or restart if the client does not detect the new skill automatically.

## Upgrade A Target Workflow

`upgrade_target_workflow` audits and plans a migration independently of installed-skill update. Planning is read-only:

```bash
python3 skill/engineering-workflow/scripts/upgrade_target_workflow.py \
  --repo <target-repository> \
  --plan \
  --target-version 0.5.0 \
  --format json
```

Apply only after reviewing the report:

```bash
python3 skill/engineering-workflow/scripts/upgrade_target_workflow.py \
  --repo <target-repository> \
  --apply \
  --target-version 0.5.0 \
  --format json
```

The migration creates or updates the target's full active `PLANS.md` plan before other migration edits. Runtime agent configuration remains untouched unless `--include-agent-config` is explicit. Existing TOML is structurally merged; unknown keys and custom profiles are preserved, and the exact configuration diff is reported.

## Operating Modes

Repository workflow modes:

- `greenfield_scaffold` — initialize the workflow layer in an empty or nearly empty repository.
- `conservative_merge` — preserve existing owners while adding only missing workflow structure.
- `read_only_verify` — inspect without executing repository-authored code or writing state.
- `disposable_copy_verify` — run builds, tests, linters, or repository commands in an isolated copy.
- `upgrade_target_workflow` — plan or apply a versioned workflow migration.

Skill lifecycle modes:

- `refresh_loaded_skill` — reread the active installation.
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
Use $engineering-workflow to produce a read-only 0.5.0 migration report for this repository. Do not apply it yet.
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

The project uses semantic versioning. Version 0.5.0 adds plan materialization and traceability, lifecycle-versus-migration routing, agent orchestration profiles, safe installed-skill update, target workflow migration, exact ownership classification, stricter command safety, and repository-wide privacy validation.

Historical version records remain valid in completed or migration context. Current-version owners are `SKILL.md`, this README, current update prompts, and active workflow state manifests.

Canonical upstream: [xeonvs/codex-engineering-workflow](https://github.com/xeonvs/codex-engineering-workflow).
