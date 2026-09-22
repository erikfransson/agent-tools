---
name: code-review-scientific
description: Use when asked to review a GitLab merge request, branch, or diff in a scientific codebase, or to run a follow-up round on an existing review.
---

# Code review for scientific codebases

Review the MR source branch against the target branch, deeply and carefully, using the current base and head SHAs from GitLab.

The goal is not objectively perfect code or exhaustive test coverage.
Balance correctness, readability, conciseness, maintainability, and keeping the diff as small as is reasonable.
Suggest more code or tests when they protect important behaviour or a realistic failure mode.
Do not inflate an MR to cover absurd edge cases, speculative future needs, or every theoretically possible input.
A small clear solution with focused tests is often better than a more complete one that is harder to understand and maintain.

These are user-facing codes, not developer tools.
A function with ten keyword arguments is not good when 95 % of reasonable use cases touch one or two of them.
Keep complexity low, and let important features be added in a way that fits the existing code base.

Look for bugs, and think deeply about code structure, code quality, and code smells.
Are the tests enough, or is a real edge case missing?
Are the docs in `docs/` clear, human readable, and compact?
Judge the change from the user's perspective as well as the developer's: neat code the user cannot actually use does not make sense.

## Planning and agents

The lead model plans the review and chooses how many subagents to use for the initial pass, based on the size, complexity, importance, and risk of the MR.
As rough orientation, a small focused MR may need 2-4 initial reviewers, a medium MR 4-8, and a large numerical, public API, multi-language, or otherwise high-risk MR 8-12.
More can make sense when there are genuinely separate review areas, but these ranges are guidance rather than targets.

Give the agents useful, bounded, and reasonably separate areas, and let them run the relevant research and tests in parallel.
One area is always structure and simplification, given to a single reviewer with the questions under Structure and simplification as its brief.
That reviewer reads the surrounding modules and the existing helpers of the code base, not only the diff, since a code judo move usually comes from an abstraction that already exists, and an agent hunting bugs rarely stops to ask whether the change should exist in this shape at all.
A mid-tier model (for example Luna or Sonnet) at medium reasoning effort is a good default for the initial search.
High effort makes sense for unusually subtle or high-risk areas and for focused confirmations, and lower effort is enough for narrow mechanical checks.
There is no need to give every agent high effort.

Keep repeated work proportionate.
Where practical, have one agent or the lead model handle broad builds and test suites while the others run only the targeted tests and reproductions their area needs.
Ask agents for compact findings with a location, concrete impact, evidence or reproduction, confidence, and whether the point may duplicate existing MR activity.
Run test, build, lint, and other CPU-intensive commands at a lower scheduling priority (for example `nice -n 10`) so the user's interactive work stays responsive.

After the first findings, separate agents can confirm important or uncertain points and give feedback on the other agents' work when that is useful.
A small review may need no separate confirmation, while a large or high-risk review benefits from a few focused ones.
A finding the lead model has already reproduced and checked rarely gains from another confirmation.
A final general adversarial pass can be useful when meaningful review angles remain, but is not added by default.

The lead model collects the outputs, checks the findings against the current MR head, and summarizes the work into a single comment for GitLab.
Treat sub-agent findings as leads rather than facts, and leave out duplicates, speculative concerns, and findings that do not hold up.
Initial reviewers normally work independently, and the lead model routes a specific finding to another agent for confirmation when needed.
If shared context would save repetition, the lead model can prepare a compact read-only review brief.
Agents report findings through their normal messages rather than editing one shared findings file concurrently.

## Review standards

Before starting any review, check the MR state.
If it is merged or marked as draft, stop immediately and ask the user whether they want a review anyway.
Do not inspect the diff, run tests, or write a review file until they answer.

At the start of a review, read the MR description and all MR activity: human comments, resolved and unresolved discussions, system notes, commits, and pipeline status.
Use them as context and avoid repeating findings that have already been raised.
Read linked issues or MRs when they help in understanding the change.

