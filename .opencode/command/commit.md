---
description: сommit current changes
agent: build
---

Commit current changes using following rules:
- Use Conventional Commits (`feat:`, `fix:`, etc.)
- Keep the header short (<= 72 chars), specific, imperative
- Prefer the reason (why) over the implementation (what)
- Commit only staged changes; if nothing is staged, ask what to stage
- Do not include unstaged changes; mention them if present
- Add a body only when needed; use a simple bullet list grouped by theme
- Do not bypass pre-commit hooks unless the user explicitly requests it
- If hooks fail: summarize grouped failures, propose fixes, and ask how to proceed
