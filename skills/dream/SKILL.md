---
name: dream
description: Consolidate session history from all agent config dirs into ~/.claude/DREAMED.md.
disable-model-invocation: true
---

# Dream

Harvest every past session across every `~/.claude*` and `~/.codex*` config directory.
Rewrite `~/.claude/DREAMED.md` as a compact set of **transferable** facts: things that hold in a project the user has not started yet.

Entries read like auto-memory hooks: one line each, imperative, the fact plus the reason it matters when the reason is not obvious.

`DREAMED.md` is imported by `~/.claude/CLAUDE.md` through a line `@~/.claude/DREAMED.md`, so it loads in every session in every project. That import is the reason to be ruthless: every line costs context on every turn, everywhere.

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
Each entry is dated and tagged with its source dir and working directory.

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
One passing line is worth more than the five corrections it generalises, so write the failure mode's line first and drop the symptoms it already covers.

Done when each candidate and failure mode is either carried forward or rejected, with none left unjudged.

### 4. Merge with the current DREAMED.md

Read `~/.claude/DREAMED.md`. A run consolidates it, it does not replace it.

- Keep every existing line unless the corpus contradicts it.
- Fold a new candidate that restates an existing line into that line; never add a second line for one fact.
- Replace a contradicted line with the most recent statement.
- Drop a line only when the corpus shows the practice has changed, not merely because it went unmentioned.

Done when every existing line has been kept, folded, replaced, or dropped for a stated reason.

### 5. Write the diff

Write the new version into the session scratchpad as `DREAMED.new.md`, then:

```bash
diff -u ~/.claude/DREAMED.md <scratchpad>/DREAMED.new.md
```

Show the user the diff.
Report the line count of the new file against the 50 to 70 line range.

### 6. Install

```bash
cp <scratchpad>/DREAMED.new.md ~/.claude/DREAMED.md
```

Report what was added, what was dropped, and the new line count.

## Selection

A fact enters `DREAMED.md` only when all five hold:

1. **Transferable.** It would still be true in a project that does not exist yet. `figsize=(3.4, H)` for single-column figures is transferable; the lattice parameter of CsGeBr3 is not.
2. **Recurring.** The user stated or restated it in at least three separate sessions, or stated it once as a standing rule ("always", "never", "from now on").
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

Between 50 and 70 lines, blank lines and headings included.
The upper end is the binding constraint: when a new fact earns a line and the file is at 70, an old one is folded or dropped to pay for it.

One `##` section per domain (Figures, Scripts, Writing, HPC, Tooling), each a bullet list. One bullet per fact, one line per bullet, written as an instruction:

```markdown
## Figures
- Single column `figsize=(3.4, H)`, double column `(6.6, H)`; only H varies, so the figure drops into a paper at 100 % scale.
- Plot scripts I run myself end with `plt.show()` after the save.
```

Carry the reason only when the instruction is not self-evident, in the same line after a semicolon.
No frontmatter, no index, no pointers to other files: `DREAMED.md` is read in full every session, so it holds the facts themselves.

## Boundaries

The per-project auto-memory stores under `~/.claude/projects/*/memory/` belong to the user, and a dream run leaves every one of them exactly as found.
Read them for context; write only `~/.claude/DREAMED.md`.

Run only on an explicit invocation: `/dream` as a slash command, or `$dream` or `$ dream` in the user's message, each optionally followed by a window.
Natural-language requests without one of those, and mentions in questions, quotes, or requests to edit the skill, do not authorize a run.
