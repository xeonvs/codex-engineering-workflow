# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Documentation Navigation And Release Adoption 0.10.0

Status: done
Owner: root
Last Updated: 2026-10-12

### Goal

Provide portable progressive documentation navigation, evidence-based documentation upkeep and snapshot-approved restructuring; safely self-update the installed skill from stable releases and propose target instruction/documentation adoption; publish and verify source, marketplace, and local updates.

### Plan Origin

plan_mode_approved

### Requested Scope

- Implement the complete approved tree-docs and self-update plan in the source skill, source maintainer guidance, target templates, deterministic tools, and regressions.
- Reuse existing inventory, ownership, indexes, safety, rollback, native plugin commands, and validation rather than a third-party generator or orchestration layer.
- Create/merge PRs, release source and marketplace, refresh local Codex/Claude installations, verify delivery, and close this plan through the lifecycle.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Source and targets support compact documentation maps and focused expansion | approved plan | WQ-01, WQ-04 | Portable read-only map, explicit roots, bounded output, honest discovery metadata | done |
| REQ-002 | Documentation authoring and upkeep have one canonical owner and reachable routes | approved plan | WQ-04 | Owner/routing checks and independent navigation/maintenance scenarios | done |
| REQ-003 | Exact proposed documentation restructuring requires snapshot approval and rolls back safely | approved plan | WQ-03, WQ-04 | No writes without exact approval; drift/link/invariant/rollback regressions | done |
| REQ-004 | Stable installed-skill self-update uses native distribution and verifies active bytes | user addition and chosen policy | WQ-02, WQ-04 | Stable vs main/marketplace-lag/offline/conflict/post-update tests | done |
| REQ-005 | Target proposals distinguish version, structural state, and semantic adoption | approved plan | WQ-02, WQ-04 | Skipped releases/customized owners/no automatic target writes/dedup tests | done |
| REQ-006 | All implementation and independent review pass applicable gates | approved plan | WQ-05 | Full/security/external validators, behavioral forward tests, aggregate review | done |
| REQ-007 | Released source, marketplace, local installations, and closed durable state agree | chosen full delivery | WQ-06, WQ-07 | CI, immutable tags, provenance/byte parity, enabled local readback, lifecycle closure | done |

### Explicit Non-Goals

- No automatic changes to arbitrary user targets, no automatic schedules, no model-GPT-6 worker assignments, no global rewriting of documentation style.
- No replacement of plugin caches, no unmanaged/domain ownership inference, no source-main updates by default, no scanner weakening or published-history rewriting.
- No duplicated runtime contracts in source docs or generic semantic merger that invents approved content.

### Constraints

- This complete plan is the first repository write. Root alone owns this plan, state integration, version owners, generated package, and release decisions.
- Preserve instruction contract 3 and existing schema versions; use compatible optional fields and bounded semantic adoption review.
- A new session or material context recovery receives one compact map; unchanged state is not repeatedly reread.
- Map defaults: at most 120 visible nodes and 8192 UTF-8 bytes, no document bodies, collapsed branches with counts and expansion instructions, complete JSON report when requested.
- Document roots are discovery scope, not ownership. Generated indexes change only explicit managed sections; author descriptions and source language remain local.
- Self-update policy is installation-scoped outside target/cache; automatic_stable is explicitly selected, while legacy unset policy remains notification-only. Remote check cache lasts 24 hours; explicit update bypasses it.
- Known local disposable checks are authorized. Run full final checks, review each logical slice and final aggregate, and security immediately before every source push.

### Inputs And Sources

- Approved conversational plan: tree docs, then complete replacement incorporating stable self-update and target adoption.
- https://openai.com/index/harness-engineering/
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
- User examples are inspiration, not literal instructions.

### User Decisions And Answers

- 2026-10-12: compact map on entry/recovery; expand relevant branches on demand.
- 2026-10-12: affected docs maintained with changes; periodic audits separately opt in.
- 2026-10-12: full source/marketplace release and local update delivery.
- 2026-10-12: auto-update trusted stable skill, propose target changes; explicitly record policy on adoption.
- 2026-10-12: use GPT-6.1 and GPT-5.6 workers, not GPT-6.
- 2026-10-12: implement the complete proposed plan.

