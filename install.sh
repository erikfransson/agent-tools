#!/usr/bin/env bash
# Link the skills in this repo into ~/.claude/skills, and into ~/.codex/skills when ~/.codex exists.
# Usage: ./install.sh [skill ...]   (no arguments links every skill)
set -euo pipefail

repo=$(cd "$(dirname "$0")" && pwd)
dests=(~/.claude/skills)
[ -d ~/.codex ] && dests+=(~/.codex/skills)

if [ "$#" -gt 0 ]; then
    skills=("$@")
else
    mapfile -t skills < <(find "$repo/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -printf '%h\n' | xargs -r -n1 basename)
fi

for skill in "${skills[@]}"; do
    src="$repo/skills/$skill"
    if [ ! -f "$src/SKILL.md" ]; then
        echo "no such skill in repo: $skill" >&2
        exit 1
    fi
    for dest in "${dests[@]}"; do
        mkdir -p "$dest"
        dst="$dest/$skill"
        if [ -e "$dst" ] && [ ! -L "$dst" ]; then
            mv "$dst" "$dst.before-agent-tools"
            echo "kept your old $dst as $dst.before-agent-tools"
        fi
        ln -sfn "$src" "$dst"
        echo "linked $dst -> $src"
    done
done
