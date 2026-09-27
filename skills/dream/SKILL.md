---
name: dream
description: Consolidate session history from all agent config dirs into ~/.claude/DREAMED.md.
disable-model-invocation: true
---

# Dream

Harvest every past session across every `~/.claude*` and `~/.codex*` config directory.
Rewrite `~/.claude/DREAMED.md` as a compact set of **transferable** facts: things that hold in a project the user has not started yet.
Keep `~/.claude/DREAMED.sources.md` beside it, the [ledger](#ledger) of incidents behind each line.

Entries read like auto-memory hooks: one line each, imperative, the fact plus a short reason.

`DREAMED.md` is imported by `~/.claude/CLAUDE.md` through a line `@~/.claude/DREAMED.md`, so it loads in every session in every project. That import is the reason to be ruthless: every line costs context on every turn, everywhere.
The ledger is never imported, so it can hold the detail `DREAMED.md` leaves out.

## Steps

### 1. Build the corpus

Translate the invocation argument into the window.
The user writes it either way: `/dream 30d`, or `/dream do the last 500 sessions`, which becomes `500s`.

Run `harvest.py` from this skill's own directory, and write the corpus into the session scratchpad directory rather than `/tmp`, so two runs cannot collide.
Replace both placeholders with real paths before running.

```bash
DREAM_CORPUS=<scratchpad>/dream-corpus.md python3 <this skill dir>/harvest.py 30d
```

The skill dir is `~/.claude/skills/dream` under Claude Code and `~/.codex/skills/dream` under Codex.

| Argument | Window |
| --- | --- |
| none | last 10 days |
| `30` or `30d` | last 30 days |
| `20s` | 20 newest sessions per source dir |

A window larger than the history simply takes everything.

Prints the prompt count and file size.
The corpus carries two sections: `RECENT` (last 7 days) and `OLDER`.
Each entry is stamped with local date and time, source dir, working directory, and the model and effort of the reply the prompt reacts to, when the session had one.

Done when the script reports a corpus containing entries from every source directory it found.

### 2. Read the corpus

Read `RECENT` in full, in slices. Then read `OLDER`, which exists to confirm that a candidate recurs rather than to introduce new ones.

Track candidates as you read. A candidate is an instruction, correction, or preference the user stated in their own words.

Track **failure modes** alongside them.
A failure mode is the cause standing behind a correction the user had to give more than once, in different projects and different words: the agent reran a finished calculation, reported done without looking at the output, loaded a whole trajectory into memory.
The correction is the symptom, the failure mode is what a line in `DREAMED.md` has to prevent.

Done when every entry in `RECENT` has been read, and every correction the user gave three or more times is attached to a named failure mode.

### 3. Select what is transferable

Apply the rules in [Selection](#selection) to every candidate and to every failure mode.
One passing line is worth more than the five corrections it generalises, so write the failure mode's line first and record the symptoms it covers as its incidents in the ledger.
A candidate that fails only on recurrence goes into the ledger under `## Unplaced`, where later runs can count it.

Done when each candidate and failure mode is either carried forward or rejected, with none left unjudged.

### 4. Merge with the current DREAMED.md

Read `~/.claude/DREAMED.md` and the ledger, treating a missing file as empty. A run consolidates them, it does not replace them.

- Keep every existing line unless the corpus contradicts it.
- File each new incident under the line it restates, and reword that line only if it does not already cover the incident. One fact gets one line.
- **Distill** when two or more lines or incidents share one cause: write one line naming that cause in concrete terms, and move all their incidents under it. An incident that fits an existing line with slight rephrasing joins it the same way.
- Replace a contradicted line with the most recent statement.
- Drop a line only when the corpus shows the practice has changed, not merely because it went unmentioned. Its incidents move to `## Unplaced`.

**Backtest** every new or reworded line against each incident filed under it:

1. It would have prevented that incident as clearly as the line it replaces.
2. It forbids or demands nothing the user never asked for, so the general form stays no more restrictive than its incidents.

An incident that fails the first check keeps its own line. A line that fails the second narrows until it passes.
A line with no incidents yet, written before the ledger existed, is kept as is and collects incidents as the corpus supplies them.

Done when every existing line has been kept, folded, replaced, or dropped for a stated reason, and every new or reworded line passes its backtest.

### 5. Write the diff

Write the new versions into the session scratchpad as `DREAMED.new.md` and `DREAMED.sources.new.md`, then:

```bash
diff -u ~/.claude/DREAMED.md <scratchpad>/DREAMED.new.md
diff -u ~/.claude/DREAMED.sources.md <scratchpad>/DREAMED.sources.new.md
```

Show the user both diffs.
Report the line count of the new `DREAMED.md` against the 100-line cap.

### 6. Install

The invocation itself is the user's confirmation to overwrite `~/.claude/DREAMED.md`, so install right after showing the diff.

```bash
cp <scratchpad>/DREAMED.new.md ~/.claude/DREAMED.md
cp <scratchpad>/DREAMED.sources.new.md ~/.claude/DREAMED.sources.md
```

Report what was added, distilled, and dropped, and the new line count.
Name the lines backed by the most incidents as candidates for the user to move into `~/.claude/CLAUDE.md` by hand.

## Selection

A fact enters `DREAMED.md` only when all five hold:

1. **Transferable.** It would still be true in a project that does not exist yet. `figsize=(3.4, H)` for single-column figures is transferable; the lattice parameter of CsGeBr3 is not.
2. **Recurring.** The user stated or restated it in at least three separate sessions, counting incidents already in the ledger, or stated it once as a standing rule ("always", "never", "from now on").
3. **Not already written.** `~/.claude/CLAUDE.md` is the single source of truth for anything it already says. Read it first and skip every overlap.
4. **Not derivable.** The agent cannot recover it by reading the repo, the git history, or `--help`.
5. **Procedure, not parameter.** A procedure survives a change of machine, cluster or project; a parameter is one setting on one system.
   "Set walltime from a rate measured on that machine" is a procedure.
   `-c 72` is a parameter, and the submit script already records it.
   A number earns its line only when it encodes a convention the user chose and no file states, like `figsize=(3.4, H)`.

Prefer the specific form over the general one: "end plot scripts with `plt.show()` after saving" beats "follow good plotting practice".
A line that a capable agent would already do by default is a no-op and costs load for nothing.

Resolve contradictions in favour of the most recent statement, and convert relative dates to absolute.

## Shape of DREAMED.md

At most 100 lines, blank lines and headings included, and each line as terse as its meaning allows.
When a new fact earns a line and the file is at 100, an old one is distilled or dropped to pay for it.

One `##` section per domain (Figures, Scripts, Writing, HPC, Tooling), each a bullet list. One bullet per fact, one line per bullet, written as an instruction:

```markdown
## Figures
- Single column `figsize=(3.4, H)`, double column `(6.6, H)`: only H varies, so the figure drops into a paper at 100 % scale.
- Plot scripts I run myself end with `plt.show()` after the save, since saving after `show()` can write a blank figure.
```

Usually carry a short reason in the same line, after a colon or as a closing clause. The reason lets the agent judge when the line applies beyond the incidents that produced it.
No frontmatter, no index, no pointers to other files: `DREAMED.md` is read in full every session, so it holds the facts themselves.

## Ledger

`~/.claude/DREAMED.sources.md` keeps the evidence that session history loses as old transcripts are cleaned up, so a later run can backtest a reworded line against the incidents that produced it.
One `##` heading per `DREAMED.md` line, its text copied verbatim, then one bullet per incident: date and time, working directory, model and effort, what the agent did, what went wrong, and the user's words.
The ledger costs no context outside a dream run, so give each incident the detail a later backtest needs rather than the terseness `DREAMED.md` demands.

```markdown
## Plot scripts I run myself end with `plt.show()` after the save, since saving after `show()` can write a blank figure.
- 2026-08-14 15:32 · ~/progs/phonons · claude-opus-5-5-medium · called `savefig` after `plt.show()` in the dispersion script · saved PNG was blank · "save it before you show it"

## Unplaced
- 2026-09-02 09:10 · ~/progs/md-runs · gpt-6-astra-low · resubmitted the 300 K equilibration without checking its log · the run had already finished · "that one was already done"
```

Keep headings in step with `DREAMED.md`: a reworded line renames its heading, a distilled line gathers the incidents of every line it replaces.

## Boundaries

The per-project auto-memory stores under `~/.claude/projects/*/memory/` belong to the user, and a dream run leaves every one of them exactly as found.
Read them for context; write only `~/.claude/DREAMED.md` and `~/.claude/DREAMED.sources.md`.

Run only on an explicit invocation: `/dream` as a slash command, or `$dream` or `$ dream` in the user's message, each optionally followed by a window.
Natural-language requests without one of those, and mentions in questions, quotes, or requests to edit the skill, do not authorize a run.
