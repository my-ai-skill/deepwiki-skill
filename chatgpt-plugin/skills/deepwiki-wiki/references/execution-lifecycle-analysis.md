# Execution lifecycle analysis

## Purpose

A repository Wiki must explain not only what components exist, but how a meaningful execution path progresses from its entry point to completion. Use this reference when the requested topic includes a test runner, command-line tool, service startup, request handling, worker, scheduler, build pipeline, device driver lifecycle, or another end-to-end flow.

Use the user's lifecycle illustration as a presentation pattern, not as a source of facts. Do not copy framework-specific stages such as pytest plugins or test collection into a different codebase unless the target source actually implements them.

## Phase 2 — identify lifecycle boundaries before approving the TOC

For each major executable path, look for:

- **Pre-entry registration**: static constructors, linker registration sections, generated registries, plugin discovery, constructor tables, test macros, or configuration-time registration that happens before the visible entry function.
- **Entry point**: `main`, `wmain`, `_tmain`, service callback, driver probe, interrupt entry, RPC handler, or the real host callback.
- **Bootstrapping**: dependency loading, built-in module registration, runtime creation, environment setup, or resource acquisition.
- **Initialization**: argument/configuration parsing, object construction, state initialization, device discovery, session creation, and event-listener installation.
- **Discovery / collection / registration**: determine whether the program dynamically discovers work at runtime or consumes items registered earlier. Do not label static registration as runtime collection.
- **Execution / dispatch**: scheduler loop, test loop, request dispatch, state machine, work queue, or device operation.
- **Observation / reporting**: event callbacks, logs, counters, result aggregation, completion notifications, and output writers.
- **Finishing / teardown**: global cleanup, per-item cleanup, resource destruction, callback unregistration, thread shutdown, and final status/exit code.
- **Alternate paths**: error returns, early exit, no-work cases, skipped/filtered work, retries, cancellation, fail-fast, timeout, exception handling, and platform/configuration variants.

Record source-derived directed relationships and assign them to a page/section. If a full lifecycle is too large for one page, split it by an explicit boundary (for example process startup, request lifecycle, and shutdown) and add cross-page links.

## Phase 3 — write an end-to-end execution explanation

For every significant lifecycle page or section, include these complementary views when the code supports them:

1. **Lifecycle stage rail**: a compact ordered list such as Bootstrap → Initialize → Discover → Execute → Report → Finish. Use the target project's actual stages and names.
2. **Call hierarchy**: the concrete function/object path from the entry point through the key dispatch or loop to the leaf operation.
3. **Sequence or event view**: include callbacks, listener notifications, state transitions, and cleanup ordering when those are essential to understand the runtime.
4. **Failure/alternate-path view**: show what changes when initialization fails, no work is selected, a test/request is skipped, fail-fast triggers, a callback fails, or cleanup is conditional.

A lifecycle diagram should make the distinction between these relationship types clear:

- call/invocation;
- event/listener notification;
- state transition;
- data/result propagation;
- ownership/lifecycle (create, destroy, acquire, release);
- conditional/alternate branch.

Do not use one generic arrow for all of them. Label edge semantics and identify conditions on branches. If the lifecycle contains a loop, show its loop boundary and termination condition. If the source has multiple entry variants, show them as separate branches rather than pretending there is one universal entry.

Explain ordering rules explicitly. For example, distinguish global setup from per-suite setup and per-test setup; state whether cleanup runs after failure; state whether listener callbacks run in forward or reverse order only when the source establishes that detail.

## Source evidence contract

Every critical lifecycle claim and relationship must record:

- exact repository-relative source path;
- real inclusive `start_line` and `end_line` from the frozen source commit;
- a short literal `contains` excerpt that actually occurs inside that range;
- importance (`critical` or `supporting`);
- exact Markdown representation anchor, or a diagram ID plus exact Mermaid fragment.

Use this shape in the claim/relationship ledger:

```json
{
  "id": "rel-run-entry-to-dispatch",
  "kind": "call",
  "source": "Program::Run",
  "target": "Runner::RunAll",
  "condition": "normal execution",
  "importance": "critical",
  "status": "covered",
  "evidence": [
    {
      "path": "src/runner.cc",
      "start_line": 120,
      "end_line": 128,
      "contains": "return runner->RunAll();"
    }
  ],
  "representation": {
    "kind": "diagram",
    "location": "Main execution lifecycle diagram",
    "diagram_id": "execution-lifecycle",
    "diagram_fragment": "ENTRY -->|calls| RUNNER"
  }
}
```

For prose/table items, use `representation.anchor` with a short exact phrase present in the Markdown page. For diagram items, use `representation.diagram_id` and `representation.diagram_fragment`; the fragment must occur in the Mermaid source associated with that diagram ID.

## Phase 4 — verify lifecycle completeness

Re-open the actual source in a separate review pass and reconstruct the path without relying on the drafted diagram. Confirm:

- the real entry and any pre-entry registration mechanism are identified;
- initialization and parsing happen in the correct order;
- the loop/dispatcher and its termination condition are shown;
- lifecycle scopes (process, session, suite, request, test, thread, device, buffer, etc.) are not conflated;
- callbacks/events and result reporting are shown where relevant;
- cleanup and ownership transitions are accurate, including failure paths;
- every critical edge in the declared diagram scope appears in the actual Mermaid block;
- every source evidence range exists at the pinned commit and the stated excerpt is present;
- prose, table, call tree, sequence diagram, and lifecycle rail do not contradict each other.

Do not claim full lifecycle coverage just because a page has a Mermaid diagram. A diagram that only shows `main -> run` is an entry-point sketch, not a complete lifecycle analysis.

## Reporting

Report lifecycle coverage independently from structural validity and Mermaid rendering. State explicitly which lifecycle stages were source-reviewed, which branches remain unknown, and whether real Mermaid.js/CLI rendering ran. If the source does not expose a stage or the host prevents inspection, mark it unknown/not inspected rather than filling it with framework conventions.
