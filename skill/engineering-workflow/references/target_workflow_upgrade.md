# Target Workflow Upgrade

Use this canonical reference for `upgrade_target_workflow`, which migrates the workflow layer of an existing target repository. It is separate from refreshing or updating the installed skill.

## Contents

1. CLI Contract
2. Planning Gate
3. Discovery
4. Ownership Classification
5. Conflict Analysis
6. Migration Report
7. Questions
8. Mutation Boundaries
9. Apply Sequence
10. Codex Configuration
11. Workflow State Manifest
12. Validation And Rollback

## CLI Contract

`scripts/upgrade_target_workflow.py` supports:

- `--repo`
- `--plan`
- `--apply`
- `--target-version`
- `--include-agent-config`
- `--format json`

`--plan` is read-only. `--apply` is allowed only after audit and migration-plan generation.

## Planning Gate

Target migration changes repository state and therefore always requires the full planning contract in the target repository.

- If `PLANS.md` is missing, create it as the first target write.
- If it exists, update it before other migration edits.
- Do not compress or overwrite unrelated active work.
- If another active task conflicts, stop with one targeted ownership/source-of-truth question.

Use `Plan Origin: direct_execution`, `plan_mode_approved`, or another truthful origin. Preserve requirement traceability, validation, recovery, and exact resume state.

## Discovery

Inspect:

- root and nested `AGENTS.md`
- `PLANS.md` and older execution-plan locations
- backlog, pitfalls, project principles, compatibility instructions, and equivalent names
- `.codex/config.toml` and `.codex/agents/*.toml`
- workflow state manifest and migration notes
- external tracker references
- repository-owned domain, product, architecture, QA, security, and operational documentation

Do not execute repository-authored code during planning.

## Ownership Classification

Classify every discovered artifact as one of:

- `managed`: exact state-manifest path, a path explicitly listed by the manifest, or an explicit managed section
- `shared`: an exact canonical workflow/config path that may also contain repository-owned content
- `protected`: domain, product, architecture, QA, security, release, or operational documentation
- `external_source_of_truth`: repository overview or externally owned tracker/documentation
- `historical`: explicitly supported archived plan/backlog paths
- `unknown`: ownership is not proven

Absence of a manifest never makes a file managed. Unknown remains protected until evidence or a user decision resolves ownership. Broad directory prefixes do not establish ownership.

## Conflict Analysis

Look for:

- duplicate owners and contradictory planning rules
- compressed-plan or repo-change-without-plan instructions
- stale active plans and stale completed next-work state
- conflicting backlog statuses
- stale model pins or unsupported/excessive reasoning defaults
- recursive delegation and multiple writers for shared state
- obsolete compatibility shims
- workflow policy embedded in protected domain docs
- workstation paths or private values
- unknown files incorrectly treated as workflow-owned

## Migration Report

Before apply, return:

- current workflow version
- detected topology
- managed, shared, protected, historical, external, and unknown paths
- conflicts and proposed changes
- intentionally untouched files
- required user questions
- validation plan
- rollback plan

## Questions

Ask only when repository evidence cannot answer a decision that changes ownership, source of truth, deletion permission, protected-document mutation, runtime agent configuration, or a real conflicting alternative.

Perform targeted read-only investigation first. Use the host's structured question mechanism when available, but do not require Plan Mode.

## Mutation Boundaries

Without a separate request, do not change product documentation, architecture manuals, domain rules, release or operational runbooks, QA/security policy, benchmark artifacts, or external tracker records.

Do not replace a shared file wholesale. Change only workflow-owned files, explicit managed sections, necessary index links, compatibility shims, and the state manifest.

## Apply Sequence

1. Re-run the read-only audit and refuse unresolved blocking conflicts.
2. Materialize or update the full target plan as the first write.
3. Create missing canonical workflow files from templates.
4. Narrowly update only managed content or explicit links in shared files.
5. Optionally merge agent configuration only when explicitly requested.
6. Write the state manifest with relative paths.
7. Validate and record exact changes in the target plan.

## Codex Configuration

When `--include-agent-config` is present:

- parse existing TOML before changing it
- preserve unknown keys, custom profiles, and current `max_threads`
- add `max_depth = 1` only when absent or already compatible
- do not overwrite a conflicting explicit depth without a user decision
- create optional agent files only under the explicit flag
- show the exact config diff

Never place Responses API-only fields in Codex TOML.

## Workflow State Manifest

Target path: `docs/codex/ENGINEERING_WORKFLOW_STATE.yaml`.

Required fields:

- `schema_version`
- `skill_name`
- `skill_version`
- `applied_at`
- `mode`
- `source_repo`
- `source_ref`
- `source_commit`
- `managed_paths`
- `shared_paths`
- `protected_paths`
- `runtime_agent_config_managed`
- `planning_contract_version`
- `orchestration_contract_version`

Use repository-relative paths. Never record a workstation path, username, home directory, credential, or private hostname. The manifest governs only listed paths or explicit managed sections; it does not claim an entire documentation directory.

## Validation And Rollback

- Keep `--plan` free of target writes, generated files, repo-code execution, network access, and plugin loading.
- Validate YAML/TOML structure, plan schema, relative manifest paths, ownership boundaries, config preservation, and absence of private paths.
- Report created, changed, untouched, and refused files.
- Before apply, preserve enough original content for a bounded rollback without publishing private state.
- On failure, restore files changed by the migration and leave the target plan with the exact failure and recovery point.
