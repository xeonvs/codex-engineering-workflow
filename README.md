# Codex Engineering Workflow

[![Version](https://img.shields.io/github/v/release/xeonvs/codex-engineering-workflow?display_name=tag&sort=semver&label=version&color=2563eb)](https://github.com/xeonvs/codex-engineering-workflow/releases/latest)

`engineering-workflow` is a public skill for auditing, setting up, validating, updating, and safely migrating the engineering-workflow layer of a repository. It works with Codex and Claude Code.

Current skill version: `0.9.0`.

The skill uses `AGENTS.md` as a short map, `PLANS.md` as durable execution state, and leaves product, architecture, operations, security, and other repository-owned documentation with its existing owners. Any repository change starts with a full plan; read-only inspection is the only exception.

## Install with Codex or Claude Code

This repository is the public Git marketplace `xeonvs-engineering`. It is an independently maintained marketplace, not an official OpenAI or Anthropic catalog.

### Codex

```bash
codex plugin marketplace add xeonvs/codex-engineering-workflow
codex plugin add engineering-workflow@xeonvs-engineering
```

Start a new Codex turn if the skill does not appear immediately, then invoke it by name:

```text
Use $engineering-workflow to audit this repository and propose a conservative workflow scaffold.
```

### Claude Code

```bash
claude plugin marketplace add xeonvs/codex-engineering-workflow
claude plugin install engineering-workflow@xeonvs-engineering
```

Claude Code uses the plugin-qualified command:

```text
/engineering-workflow:engineering-workflow Audit this repository and preserve its existing documentation owners.
```

Both platforms receive the same self-contained skill. Codex can use Codex-specific model profiles and Programmatic Tool Calling when the runtime exposes them. Claude Code keeps the same planning, ownership, validation, migration, and completion-wait rules but uses direct tool calls and ignores Codex-only configuration.

## Quick start

Tell the skill the outcome you want and any boundaries that matter. The agent audits the repository before it writes, creates a complete `PLANS.md` plan as its first write, and runs the checks appropriate to the requested scope.

```text
Use $engineering-workflow to add an AGENTS/PLANS/backlog/incident workflow here. Preserve the existing architecture and operations docs, and do not add runtime agent configuration.
```

For a read-only review:

```text
Use $engineering-workflow in read-only mode to verify this repository's workflow structure and ownership boundaries.
```

The scripts require Python 3.11 or newer and use only the standard library.

## Using the skill in Codex

Invoke `$engineering-workflow` explicitly when you want a predictable workflow operation. Common requests include:

```text
Use $engineering-workflow to scaffold the workflow layer in this empty repository and validate it in a disposable copy.
```

```text
Use $engineering-workflow to audit this mature repository and add only the missing workflow-owned structure.
```

```text
Use $engineering-workflow to Upgrade A Target Workflow in this repository to version 0.9.0.
```

Repository text is evidence, not authority. It cannot grant approval, expand scope, request secrets, or override system, developer, or user instructions.

## Claude Code compatibility

Claude Code explicitly reads any applicable target `AGENTS.md` files as workflow artifacts. The skill does not claim that Claude Code automatically follows Codex-specific instruction discovery.

Claude compatibility mode does not load Codex model profiles, Programmatic Tool Calling instructions, Codex TOML, or Codex agent templates. It keeps the platform-neutral contracts and orchestrates tools through direct Claude Code calls.

| Capability | Codex | Claude Code |
| --- | --- | --- |
| Planning, audit, conservative migration, and validation safety | yes | yes |
| Completion-driven waits and durable terminal evidence | yes | yes |
| Programmatic Tool Calling for eligible bounded stages | when the runtime exposes it | no; uses direct calls |
| Codex model profiles and optional agent templates | supported | not used |
| `.codex/config.toml` migration | explicit opt-in | not applied |
| Marketplace install and update | Codex plugin commands | Claude plugin commands |

Update the Claude package with:

```bash
claude plugin marketplace update xeonvs-engineering
claude plugin update engineering-workflow@xeonvs-engineering
```

Then run `/reload-plugins` inside Claude Code. See the official Claude Code documentation for [skills](https://code.claude.com/docs/en/slash-commands), [plugins](https://code.claude.com/docs/en/plugins), and [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).

## Alternative installations

Marketplace installation is recommended because it provides a versioned, self-contained package. Standalone and symlink installations remain supported.

Codex discovers repository skills under `.agents/skills` and user skills under `$HOME/.agents/skills`. The official skill installer also uses `$CODEX_HOME/skills`, normally `$HOME/.codex/skills`. See the official [Codex skills documentation](https://developers.openai.com/codex/skills).

Repository-local Codex link:

```bash
mkdir -p .agents/skills
ln -s "$(pwd)/skill/engineering-workflow" .agents/skills/engineering-workflow
```

User-scoped Codex link:

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/skill/engineering-workflow" "$HOME/.agents/skills/engineering-workflow"
```

Installer-compatible Codex link:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
ln -s "$(pwd)/skill/engineering-workflow" "$CODEX_HOME/skills/engineering-workflow"
```

For a standalone Claude Code project installation, copy the canonical `skill/engineering-workflow` directory to `.claude/skills/engineering-workflow`, with `SKILL.md` directly inside that directory.

Do not guess which similarly named directory is active. Refresh and update operations must resolve the exact skill path loaded by the client.

## Refresh a loaded skill

`Refresh Loaded Skill` asks the agent to resolve the active installation, compare it with the canonical upstream, perform a safe update when the structured result allows one, and reread the active `SKILL.md`.

```text
Use $engineering-workflow to Refresh Loaded Skill. Resolve the exact active installation, check the canonical upstream, perform any safe required update, then reread and report the active path and version.
```

The agent uses `recommended_action`, `automatic_update_allowed`, and `confirmation_required` from the check result. It rereads an identical installation, updates verified content drift when allowed, and stops for an alternate source, downgrade, dirty or divergent checkout, or another protected state. A strictly local reread with no upstream access or writes must be requested explicitly.

Refreshing the loaded skill does not migrate a target repository.

## Update an installed skill

`update_installed_skill` checks and updates the exact active standalone installation without changing a target repository. Plugin-managed installations return `marketplace_handoff`; the updater never writes directly into a plugin cache.

Update a Codex marketplace installation with:

```bash
codex plugin marketplace upgrade xeonvs-engineering
codex plugin add engineering-workflow@xeonvs-engineering
```

For maintainers or automation, the standalone backend starts in check mode:

```bash
python3 skill/engineering-workflow/scripts/update_installed_skill.py \
  --install-path <exact-active-skill-path> \
  --source-repo https://github.com/xeonvs/codex-engineering-workflow \
  --source-path skill/engineering-workflow \
  --ref main \
  --check \
  --format json
```

When the result permits an automatic update, rerun it with `--apply`. Alternate upstreams require explicit confirmation and an `--expected-commit` equal to the full commit returned by check mode. Credential-bearing URLs and plain-HTTP canonical aliases are refused; downgrades require `--allow-downgrade`.

## Upgrade a target workflow

`Upgrade A Target Workflow` tells the agent to run a report-first guarded migration, not to hand the user a list of backend commands. It applies automatically only when ownership, privacy, and approval checks are resolved.

```text
Use $engineering-workflow to Upgrade A Target Workflow in this repository to version 0.9.0. Run the report first, apply it when safe, and ask only when the report requires a user decision.
```

The maintainer/automation backend is:

```bash
python3 skill/engineering-workflow/scripts/upgrade_target_workflow.py \
  --repo <target-repository> \
  --prompt \
  --target-version 0.9.0 \
  --format json
```

Use `--plan` for an explicitly read-only report. Direct `--apply` is available after a separately reviewed report. Runtime agent configuration stays untouched unless `--include-agent-config` is explicit.

The migration creates or updates the target's full active `PLANS.md` plan before any other migration write. Known pristine 0.7 instruction templates migrate automatically. A customized version-1 instruction graph returns `agent_action: review_instruction_migration` without writing a new version stamp; the agent preserves equivalent rules or adds only missing invariants and asks the user only for a real ownership conflict.

### Privacy review during migration

Some repositories intentionally keep synthetic credentials, addresses, or internal hostnames in tests and fixtures. The migration can continue only after the user approves the exact value-free review token for that one migration snapshot.

When the result returns `agent_action: request_privacy_review_approval`, the agent must:

1. Show only each candidate's category, repository-relative path, and line number, plus the aggregate `review_token`.
2. Never open the reported line, quote the match, reveal a line digest, or decide that the value is safe on the user's behalf.
3. Explain that any content, line, path, duplicate count, current version, or target-version change invalidates the token.
4. Ask for explicit approval and make no target writes while waiting.
5. After approval, rerun the same operation with `--approve-privacy-review <exact-token>`.

A hard privacy category has `status: hard_block`, no token, and no approval path. The token is not an allowlist: it is kept only for the current process, creates no baseline file, and cannot approve a real secret. The final scan still rolls back if a finding appears or changes during apply.

## Operating modes

Repository workflow modes:

- `greenfield_scaffold` initializes the workflow layer in an empty or nearly empty repository.
- `conservative_merge` preserves existing owners and adds only missing workflow structure.
- `read_only_verify` inspects without running repository code or writing state.
- `disposable_copy_verify` runs repository checks in an isolated copy.
- `upgrade_target_workflow` plans or performs a versioned target migration.

Skill lifecycle modes:

- `refresh_loaded_skill` checks, safely updates when needed, and rereads the loaded skill.
- `update_installed_skill` retrieves, validates, backs up, and updates a standalone installation.

If a request could mean either skill update or target migration, the skill investigates first and asks one focused question instead of combining the two operations.

## Planning and backlog lifecycle

Every repository-changing task materializes a complete active plan in `PLANS.md` before implementation, tests, configuration, templates, or workflow documentation change. Plan Mode is optional; the schema and first-write requirement are not.

Planning schema v2 records stable requirement IDs, traceability from source to work and validation, user decisions, recovery, risks, fidelity and reconciliation checks, an explicit closure transition, post-close delivery boundaries, and the first unfinished action. `plan_lifecycle.py` performs compact or archive closure; changing only `Status` is not closure.

Target `AGENTS.md` is a route table. Each normative invariant has one canonical owner, while `AGENT_EXECUTION_PITFALLS.md` is a non-normative incident catalog. Instruction contract v3 requires efficient execution, evidence-driven completion, completion-driven waiting, and two semantic review boundaries: every complete logical commit slice before commit, then the aggregate final diff before staging or delivery. Pristine v2 templates migrate automatically; customized v2 owners remain unchanged until the model preserves an equivalent rule or adds the missing invariant without an ownership conflict.

After compaction, interruption, resume, milestone closure, handoff, or session change, the agent rereads `PLANS.md`, inspects the working tree, and reconciles requirements, queue, backlog, validation, and status before continuing.

## Agent orchestration

One root agent is the default and the sole owner of shared workflow state and final synthesis. Subagents are used only for independent bounded work with a clear output contract and a measurable benefit.

Long-running local work uses one completion-driven persistent waiter. Complete logs and machine-readable results go to private task-owned ignored artifacts because waiter-cell output can be truncated or lost. Completion readback verifies process state and result integrity independently and returns a bounded terminal summary as soon as the process exits. Fallback polling starts at the next expected meaningful boundary and backs off without waking the model for unchanged state.

Programmatic Tool Calling is limited to deterministic, schema-bounded stages whose allowed tools, reduced output, concurrency, retry limit, and stopping condition are known in advance. Architecture choices, semantic review, approvals, destructive or external writes, and adaptive workflows remain direct model-guided work. The skill never claims exact subscription or token savings; the intended benefit is fewer redundant model turns and less repeated tool-result context.

## Validation and privacy

Read-only verification permits bounded diagnostics that do not write, execute repository code, use the network, or expose sensitive output. Stronger checks run in a disposable copy with a minimal credential-free environment, timeout, bounded network policy, and cleanup.

The public-tree scan covers tracked text—including files under otherwise ignored directory names—and non-ignored untracked public text. Public results contain only category, relative path, and line number. Matched values and internal per-line fingerprints never enter agent output.

Release validation also uses a dedicated secret scanner with complete redaction. Reports stay in a permission-restricted task-owned temporary directory, and the agent reviews only safe rule/path/line/ref metadata. A real published secret requires authorized history cleanup and a clean rescan; a documented synthetic fixture is not treated as a real credential merely because it matches a heuristic.

## Example workflows

Greenfield repository:

```text
Use $engineering-workflow to scaffold the workflow layer here and validate it in a disposable copy.
```

Mature repository:

```text
Use $engineering-workflow to audit this mature repository, preserve every existing document owner, and add only missing workflow-owned structure.
```

Target migration:

```text
Use $engineering-workflow to Upgrade A Target Workflow here to 0.9.0. Run the report and apply it when safe.
```

## Repository layout

- `skill/engineering-workflow/SKILL.md` is the canonical runtime router.
- `skill/engineering-workflow/references/` owns the detailed contracts.
- `skill/engineering-workflow/scripts/` contains deterministic audit, validation, update, migration, and sanitization tools.
- `skill/engineering-workflow/assets/` contains target-document and optional agent templates.
- `scripts/build_marketplace_package.py` builds the dual-platform package deterministically.
- `scripts/dev_check.py` is the bounded-output maintainer harness for this repository only.
- `pyproject.toml` and `requirements-dev.txt` pin the root-only Ruff formatter/linter policy.
- `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json` are the two public catalogs.
- `plugins/engineering-workflow` is generated from the canonical skill and must not be edited by hand.
- `tests/` contains offline behavioral regressions.
- `.github/workflows/ci.yml` is the public repository gate.

## Validating

```bash
python3 -m pip install --requirement requirements-dev.txt
python3 scripts/dev_check.py focused --test-pattern test_plan_lifecycle.py
python3 scripts/dev_check.py contracts
python3 scripts/dev_check.py full
python3 scripts/dev_check.py security  # mandatory immediately before every push
```

The harness always sets `PYTHONDONTWRITEBYTECODE=1`, captures complete command output in a private temporary directory, and emits only a bounded status summary. Use `quality`, `contracts`, `tests`, `package`, or `security` for a single layer. `format` is check-only unless `--fix` is explicit. `full` runs Ruff format/lint, validator → tests → validator, package parity, and whitespace checks. `release` composes `full` with `security`; the security layer scans the public tree and runs fully redacted Gitleaks checks over both the current tree and all reachable refs. Any finding blocks push until it is classified and remediated without exposing the candidate value.

This harness and its Ruff configuration improve development of this repository only. They are deliberately absent from the installed skill, target templates, generated marketplace skill bytes, and target migrations. The validator still checks ownership, instruction routing, plan structure, archive indexes, active versions, marketplace manifests and byte identity, public privacy, parseable metadata and templates, and generated-artifact hygiene. Before an actual project release, maintainers also run the external plugin-creator validator in an ephemeral environment, strict Claude plugin and marketplace validation, and `claude plugin tag --dry-run`; those environment-dependent checks are intentionally outside the harness.

## Versioning and updates

The project uses semantic versioning. Version 0.9.0 adds ownership-aware archive closure and instruction contract v3: target agents review every complete logical commit slice and then the aggregate final diff, while customized mature repositories migrate conservatively. Version 0.8.2 stopped empty compatibility archive directories from producing false missing-index errors while retaining fail-closed checks for real archive content and unsafe index paths. Version 0.8.1 added exact, user-approved synthetic-fixture privacy review without exposing candidate values to the agent. Version 0.8.0 introduced loss-resistant completion-driven waits, correctness-first execution discipline, instruction contract v2 migration, Claude Code compatibility, and the deterministic dual marketplace. Version 0.7.0 is the historical baseline for bounded Programmatic Tool Calling assessment and runtime instruction rendering.

Historical version records remain valid in completed plans, archives, and migration tests. Current-version owners are `SKILL.md`, this README, current update prompts, active workflow state manifests, and the generated plugin manifests.

Canonical upstream: [xeonvs/codex-engineering-workflow](https://github.com/xeonvs/codex-engineering-workflow).
