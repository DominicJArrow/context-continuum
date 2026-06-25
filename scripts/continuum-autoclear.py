#!/usr/bin/env python3
"""Continuum auto-clear - the zero-keystroke watcher ("robot finger").

A hook can't press /clear (Claude Code locks slash commands away from the
automation layer, on purpose). So we do what a human does instead: an OUTSIDE
process watches the live context fill and *types* `/clear` + Enter into the
session for you. When the clear lands, the SessionStart(clear) hook re-injects
the Board automatically - so you continue lean, having touched nothing.

How it knows the percentage: the status-line HUD (continuum-hud.py) writes the
live % to .continuum/pct.txt every render. This watcher just polls that file.

    sensor (HUD writes pct.txt)  ->  watcher (this)  ->  finger (send-keys)
        ->  Claude clears  ->  SessionStart(clear)  ->  Board re-injects

Two backends for the "finger":
  --backend tmux     Linux/harness. Targets an exact tmux pane - rock solid,
                     no window-focus games. THIS is the real, unattended one.
  --backend windows  Demo on Windows. Sends keystrokes to the FOCUSED window
                     via PowerShell SendKeys. Fragile: if the wrong window is
                     focused when it fires, the keys go there. Watch it work,
                     don't trust it unattended.

Examples:
  # Harness (Claude running in a tmux pane named "claude"):
  python continuum-autoclear.py --backend tmux --target claude --project /srv/work

  # Windows demo (focus your Claude terminal when it counts down):
  python continuum-autoclear.py --backend windows --project C:/Users/Artanis
"""
import argparse
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def read_pct(pct_file):
    """Return the last % the HUD wrote, or None if unavailable."""
    try:
        with open(pct_file, encoding="utf-8") as f:
            return int(float(f.read().strip()))
    except Exception:
        return None


def send_clear_tmux(target):
    """Type `/clear` + Enter into a tmux pane. Robust, no focus needed."""
    # Two send-keys calls: the literal text, then the Enter key separately, so
    # tmux can't mis-parse "/clear" as a flag.
    subprocess.run(["tmux", "send-keys", "-t", target, "/clear"], check=True)
    subprocess.run(["tmux", "send-keys", "-t", target, "Enter"], check=True)


def send_clear_windows(countdown):
    """Type `/clear` + Enter into the FOCUSED window via PowerShell SendKeys.

    Prints a countdown first so you can click the Claude terminal in time.
    """
    for n in range(countdown, 0, -1):
        print("  firing /clear in {}s - focus your Claude terminal now"
              .format(n))
        time.sleep(1)
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('/clear'); "
        "Start-Sleep -Milliseconds 150; "
        "[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def fire(backend, target, countdown):
    if backend == "tmux":
        send_clear_tmux(target)
    else:
        send_clear_windows(countdown)


def main():
    ap = argparse.ArgumentParser(description="Continuum zero-keystroke auto-clear watcher")
    ap.add_argument("--project", default=os.getcwd(),
                    help="project dir that contains .continuum/ (default: cwd)")
    ap.add_argument("--backend", choices=["tmux", "windows"], required=True,
                    help="how to type /clear: tmux pane (robust) or windows SendKeys (demo)")
    ap.add_argument("--target", default="claude",
                    help="tmux pane/window target (tmux backend only)")
    ap.add_argument("--threshold", type=int, default=95,
                    help="fire when fill %% >= this (default: 95)")
    ap.add_argument("--rearm", type=int, default=50,
                    help="re-arm once fill %% drops below this (default: 50)")
    ap.add_argument("--interval", type=float, default=5.0,
                    help="seconds between checks (default: 5)")
    ap.add_argument("--countdown", type=int, default=5,
                    help="windows backend: seconds to focus the terminal (default: 5)")
    args = ap.parse_args()

    pct_file = os.path.join(args.project, ".continuum", "pct.txt")
    armed = True
    print("Continuum auto-clear watching {} | fire>={}% rearm<{}% backend={}"
          .format(pct_file, args.threshold, args.rearm, args.backend))

    while True:
        pct = read_pct(pct_file)
        if pct is not None:
            if armed and pct >= args.threshold:
                print("[{}%] threshold hit - sending /clear".format(pct))
                try:
                    fire(args.backend, args.target, args.countdown)
                    print("    /clear sent. Board will re-inject on reset.")
                except Exception as e:
                    print("    failed to send /clear: {}".format(e))
                armed = False
            elif not armed and pct < args.rearm:
                print("[{}%] dropped below re-arm - armed again".format(pct))
                armed = True
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
