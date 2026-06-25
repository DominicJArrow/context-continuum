## Continuum - session memory (add this block to your project's CLAUDE.md)

This project uses Context Continuum. Maintain `.continuum/memory.md` (the Checklist)
as you work - it is the source of truth for what this session is doing.

- **Keep it current:** as tasks move, tick them in place - `[ ]` → `[/]` → `[x]`,
  and `[-]` for anything dropped or deferred. Do NOT append a running history.
- **Keep it lean:** the Checklist is capped at 50 lines. When it grows past that,
  sweep cold `[x]` and `[-]` items into `.continuum/standby-done.md` and
  `.continuum/standby-backlog.md` (or run `python scripts/continuum-sweep.py`).
- **One-liners only.** The top `Topic:` line says what the session is about.
- **After a reset:** the Checklist is re-injected automatically. Trust it as your
  memory of the session and carry on from the open items.