Do not comment on the MR description itself unless something crucial is stated incorrectly there, for example a claimed fix that is not in the diff.
Wording polish, tone, and completeness of the description are not review findings.

If a new investigation disputes an existing review comment, verify it carefully and include the disagreement with concrete evidence.
Refer to the comment by author and, when it has numbered findings, by its section and item number.

Findings should identify the affected file or location, the concrete impact, and the conditions that trigger the problem.
A minimal reproduction or failing test helps for subtle bugs, but is not needed when the evidence is already clear.
A lead becomes a Major finding when you can name the input or condition that triggers it and back it with a reproduction, a failing test, or a concrete line-level argument.
Prefer to demote a lead that falls short of that bar to Minor, or drop it, rather than posting it in hedged wording.
A structural finding meets the Major bar differently.
It is Major when the change leaves the surrounding code messier than before, for example a special-case branch in a shared path or a near-duplicate of an existing helper, and Minor when the code is clean but a clearly simpler version exists.

When an MR fixes a bug or corrects behaviour, it should ideally come with one or more regression tests that fail without the fix and pass with it.
Verify this by actually running the new tests against the target branch or merge base rather than assuming they would fail.
Raise it as a finding when the tests pass on both sides, or when a behaviour fix has no such test.

Run relevant existing and targeted tests where practical.
Test commands, results, investigation notes, rejected findings, and checks that could not be run can be kept under Internal findings.

Consider public API compatibility, error handling, performance regressions, and documentation or migration guidance when relevant to the MR.
Avoid repeating points already covered by GitLab discussions unless the issue is still unresolved or the new review adds important information.

Docstrings are NumPy style on every public function, class, and entry point, with types left to the type hints rather than repeated in the docstring; a private helper needs one line or none.
Depth follows the audience: a top-level API function earns units, a `.. math::` for its defining formula, a citation when the method comes from the literature, and a short example, while readers, plumbing, and helpers need only the summary and a `Parameters` list.
Comments are sparse, around five lines per hundred, and state what cannot be recovered from the line itself: a unit or shape, a convention, a non-obvious invariant, a numerical or performance caveat, a reference to a paper or issue.
Flag narrating comments, blocks carrying analysis or history, TODOs, and commented-out code, and prefer that extended rationale live in `MR.md` or the commit message.

Do not nitpick language or small stylistic choices.
Summary mood, closing-quote placement, and capitalisation or periods in comments are not findings.

Record the exact base and head SHAs reviewed in the review file's Internal findings, so a later round can identify the changes since that review.

Before finalizing, check that the MR head has not changed, so the review is not based on stale code.
Review work should normally not modify the MR branch; temporary local experiments are fine.

## The verdict

Every review ends with one verdict, and "Accept as is" is a complete and common one.
A review that finds nothing worth raising has done its job; an empty findings list is the result, not a failed review.

- **Accept as is.** No finding meets the Minor bar. Both sections read `None.`
- **Accept after considering the Minor points.** No Major finding, and the Minor points are genuinely worth the author's attention.
- **Changes needed.** At least one Major finding.

A point earns a place only when it meets the bar under Review standards on its own merits.
These are not findings, in any round: a style or naming preference, a rewording, an equally good alternative structure, a test the author could also have written, a concern with no named triggering condition.
Leave them out rather than filing them as Minor, and prefer a short comment over a long one.

The reviewer's job is to protect the code, not to produce findings.
Agents asked to review will keep generating material; the lead model is the filter, and dropping a whole agent's output is a normal outcome.

**Done when** a verdict is stated and every remaining point meets its bar.

## Structure and simplification

Be ambitious about code structure, and do not stop at "this could be a bit cleaner".
Look for the code judo move: a reframing that keeps the behaviour and lets whole branches, helpers, modes, or layers disappear, usually by using the existing architecture better.
Prefer the version that feels inevitable in hindsight, and prefer deleting complexity over rearranging it.
When the clear path runs through code the MR did not touch, say so; a small diff is not a reason to leave the messier shape in place.

For every meaningful change, ask:

