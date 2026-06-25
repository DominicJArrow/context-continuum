#!/usr/bin/env python3
"""Continuum HUD - Claude Code status line.

Reads the status-line JSON on stdin and prints a one-line context-health
readout: a colour-coded fill gauge + the session topic + live task counts
parsed from the Checklist (.continuum/memory.md).

Wire it up in settings.json:
    "statusLine": { "type": "command",
                    "command": "python /path/to/scripts/continuum-hud.py" }
"""
import json
import os
import subprocess
import sys

# Always emit UTF-8 so the gauge/symbols render regardless of console codepage
# (Windows consoles default to cp1252 and would otherwise crash).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Zone thresholds, as a percentage of the context window used.
AMBER = 60
ORANGE = 85
RED = 95


def read_input():
    """Read the status-line JSON from stdin once; return (data, raw_text).

    We keep the raw text around so we can feed it unchanged to an adopter's own
    status-line command (see run_wrapped) if they want to keep theirs.
    """
    raw = ""
    try:
        raw = sys.stdin.read()
        return json.loads(raw), raw
    except Exception:
        return {}, raw


def run_wrapped(raw):
    """Append our gauge to an EXISTING status line instead of replacing it.

    Claude Code allows only one status-line command, so by default ours would
    replace whatever the user already had. If they set CONTINUUM_WRAP to their
    original command, we run it first (feeding it the same stdin JSON we got)
    and return its output, so our gauge can sit at the END of their line.
    Best-effort and fast: any failure or slowness just yields no upstream text.
    """
    cmd = os.environ.get("CONTINUUM_WRAP", "").strip()
    if not cmd:
        return ""
    try:
        res = subprocess.run(cmd, shell=True, input=raw, capture_output=True,
                             text=True, timeout=5)
        return (res.stdout or "").strip()
    except Exception:
        return ""


def project_root(data):
    ws = data.get("workspace", {}) or {}
    return ws.get("project_dir") or ws.get("current_dir") or os.getcwd()


def parse_checklist(path):
    topic = ""
    counts = {"todo": 0, "doing": 0, "done": 0, "backlog": 0}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                low = s.lower()
                if low.startswith("topic:"):
                    topic = s.split(":", 1)[1].strip()
                elif s.startswith("[ ]"):
                    counts["todo"] += 1
                elif s.startswith("[/]"):
                    counts["doing"] += 1
                elif s.startswith("[x]") or s.startswith("[X]"):
                    counts["done"] += 1
                elif s.startswith("[-]"):
                    counts["backlog"] += 1
    except FileNotFoundError:
        pass
    return topic, counts


def write_pct(root, pct):
    """Persist the live fill % so an external watcher can read it.

    The status line is the ONLY place that sees the real context percentage,
    so we drop it to a tiny sidecar file (.continuum/pct.txt) on every render.
    A separate watcher process polls that file and fires the auto-reset. Any
    failure here must never break the status line, so it's best-effort.
    """
    try:
        path = os.path.join(root, ".continuum", "pct.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(pct))
    except Exception:
        pass


def light(pct):
    if pct >= RED:
        return "\U0001F534"      # red
    if pct >= ORANGE:
        return "\U0001F7E0"      # orange
    if pct >= AMBER:
        return "\U0001F7E1"      # yellow
    return "\U0001F7E2"          # green


def main():
    data, raw = read_input()
    cw = data.get("context_window", {}) or {}
    try:
        pct = round(float(cw.get("used_percentage", 0)))
    except (TypeError, ValueError):
        pct = 0

    root = project_root(data)
    write_pct(root, pct)  # sensor feed for the auto-reset watcher
    checklist = os.path.join(root, ".continuum", "memory.md")
    topic, c = parse_checklist(checklist)

    segments = []
    upstream = run_wrapped(raw)  # the adopter's existing status line, if any
    if upstream:
        segments.append(upstream)
    segments.append("{} {}%".format(light(pct), pct))
    if topic:
        segments.append(topic[:40])
    segments.append(
        "☐{todo} ◐{doing} ✓{done} ⊘{backlog}".format(**c)
    )
    print("  ·  ".join(segments))


if __name__ == "__main__":
    main()
