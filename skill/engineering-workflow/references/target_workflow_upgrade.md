# Target Workflow Upgrade

Use this canonical reference for `upgrade_target_workflow`, which migrates the workflow layer of an existing target repository. The natural-language prompt `Upgrade A Target Workflow` tells the agent to execute this workflow itself. It remains separate from refreshing or updating the installed skill.

## Contents

1. Prompt Invocation
2. CLI Contract
3. Planning Gate
4. Discovery
5. Ownership Classification
6. Conflict Analysis
7. Migration Report
8. Questions
9. Mutation Boundaries
10. Apply Sequence
11. Codex Configuration
12. Workflow State Manifest
13. Validation And Rollback

## Prompt Invocation

Treat `Upgrade A Target Workflow` plus a target repository as an authorized repo-changing prompt, not as a request for CLI instructions.

1. Resolve the target path and requested version from context; default to the installed skill version.
2. Invoke `scripts/upgrade_target_workflow.py --prompt` yourself.
3. Prompt mode builds and reviews the read-only migration report first.
4. If ownership, conflicts, privacy, and approvals are resolved, it proceeds through guarded apply and validation automatically.
5. If the result returns `agent_action: ask_targeted_question`, ask only `question_to_ask`; keep any later questions deferred and do not write target files.
6. If it returns `privacy_review_required`, report the finding categories and paths without values and make no target writes.
7. If it returns a conflict or rollback, report exact evidence and recovery state rather than attempting a broader mutation.

The user may explicitly request report-only behavior; then invoke `--plan`. Runtime agent configuration remains opt-in through the user's prompt and `--include-agent-config`.

## CLI Contract

`scripts/upgrade_target_workflow.py` supports:

- `--repo`
- `--plan`
- `--apply`
- `--prompt`
- `--target-version`
- `--include-agent-config`
- `--format json`

`--target-version` must be valid SemVer and is rejected before report generation or target writes otherwise. `--plan` is read-only. `--apply` is allowed only after audit and migration-plan generation. `--prompt` is the agent-owned report-then-apply route for an authorized natural-language upgrade request and stops before writes whenever a question, privacy finding, or conflict remains.

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

1. Capture the target-root filesystem identity, re-run the read-only audit, and refuse unresolved blocking conflicts or privacy findings.
2. Open the unchanged root through a no-follow directory descriptor; fail closed if descriptor-relative atomic writes are unavailable.
3. Materialize or update the full target plan as the first write.
4. Create missing canonical workflow files from templates.
5. Narrowly update only managed content or explicit links in shared files.
6. Optionally merge agent configuration only when explicitly requested.
7. Write the state manifest with relative paths.
8. Validate and record exact changes in the target plan.
9. Re-run the public privacy scan immediately before success.

Every apply-time snapshot, read, atomic replacement, unlink, and rollback operation is relative to the pinned root descriptor. Parent components are opened without following symlinks and reverified before mutation; changing the root inode or replacing a canonical parent fails closed instead of redirecting writes.

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
- Treat the fresh apply-time report as authoritative: any privacy finding returns `privacy_review_required` before the first write, even when an earlier prompt report was clean.
- Validate YAML/TOML structure, plan schema, relative manifest paths, ownership boundaries, config preservation, and absence of private paths.
- Report created, changed, untouched, and refused files.
- Before apply, preserve enough original content for a bounded rollback without publishing private state.
- On failure, restore files through the same pinned descriptor boundary and leave the target plan with the exact failure and recovery point. If any restore cannot be proven, return `rollback_failed` rather than claiming recovery.
