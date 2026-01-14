# Issues Workflow (.memory/issues)

This directory tracks work as one folder per issue.

## Naming
- Issue folder: `.memory/issues/<issue-id>-<short-kebab>`
- Context: `.memory/issues/<issue>/CONTEXT.md`
- Plan (optional): `.memory/issues/<issue>/PLAN.md`
- Task: `.memory/issues/<issue>/TASK-<nn>-<short-kebab>.md` (nn = 01, 02, ...)
- Review: `.memory/issues/<issue>/REVIEW-<nn>.md` (matches task nn)

## Templates
- Plan: `.memory/templates/PLAN.md`
- Task: `.memory/templates/TASK.md`
- Review: `.memory/templates/REVIEW.md`

## Rules
- Derive tasks from `PLAN.md` (when present).
- Write tasks as agent-ready instructions (LLM-friendly): explicit steps, repo-root paths, commands, and DoD.
- Use repo-root paths in backticks for cross-references (no Markdown links).
- Fill `Notes` only during implementation; append `NOTE-01`, `NOTE-02`, ...
- Fill `Report` only when explicitly requested.
- Keep text short, concrete, and free of contradictions.
- Use only sections presented in templates (no custom ones)

## Reviews
- Each thread groups one topic and is marked `open` or `resolved` by reviever.
- A review is resolved when every `Q-..` has an `A-..` and the referenced changes are done.
- Reviewer can touch only `Q-...` notes
- Reviewee can touch only `A-...` notes
