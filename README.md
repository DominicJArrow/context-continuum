# Context Continuum

**A small, free tool that keeps an AI coding assistant sharp across a long session, by replacing blind context-compaction with a living, auditable checklist.**

Context Continuum (or just Continuum) fights **context rot**: the well-documented fact that large language models get less reliable as their context window fills up, long before they hit the advertised limit. Instead of letting your CLI silently summarise (and quietly lose) your work, Continuum keeps one tiny **Checklist** of what's done, in progress, and still to do, and re-injects it automatically after every context reset. The session stays lean, and the model stays focused on what actually matters.

> Built first for **Claude Code**, designed to be **model-agnostic**. The heart of it is a plain text file any AI can read.

**If you are looking for** a way to fight context rot, stop `/compact` and auto-compaction from silently losing your work, add persistent working memory to Claude Code, or simply keep an LLM sharp deep into a long session, Continuum is the simple, all-in-one, open-source answer. One living Checklist, one status-line gauge, zero lost context.

---

## The problem

People say "context rot" as if it's one thing. It's really three:

1. **The dumb zone.** A model's advertised window (200K, 1M tokens) is capacity, not competence. Quality measurably drops well before the limit as attention spreads thinner across more tokens.
2. **Lost in the middle.** Models attend strongly to the start and the most recent turns, and weakly to the middle. A decision you made 60K tokens ago is physically present but functionally invisible. (See Liu et al., Lost in the Middle.)
3. **Blunt compaction.** `/compact` and auto-compact are lossy summarisation, a guillotine. They often drop the one detail you cared about, and you cannot see what was lost.

Continuum does not try to make the window bigger. It keeps your working context lean and high-signal, so you spend less time in the dumb zone. And when a reset is unavoidable, what survives is a checklist you can audit, not a fog.

## The idea

One living **Checklist** per project, not a summary:

- It records the session's durable spine: what the work is, what's done, what's left, what's been dropped.
- It is edited **in place** (ticking a box does not grow the file), so it stays tiny, a hard cap of **50 lines**.
- When the context resets, the Checklist is **re-injected automatically**, so the model picks up sharp instead of foggy.
- Finished and dropped items are swept off to cold **Standby** files that are never re-injected. They live on disk if you ever need them, but they never weigh down a fresh start.

In memory terms, the Checklist is **externalized working memory**: the "what am I doing right now" scratchpad that a model normally loses first on compaction, made durable so it always comes back.

## How it works (Claude Code)

Continuum is two parts: a **brain** (plain text files) and **adapters** (hooks and scripts).

```
You work  ->  the Checklist is kept current as tasks move ([ ] -> [/] -> [x])
        |
        v  context fills toward the limit
   the context resets (auto-compact, or a clean auto-clear)
        |
        v
   SessionStart hook re-injects the Checklist  ->  you continue, sharp
```

- **The eyes, status line.** A status-line script reads Claude Code's live `context_window.used_percentage` and shows a minimal colour-coded gauge with the fill percentage (green, yellow, orange, red). This is your early-warning light. It also writes the live percentage to `.continuum/pct.txt` so the optional auto-clear watcher can see it. Want more on the line? Set `CONTINUUM_HUD_FULL=1` to also show the session topic and live task counts.
- **The hands, SessionStart hook.** After any reset (`compact`, `clear`, or `startup`), this hook prints the Checklist back into the fresh context automatically.

### Two ways to reset (pick your comfort level)

Continuum supports both, you choose:

1. **Fully hands-off (auto-compact).** Do nothing. Claude's built-in auto-compact fires by itself when the window gets full, and the SessionStart hook drops the clean Checklist on top. Claude still writes its own summary (we cannot delete that), so the Checklist simply sits above it as the sharp source of truth.
2. **Zero-keystroke clean reset (optional auto-clear watcher).** A small background watcher gives you a truly clean wipe with no summary at all, and still no keystroke from you. See below.

### Zero-keystroke auto-clear (optional)

No hook is allowed to press `/clear` for you (Claude Code locks slash commands away from automation, on purpose). So we do what a human does: an outside watcher types `/clear` for you when the context gets full. Three small pieces:

```
sensor (HUD writes pct.txt)  ->  watcher (reads it)  ->  finger (types /clear)
      ->  Claude clears  ->  SessionStart(clear) re-injects the Checklist
```

- **Sensor:** the status-line HUD writes the live fill percentage to `.continuum/pct.txt` on every render. (The status line is the only place that sees the real percentage.)
- **Watcher:** `scripts/continuum-autoclear.py` polls that file, fires at a threshold (default 95%), and re-arms once the fill drops back down (default 50%). You decide *when* it fires with `--threshold` (or the `CONTINUUM_AUTOCLEAR_PCT` env var). Test your setup safely with `--dry-run` (detects and logs, sends no keystrokes); `--once` checks a single time and exits.
- **Finger:** how it types `/clear` depends on where you run it:
  - `--backend tmux` for Linux or a server. It targets an exact tmux pane (`tmux send-keys`), so it is robust and unattended. This is the real production version.
  - `--backend windows` for a desktop demo. It sends keystrokes to the focused window. Watch it work, but do not trust it unattended (if the wrong window is focused, the keys land there).

Example (Linux, Claude running in a tmux pane named "claude"):
```
python scripts/continuum-autoclear.py --backend tmux --target claude --project /path/to/project
```

### Plays nice with your existing status line (additive)

