#!/usr/bin/env python3
"""Continuum inject - re-injects the Board into a fresh context.

Wire this to Claude Code's SessionStart hook (matchers: startup, compact,
clear). After any context reset it prints the live Board so it lands straight
back into context. Cold standby files are NOT printed - only pointed at - so
the injection stays small and fast.

Anything this script prints to stdout is added to the model's context.
"""
import json
import os
import sys

# Always emit UTF-8 (the Board may contain non-ASCII; Windows consoles default
# to cp1252 and would otherwise crash).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def project_root(data):
    ws = data.get("workspace", {}) or {}
    return ws.get("project_dir") or ws.get("current_dir") or os.getcwd()


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    root = project_root(data)
    board = os.path.join(root, ".continuum", "memory.md")
    if not os.path.exists(board):
        return  # nothing to inject yet

    with open(board, encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return

    print("=== Continuum: active session memory (re-injected) ===")
    print(content)
    print()
    print("(Finished items live in .continuum/standby-done.md and dropped/"
          "deferred items in .continuum/standby-backlog.md - read those only "
          "if you actually need them. Treat the Board above as your memory of "
          "this session and continue from the open items.)")


if __name__ == "__main__":
    main()