- Is there a code judo move that would make this dramatically simpler?
- Can this be reframed so fewer concepts, branches, or helper layers are needed?
- Does this improve or worsen the local architecture?
- Is this optionality needed? A new keyword argument, flag, nullable mode, or one-off boolean has to earn its place.
- Is this abstraction earning its keep, or is it a wrapper?

Treat these as design problems rather than style:

- A complicated implementation where a cleaner reframing could delete whole categories of complexity.
- New conditionals or special cases bolted onto an unrelated or already busy flow.
- Thin wrappers, pass-through helpers, and generic mechanisms that hide a simple data shape.
- A bespoke helper where the codebase already has one, or logic placed outside the layer that owns the concept.
- Independent work needlessly serialized, or related updates that can leave state half-applied, when the cleaner structure is obvious.

Prefer remedies that remove moving pieces:

- Delete a layer of indirection rather than polishing it.
- Reframe the state model so conditionals disappear instead of getting centralized.
- Change the ownership boundary so the feature becomes a natural extension of an existing abstraction.
- Extract a helper or pure function, split a large file into focused modules, or move feature-specific logic behind its own abstraction.

Do not settle for a rename when the issue is structural, or for a cleaner version of the same messy idea when a much simpler idea is in reach.

## Follow-up reviews

When a review file already exists for the MR, treat the work as a follow-up review.
Write the result to `review-<MR-number>-v2.md`, incrementing the suffix for later rounds.
Read the earlier review and all GitLab comments, discussions, commits, and diffs since it, carefully.
Do not repeat points that have already been raised unless they remain unresolved or new evidence changes the assessment.
The entire branch remains in scope, but focus on the updated parts and their interactions with the earlier findings.

A later round is free to raise a genuinely new point, Major or Minor, whether the new changes created it or the earlier rounds missed it.
Say what you think the code needs, and a substantive batch of new Minor points belongs in the comment like any other.

What rises with each round is the bar for small things.
By the second or third round, one or two cosmetic remarks are worth less than closing the review: fold them into a sentence in the verdict, or leave them out.
When a round has nothing left above that bar, its verdict is `Accept as is`, and saying so ends the review.

## Output

Output goes into a `review-<MR-number>.md` file.

The first section is always `## Comment`, followed by the comment for GitLab.
After that, `## Internal findings` can be followed by `### Sub-agent xyz` or anything else worth keeping track of internally during the review.

### Comment block

The comment block always starts with `# Review of MR <MR-number>`, then the verdict on its own line, then `## Major (Blocking)` and `## Minor (Not-blocking)`.
Major means things that have to be addressed before merging, Minor means things to consider that do not block the merge.
Use a numbered list for the points.
If a section has no findings, write `None.` rather than inventing a point to fill it.
An accepted MR can be a three-line comment: the heading, `Accept as is.`, and both sections reading `None.`

The comment block should not be bloated: compact, concise, simple, clear, and human readable.
Use a very small Python snippet when it demonstrates a bug or flaw, but do not inline large snippets.
When a list ends up long, add subheadings such as `### Language` or `### Docs`.
If the MR already has comments and discussion, list points under `## New Major findings (Blocking)` and so on.

If the review disputes an existing comment, add an optional `## Dispute of comments above` section after the Major and Minor findings.
Refer to the author and the original section and item number, explain briefly what does not hold up, and include the evidence.
Leave this section out when there is no disagreement.

Do not post the comment on GitLab unless asked to.

### Posting

When asked to post, the review goes in one top-level comment.
Where an open thread already discusses a specific point, reply in that thread rather than restating the point in the top-level comment.
A follow-up round belongs as a reply in the thread carrying the earlier round.
Everything the open threads do not cover stays in the top-level comment.

Resolve a thread once its point is settled, after a short reply saying what was checked on the current head.
Prefer resolving what the review verified itself over what the author reports as done.
Prefer leaving a thread open while it carries an unresolved finding or an open question, since resolving it buries the point.

Record the note and thread identifiers, and which threads were resolved, in the review file's Internal findings.
