# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.9.1 Astra And Claude Compatibility

Status: done
Owner: root
Last Updated: 2026-09-05

### Goal

Prepare a validated 0.9.1 skill and dual-platform package with current Codex model profiles, clearer autonomy and continuation rules, and preserved Claude Code model/effort inheritance.

### Plan Origin

plan_mode_approved

### Requested Scope

- Implement the approved Astra migration and behavior refinements as a compatible patch release.
- Preserve native Claude Code settings and existing target-owned configurations.
- Validate model templates, platform boundaries, migration preservation, generated package parity, and realistic instruction-following scenarios.
- Review the complete change, then close and archive this full plan through the canonical lifecycle.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Codex standard/review recommend Astra at medium/high, utility/explorer retain Terra, and unsupported effort/pinned-model boundaries are explicit. | Approved plan | WQ-01, WQ-03 | Parsed model-template validation and mutation regressions. | done |
| REQ-002 | Claude inherits native session or agent model/effort without shared-frontmatter overrides or Codex configuration changes. | User decision: inherit Claude choice | WQ-01, WQ-03 | Frontmatter, platform, migration, and native manifest checks. | done |
| REQ-003 | Canonical rules preserve existing authorization, make pauses attributable, handle steering without losing the goal, and bound delegation, testing, and communication. | Approved plan and Astra guide | WQ-02, WQ-04 | Reachable single owners and independent scenario review. | done |
| REQ-004 | Active version owners and generated Codex/Claude manifests/skill bytes agree at 0.9.1 without schema changes. | Approved patch version | WQ-03 | Builder parity, active-version checks, and full gate. | done |
| REQ-005 | Final code and instruction review, required validation, privacy hygiene, and lifecycle archive complete with truthful evidence. | Approved implementation and repository contract | WQ-04, WQ-05 | Full checks, external static validators, aggregate review, and lifecycle check. | done |
| REQ-006 | Review the complete text of every target/agent template against canonical owners, Astra behavior, Claude compatibility, and its rendering/migration consumers. | User follow-up during implementation | WQ-04 | Complete template inventory, semantic review, resolved findings, and affected regression checks. | done |
| REQ-007 | Route this repository's maintainer instructions to the updated canonical platform, authorization, continuation, and validation owners. | User follow-up | WQ-04 | Root AGENTS review and maintainer/package-boundary tests. | done |

### Explicit Non-Goals

- Tags, GitHub release creation, and local plugin installation remain outside scope. The user subsequently authorized commit and push after final self-review.
- Automatic target-language adaptation is an explicit separate follow-up, as chosen by the user after template review; this patch does not implement localization.
- No new Claude model catalog, automatic model resolver, API client integration, or changes to target schema/invariant requirements.
- No migration of real target repositories; use disposable fixtures.

### Constraints

- Preserve planning/state version 2, instruction/orchestration version 3, and platform/privacy version 1.
- Preserve user-pinned models, native host permission policies, privacy review tokens, and required full plans.
- Keep concrete Codex model mappings under their canonical owner and optional agent templates.
- Keep scanner, evaluation, cache, and temporary artifacts outside the repository; do not edit generated package bytes manually.
- Use root-only maintainer tooling for this source repository; runtime tools must not treat the maintainer AGENTS.md as target instructions.

### Inputs And Sources

- User approved the detailed 0.9.1 plan and explicitly chose Claude model/effort inheritance.
- https://developers.openai.com/api/docs/guides/latest-model
- https://learn.chatgpt.com/docs/models
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/slash-commands
- Repository canonical references, maintainer harness, deterministic package builder, and current tests.

### User Decisions And Answers

