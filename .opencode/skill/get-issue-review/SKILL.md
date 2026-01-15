---
name: get-issue-review
description: Reviewee workflow for .memory/issues reviews (answer questions, update status, stop on done).
---

## Role
You are the reviewee.

Scope: use this skill only for the formal `.memory/issues` review procedure.

## Input (ask if missing)
- Review file path (required): `.memory/issues/<issue-id>-<short>/REVIEW-<nn>.md`

## Review file contract
- Must match `.memory/templates/REVIEW.md`.
- Must contain `status: <value>` directly under `# REVIEW-<nn>`.
- Allowed status values: `need_feedback`, `feedback_provided`, `done`.
- Ownership:
  - Reviewee edits: `A-...` and may set `status: feedback_provided`.
  - Reviewer edits: thread headings (`open`/`resolved`), `Q-...`, and `status:` (`need_feedback`/`done`).

## Workflow
1. Ensure the review file exists; if missing, create it from `.memory/templates/REVIEW.md` (leave `status: feedback_provided`).
2. Wait for review questions (or completion):
   - `bash .opencode/skill/get-issue-review/poll.sh .memory/issues/<issue>/REVIEW-<nn>.md`
3. When `status: need_feedback`:
   - Answer every question by filling the corresponding `A-...` blocks.
   - Make any required code changes.
   - Do not modify `Q-...` or thread headings.
   - Set `status: feedback_provided`.
4. Repeat steps 2–3 until the reviewer sets `status: done` (the poll script exits on `done`).
