import glob, json, os, re, sys
from datetime import datetime, timezone, timedelta

# parameters
SOURCES = sorted(d for pat in ("~/.claude*", "~/.codex*")
                 for d in glob.glob(os.path.expanduser(pat)) if os.path.isdir(d))
WINDOW = "10d"
RECENT_DAYS = 7
MAX_CHARS = 2000
MIN_CHARS = 15
SIGNAL_ONLY = True
OUT = os.environ.get("DREAM_CORPUS", "/tmp/dream-corpus.md")

if len(sys.argv) > 1:
    WINDOW = sys.argv[1].strip().lower()

NOW = datetime.now(timezone.utc)
if WINDOW.endswith("s"):
    MAX_SESSIONS, WINDOW_START = int(WINDOW[:-1]), None
else:
    MAX_SESSIONS = None
    WINDOW_START = NOW - timedelta(days=int(WINDOW.rstrip("d")))
CUTOFF = NOW - timedelta(days=RECENT_DAYS)

SIGNAL = re.compile(
    r"\b(always|never|don'?t|do not|instead|prefer|should( not)?|must|"
    r"from now on|remember|stop|no need|rather than|i want|wrong|"
    r"not what i|as i said|please (use|keep|make sure))\b", re.I)

SKIP = re.compile(
    r"^(<(command-name|local-command|command-message|bash-input|system-reminder)|"
    r"\[Request interrupted|Caveat: The messages below)", re.I)


def ts_parse(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") in ("text", "input_text") and b.get("text"):
                    out.append(b["text"])
        return "\n".join(out)
    return ""


def claude_records(path):
    with open(path, errors="ignore") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("type") != "user" or r.get("isMeta"):
                continue
            msg = r.get("message") or {}
            c = msg.get("content")
            if isinstance(c, list) and any(
                    isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                continue
            yield ts_parse(r.get("timestamp")), r.get("cwd", ""), text_of(c)


def codex_records(path):
    cwd = ""
    with open(path, errors="ignore") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            p = r.get("payload") or {}
            if r.get("type") == "session_meta":
                cwd = p.get("cwd", "") or cwd
                continue
            if r.get("type") == "response_item" and p.get("type") == "message" \
                    and p.get("role") == "user":
                yield ts_parse(r.get("timestamp")), cwd, text_of(p.get("content"))


def collect():
    rows = []
    for root in SOURCES:
        if not os.path.isdir(root):
            continue
        tag = os.path.basename(root)
        files = []
        for dirpath, _, names in os.walk(root):
            for n in names:
                if n.endswith(".jsonl"):
                    p = os.path.join(dirpath, n)
                    files.append((datetime.fromtimestamp(os.path.getmtime(p),
                                                        timezone.utc), p))
        files.sort(reverse=True)
        if MAX_SESSIONS:
            files = files[:MAX_SESSIONS]
        else:
            files = [f for f in files if f[0] >= WINDOW_START]
        for mtime, path in files:
                reader = codex_records if "codex" in tag else claude_records
                try:
                    for t, cwd, txt in reader(path):
                        txt = (txt or "").strip()
                        if len(txt) < MIN_CHARS or SKIP.match(txt):
                            continue
                        if SIGNAL_ONLY and not SIGNAL.search(txt):
                            continue
                        rows.append(((t or mtime), tag, cwd, txt[:MAX_CHARS]))
                except Exception:
                    continue
    return rows


rows = collect()
rows.sort(key=lambda r: r[0])
seen, uniq = set(), []
for r in rows:
    k = r[3][:200]
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)

recent = [r for r in uniq if r[0] >= CUTOFF]
older = [r for r in uniq if r[0] < CUTOFF]

with open(OUT, "w") as fh:
    fh.write(f"# Dream corpus\n\ngenerated {NOW.isoformat()}\n")
    fh.write(f"sources: {', '.join(SOURCES)}\nwindow: {WINDOW}\n")
    fh.write(f"prompts: {len(uniq)} unique ({len(recent)} recent, {len(older)} older)\n")
    for label, chunk in (("RECENT (last %d days, weight high)" % RECENT_DAYS, recent),
                         ("OLDER (weight low, confirm only)", older)):
        fh.write(f"\n\n## {label}\n")
        for t, tag, cwd, txt in chunk:
            fh.write(f"\n### {t.date()} [{tag}] {cwd}\n{txt}\n")

print(f"window {WINDOW}: {len(uniq)} unique prompts -> {OUT}")
print(f"  recent {len(recent)}  older {len(older)}")
print(f"  size {os.path.getsize(OUT)/1024:.0f} KB")
