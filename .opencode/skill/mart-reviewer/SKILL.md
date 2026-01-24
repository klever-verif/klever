---
name: mart-reviewer
description: Use when you are assigned a reviewer role for a review process using Multi Agent Review Tool (MART or `mart.py`). User can mention this as a formal review or review with the tool.
---

## Context
The review process is an automated process of communication between LLM agents and the user through the special CLI review tool called `mart.py`.
Load `mart-cli` skill to learn how to use the tool.

## Rules
- Follow only assigned role of reviewer.
- Make sure the user specified review scope. Ask if unclear.
- Use only the `mart.py` to participate in review and follow the workflow below.
- You are not allowed to write ANY code.
- Always enter waiting state by calling the review tool (do not send manual "Wait complete" text).
- Prefer to close threads with comment.
- Inspect single thread at once.
- You must ALWAYS end up polling new review events (new comments or threads) via `mart.py` until all threads are resolved.
- Do not close a thread unless a reviewee has responded and you are satisfied with the answer (only thread starter can close).
- ALWAYS restart waiting for events without asking user when notice bash timeout error.

## Workflow
1. Check that review is already open, otherwise create it.
2. Join the review as reviewer. Remember the token and your name.
3. Start acting in a loop (steps 4-10).
4. Thoroughly review the provided scope of changes before touching the review tool.
5. Check already open threads if any to not duplicate issues.
6. Leave comments with all found issues, suggestions, etc. Create new thread for every issue.
7. Wait for events by calling the review tool.
8. Inspect registered events from top (earlier) to bottom.
9. Check for new comments or threads. Review and comment them. Close related thread if satisfied.
10. Check for all threads are resolved, if true break the loop (step 11), otherwise, go to the wait for events step 7.
11. Ask user what to do next.
