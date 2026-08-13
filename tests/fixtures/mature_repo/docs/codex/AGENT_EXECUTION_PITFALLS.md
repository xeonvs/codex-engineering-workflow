# Agent Execution Incidents

incident_schema_version: 1

## Entries

### INC-101 — Provider result published before readback

- Symptom: Provider success was reported before the persisted record was read back.
- Cause: `unguarded_rule`
- Invariant: `provider.persist-readback`
- Owner: `docs/providers.md#provider-completion-boundary`
- Route: `provider-change`
- Guard: `test:provider-contract`
- Evidence: sanitized provider regression fixture.
- Status: `guarded`
- Retirement: Retire after the behavior gate remains stable across supported providers.

### INC-102 — Build-only UI acceptance

- Symptom: A frontend change was closed after compilation without rendered evidence.
- Cause: `unreachable_rule`
- Invariant: `ui.rendered-acceptance`
- Owner: `docs/ui.md#rendered-acceptance`
- Route: `ui-change`
- Guard: `harness:rendered-ui`
- Evidence: sanitized UI regression fixture.
- Status: `guarded`
- Retirement: Retire after every frontend route requires rendered evidence.

### INC-103 — Release work bypassed updater ownership

- Symptom: Release state was changed outside the repository updater boundary.
- Cause: `unguarded_rule`
- Invariant: `release.updater-owned`
- Owner: `docs/operations.md#release-ownership`
- Route: `release-change`
- Guard: `release_gate:release-check`
- Evidence: sanitized operations regression fixture.
- Status: `guarded`
- Retirement: Retire after release entrypoints all use the same gate.

### INC-104 — Narrow browser repair expanded across helpers

- Symptom: A bounded browser repair changed unrelated helpers and constants.
- Cause: `unreachable_rule`
- Invariant: `browser.change-radius`
- Owner: `docs/browser.md#bounded-browser-change-radius`
- Route: `browser-change`
- Guard: `lint:source-shape`
- Evidence: sanitized browser/refactor regression fixture.
- Status: `guarded`
- Retirement: Retire after the browser route and source-shape gate remain stable.
