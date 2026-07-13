# Skill Refresh And Update

Use this canonical reference when a user asks to reread, refresh, download, or update the installed `engineering-workflow` skill. Do not combine these operations with target-repository migration.

## Contents

1. Invocation Semantics
2. Refresh Loaded Skill
3. Update Installed Skill
4. CLI Contract
5. Installation Types
6. Candidate Validation
7. Trust Boundary
8. Backup And Rollback
9. Structured Result
10. Completion Boundary

## Invocation Semantics

Route phrases that mean "reread this skill" to `refresh_loaded_skill`. Route phrases that mean "download/update this installed skill" to `update_installed_skill`. Route phrases that mean "apply the newer workflow to this repository" to `upgrade_target_workflow`.

If repository evidence cannot resolve real ambiguity, ask one targeted question that distinguishes installed-skill update from target-workflow migration.

## Refresh Loaded Skill

`refresh_loaded_skill`:

1. Resolve the exact active skill path rather than guessing from similar folders.
2. Reread its `SKILL.md` and report `metadata.version`.
3. Reread only the references needed for the current task.
4. Use the refreshed instructions for the rest of the turn.

It does not use the network, mutate the installation, or change a target repository.

## Update Installed Skill

`update_installed_skill` obtains a structurally validated candidate from a trusted upstream and updates only the exact active installation.

Canonical upstream:

- repository: `https://github.com/xeonvs/codex-engineering-workflow`
- source path: `skill/engineering-workflow`

Use `scripts/update_installed_skill.py`. Do not execute candidate scripts as a validation technique.

## CLI Contract

The updater supports:

- `--install-path`
- `--source-repo`
- `--source-path`
- `--ref`
- `--check`
- `--apply`
- `--allow-downgrade`
- `--backup-dir`
- `--format json`

Alternate upstream apply requires explicit confirmation after structural inspection and diff summary.

## Installation Types

### Symlinked Installation

- Resolve the real target and preserve the symlink.
- If the target belongs to a canonical Git checkout, verify remote, source path, branch/ref, and clean state.
- Fetch and fast-forward only; never force, reset, or discard local changes.
- Stop with a structured conflict for dirty or divergent state.
- If the target is a copied tree, replace the target atomically while leaving the symlink itself intact.

### Git Checkout Installation

- Verify the checkout remote and installed source path.
- Refuse dirty state, divergent history, merge commits, branch changes, and downgrade unless explicitly allowed.
- Update only by fast-forward.

### Copied Installation

- Materialize the candidate in a temporary directory.
- Validate it statically.
- Compare SemVer and refuse downgrade by default.
- Create a backup and stage a sibling replacement.
- Replace atomically where the filesystem permits.
- Restore the backup after any failed replacement.
- Leave no partial installation.

## Candidate Validation

Require:

- regular `SKILL.md`
- valid frontmatter
- `name: engineering-workflow`
- valid SemVer `metadata.version`
- required skill paths
- no path traversal
- no symlink escaping the candidate tree

Materialize a Git candidate through inert object reads rather than a working-tree checkout, so candidate attributes cannot trigger checkout filters during inspection. Validation reads candidate content but does not execute fetched code.

## Trust Boundary

Automatic apply is allowed only for the canonical upstream or a source repository explicitly confirmed by the user.

For an alternate source:

1. Inspect structure.
2. Report source repository, version, resolved commit, and diff summary.
3. Return `confirmation_required` before apply unless explicit confirmation is already supplied.

## Backup And Rollback

Backups must be outside the replaced directory, permission-appropriate for the local filesystem, and named so multiple updates do not collide. Do not delete the backup until the caller accepts the successful result.

If staging or replacement fails after the old installation moved, restore it immediately and return a rollback result. Never report success while the active path is partial or missing.

## Structured Result

Return:

- previous version
- candidate version
- source repository and path
- source ref and resolved commit
- active installation path
- resolved target path
- installation type
- backup path
- validation result
- update status
- restart or next-turn requirement

Do not include credentials or fetched secret values.

## Completion Boundary

After a successful update:

1. Reread the new `SKILL.md`.
2. Report the installed version.
3. Stop the update operation.
4. Run target migration only in a new turn or after a confirmed restart when updated instructions are active.

Current Build Skills documentation detects changed skills automatically and recommends restart only when the change does not appear. The official installer still uses `$CODEX_HOME/skills`; current authoring discovery also includes repository/user `.agents/skills`, admin, system, copied, and symlinked locations. Never assume one universal installation directory.
