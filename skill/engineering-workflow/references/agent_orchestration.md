# Agent Orchestration

Use this canonical reference when deciding whether work belongs to a deterministic tool, the root agent, or a subagent. Keep concrete model names in `model_profiles.md`, not here.

## Contents

1. Default Route
2. Deterministic Route
3. Utility Route
4. Explorer Route
5. Standard Worker Route
6. Review Route
7. Exceptional Quality Route
8. Fan-Out And Nesting
9. Shared State
10. Subagent Contract
11. Monitoring And Long-Running Work
12. Configuration Boundaries

## Default Route

Use one root agent by default. Add a subagent only when the delegated work is independent, bounded, has a clear output contract, avoids frequent writes to shared mutable state, and has a measurable latency, context-isolation, or coverage benefit.

Tool availability is not a reason to delegate. Keep ordered dependency chains, small tasks, shared-resource work, and tasks dominated by one slow external operation with the root agent.

The root agent owns user communication, scope decisions, approval boundaries, final synthesis, validation reconciliation, and task closure.

## Deterministic Route

Use a tool, script, scheduler, hook, or harness layer instead of an LLM subagent for:

- sleep or waiting
- polling and exit-code checks
- timestamps and file/process existence
- unambiguous JSON status reads
- sorting, filtering, joining, ranking, aggregation, or deduplication
- repeating one command
- bounded retries and backoff
- deterministic stop conditions

Do not use a language-model subagent for these deterministic tasks.

Do not spend model turns waiting. A periodic workflow should run a bounded deterministic check, return a minimal structured snapshot, and invoke a model only when state changed, an anomaly appeared, or semantic judgment is required.

Keep approvals, semantic decisions, native-artifact validation, and final evidence review as direct root-agent actions.

## Utility Route

Use a utility agent only for small bounded language or semantic work that is not fully deterministic, such as:

- interpreting one concise status
- read-only inspection of one condition
- normalizing a small result
- producing a simple non-destructive command
- comparing two structured snapshots
- classifying a known state
- returning a brief evidence summary

Require bounded input, a fixed output schema, no scope expansion, no child agents, no shared-state writes, at most one transient retry, a stop condition, and a `needs_escalation` outcome. Resolve its current model and reasoning settings through `model_profiles.md`.

## Explorer Route

Use an explorer for independent read-heavy work such as codebase mapping, documentation review, large-file inspection, evidence collection, or test/log summarization.

Give it a bounded path scope and require file references plus distilled findings. Keep it read-only. Do not let it edit workflow state or paste unbounded raw output into the root context.

## Standard Worker Route

Use a standard worker for bounded multi-step analysis or implementation when ownership can be isolated to specific files or a subsystem.

Give it the smallest necessary permissions, explicit owned paths, local validation, and a required diff/validation summary. Run standard workers in parallel only when their write sets and mutable resources do not overlap.

## Review Route

Use a reviewer or high-risk specialist for correctness, security, concurrency, races, data loss, complex migration, ambiguous architecture, and edge-case review.

Keep review evidence-first and normally read-only. Require findings with severity, confidence, exact evidence, and a clear no-findings result when appropriate. The reviewer hands findings to the root agent and does not silently mutate shared state.

## Exceptional Quality Route

Use the highest reasoning levels or API pro mode only when the task is objectively difficult, error cost is high, quality materially outweighs latency/cost, acceptance criteria are measurable, and evaluation shows a gain over cheaper profiles.

Do not assume the highest reasoning level is automatically best. Do not invent a separate pro model name, and do not place Responses API-only reasoning fields in Codex TOML.

## Fan-Out And Nesting

- Keep ordinary fan-out to two or three genuinely independent agents.
- Do not consume every available thread merely because capacity exists.
- Keep `agents.max_depth = 1` by default.
- Do not enable recursive delegation without an explicit, measured requirement.
- Keep a single-writer rule for every shared mutable resource.
- Stop fan-out when coordination cost exceeds latency or coverage benefit.
- Subagents never close the user task.

## Shared State

Only the root agent writes:

- `PLANS.md`
- requirement traceability and work-queue status
- backlog promotion or closure state
- the workflow state manifest
- final validation reconciliation
- final user-facing synthesis

A subagent may return a proposed patch or evidence, but the root agent reconciles it against current shared state before applying or accepting it.

## Subagent Contract

Every delegation states:

- bounded objective and scope
- inputs and allowed paths
- read/write permissions
- capability/model profile name
- required output schema and evidence
- stopping condition
- escalation condition
- retry budget
- whether the root waits for all results

Do not leak the expected answer or a hidden diagnosis into an independent evaluation prompt. Give raw artifacts and the minimum task-local context needed for transferable validation.

## Monitoring And Long-Running Work

Do not implement monitoring as a model sleep loop. Let a scheduler or harness own timing, retries, and backoff. Invoke a utility or standard agent only for changed state or anomalies.

One long-running external operation does not justify multi-agent fan-out. Keep deterministic waiting with the execution layer and preserve one clear continuation point for the root agent.

## Configuration Boundaries

Custom-agent files may set supported Codex keys such as `model`, `model_reasoning_effort`, and `sandbox_mode`. Preserve parent approvals and runtime restrictions; a child cannot broaden authority.

When structurally merging `.codex/config.toml`:

- preserve unknown keys and custom profiles
- preserve an existing `max_threads` unless a measured need justifies a user-approved change
- add depth `1` only when absent or already consistent
- show the exact config diff
- install optional agent templates only after an explicit request or `--include-agent-config`

Use Responses Multi-agent and Programmatic Tool Calling documentation only for general orchestration principles. Do not copy their API request fields into Codex configuration.

Official guidance:

- `https://learn.chatgpt.com/docs/agent-configuration/subagents`
- `https://developers.openai.com/api/docs/guides/responses-multi-agent`
- `https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling`
