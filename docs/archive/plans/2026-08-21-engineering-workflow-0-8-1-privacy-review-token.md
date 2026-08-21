# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.8.1 Privacy Review Token

Status: done
Owner: root
Last Updated: 2026-08-21

### Goal

Release `engineering-workflow` 0.8.1 with a lossless, one-migration privacy-review token for explicitly approved synthetic fixture findings, clear agent-facing approval instructions, natural installation guidance for Codex and Claude Code, complete regression coverage, and verified public delivery that closes GitHub issue #3.

### Plan Origin

plan_mode_approved

### Requested Scope

- Resolve GitHub issue #3 without weakening the fail-closed public-tree privacy gate.
- Let a user explicitly approve an unchanged, reviewed set of eligible synthetic findings for one exact target-workflow migration.
- Make the required approval exchange unambiguous to agents that run the skill.
- Move Codex and Claude Code installation near the top of README and edit the full document into natural user-facing English.
- Run a redacted local `gitleaks` audit that keeps secret values out of agent context; if a real secret is validated, remove it from local and GitHub history and verify every affected public ref again.
- Publish the completed work as 0.8.1 through a non-draft PR, merge commit, annotated tag, GitHub Release, issue closure, and public-tag readback.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | A deterministic `privacy-review-v1` token binds contract version, current workflow version, target version, and the sorted multiset of exact eligible finding fingerprints; only the five approved synthetic categories are eligible and all other categories remain hard blocks. | User-approved plan; GitHub issue #3 | WQ-01, WQ-04 | Unit tests cover determinism, multiplicity, category boundary, malformed/mismatched tokens, and version/path/line/content changes. | done |
| REQ-002 | Report, apply, and prompt upgrade modes expose a stable value-free review schema; apply validates a fresh snapshot before writing, final scan detects races, rollback remains intact, and no persistent baseline/token file is created. | User-approved plan; GitHub issue #3 | WQ-01, WQ-02, WQ-04 | Migration matrix proves unchanged approval succeeds while new, changed, moved, hard-blocked, and during-apply findings stop without residue or leaked values. | done |
| REQ-003 | Runtime skill and canonical upgrade/privacy references teach agents to show only category/path/line, request explicit user approval, never self-approve, and rerun with the exact token only after approval. | User: agents must understand correct use | WQ-02, WQ-04 | Structural and behavioral tests verify routing/action semantics; direct semantic review confirms one canonical owner and clear agent procedure. | done |
| REQ-004 | README begins with natural Codex and Claude Code installation/use guidance, preserves honest capability differences and alternatives, and explains the two-step privacy review in user language. | User request | WQ-03, WQ-04 | README structure tests plus full direct editorial review and link/command verification. | done |
| REQ-005 | Every active version owner and deterministic dual-marketplace package consistently identifies skill/plugin version 0.8.1 without changing instruction or orchestration contract versions. | User-approved release scope | WQ-03, WQ-04 | Active-version search, package byte-for-byte drift check, manifest validators, and platform validators pass. | done |
| REQ-006 | Focused regressions, repository gate, privacy scan, diff review, and release checks are green on final content. | Repository contract | WQ-04, WQ-05 | Validator, full unittest suite, validator, diff check, public-tree scan, plugin validators, and self-review pass. | done |
| REQ-007 | Authorized delivery preserves the release commit through PR merge, publishes annotated tag and GitHub Release v0.8.1, closes issue #3, validates remote CI and a fresh public tag clone, and leaves clean synchronized `main`. | User-approved plan | WQ-06 | GitHub/readback evidence for PR jobs and steps, merge parents, tag/release/issue, public clone, and final local/remote state. | out_of_scope |
| REQ-008 | A redacted `gitleaks` audit covers the working tree and Git history without exposing candidate values to the agent; any validated real secret is removed from local and GitHub history and all affected refs are rescanned. | User security request | WQ-04, WQ-05, WQ-06 | Redacted scan/report summary, false-positive classification without value ingestion, and—only if required—history-rewrite/ref/readback evidence plus a clean rescan. | done |

### Explicit Non-Goals

- Do not create a persistent privacy baseline, allowlist, or reusable approval file.
- Do not expose matched values or per-line digests in CLI, JSON, logs, tests, documentation, or agent messages.
- Do not ingest or print `gitleaks` secret values; review only fully redacted rule/path/line/ref metadata and deterministic test-fixture provenance.
- Do not make user paths, file URLs, private keys, known token prefixes, credential URLs, SSH repository URLs, or other hard categories approvable.
- Do not change instruction contract version 2, planning contract version 2, or orchestration contract version 3.
- Do not install or update the locally cached skill/plugin as part of this release.
- Do not delete the remote feature branch after merge without separate authorization.

### Constraints