- 2026-09-05: Implement the approved plan; use 0.9.1 because this changes recommendations and compatibility guidance without introducing a new schema or feature family.
- 2026-09-05: Claude Code keeps its native model and effort choices; do not introduce dedicated Claude profiles.
- 2026-09-05: The user explicitly requires a full semantic review of all template texts, beyond model fields and configuration-preservation tests.
- 2026-09-05: The user chose to keep the pre-existing automatic target-language adaptation defect as a separate follow-up and complete 0.9.1 with Astra/Claude corrections.
- Publication and local installation were initially excluded in the approved plan; the later commit/push instruction supersedes only those delivery exclusions.
- 2026-09-05: The user requests matching maintainer instructions for this source repository and explicitly authorizes final self-review, commit, and push. The delivery phase includes the required pre-push security gate and exact GitHub Actions verification.

### Completed Baseline State

- [x] Clean main at 6dbdf964b31ea983b31f2e44d3391bf990f6b7fc; current canonical and packaged version is 0.9.0.
- [x] Current model-profile bytes match the generated package and active 0.9.0 plugin cache.
- [x] Official Astra, Codex, and Claude guidance was fetched during planning; the model/effort and shared-frontmatter boundaries are established.
- [x] Native Claude manifest validator is available and supports --strict.

### Current Work Queue

- [x] WQ-01 — Update model recommendations and platform inheritance boundaries for REQ-001 and REQ-002. `done`
- [x] WQ-02 — Refine reachable canonical autonomy, steering, delegation, validation, and communication rules for REQ-003. `done`
- [x] WQ-03 — Add behavioral/structural regression coverage, update active version owners, and generate the package for REQ-001, REQ-002, and REQ-004. `done`
- [x] WQ-04 — Review every template text and its consumers, align root maintainer routes, run focused/full/static platform gates, independent scenario evaluation, and complete diff review for REQ-003, REQ-005, REQ-006, and REQ-007. `done`
- [x] WQ-05 — Reconcile final evidence and prepare the canonical atomic archive transition and lifecycle/package readback for REQ-005. `done`

### Locked Decisions

- Codex defaults: utility Terra/low, explorer Terra/medium template, standard Astra/medium, reviewer Astra/high; exceptional effort remains evaluated rather than automatic.
- Claude native session, existing-agent, provider, and managed settings determine its models and effort; do not equate effort levels across providers.
- The shared skill remains in the invoking context without model/effort/fork/tool-permission frontmatter overrides.
- Question decisions belong in question_matrix; task continuation and delegation belong in agent_orchestration; testing discipline belongs in validation_safety; the router provides short loading routes.
- Schema requirements remain unchanged. Template review corrections preserve exact 0.9.0 templates as test fixtures and known pristine fingerprints; customized target instructions remain protected. New optional Codex reviewer files get Astra, existing files are preserved.

### Verification

- Focused model/profile, platform, skill-validator, migration, updater, and marketplace tests through scripts/dev_check.py.
- python3 scripts/dev_check.py full after package generation.
- Official skill quick validation; native Claude plugin and marketplace validation with --strict.
- Independent scenario evaluation in temporary resources without supplying expected outcomes to the evaluator; distinguish simulated platform review from real Claude runtime evidence.
- Aggregate diff review, public-tree privacy scan, no generated/cache/evaluation residue, and exact version/package parity.
- Canonical lifecycle check/close with archive disposition, followed by lifecycle and package readback.
- After the closed implementation is committed, run scripts/dev_check.py security immediately before the authorized push, read back remote HEAD, and verify the exact GitHub Actions run.

### Latest Validation Results

