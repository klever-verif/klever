---
name: issues-reviewee
description: Use when you are assigned a reviewee role for a task within `.memory/issues`.
---

## Context
The review process is an automated process of communication between LLM agents and the user through the special review tool.
Load `issues-review-control` skill to learn how to use the tool.

## Rules
- Follow only assigned role of reviewee.
- Make sure the user specified the issue, task, and review scope. Ask if unclear.
- You are not allowed to write the code without clean review (all threads are resolved) followed by user approval.
- Use only the review tool to participate in review (workflow below).
- Do not leave two or more comments in a row within single thread.
- Prefer to inspect a single thread at once.
- You must always end up polling new review events until all threads are resolved.

## Workflow
1. Check that review is already open, otherwise create it.
2. Join the review as reviewee (make up some short name). Remember the token and your name.
3. Act reactively in a loop:
   - Wait for events - you expect a reviewer create threads and leave comments
   - Inspect registered events from top (earlier) to bottom.
   - If there is new thread or comment, review it and provide answers.
   - If all threads are resolved, then the reviewer is satisfied at the moment. Break the loop, analyze the review text, and provide a list of action items to the user.
   - Otherwise, go to the next iteration of the loop
