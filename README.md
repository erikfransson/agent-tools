# agent-tools

Skills for coding agents, written for research work: simulation and analysis codebases, publication figures, and the scientific software around them.
They run under Claude Code and Codex, which both read a `SKILL.md` from a skills directory.

## Skills

- [`code-review-scientific`](#code-review-scientific): multi-agent review of a GitLab merge request in a scientific codebase.
- [`figure-polish`](#figure-polish): conventions and QA for publication figures made with matplotlib and mplpub.
- [`dream`](#dream): consolidate past session history into a short set of transferable facts loaded in every session.

### `code-review-scientific`

Multi-agent review of a GitLab merge request in a scientific codebase.
Weighs correctness against a small, readable diff, judges the change from the user's side as well as the developer's, and hunts for the structural simplification rather than stopping at style.
Writes the result to a `review-<MR-number>.md` file, and posts it as a single GitLab comment when asked.
Assumes the `glab` command line tool is authenticated.

### `figure-polish`

Conventions and QA for publication figures made with matplotlib and [mplpub](https://gitlab.com/materials-modeling/mplpub).
Fixed column widths of 3.4 and 6.6 inches, compact multi-panel layout, layout variants rendered side by side into one contact sheet instead of one guess per round trip.
Nothing is reported as finished until the rendered image has been looked at.

### `dream`

Consolidates the session history of every local agent config directory into a short `~/.claude/DREAMED.md` of transferable facts: the conventions and procedures that still hold in a project that does not exist yet.
Import that file from your `~/.claude/CLAUDE.md` with a line `@~/.claude/DREAMED.md`.
Runs only when invoked explicitly, and writes that one file.

## Examples

- [`examples/figure-polish`](examples/figure-polish): the same sloppy 2x2 figure request, run without and with the `figure-polish` skill, with both scripts and both rendered figures.

## Install

```
git clone https://github.com/erikfransson/agent-tools.git
agent-tools/install.sh
```

`install.sh` symlinks every skill under `skills/` into `~/.claude/skills`, and into `~/.codex/skills` when `~/.codex` exists.
Name skills as arguments to link only those.
An existing directory with the same name is moved aside as `<name>.before-agent-tools` rather than overwritten.

## Update

```
git -C agent-tools pull
```

The symlinks pick the new content up immediately, including in a running session.
A skill added to the repo after install needs one more `install.sh <name>`.

## License

MIT, see `LICENSE`.