- Canonical and generated package version is 0.9.1; builder reports zero drift.
- Independent evaluation covered five scenarios: prior authorization, mid-task steering, native Claude configuration, changed privacy snapshot, and bounded delegation. Two documentation ambiguities were corrected and independently rechecked with no remaining finding in those passages.
- First full gate passed Ruff version/format/lint and the structural validator; 244 tests ran with one expected filesystem skip and one environment failure. The failing existing disposable-copy test returned 71 because the outer host sandbox refuses nested sandbox-exec; a minimal diagnostic reproduced sandbox_apply: Operation not permitted. Required checks will rerun with the needed host permission, without weakening internal isolation.
- 2026-09-05: Added and passed quoted/whitespace frontmatter-key regressions; profile drift and unsupported Astra effort are rejected, while native shared frontmatter remains unchanged.
- 2026-09-05: Fully reviewed all 18 template files: AGENTS, PLANS, backlog, incident catalog, state manifest, programmatic stage, principles, adoption/migration notes, six indexes, and three agent profiles. The root and independent evaluator both traced their consumers. Corrected downstream platform/question/continuation reachability and duplicate normative migration-note prose. Preserved exact 0.9.0 fixtures and added pristine-versus-customized migration coverage.
- 2026-09-05: Optional Codex syntax and symlink checks now follow include_agent_config. Temporary-target tests prove malformed/symbolic unrequested configuration is preserved, opted-in unsafe configuration still stops before writes, existing reviewer pins remain unchanged, and new opted-in reviewers receive the current profile.
- 2026-09-05: Final full gate passed 9/9 checks with pinned Ruff 0.16.4: format, lint, structural validator before and after tests, all tests, package parity, and working-tree/HEAD whitespace. All 247 tests completed successfully with one expected macOS filesystem skip for non-UTF-8 names. The outer sandbox limitation was resolved by running the gate with permission to invoke its own internal sandbox; isolation tests were not weakened.
- 2026-09-05: Official skill quick validator and native Claude plugin/marketplace --strict validation passed. Claude model behavior was assessed by independent instruction scenarios and temporary-repository preservation tests, not a live Claude model session.
- 2026-09-05: Aggregate self-review covered all changed source, templates, tests, root maintainer guidance, manifests, and verified generated/source byte parity. No actionable in-scope finding remains. Current public-tree privacy and residue checks passed within the validator; no scanner/evaluation artifacts were added.

### Risks And Recovery

- Stronger autonomy wording could override real permission boundaries: retain explicit host/managed-policy and exact-snapshot privacy protections and test both allowed and blocked scenarios.
- Codex model settings could affect Claude through shared frontmatter: add rejection coverage and preserve model/effort inheritance.
- Generated parity or migration could drift: use the existing atomic builder and temporary target fixtures, preserve existing profile bytes, and review the aggregate diff.
- Correct only task-owned changes if a gate fails; do not reset unrelated files or weaken validation.
- Explicit deferred follow-up: automatic target-language adaptation. A future localization task should gate report/apply on the target's established workflow language and adapt generated prose while retaining structural markers and repository ownership. This pre-existing behavior was reviewed and explicitly excluded by the user from 0.9.1.

### Resume Point

- No unfinished in-scope implementation work remains.

### Plan Fidelity Check

- [x] Every approved outcome, source, and user choice has been preserved.
- [x] REQ-001 through REQ-007 map to ordered work and observable acceptance criteria.
- [x] Scope, version, contracts, native-platform behavior, risks, and delivery exclusions are explicit.
- [x] Every implementation queue item is terminal; the full plan preceded implementation and preserves both follow-up instructions and the explicit language deferral.

### Reconciliation Check

- [x] Final implementation, generated package, validation evidence, template-review scope, user delivery authorization, and terminal queue state agree.
- [x] There is no unrelated active plan or backlog work to reconcile.

### Closure Gate

- [x] Every requirement and queue item is terminal.
- [x] Validation and aggregate review cover the final content.
- [x] Root plan and archive indexes can close atomically with no stale state.

### Post-Close Delivery

- Repository implementation and its validation close before delivery. Commit, security-gated push, and exact GitHub Actions verification are authorized post-close delivery operations, outside the implementation queue; tags, GitHub release creation, and local installation remain out of scope. Any delivery failure that requires code changes starts corrective active work.

### Handoff Notes

- Completed implementation and validation. No in-scope work remains; automatic language adaptation and local plugin installation are outside scope. Native Claude manifest validation passed; no live Claude model session was evaluated. Authorized post-close delivery is classified above.

## Recently Completed

- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
- [x] 2026-08-13: Completed Remove CI Runtime Deprecation.
- [x] 2026-08-13: Completed Complete Engineering Workflow 0.6.0 Publication.
- [x] 2026-08-13: Completed Publish Engineering Workflow 0.6.0.
