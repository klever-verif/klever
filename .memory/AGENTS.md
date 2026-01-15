# Knowledge Storage (.memory)

This directory is a persistent, repo-local knowledge base.

## Structure
- `.memory/TODO.md`: Global backlog (simple bullet list).
- `.memory/templates/`: Canonical templates for plans, tasks, and reviews.
- `.memory/issues/`: Per-issue working folders.

## Persistence Rules
- Everything under `.memory/` is persistent.
- Do not delete, rewrite, or “clean up” history unless explicitly requested.

## Writing Rules
- Keep files short and consistent with templates.
- Use repo-root paths for all references (e.g. `src/...`, `.memory/...`).
- For cross-links, use repo-root paths in backticks (no Markdown links).
