# Workflow-runner compatibility contract

This document makes the original `workflow-runner.agent.md` behavior explicit for runtimes that need an adapter. It is not a replacement for the upstream agent specification.

## Original invariant

One invocation = exactly one phase. Load its phase specification first, then only references explicitly listed by that spec. Produce only declared outputs, run declared validations, and stop at the first failed required action with an actionable failure report.

## Phase identifiers

- `repo-scan`
- `toc-design`
- `doc-write`
- `validate-docs`
- `doc-summary`
- `incremental-sync`

## Execution matrix

| Host capability | Required behavior |
|---|---|
| Native subagents + concurrency | Main orchestrator dispatches a workflow-runner per independent task; `doc-write` uses one page-scoped worker per page. |
| Native subagents, no concurrency | Dispatch workers according to host limits; preserve page boundary and one-phase contract. |
| No subagents | Current agent becomes the runner and executes phase specs sequentially, preserving the same inputs, references, outputs, and validation. |
| Browser-only model | Produce artifacts and explicit next-step instructions; never claim local scripts or browser JS ran unless actually executed. |

## Page-scoped `doc-write`

The orchestrator passes `phase_id=doc-write`, the exact `phase_spec`, TOC path/content, repo context, output directory, locale, and one `page_id`. A worker returns exactly one page plus source inventory and validation notes. It must not write to other pages. Workers run in foreground and all must complete before Phase 4. Retry failed page workers only; do not repeat successful pages. Merge and validate cross-page links centrally.

## Shared-state safety

Workers return page artifacts to the orchestrator instead of concurrently writing the same shared files. The orchestrator owns merging, cross-page validation, final writes, and commit operations. A worker cannot commit or push unless the user explicitly authorized that scope and its task contract includes it.

## Required truthful reporting

Report `parallel` only if multiple workers were actually scheduled concurrently by the host. Otherwise report `sequential fallback`. Report the actual number of workers and completed/failed pages when those facts are available.
