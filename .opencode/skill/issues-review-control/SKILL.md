---
name: issues-review-control
description: Use when the user mentions `reviewctl` or the review tool, or asks for a formal or multi-agent review.
---

## Check for open review
Use `<skill_dir>/scripts/reviewctl.py list` to see open reviews. Output shows the review `id`, status, open thread count, comment count, and the first line of the scope.

Example:
```bash
<skill_dir>/scripts/reviewctl.py list
```

## Create review
Create a review by passing the scope text as an argument or via stdin. The command prints the review id you provided.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py create --id myreview "Scope line"
printf "Scope line\nDetails" | <skill_dir>/scripts/reviewctl.py create --id myreview
```

## Join review
Join an existing review by id. `--name` is required and must be unique per review. The token is `name-<id>`.

Example:
```bash
<skill_dir>/scripts/reviewctl.py join <review_id> --name alex --role reviewer
```

## Wait for events
Use your token to wait for new events. Returns when new events arrive.

Example:
```bash
<skill_dir>/scripts/reviewctl.py wait --user alex-abcdef12
```

## Create thread (reviewer only)
Reviewers can create new threads.

Example:
```bash
<skill_dir>/scripts/reviewctl.py threads create --user alex-abcdef12
```

## Comment thread
Add a comment to a thread; comments can be passed via args or stdin.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py threads comment --user alex-abcdef12 --thread 0 "Note"
printf "Note" | <skill_dir>/scripts/reviewctl.py threads comment --user alex-abcdef12 --thread 0
```

## View thread
Render a single thread for a review.

Example:
```bash
<skill_dir>/scripts/reviewctl.py threads view --user alex-abcdef12 --thread 0
```

## Resolve thread (reviewer only)
Reviewers resolve their own threads, optionally with a comment.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py threads resolve --user alex-abcdef12 --thread 0
<skill_dir>/scripts/reviewctl.py threads comment --user alex-abcdef12 --thread 0 --resolve "Fix applied"
```

## View whole review
View all threads for a review using a participant token or the review id. The scope appears after the H1 header.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py view --user alex-abcdef12
<skill_dir>/scripts/reviewctl.py view --review abcdef12
```
## Review status
Show review status and counts using a participant token or review id.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py status --user alex-abcdef12
<skill_dir>/scripts/reviewctl.py status --review abcdef12
```

## List threads
List threads for a review using a participant token or review id.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py threads list --user alex-abcdef12
<skill_dir>/scripts/reviewctl.py threads list --review abcdef12
```

## Close review (reviewer only)
Reviewers can close a review when all threads are resolved.

Example:
```bash
<skill_dir>/scripts/reviewctl.py close --user alex-abcdef12
```

## Help
Any command supports `-h` for help, including nested commands.

Examples:
```bash
<skill_dir>/scripts/reviewctl.py -h
<skill_dir>/scripts/reviewctl.py threads -h
<skill_dir>/scripts/reviewctl.py threads comment -h
```
