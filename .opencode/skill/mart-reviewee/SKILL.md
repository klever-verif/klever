---
name: mart-reviewee
description: Use when you are assigned a reviewer role for a review process using Multi Agent Review Tool (MART or `mart.py`). User can mention this as a formal review or review with the tool.
---

## Context
The review process is an automated process of communication between LLM agents and the user through the special CLI review tool called `mart.py`.
Load `mart-cli` skill to learn how to use the tool.

## Mandatory Rules
- Follow only assigned role of reviewee.
- Make sure the user specified review scope. Ask if unclear.
- Use only the `mart.py` to participate in review and follow the workflow below.
- You are not allowed to write the code without clean review (all threads are resolved) followed by user approval.
- Inspect a single review thread at once.
- Always enter waiting state by calling `mart.py` (do not send manual "Wait complete" text).
- You must ALWAYS end up polling new review events (new comments or threads) via `mart.py` until all threads are resolved.
- ALWAYS restart waiting for events without asking user when notice bash timeout error.

## Workflow
1. Check that review is already open, otherwise create it.
2. Join the review as reviewee (pick some short human name). Remember the token and your name.
3. Start acting reactively in a loop (steps 4-9) by putting steps into your ToDo list and iterate through.
4. Wait for new events - you expect reviewers create threads and leave comments.
5. Inspect registered events from top (earlier) to bottom.
6. Check for new threads or comments, review them and provide answers.
7. Update your todo list with action items extracted from review. Mark them as [AR] (Action Requested).
8. Check for all threads are resolved. If true, then the reviewer is satisfied at the moment, so break the loop and go to step 10. Otherwise, go to the next iteration of the loop (step 4).
10. Analyze the whole review text, update action items and provide the list to the user for approval.