### Completed Baseline State

- [x] WQ-00 — Initial clean main at fb42a0a; installed/public skill 0.9.10 and marketplace 1.0.10. Live tags were rechecked before publication.
- [x] WQ-00A — Independent read-only audits confirmed reusable inventory/index machinery, plugin updater handoff-only gap, default main ref, and absence of target notification/adoption metadata.
- [x] WQ-00B — Source docs primarily contain archives; live runtime contracts are under skill/engineering-workflow/references and must appear in the source map without relocation or duplication.

### Current Work Queue

- [x] WQ-01 — Implement read-only documentation navigation and managed-index planning/checking for REQ-001. `done`
- [x] WQ-02 — Implement stable candidate discovery, installation policy/state, native update orchestration, target recommendation and adoption/provenance support for REQ-004 and REQ-005. `done`
- [x] WQ-03 — Implement exact snapshot-approved restructuring with validation and atomic rollback for REQ-003. `done`
- [x] WQ-04 — Integrate canonical references, source/target routes, compatible migration/config preservation, validators, active version owners and generated package for REQ-001, REQ-002, REQ-003, REQ-004, and REQ-005. `done`
- [x] WQ-05 — Run affected and full/security/external gates, independent forward scenarios and semantic review; fix findings for REQ-006. `done`
- [x] WQ-06 — Create/merge source PR after CI and publish stable source release for REQ-007. `done`
- [x] WQ-07 — Import exact source bytes, review/merge marketplace PR, publish catalog release, update local installations, verify and prepare checked closure for REQ-007. `done`

### Locked Decisions

- Source 0.10.0 / marketplace 1.0.11 if current tags remain unchanged; stable publication channels only by default.
- Retain existing archive semantics. Shared generic helpers may be extracted, but broad docs roots do not become managed.
- No mandatory document frontmatter, automatic summaries, table/link prohibition, or universal physical docs taxonomy.
- An update proposal includes existing local owners and semantic changes. A version stamp is not adoption evidence; applicable change IDs are recorded only after acceptance checks.
- Normal target upgrade remains distinct from exact approved document moves/merges/deletions. Before restructuring, preserve incoming links/anchors/invariant IDs or explicitly resolve compatibility.
- Transport failure means currentness unknown and continuation on installed content, not false success or interruption of unrelated work.

### Verification

- REQ-001: Git/non-Git and unusual-name discovery, custom roots, ignored/symbolic paths, deterministic output bounds/collapse, no writes or repository execution, readable complete report.
- REQ-002: routes load one writing/maintenance owner, existing owner/language preservation, scoped documentation impact review, forward scenarios on small/large/custom targets.
- REQ-003: approval absent/stale/proposal drift/input drift produce zero writes; links/anchors/invariants persist; induced write/validation failure restores exact bytes.
- REQ-004: unpublished main, stable tags and catalog lag; explicit ref, offline, unchanged candidate, dirty/divergent installs, native cache update and verified readback.
- REQ-005: version/loaded/installed/adopted distinction, skipped releases, semantic review on customized owners, deduplicated/rejected proposals and no implicit target mutation.
- REQ-006: final dev_check full/security, native Codex/Claude validators, package parity, independent GPT-6.1/GPT-5.6 scenarios and final-diff review.
- REQ-007: exact CI jobs, annotated immutable tags, recorded provenance, released/imported/cache bytes, local enabled versions, lifecycle/archive indexes and clean main.

### Latest Validation Results

Final verification date: 2026-10-12.

