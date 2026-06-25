#!/usr/bin/env python3
"""Continuum sweep - keep the Board lean.

Moves completed [x] and dropped [-] items out of .continuum/memory.md into the
cold standby files, leaving only the Topic line and the active [ ] / [/] tasks.
By default it only acts when the Board exceeds the line cap; pass --force to
sweep regardless.

Usage:
    python continuum-sweep.py [project_dir] [--force]
"""
import datetime
import os
import sys

MAX_LINES = 50


def _append(path, header, stamp, items):
    exists = os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if not exists:
            f.write(header + "\n")
        f.write("\n## swept {}\n".format(stamp))
        for item in items:
            f.write(item + "\n")


def sweep(root, force=False):
    cdir = os.path.join(root, ".continuum")
    board = os.path.join(cdir, "memory.md")
    done_f = os.path.join(cdir, "standby-done.md")
    back_f = os.path.join(cdir, "standby-backlog.md")

    if not os.path.exists(board):
        print("No Board at {}".format(board))
        return

    with open(board, encoding="utf-8") as f:
        lines = f.readlines()

    if not force and len(lines) <= MAX_LINES:
        print("Board is {} lines (cap {}); no sweep needed.".format(
            len(lines), MAX_LINES))
        return

    keep, done, back = [], [], []
    for line in lines:
        s = line.strip()
        if s.startswith("[x]") or s.startswith("[X]"):
            done.append(s)
        elif s.startswith("[-]"):
            back.append(s)
        else:
            keep.append(line.rstrip("\n"))

    if not done and not back:
        print("Nothing cold to sweep (no [x] or [-] items).")
        return

    stamp = datetime.date.today().isoformat()
    if done:
        _append(done_f, "# Standby Done (cold storage - not injected)",
                stamp, done)
    if back:
        _append(back_f, "# Standby Backlog (cold storage - not injected)",
                stamp, back)

    with open(board, "w", encoding="utf-8") as f:
        f.write("\n".join(keep).rstrip() + "\n")

    print("Swept {} done + {} backlog items. Board now {} lines.".format(
        len(done), len(back), len(keep)))


if __name__ == "__main__":
    argv = sys.argv[1:]
    force = "--force" in argv
    argv = [a for a in argv if a != "--force"]
    root = argv[0] if argv else os.getcwd()
    sweep(root, force=force)
