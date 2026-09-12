# Execution Plans

plan_schema_version: 2

Use this file for active, blocked, ready-for-closure, or recently completed execution work. The canonical lifecycle is the installed `engineering-workflow` planning reference.

## Active Plan: Engineering Workflow 0.9.4 Plugin Brand Icon

Status: done
Owner: root
Last Updated: 2026-09-12

### Goal

Publish `engineering-workflow` 0.9.4 with the approved opaque workflow-cycle
identity, deterministic SVG/PNG assets, and valid Codex UI metadata while
preserving runtime behavior, package parity, and Claude Code compatibility.

### Plan Origin

direct_execution

### Requested Scope

- Reconstruct the user-approved third-round Engineering Workflow icon as clean
  vector geometry with no transparency holes, gradients, shadows, or generated
  raster artifacts.
- Package the icon for Codex `composerIcon`, `logo`, `logoDark`, and
  `brandColor`, retaining the assets in the shared plugin bundle for Claude
  without inventing unsupported Claude image fields.
- Release the asset-only plugin update and make it eligible for verified import
  into the unified `xeonvs-engineering` marketplace.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Approved cycle/checkmark geometry exists as an opaque canonical SVG and deterministic 1024 px and 128 px PNG renders. | User approval, 2026-09-12 | WQ-01 | XML parse, dimensions/opacity checks, and visual QA at full and compact sizes. | done |
| REQ-002 | Codex manifest references real self-contained icon files and a matching brand color; Claude manifest remains schema-valid without unsupported image fields. | Codex plugin manifest contract and Claude Code schema | WQ-02 | Builder/package tests plus external Codex and Claude validators. | done |
| REQ-003 | Every active version owner and generated package agrees at 0.9.4 without runtime, schema, model, or target-workflow changes. | User version-bump decision, 2026-09-12 | WQ-02 | Active-version search, generated/source parity, aggregate diff review, and full gate. | done |
| REQ-004 | Source release and downstream import remain exact, immutable, and security-gated. | User delivery request | WQ-03 and Post-Close Delivery | Signed annotated tag, source CI/release readback, and exact marketplace provenance. | out_of_scope |

### Explicit Non-Goals

- Change workflow instructions, lifecycle behavior, model profiles, schemas, or
  target migration semantics.
- Add marketplace-level image fields that current schemas do not support.
- Preserve the rejected generated raster previews as shipped assets.

### Constraints

- SVG is the canonical art source; committed PNGs must be reproducible renders.
- Every shipped PNG is fully opaque and visually legible at compact icon size.
- Generated package bytes come only from `scripts/build_marketplace_package.py`.
- Do not edit installed plugin or marketplace caches directly.

### Inputs And Sources

- User-approved third-round Engineering Workflow concept: three colored
  workflow stages around a solid verified-result badge.
- Codex plugin interface fields: `brandColor`, `composerIcon`, `logo`, and
  `logoDark` from the installed plugin-creator schema.
- Claude Code plugin manifest reference:
  `https://code.claude.com/docs/en/plugins-reference`.

### User Decisions And Answers

- 2026-09-12: Approve the last three no-hole concepts.
- 2026-09-12: Raise versions so immutable source tags and marketplace
  provenance can deliver the images immediately.

### Completed Baseline State

- [x] WQ-00 — Clean synchronized `main` at
  `6788076c2087c104101875ef494f6d8cb002c2f0`, released as 0.9.3.
- [x] WQ-00 — The approved vector was reconstructed and previewed outside the
  repository at 1024 px and 128 px; both renders are fully opaque.

### Current Work Queue

- [x] WQ-01 — Add and validate canonical/rendered brand assets for REQ-001. `done`
- [x] WQ-02 — Wire Codex metadata, update 0.9.4 owners, rebuild the package, and validate REQ-002 and REQ-003. `done`
- [x] WQ-03 — Complete final visual/semantic review and prepare exact Post-Close Delivery for REQ-004. `done`

### Locked Decisions

- Use navy `#101828`, cobalt `#3972F6`, cyan `#22C7D9`, teal `#2DD4BF`, and
  warm white `#F6F7F9`; no alpha channel is required for UI safety.
- Keep one theme-independent opaque logo for both `logo` and `logoDark`; the
  dark tile already has sufficient contrast on light and dark surfaces.
- Release as 0.9.4 because the existing 0.9.3 annotated tag is immutable and
  the unified marketplace accepts only strictly newer stable SemVer packages.

### Verification

- REQ-001 / WQ-01: parse SVG; render with `rsvg-convert`; verify 1024x1024 and
  128x128 dimensions and full opacity with ImageMagick; inspect both sizes.