- Final source and fresh released-clone full gates passed 9/9; pre-push privacy/Gitleaks passed 3/3. Strict Claude plugin/catalog and skill-creator checks passed. Current Codex CLI has no standalone plugin validator; source structural checks and actual native installation/readback passed.
- Independent forward and aggregate reviews resolved all reproduced findings: cache failures/local drift, native platform/path/scope and partial state, nested/custom writing owners, mid-apply adoption drift, approval dependencies, HTML/reference links, code examples and snapshot recovery.
- Source PR #23 and both validate jobs passed; annotated v0.10.0 is released at 93f5163396aecc3005fe37df969ae771b78ddd34.
- Sync run 38240471498 and catalog PR #24 passed. Catalog 16 tests, validator, recorded-upstream verification and pre-push scans passed. Annotated marketplace v1.0.11 is released at 2795f988639575070259e5f3e9720b64ec1fbccf; release run 38241287497 succeeded.
- Release archive checksum b126c17e47c8384e0bd78088d48c95a0bf8dc1db70fbc733377414dd5d4879e1 verified; Git and executable caches are absent. Source/imported/Codex/Claude bundle digest is bff29b06f8672492a594de3b9595781ac0803e5d09b8ffffc2c2262a9ce031d1.
- Both native installations are enabled at 0.10.0 with automatic_stable policy; installed updater checks report up_to_date against source v0.10.0/catalog v1.0.11. Target mutation remains false. tgrep-search 1.0.3 remains unchanged and enabled. Existing Claude sessions require native plugin reload/restart to consume updated instructions; no user session was forcibly restarted.

### Risks And Recovery

- Risk: broad index generation claims domain files or breaks custom archives. Recovery: explicit section ownership, preserved defaults, disposable regressions and atomic rollback.
- Risk: self-update changes an active installation or silently installs unreleased content. Recovery: policy opt-in, pinned stable/delivery identity, existing backups/native commands, verified reread and explicit unknown/failure states.
- Risk: target stamp masks missed semantic adoption. Recovery: applicable change IDs plus evidence-backed owner review before stamping; never use phrase matching as semantic proof.
- Risk: restructuring drops incoming links or user content. Recovery: exact input/output proposal, preflight graph/invariant checks, fail closed on unresolved dependencies, root-pinned transaction and rollback.

### Resume Point

- No remaining in-scope implementation or artifact delivery. Checked lifecycle closure is ready; subsequent documentation delivery changes no release bytes.

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

- [x] Affected work state, repository state, and applicable validation agree.
- [x] Plan and requirement statuses, queue, resume point, indexes, and related docs agree.
- [x] Completed sections contain no stale next-work or blocker wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Compact or archive disposition can be applied atomically.

### Post-Close Delivery

- Source/marketplace releases and local verification are completed. Post-close documentation delivery is outside implementation scope; no additional release is required.

### Handoff Notes

- Verified source/catalog releases and local installations agree. Root retains documentation delivery ownership; no unresolved blocker or unreviewed implementation remains.

## Recently Completed

- [x] 2026-09-25: Completed Repair Custom Archive Upgrade And Add Claude Subagent Profiles; [full archived plan](2026-09-25-repair-custom-archive-upgrade-and-add-claude-subagent-profiles.md).
- [x] 2026-09-23: Completed Privacy Preflight Exact Review V2 And Release; [full archived plan](2026-09-23-privacy-preflight-exact-review-v2-and-release.md).
- [x] 2026-09-23: Completed GPT-6 Model Profiles And Marketplace Release; [full archived plan](2026-09-23-gpt-6-model-profiles-and-marketplace-release.md).
- [x] 2026-09-20: Completed Publish Repository Audit Fix 0.9.7; [full archived plan](2026-09-20-publish-repository-audit-fix-0-9-7.md).
- [x] 2026-09-20: Completed Bounded Git-Aware Repository Audit 0.9.7; [full archived plan](2026-09-20-bounded-git-aware-repository-audit-0-9-7.md).
- [x] 2026-09-15: Completed Context Discipline And Bounded Delegation 0.9.6; [full archived plan](2026-09-15-context-discipline-and-bounded-delegation-0-9-6.md).
- [x] 2026-09-13: Completed Astra Workflow Instruction Efficiency; [full archived plan](2026-09-13-astra-workflow-instruction-efficiency.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.4 Plugin Brand Icon; [full archived plan](2026-09-12-engineering-workflow-0-9-4-plugin-brand-icon.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