Already have your own Claude Code status line? Keep it. Claude Code only allows one status-line command, so by default ours would replace yours. To avoid that, set an environment variable `CONTINUUM_WRAP` to your original status-line command. Continuum runs your command first and appends its own gauge to the END of your line, so you keep everything you had, with the context gauge tacked on:

```
your existing status line   ·   green 8%
```

If `CONTINUUM_WRAP` is not set, Continuum just prints its own line as normal.

### The files

Everything lives in a `.continuum/` folder inside your project:

| File | Role | Re-injected? |
|---|---|---|
| `.continuum/memory.md` | the Checklist itself, live (50 lines max) | yes, every reset |
| `.continuum/pct.txt` | live fill percentage the HUD writes (sensor for auto-clear) | no |
| `.continuum/standby-done.md` | Standby Done, cold finished items | no |
| `.continuum/standby-backlog.md` | Standby Backlog, cold dropped or deferred items | no |

### The scripts

| Script | Role |
|---|---|
| `scripts/continuum-hud.py` | status-line gauge, live counts, and the pct.txt sensor |
| `scripts/continuum-inject.py` | SessionStart hook, re-injects the Checklist after a reset |
| `scripts/continuum-sweep.py` | keeps the Checklist under 50 lines by sweeping cold items to Standby |
| `scripts/continuum-autoclear.py` | optional zero-keystroke auto-clear watcher (tmux or windows) |

### The checklist states

```
[ ]  To Do      not started
[/]  Doing      in progress right now
[x]  Done       finished
[-]  Backlog    deliberately dropped or deferred (stops re-arguing dead ideas)
```

Tasks are one-liners. A slightly long one-liner is fine; multi-sentence essays are not.

## Platform support

Continuum runs anywhere Python and Claude Code run. **Linux is the recommended, first-class home**, and it is where the zero-keystroke auto-clear is at its best.

- **Linux (recommended).** Everything works, and the auto-clear watcher runs in its strongest, fully unattended form: `--backend tmux` drives `/clear` into an exact tmux pane (`tmux send-keys`), so there are no window-focus games and nothing to babysit. This is the intended setup for an always-on or headless server.
- **macOS.** Same story as Linux. The tmux backend behaves identically.
- **Windows.** The core works fully: the Checklist, the live status-line gauge, SessionStart re-injection, the sweep, and the `pct.txt` sensor. The auto-clear "finger" is a watch-it-work demo only here (`--backend windows` sends keystrokes to the focused window), because Windows has no tmux-style pane targeting. Use Windows for everyday work with the hands-off auto-compact path; use Linux, macOS, or any tmux session when you want the fully unattended auto-clear.

The brain (the Checklist and the cold Standby files) is plain text and byte-for-byte identical on every platform. Only the auto-clear "finger" differs by OS.

## Install (Claude Code)

1. Clone this repo somewhere stable.
2. In the project you want to protect, create a `.continuum/` folder and copy the three template files into it (`memory.md`, `standby-done.md`, `standby-backlog.md`).
3. Add the standing rule from `templates/CLAUDE.snippet.md` to your project's `CLAUDE.md`.
4. Wire up the hooks and status line in your Claude Code `settings.json`. See `templates/settings.example.json` and point the paths at your clone.
5. (Optional) Already have a status line? Set `CONTINUUM_WRAP` to your original command so ours appends instead of replacing.
6. (Optional) Want the truly clean zero-keystroke reset? Run `scripts/continuum-autoclear.py` in the background with the backend for your platform.

That's it. Open the project and you will see the status-line gauge; the Checklist re-injects itself after every reset.

> Windows note: use the `py` launcher (or full `python.exe` path) and an absolute path to the scripts in `settings.json`. Forward slashes work fine in JSON.

## Leanness rules (the whole point)

- **Edit in place, never append.** The Checklist is a whiteboard, not a diary.
- **One Checklist, 50 lines max.** Over the cap, run the sweep (`scripts/continuum-sweep.py`).
- **Only the Checklist is ever injected.** Standby files stay cold, so injections stay fast.
- **Keep `CLAUDE.md` feather-light.** It rides along on every single turn.

## Roadmap

- **v0:** Claude Code (this).
- **Next:** adapters for other CLIs (Codex, Gemini CLI). The Checklist is already model-agnostic; each CLI just needs its own thin hook layer.
- **Later:** smarter "cold" detection for the sweep; optional topic-switching support (v0 assumes one session is one topic).

## Prior art and thanks

Continuum stands on ideas from MemGPT and Letta (tiered, self-managed memory), Manus (filesystem as context), and the research that proved the problem is real: Liu et al., Lost in the Middle, and Chroma's Context Rot report. Continuum's contribution is to make the proven "filesystem spine" pattern a small, standard, token-aware, bolt-on tool, and to put a fidelity warning light in front of the human, not just memory behind the model.

## Keywords

For anyone searching, Continuum helps with: context rot, context-rot mitigation, the AI "dumb zone", lost in the middle, long-context degradation, context window management, context engineering, persistent memory for LLMs, AI working memory, agent memory, session memory, checklist memory, anti-compaction, how to stop `/compact` and auto-compact from losing context, keeping an AI coding assistant sharp in long sessions, Claude Code memory, Claude Code status line, Claude Code hooks, model-agnostic context management, and an open-source LLM context-management tool.

## License

MIT, free for everyone, for the greater good. See [LICENSE](LICENSE).
