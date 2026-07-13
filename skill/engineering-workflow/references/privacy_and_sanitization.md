# Privacy And Sanitization

Use this canonical reference for public-tree, output, and history sanitization.

## Public Scan Scope

Scan every tracked public text file, including root plans, README, workflow files, templates, scripts, tests, fixtures, and CI configuration.

Exclude Git object storage, binary files, generated caches, build output, and vendored dependency trees that are not intentionally part of the public artifact.

## Sensitive Categories

Detect and remove or generalize:

- macOS, Linux, and Windows user-profile paths
- local file URL schemes
- private SSH key locations and private key material
- internal hostnames
- credential-like assignments
- known token and API-key shapes
- passwords and bearer material
- repository URLs containing credentials or using unintended private SSH endpoints
- private names, customers, codenames, emails, and user-specific identifiers when they are not intentionally public

Do not echo a candidate secret value in logs or reports. Return only its category, relative file, line number, commit identifier when applicable, and remediation status.

## Safe Reuse

Reuse generic file names, section headings, neutral workflow patterns, and public source URLs. Do not transplant donor-repository prose or workstation-specific installation paths into retained artifacts.

## Historical Versions

Do not ban every old version string. Historical versions are valid in completed plans, migration records, changelogs, archives, and tests.

Enforce current-version consistency only for active sources such as `SKILL.md`, README's current-version declaration, current update prompts, active state manifests, and active installation checks.

## History Scan And Rewrite

When a user authorizes historical remediation:

1. Scan every reachable commit and blob with a dedicated secret scanner when available plus repository-specific path and credential rules.
2. Classify findings without printing values.
3. Create a permission-restricted temporary recovery artifact.
4. Rewrite every affected commit, not only the tip.
5. Remove legacy refs that keep the sensitive objects reachable after verified recovery.
6. Rescan the rewritten history and current tree.
7. Update the remote only with an object-ID-pinned force-with-lease.
8. Delete the recovery artifact after remote readback succeeds.

History rewriting changes commit IDs and requires downstream clones to rebase carefully or reclone. Report the old-to-new mapping and residual external-copy risk.
