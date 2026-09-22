---
name: handoff
description: Save session objectives, state, and running-job details to handoff.md.
disable-model-invocation: true
---

Write `handoff.md` in the current working directory.
If work spans directories and the intended handoff location is unclear, ask which directory should own it.
Read an existing handoff there before replacing it with one current account, rather than an appended log.
For an older `HANDOFF.md`, read it as migration context if lowercase `handoff.md` is absent; write the lowercase file and mention the legacy file without deleting it.

Keep these sections compact:

1. **Context.** Date, repository and working directory, session purpose, and the user's intended focus for the next session if provided.
2. **Objectives.** Carry over every session objective with its stable ID and wording, including completed objectives.
3. **Status.** One entry per objective, giving its state, verified findings, remaining uncertainty, and blockers.
4. **Running work.** Local background processes, HPC jobs, and any monitoring or waiting sessions associated with them.
5. **Next actions.** The next useful moves, their objective IDs, and any prerequisites or permission still needed.
6. **Continuity.** Decisions, constraints, partially completed edits, relevant paths, outdated claims, and suggested skills that the next agent needs.

For objectives and statuses, read [the reporting conventions](../status-report/SKILL.md) as reference without issuing a separate report.
Ask if the intended objectives are unclear instead of inventing scope.

For each running or queued item, record its objective ID, purpose, machine or cluster, working directory, job ID (including array task IDs where relevant) or PID/session ID, and log and output paths.
Include the last observed state and observation time, how to check or collect the result, and an expected completion time only when supported.
Record monitoring separately from the job itself, including whether it can survive the session ending.
Label unknown fields and unverified current states explicitly.
Say when no jobs are known to be running, with the limits of that knowledge.
Use existing observations and authorized lightweight checks; preparing a handoff does not grant remote access or permission to submit, cancel, or clean up jobs.

Link durable findings and project notes by path rather than copying them into the handoff.
Update established project notes only when within the authorized task; avoid creating a documentation suite just for a handoff.
Keep secrets and unrelated personal data out.

Read back the saved file and check that every objective has a status and every known running item has enough context to locate it, with gaps marked.
Report the saved path and any unresolved continuity gaps.
