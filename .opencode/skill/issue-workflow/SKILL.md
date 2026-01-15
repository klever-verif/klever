---
name: issue-workflow
description: Use when you need to read/modify/create files within `.memory/issues`.
---

`.memory/issues` is a folder for Markdown-based task management.

## Naming
- Issue folder: `.memory/issues/<issue-id>-<short-kebab>`
- Context: `.memory/issues/<issue>/CONTEXT.md`
- Plan: `.memory/issues/<issue>/PLAN.md`
- Task: `.memory/issues/<issue>/TASK-<nn>-<short-kebab>.md` (nn = 01, 02, ...)
- Review: `.memory/issues/<issue>/REVIEW-<nn>.md` (matches task nn)

## Templates
- Plan: `.memory/templates/PLAN.md`
- Task: `.memory/templates/TASK.md`
- Review: `.memory/templates/REVIEW.md`

## Common Rules
- `.memory/issues` tracks work as one folder per issue.
- Directory and content are persistent.
- Use repo-root paths in backticks for cross-references (no Markdown links).
- Keep text short, concrete, and free of contradictions.
- Use only sections presented in templates (NO CUSTOM SECTIONS).
- Update any status only AFTER finishing current edits.

## Plan Rules
- `CONTEXT.md` cannot be modified after `PLAN.md` is created.
- `PLAN.md` is derived from `CONTEXT.md` (if present).

## Task Rules
- Derive tasks from `PLAN.md` (if presented).
- Write tasks as agent-ready instructions (LLM-friendly): explicit steps, repo-root paths, commands, and DoD.
- Edit task text only while `Status: todo`.
- When the user requests implementation, set task `Status` to `wip`.
- When `Status: wip`, only append new entries to `## Notes` (`NOTE-01`, `NOTE-02`, ...).
- When `Status: done`, do not modify the task file.
- Do not set `Status: done` without user approval.
- Write the `## Report` section only when moving the task to `done`.

## Review Rules
- The user specifies whether you act as reviewer or reviewee. Ask if missing and follow only that role.

### Review file contract
- Must match `.memory/templates/REVIEW.md`.
- Must contain `status: <value>` directly under `# REVIEW-<nn>`.
- Allowed status values: `need_feedback`, `feedback_provided`, `clean`, `done`.
- Ownership:
  - Reviewer edits: thread headings (`open`/`resolved`), `Q-...`, and `status:` (`need_feedback`/`clean`/`done` with user approval).
  - Reviewee edits: `A-...` and may set `status: feedback_provided`.
- Each thread groups one topic and is marked `open` or `resolved` by the reviewer.
- A review is resolved when every `Q-..` has an `A-..` and referenced changes are complete.
- Do not write code during review unless the user explicitly approves it.
- Update any review status only after finishing current edits.

### Polling
Run polling without asking permission when it is required.

- `bash .opencode/skill/issue-workflow/poll_review.sh <review-file> <status>`
- `bash .opencode/skill/issue-workflow/poll_review.sh <review-file> <status1> <status2>`

### Reviewer Workflow
1. Ensure the review file exists; if missing, create it from `.memory/templates/REVIEW.md` with `status: feedback_provided`.
2. Check review file and review the requested code scope.
3. For each topic, add a thread and questions:
   - `## THREAD-XX - open - <brief>`
   - `Q-XX:` (one or more)
   - leave matching `A-XX:` empty
4. If any questions/threads remain open, set `status: need_feedback` after finishing edits.
5. Wait for responses:
   - `bash .opencode/skill/issue-workflow/poll_review.sh .memory/issues/<issue>/REVIEW-<nn>.md feedback_provided`
6. When `status: feedback_provided`, validate answers and any user-approved code changes.
7. Close out:
   - If follow-ups are needed: add new `Q-...`, keep threads `open`, set `status: need_feedback` after finishing edits.
   - If satisfied with answers: mark all threads `resolved`, then set `status: clean` after finishing edits.
8. Repeat steps 5–7 until `status: clean`.
9. Reviewee may now start modifying the code only with user approval after `status: clean`.
10. Ask the user for permission to set `status: done` or start polling again (step 5).

### Reviewee Workflow
1. Ensure the review file exists; if missing, create it from `.memory/templates/REVIEW.md` (leave `status: feedback_provided`).
2. Wait for review questions (or completion):
   - `bash .opencode/skill/issue-workflow/poll_review.sh .memory/issues/<issue>/REVIEW-<nn>.md need_feedback clean`
3. When `status: need_feedback`:
   - Answer every question by filling the corresponding `A-...` blocks.
   - Do not modify `Q-...` or thread headings.
   - Do not write code, only provide answers.
   - Set `status: feedback_provided` after finishing edits.
4. Repeat steps 2–3 until the reviewer sets `status: clean`.
5. Ask the user for permission to do requested code changes during review.
   - If modifications are needed: set `status: feedback_provided` after finishing edits.
   - If no changes are expected: ask permission to finish review.