- Preserve unrelated user work and stage only reviewed files explicitly.
- Use direct model judgment for implementation, semantic review, approvals, external writes, and release decisions; any programmatic stage must be bounded and evidence preserving.
- Token approval is user authority for the exact reviewed snapshot, never model authority and never a general privacy exception.
- The user has authorized local and GitHub history rewriting only when a redacted audit establishes a real published secret; synthetic fixtures and false positives are classified without destructive rewriting.
- Generated marketplace contents come only from the repository builder and are never edited manually.
- Public release delivery happens only after the closable implementation plan is validated and archived.

### Inputs And Sources

- User request: implement the approved 0.8.1 plan, take GitHub issue #3, improve README placement/language, and ensure agents understand correct use.
- GitHub issue: https://github.com/xeonvs/codex-engineering-workflow/issues/3
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- Claude Code skills: https://code.claude.com/docs/en/slash-commands
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Claude Code marketplaces: https://code.claude.com/docs/en/plugin-marketplaces

### User Decisions And Answers

- 2026-08-21: use release version 0.8.1 and complete the full publication lifecycle.
- 2026-08-21: approval is a stateless one-migration token, not a persistent baseline file.
- 2026-08-21: only credential-like assignment, environment-secret assignment, bearer token, email, and internal-hostname synthetic findings are review eligible.
- 2026-08-21: keep hard privacy categories unconditionally blocking.
- 2026-08-21: put installation for Codex and Claude Code near the top of README and edit the whole document for natural language.
- 2026-08-21: agent-facing instructions are the primary correctness surface for the approval workflow.
- 2026-08-21: run `gitleaks` locally with secret-safe output; if a real secret is found, forcibly clean local and GitHub history and verify the rewritten refs.

### Completed Baseline State

- [x] WQ-00 — Audited clean synchronized `main`, GitHub issue #3 and owner clarification, privacy scanner/upgrader/test structure, current README/version owners, marketplace builder, canonical instruction ownership, and official platform installation guidance; created `codex/privacy-review-token-0.8.1` and materialized this full plan.

### Current Work Queue

- [x] WQ-01 — Implement the internal fingerprint multiset, aggregate review token, eligibility boundary, stable value-free report schema, and fresh pre-write validation for REQ-001 and REQ-002. `done`
- [x] WQ-02 — Integrate prompt/apply actions, final-scan race protection, CLI option, and canonical agent-facing privacy/upgrade instructions for REQ-002 and REQ-003. `done`
- [x] WQ-03 — Reorganize and edit README, update active 0.8.1 owners, and rebuild the dual-marketplace package for REQ-004 and REQ-005. `done`
- [x] WQ-04 — Add the complete migration/privacy/agent/README/package regression matrix, run focused checks, perform implementation plus semantic self-review, and run redacted working-tree/history secret scans for REQ-001 through REQ-006 and REQ-008. `done`
- [x] WQ-05 — Run the full repository and release gate, confirm that no validated secret requires the authorized history-cleanup path, reconcile lifecycle state, and prepare this plan for atomic archive closure for REQ-006 and REQ-008. `done`
- [x] WQ-06 — Commit, push, PR, CI, merge, tag, Release, issue closure, public readback, and final synchronization for REQ-007 are outside the closable implementation lifecycle and governed by the explicitly authorized immediate Post-Close Delivery boundary. `out_of_scope`

### Locked Decisions

- The public review surface contains only contract version, status, aggregate token, value-free candidates, and approved count; the existing `privacy_findings` field continues to mean currently blocking findings.
- An eligible finding fingerprint binds category, repository-relative path, one-based line number, and SHA-256 of the exact decoded source line including its line ending. The public aggregate token binds the sorted multiset, contract version, current workflow version, and target version.
- Mixed eligible and hard findings are a hard block and produce no review token.
- A stale token is ignored when no finding requires approval; malformed or mismatched tokens never authorize writes.
- Fresh apply validation happens before the first write. The final scan compares against the in-memory approved fingerprint multiset from that fresh snapshot, rather than accepting a newly recomputed token.
- If an approved finding disappears during migration, it does not block; any new, changed, or moved finding does block and triggers rollback.
- README explains user operation; `SKILL.md` routes runtime behavior; target-workflow and privacy references own the detailed agent contract.

### Verification

