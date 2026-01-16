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
- The review process is an automated process between two LLM agents synchronized with a polling script.
- DO NOT STOP OR ASK USER UNLESS WORKFLOW ALLOWS IT

### Review file contract
- Must match `.memory/templates/REVIEW.md`.
- Must contain `status: <value>` directly under `# REVIEW-<nn>`.
- Allowed status values: `wait_reviewer`, `wait_reviewee`, `clean`, `done`.
- Ownership:
  - Reviewer edits: thread headings (`open`/`resolved`), `Q-...`, and `status:` (`wait_reviewee`/`clean`/`done` with user approval).
  - Reviewee edits: `A-...` and may set `status: wait_reviewer`.
- Each thread groups one topic and is marked `open` or `resolved` by the reviewer.
- Threads are persistent and cannot be removed.
- New threads and questions may be added manually by the user.
- A review is resolved when every `Q-..` has an `A-..`, all threads are resolved, and referenced changes are complete.
- UPDATE ANY REVIEW `status:` ONLY AFTER FINISHING CURRENT THREAD EDITS.
- DO NOT WRITE CODE DURING REVIEW UNLESS `status: clean` AND THE USER EXPLICITLY APPROVES IT.

Run polling without asking permission when it is required.

### Reviewer Workflow
1. Ensure the review file exists; if missing, create it from `.memory/templates/REVIEW.md` with `status: wait_reviewer`.
2. YOU DO NOT EDIT CODE
3. Check review file and review the requested code scope.
4. For each topic, add a thread and questions:
   - `## THREAD-XX - open - <brief>`
   - `Q-XX:` (one or more)
   - leave matching `A-XX:` empty
5. If any questions/threads remain open, set `status: wait_reviewee` after finishing edits.
6. ALWAYS run polling without asking permission when status is updated with `wait_reviewee`:
   - `bash .opencode/skill/issue-workflow/poll_review.sh .memory/issues/<issue>/REVIEW-<nn>.md wait_reviewer`
7. ALWAYS re-read the review document after polling is done. If there is evidence of a race, run it again.
8. When `status: wait_reviewer`, validate answers and any user-approved code changes.
9. If satisfied with answers (non-empty) within a thread - mark it as `resolved`.
   - If follow-ups are needed: add new `Q-...`, keep threads `open`, set `status: wait_reviewee` after finishing edits and start polling.
   - If satisfied with answers: make sure all threads `resolved`, then set `status: clean` after finishing edits.
10. Repeat steps 5–7 until `status: clean`.
11. Reviewee may now start modifying the code only with user approval after `status: clean`.
12. Ask the user for permission to set `status: done` or start polling again (step 5).

### Reviewee Workflow
1. Ensure the review file exists; if missing, create it from `.memory/templates/REVIEW.md` (leave `status: wait_reviewer`).
2. Wait for review questions (or completion):
   - `bash .opencode/skill/issue-workflow/poll_review.sh .memory/issues/<issue>/REVIEW-<nn>.md wait_reviewee clean`
3. ALWAYS re-read the review document after polling is done. If there is evidence of a race, run it again.
4. When `status: wait_reviewee`:
   - Answer every question by filling the corresponding `A-...` blocks.
   - Do not modify `Q-...` or thread headings.
   - Do not write code, only provide answers.
   - Set `status: wait_reviewer` after finishing edits.
   - ALWAYS run polling without asking permission when status is updated with `wait_reviewer`:
5. Repeat steps 2–3 until the reviewer sets `status: clean`.
6. Ask the user for permission to do requested code changes during review.
   - If modifications are needed: set `status: wait_reviewer` after finishing edits.
   - If no changes are expected: ask permission to finish review.
