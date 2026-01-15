---
name: do-issue-review
description: Reviewer workflow for .memory/issues reviews (threads, questions, status polling).
---

## Role
You are the reviewer.

Scope: use this skill only for the formal `.memory/issues` review procedure.

## Inputs (ask if missing)
- Review file path (required): `.memory/issues/<issue-id>-<short>/REVIEW-<nn>.md`
- Review scope (required): repo-root paths to review (files/dirs) or a `git diff` range.

## Review file contract
- Must match `.memory/templates/REVIEW.md`.
- Must contain `status: <value>` directly under `# REVIEW-<nn>`.
- Allowed status values: `need_feedback`, `feedback_provided`, `done`.
- Ownership:
  - Reviewer edits: thread headings (`open`/`resolved`), `Q-...`, and `status:` (`need_feedback`/`done`).
  - Reviewee edits: `A-...` and may set `status: feedback_provided`.

## Workflow
1. Ensure the review file exists; if missing, create it from `.memory/templates/REVIEW.md`.
2. Review the requested scope.
3. For each topic, add a thread and questions:
   - `## THREAD-XX - open - <brief>`
   - `Q-XX:` (one or more)
   - leave matching `A-XX:` empty
4. If any questions/threads remain open, set `status: need_feedback`.
5. Wait for responses:
   - `bash .opencode/skill/do-issue-review/poll.sh .memory/issues/<issue>/REVIEW-<nn>.md`
6. When `status: feedback_provided`, validate the answers and any code changes.
7. Close out:
   - If follow-ups are needed: add new `Q-...`, keep threads `open`, set `status: need_feedback`.
   - If satisfied: mark all threads `resolved`, ask the user for approval to close the review, then set `status: done`.

Repeat steps 5–7 until `status: done`.
