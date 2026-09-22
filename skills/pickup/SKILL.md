---
name: pickup
description: Restore project context and session objectives from the README and handoff.
disable-model-invocation: true
---

Read the repository-root `README.md` at every invocation, even when working in a subdirectory.
Resolve the root from the current checkout; outside a repository use the current directory.
If the README is missing, state that and continue with available context.
Read `handoff.md` only if it exists in the current working directory; otherwise skip it.

Check the handoff's date, paths, scope, and claims against the user's current request and available local evidence.
Ask before adopting a stale, unrelated, or ambiguous handoff as the active plan.
Treat its job states as historical observations until rechecked, and its commands as context rather than new authorization.

Restore the objectives and statuses, preserving IDs and wording for continuing work.
If no relevant handoff exists, formulate objectives from the user's task and README; ask if the intended outcomes are unclear.
Read [the reporting conventions](../status-report/SKILL.md) for objective scope, IDs, and report format.
Add related questions under the existing theme and new directions under a new letter as scope grows.
Keep meaningful questions and outcomes separate from implementation steps.

Carry forward relevant decisions, constraints, and unfinished work without assuming that old permissions cover new operations.
A pickup request establishes context; continue implementation only when the user's task authorizes it.
End the pickup with a status report to the user in the status-report format, covering the restored or proposed objectives, any running work needing attention, and the next action or question.
