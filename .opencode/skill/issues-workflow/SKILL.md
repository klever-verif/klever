---
name: issues-workflow
description: Use when you need to do issue/task managing job within `.memory/issues`.
---

`.memory/issues` is a folder for Markdown-based task management.

## Naming
- Issue folder: `.memory/issues/ISSUE-<n>-<short-kebab>` (n = 1, 2, ...)
- Context: `.memory/issues/<issue>/CONTEXT.md`
- Plan: `.memory/issues/<issue>/PLAN.md`
- Task: `.memory/issues/<issue>/TASK-<m>-<short-kebab>.md` (e.g. issue=42, task=0, m=4200; issue=3, task=12, m=312)

## Templates
- Plan: `.memory/templates/PLAN.md`
- Task: `.memory/templates/TASK.md`

## Common Rules
- `.memory/issues` tracks work as one folder per issue.
- Directory and content are persistent.
- Use repo-root paths in backticks for cross-references (no Markdown links).
- Keep text short, concrete, and free of contradictions.
- Use only sections presented in templates (NO CUSTOM SECTIONS).
- Update any status only AFTER finishing current edits.
- All files with status `done` are read-only.

## Review Rules
- The user specifies whether you act as reviewer or reviewee. Ask if missing and follow only that role.
- Reviewer workflow relies on skill `mart-reviewer`
- Reviewee workflow relies on skill `mart-reviewee`

## Workflow
1. Setup phase
   - Create a new folder for issue
   - If user creates themselves, then check for naming pattern
   - If agent creates, then agent must ask purpose of the issue
   - Issue-related git branch is created
2. Exploration phase
   - Create `CONTEXT.md` in free form (no template) within issue folder
   - User may create raw version themself
   - Agent performs user interview regarding needs, purpose, features, behaviors, stories, etc.
   - Purpose is to collect as much complete relevant context as possible
   - Marked as `done` before next step
3. Coarse planning phase
   - Agent derives `PLAN.md` from `CONTEXT.md` filling the template and clarify details with user if needed
   - Purpose is to create a complete, contradiction-free implementation plan
   - Important to define concrete and clear exit criteria
   - Plan outlines a list of concrete tasks (every task is ~2-4 SWE man-hours)
   - Marked with status `wip` until all tasks are done
4. Fine planning phase
   - Agent iteratively moves through plan creating and filling `TASK-` files according to template.
   - Make sure all steps are agent-ready instructions (LLM-friendly): explicit steps, repo-root paths, commands, and DoD.
   - `PLAN.md` might be refined
   - All tasks marked with status `todo`
5. Implementation phase
   - User specifies what task to implement
   - Agent implements the task using task implementation flow below
   - Back to the loop start until all tasks are done
6. Exit phase
   - All branch changes reviewed against original plan (according review rules)
   - Check DoD and deliverables
   - After user approve plan marked as `done`

### Task Implementation
1. Audit phase
   - User specifies what task to implement, agent sets status `wip`
   - Agent performs audit of task (completeness, clearness, no contradictions)
   - After plan is approved implementation started
2. Coding phase
   - Agent goes through task implementation process step by step
   - During the phase, the agent records notes within the task file to capture important findings or decisions
   - Agent may exit phase when DoD are met, lints are clear, tests are green
3. Review phase
   - Review follows the implementation (according review rules)
   - User spawns reviewers and may do review themself
   - Reviewee must fill notes with review decisions during after-review fixes
   - Review is iterative: threads open - discuss - threads resolved - fix - threads open - ...
   - Review is done until reviewer is satisfied, all threads are resolved and review is marked as closed
4. Signoff phase
   - Reviewee must analyze the whole review and make sure all important information and decisions are transferred to task notes, code comments, documentation, etc.
   - User approves completion of the task, task is marked as `done`, result is committed to git
