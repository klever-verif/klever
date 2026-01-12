# Knowledge Storage Guidelines

This directory stores knowledge for the current feature/fix branch and the global backlog.

## Rules
- Each feature/fix gets its own branch and a dedicated knowledge folder in `.memory`.
- The `main` branch must contain only persistent files (list below) in `.memory`.
- Working branches should commit additional temporary files (list below) required for the current work.
- Cleanup procedure must be performed before opening a PR or merging to `main`.

## Persistent Files
- `AGENTS.md`: These agent instructions.
- `TODO.md`: Global project backlog as a simple bullet list.

## Temporary Files
- `DESIGN.md`: Free-form context/design requirements for the current feature/fix.
- `PLAN.md`: Implementation plan derived from `DESIGN.md` and reviewed with a human.
- `TASK-###.md`: Plan decomposition into agent-ready tasks (`###` is sequential task number, e.g., `001`).
- `REVIEW-###.md`: Human/agent review notes for a specific task.
- Other temporary files needed for the current work are allowed.

## Cleanup Procedure
- Before opening a PR or merging to `main`, delete every temporary file in `.memory` except persistent ones.
- Before deleting `.memory` files, review accumulated knowledge and decide what must be moved into docstrings, documentation, tickets, or other durable sources. Ask a human when topics are unclear. If nothing is useful, delete the files (git history preserves them).