- REQ-001 / WQ-01, WQ-04: focused privacy and upgrader unit tests for token/fingerprint/category/version/multiplicity behavior.
- REQ-002 / WQ-01, WQ-02, WQ-04: report/apply/prompt migration matrix, byte-preservation checks, no-write assertions, final-scan race rollback, and absence of a baseline artifact.
- REQ-003 / WQ-02, WQ-04: skill validator, routing/action tests, and direct full-text semantic review of `SKILL.md` plus canonical privacy/upgrade references.
- REQ-004 / WQ-03, WQ-04: README heading/order tests, verified installation commands and links, and direct editorial read-through.
- REQ-005 / WQ-03, WQ-04: active-version search, marketplace builder `--check`, repository manifest/catalog validator, plugin-creator validation, Claude strict validation, and tag dry-run.
- REQ-006 / WQ-04, WQ-05: validator → full unittest suite → validator → privacy scan → `git diff --check`, plus complete diff and commit readback.
- REQ-007 / WQ-06: inspect every GitHub Actions job/step for branch, PR, main, and tag runs; verify merge parents, annotated tag, Release and issue state; validate a fresh public tag clone; finish on clean synchronized `main`.
- REQ-008 / WQ-04, WQ-05, WQ-06: run `gitleaks` with complete redaction over the final tree and history, summarize only safe metadata, and if a real secret is validated, rewrite the exact affected refs, force-publish them, and repeat remote/public-clone scans.

### Latest Validation Results

- 2026-08-21: focused target-upgrade matrix passed 40 tests; sanitizer, platform compatibility, marketplace package, and repository-validator focused suites passed.
- 2026-08-21: final gate passed validator → 212 tests with 1 platform-dependent skip → validator → deterministic package check → `git diff --check`.
- 2026-08-21: skill-creator quick validation, plugin-creator validation in ephemeral `uv` with PyYAML, and Claude strict plugin/marketplace validation passed.
- 2026-08-21: fully redacted `gitleaks` scans of the final working tree and Git history with explicit `--all` returned zero findings; raw reports were removed and no history rewrite condition was met.
- 2026-08-21: full code/diff and README editorial self-review completed; the only gate findings were self-triggering test variable names and one capability-matrix wording drift, both corrected before the final green gate. Claude tag dry-run remains correctly deferred until the release commit makes the tree clean.

### Risks And Recovery

- Risk: a review token becomes a reusable allowlist. Recovery: bind it to both versions and the exact current multiset, persist nothing, and validate a fresh snapshot before writes.
- Risk: sensitive values escape through diagnostics. Recovery: keep raw lines/digests internal, test serialized public output for absence, and run the public-tree privacy scan.
- Risk: a scanner report itself exposes a secret. Recovery: require full `gitleaks` redaction, store any report in a task-owned ignored temporary directory, parse only safe metadata, and delete it after verification.
- Risk: secret remediation rewrites too much history. Recovery: validate the finding from redacted provenance first, enumerate affected refs, preserve recovery refs outside the published namespace, rewrite only when the user-authorized condition is met, and verify every force-updated ref.
- Risk: a finding changes between approval and completion. Recovery: retain approved fingerprints in memory, rescan before success, and use the existing transactional rollback path.
- Risk: generated marketplace drift or platform-specific breakage. Recovery: rebuild from the canonical skill, require byte-for-byte check and both platform validators, and validate a fresh public tag clone.
- Risk: remote delivery partially completes. Recovery: read back each remote state, preserve the remote feature branch, and stop before any unsafe rewrite or destructive correction.

### Resume Point

- No unfinished in-scope implementation work remains.

### Plan Fidelity Check

- [x] Every agreed outcome has a requirement ID.
- [x] Every source URL is preserved.
- [x] Every user answer and locked decision is preserved.
- [x] No requirement was silently narrowed or removed.
- [x] The queue covers every requirement ID.
- [x] Validation covers every acceptance criterion.
- [x] Non-goals do not contradict requested scope.
- [x] The resume point names the first unfinished queue item.
- [x] This plan is not a compressed rewrite of a more detailed approved plan.

### Reconciliation Check

- [x] Plan status, requirement statuses, first unfinished queue item, resume point, backlog promotion, latest validation, working tree, indexes, and related workflow docs agree.
- [x] Completed sections contain no stale next-work, resume, current-milestone, active-blocker, or open-status wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for the final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive disposition can be applied atomically.

### Post-Close Delivery

- Outside the closable repository-implementation scope and explicitly authorized for immediate delivery after archive closure: exact staging and commit `Release engineering-workflow 0.8.1`, any conditionally required verified local/GitHub secret-history cleanup, push, non-draft PR with `Closes #3`, completion-driven CI inspection, merge commit, annotated `v0.8.1` tag, GitHub Release, issue/public-tag readback, and final clean synchronized `main`. The remote feature branch remains unless separately authorized for deletion.

### Handoff Notes

- No in-scope implementation work remains; external delivery is governed solely by the Post-Close Delivery boundary.

## Recently Completed

- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
- [x] 2026-08-13: Completed Engineering Workflow 0.6.0; [full archived plan](docs/archive/plans/2026-08-13-engineering-workflow-0-6-0.md).
- [x] 2026-07-13: Completed implementation, review, security/privacy remediation, and validation for `engineering-workflow` 0.5.1; the [legacy schema-v1 plan](docs/archive/plans/2026-07-13-engineering-workflow-0.5.1.md) preserves its historical record.
