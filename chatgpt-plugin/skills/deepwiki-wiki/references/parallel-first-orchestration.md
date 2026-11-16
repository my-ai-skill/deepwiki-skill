# Parallel-first orchestration runbook

## Goal

Make `doc-write` parallel by default on hosts with a genuine native subagent facility, without changing the original six-phase workflow or inventing concurrency on unsupported hosts.

## Before execution

- Identify the host surface (ChatGPT Work, Codex app/CLI/IDE, ordinary ChatGPT chat, or another agent runtime).
- Inspect whether it exposes real subagent spawn/delegate and wait/collect operations.
- Do not treat simultaneous GitHub connector calls as Subagent execution.
- Confirm the repository, exact source ref, write authorization, and requested output scope.

## Scheduling algorithm

1. Run `repo-scan` and then `toc-design` in order.
2. Parse all pages from the validated TOC.
3. For each page, create a self-contained `workflow-runner` task with `phase_id=doc-write`, the exact `doc-write.md` phase spec, exact `page_id`, source mappings, output directory, language, and required citation policy.
4. Submit all page tasks to the host's native subagent mechanism in one parallel dispatch wave (or in batches bounded by host concurrency).
5. Workers return artifacts; they do not commit, push, or concurrently write shared output files.
6. Wait for all workers. Retry failures only. Merge artifacts in the orchestrator.
7. Run `validate-docs` only after every page task has completed; then run `doc-summary`.

## Host-specific invocation

- **ChatGPT Work**: explicitly ask the host to delegate one independent worker per Wiki page, run them concurrently, wait for all, and show subagent activity. The host's available worker tools are authoritative.
- **Codex app / CLI / IDE**: explicitly request one subagent per page. In CLI, inspect live threads with `/subagents`. Skill instructions may trigger delegation where the active client supports it.
- **Ordinary ChatGPT chat without subagent tools**: do not claim parallel execution. Use the sequential fallback or move the same skill and repository workspace to ChatGPT Work/Codex.
- **Custom agent backend**: parallel execution requires an actual orchestrator (for example, a supported Agents/Responses API multi-agent runtime) and tool wiring. A skill markdown file alone cannot create that backend.

## Proof required

Record host-visible worker IDs, submitted page IDs, observed start/completion states, peak concurrent running count, failures/retries, and Phase 4 start time/order where the host exposes those facts. If the host does not expose a particular field, mark it unavailable rather than fabricate it.

## Safety

Page workers may read source and return page drafts. The orchestrator alone owns final file writes and Git operations. Respect the user's explicit path boundary; for a `docs/wiki/`-only test, no output may be written outside that directory.