- REQ-002 / WQ-02: focused package tests, plugin-creator validator, and native
  Claude strict validation.
- REQ-003 / WQ-02: builder parity, active-version search, affected tests, then
  `python3 scripts/dev_check.py full`.
- REQ-004 / WQ-03: complete diff review and `python3 scripts/dev_check.py
  security` immediately before push; exact remote/tag/CI/release readback.

### Latest Validation Results

- 2026-09-12: Canonical and packaged SVGs parsed; committed PNG candidates are
  1024x1024/128x128, RGB, fully opaque, byte-identical across normal/dark logos,
  and visually legible at full and compact sizes.
- 2026-09-12: Focused marketplace-package tests passed, deterministic builder
  reported 0.9.4 with zero drift, and source/generated icon paths resolved.
- 2026-09-12: Final `scripts/dev_check.py full` passed 9/9 with pinned Ruff
  0.16.4; skill quick validation, Codex plugin validation, Claude plugin strict
  validation, and Claude marketplace strict validation also passed.
- 2026-09-12: Aggregate diff review found only approved assets, Codex UI
  metadata, synchronized version owners, generated package bytes, focused tests,
  README branding/release notes, and lifecycle state; runtime instructions and
  contract/schema versions are unchanged.

### Risks And Recovery

- Risk: the approved large icon becomes ambiguous at composer size. Recovery:
  inspect the deterministic 128 px render and simplify only the SVG geometry.
- Risk: asset paths work in source but are absent from the generated plugin.
  Recovery: make the canonical skill tree own the assets and require builder
  plus manifest path-existence tests before delivery.
- Risk: a UI-only release accidentally changes runtime instructions. Recovery:
  reject any aggregate diff outside assets, manifests, version owners, tests,
  release notes, generated package, and lifecycle state.

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

- [x] Changed results and affected plan entries agree.
- [x] Plan, validation, working tree, generated package, and indexes agree.
- [x] Completed sections contain no stale unfinished-work wording.

### Closure Gate

- [x] Every in-scope requirement and queue item is terminal.
- [x] Applicable validation is current for final content.
- [x] Review feedback, omissions, backlog, and indexes are reconciled.
- [x] Resume Point contains no future in-scope work.
- [x] Archive closure can be applied atomically.

### Post-Close Delivery

- Authorized commit, push, exact-head PR/merge if required, signed annotated
  `v0.9.4`, GitHub release, CI readback, unified-marketplace import, and local
  Codex/Claude refresh are outside the closed implementation scope and proceed
  only after all gates pass.

### Handoff Notes

- None.

## Recently Completed

- [x] 2026-09-12: Completed Engineering Workflow 0.9.3 Preserve Customized Plan Sections On Closure; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-3-preserve-customized-plan-sections-on-closure.md).
- [x] 2026-09-12: Completed Engineering Workflow 0.9.2 Current-State Efficiency And Agent-Neutral Continuation; [full archived plan](docs/archive/plans/2026-09-12-engineering-workflow-0-9-2-current-state-efficiency-and-agent-neutral-continuati.md).
- [x] 2026-09-05: Completed Engineering Workflow 0.9.1 Astra And Claude Compatibility; [full archived plan](docs/archive/plans/2026-09-05-engineering-workflow-0-9-1-astra-and-claude-compatibility.md).
- [x] 2026-08-29: Completed Engineering Workflow 0.9.0 Ownership-Aware Closure And Review Discipline; [full archived plan](docs/archive/plans/2026-08-29-engineering-workflow-0-9-0-ownership-aware-closure-and-review-discipline.md).
- [x] 2026-08-29: Completed Add Dynamic Release Version Badge.
- [x] 2026-08-28: Completed Engineering Workflow 0.8.2 Empty Compatibility Archive Index Fix; [full archived plan](docs/archive/plans/2026-08-28-engineering-workflow-0-8-2-empty-compatibility-archive-index-fix.md).
- [x] 2026-08-21: Completed Engineering Workflow 0.8.1 Privacy Review Token; [full archived plan](docs/archive/plans/2026-08-21-engineering-workflow-0-8-1-privacy-review-token.md).
- [x] 2026-08-20: Completed Engineering Workflow 0.8.0 Execution Discipline And Dual Marketplace; [full archived plan](docs/archive/plans/2026-08-20-engineering-workflow-0-8-0-execution-discipline-and-dual-marketplace.md).
- [x] 2026-08-16: Completed PTC Partial-Evidence Closure Correction 0.7.0.
- [x] 2026-08-16: Completed Programmatic Tool Calling Runtime Contract 0.7.0; [full archived plan](docs/archive/plans/2026-08-16-programmatic-tool-calling-runtime-contract-0-7-0.md).
