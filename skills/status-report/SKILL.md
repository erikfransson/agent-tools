---
name: status-report
description: Use when the user asks for a status report, a progress overview, or where the session's objectives stand.
---

Present the session's objectives and their current statuses in two compact lists.
Use existing objective IDs and wording, including completed objectives, so the user can follow the same questions over time.
If objectives have not been established, formulate them from the task and available context; ask the user wherever the intended outcomes are unclear.

An objective is a meaningful question or outcome, not an implementation step.
Group related questions under letters and number them within each theme, such as A1, A2, and B1.
Add B2 for a new related question or C1 for a new theme when the session's scope grows.
Prefer a handful of substantial objectives; a longer list should reflect genuinely distinct outcomes, not every action needed to reach them.
Keep IDs stable and change wording only when the intended scope changes, noting that change.

Use this shape, with one status for every objective:

```text
Objectives:
- A1: Can the conversion model explain the observed pressure dependence?
- B1: Does the reference run reproduce the baseline transport rate?

Status:
- A1: In progress. The trend holds at two temperatures; the third remains unchecked.
- B1: Blocked. The reference run failed before producing usable data.
```

Lead each status with its state, then the finding, remaining uncertainty, or blocker.
Prefer one sentence, with extra detail only for a material finding or blocker.
Mention scripts, files, and job IDs only when needed to understand or act on the status.
Distinguish last-known job state from a fresh observation; this report does not itself authorize remote inspection.
Finish with the next useful action if it is not already clear.
Reporting status does not require writing files or starting work.
