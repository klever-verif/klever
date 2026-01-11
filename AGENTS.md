# Repository Guidelines

## Project Structure & Modules
- Development container configuration in `.devcontainer`
- Python package lives in `src/klever`

## Environment & Tooling Notes
- You are running inside isolated Docker devcontainer
- Dependency and Python version management use `uv`; avoid `pip` unless justified.
- Metadata: `pyproject.toml` (tooling, dependencies), `uv.lock` (locked deps)
- `pre-commit` is used to enforce formatting/lint and code quality checks
- `ruff` is used for linting and formatting
- `pyright` is used for type checks
- `pytest` is used for testing
- Current python version is specified in @.python-version

## Build, Test, and Dev Commands
- Use `Makefile` in root to perform code management (lint, format, check, etc.)
- Available commands are available with `make help`
- Prefer `uv run <command>` if invoking tools directly.

## Coding Style
- TBD

## Testing Guidelines
- TBD

## Commit & PR Guidelines
- Git history follows Conventional Commits (`feat: ...`, `fix: ...`, `ci: ...`). Match that style; scope is optional but encouraged.
- Keep commits focused and linted; run `make check` before committing.
