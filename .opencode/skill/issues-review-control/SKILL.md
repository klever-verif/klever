---
name: issues-review-control
description: Use when users mentions `reviewctl` or `the review tool`, or you are taking part in review for a task within `.memory/issues`.
---

## Check for open review
Use `.opencode/skill/issues-review-control/scripts/reviewctl.py list` to see open reviews. Output shows the review `id` and the first line of the scope.

Example:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py list
```

## Create review
Create a review by passing the scope text as an argument or via stdin. The command returns an 8-character review id.

Examples:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py create "Scope line"
printf "Scope line\nDetails" | .opencode/skill/issues-review-control/scripts/reviewctl.py create
```

## Join review
Join an existing review by id. `--name` is required and must be unique per review. The token is `name-<id>`.

Example:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py join <review_id> --name alex --role reviewer
```

## Wait for events
Use your token to wait for new events. Returns when new events arrive.

Example:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py wait --token alex-abcdef12
```

## Create thread (reviewer only)
Reviewers can create new threads.

Example:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py threads create --token alex-abcdef12
```

## Comment thread
Add a comment to a thread; comments can be passed via args or stdin.

Examples:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py threads comment --token alex-abcdef12 -n 0 "Note"
printf "Note" | .opencode/skill/issues-review-control/scripts/reviewctl.py threads comment --token alex-abcdef12 -n 0
```

## View thread
Render a single thread for a review.

Example:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py threads view --token alex-abcdef12 -n 0
```

## Resolve thread (reviewer only)
Reviewers resolve their own threads, optionally with a comment.

Examples:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py threads resolve --token alex-abcdef12 -n 0
.opencode/skill/issues-review-control/scripts/reviewctl.py threads comment --token alex-abcdef12 -n 0 --resolve "Fix applied"
```

## View whole review
View all threads for a review using a token or the review id. The scope appears after the H1 header.

Examples:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py view --token alex-abcdef12
.opencode/skill/issues-review-control/scripts/reviewctl.py view --id abcdef12
```

## Close review (reviewer only)
Reviewers can close a review when all threads are resolved.

Example:
```bash
.opencode/skill/issues-review-control/scripts/reviewctl.py close --token alex-abcdef12
```
