# code-review-scientific: the same commit, with and without the skill

One commit from the `ovito-reader` branch of [dynasor](https://gitlab.com/materials-modeling/dynasor), `5d4b66d` ("initial test of ovito reader"), reviewed against its merge base `3260689` by two independent Sonnet agents.
It adds a 120-line `OvitoTrajectoryReader` plus 212 lines of tests, and is the kind of nearly-finished commit where a review is worth something: the cell-transpose bug it contains survived in the branch for four months.

Without the skill:

```
Review the commit 5d4b66d in dynasor vs master commit 3260689
```

[`review-plain.md`](review-plain.md), 5 findings in a flat list.

With the skill:

```
Review the commit 5d4b66d in dynasor vs master commit 3260689
using the code-review-scientific skill
```

[`review-skill.md`](review-skill.md), 3 Major and 8 Minor findings, split into a comment ready to paste into GitLab and an internal section recording the reviewed SHAs, the commands run, the subagent reports and the severity calls.

Both found the transposed cell matrix, the bug that matters, and both reproduced it rather than asserting it.
The skill run added a duplicate-identifier case that silently swaps atoms between frames, an unhandled error path, and a mutation test showing that deleting the reader's whole reorder mechanism still passes all 27 new tests, so the part of the code the reader exists for is unprotected.
It cost roughly 130k tokens and 11 minutes against 100k and 5, and it ran three reviewers in parallel before the lead checked their leads itself.

Neither review found the fix the branch eventually took, which was to pass `sort_particles=True` to OVITO and delete the reordering code entirely.
