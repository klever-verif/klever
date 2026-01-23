---
name: issues-reviewer
description: Use when you are assigned a reviewer role for a task within `.memory/issues`.
---

## Context
The review process is an automated process of communication between LLM agents and the user through the special review tool.
Load `issues-review-control` skill to learn how to use the tool.

## Rules
- Follow only assigned role of reviewer.
- Make sure the user specified the issue, task, and review scope. Ask if unclear.
- You are not allowed to write ANY code.
- Use only the review tool to participate in review (workflow below).
- Always enter waiting state by calling the review tool (do not send manual "Wait complete" text).
- Do not leave two or more comments in a row within single thread.
- Prefer to close threads with comment.
- Prefer to inspect single thread at once.
- You must always end up polling new review events until all threads are resolved.
- Do not close a thread unless the reviewee has responded in that thread or the user explicitly instructs you to close it.

## Workflow
1. Check that review is already open, otherwise create it.
2. Join the review as reviewer (make up some short name). Remember the token and your name.
3. Act in a loop:
   - Thoroughly review the provided scope of changes
   - Leave comments with all found issues, suggestions, etc. Create new thread for every issue.
   - Wait for events by calling the review tool (do not send manual wait text).
   - Inspect registered events from top (earlier) to bottom.
   - If there is a new comment, review it and continue the thread or close it if satisfied.
   - If all threads are resolved, then break the loop and ask user what to do next.
   - Otherwise, go to the wait for events step.
