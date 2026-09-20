# agent-tools

Skills for coding agents, written for scientific software work.
They run under Claude Code and Codex, which both read a `SKILL.md` from a skills directory.

## Skills

- `code-review-scientific`: multi-agent review of a GitLab merge request in a scientific codebase, with a written review file and an optional post to GitLab.
  Assumes the `glab` command line tool is authenticated.
- `figure-polish`: conventions and QA for publication figures made with matplotlib and [mplpub](https://github.com/materials-modeling/mplpub).
- `dream`: consolidate the session history of all local agent config directories into a short `~/.claude/DREAMED.md` of transferable facts.
  Import that file from your `~/.claude/CLAUDE.md` with a line `@~/.claude/DREAMED.md`.

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
