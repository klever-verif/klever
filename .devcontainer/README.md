# Devcontainer Overview

Custom Ubuntu 24.04 devcontainer with ready-to-use tooling for RTL verification and Python work.

## Workspace and mounts

- Mounts the repo parent so Git worktrees under the same parent work.
  - `workspaceMount`: `source=${localWorkspaceFolder}/..,target=/workspaces,type=bind`
  - `workspaceFolder`: `/workspaces/${localWorkspaceFolderBasename}`
- Persists CLI agent auth and sessions by mounting host state:
  - Codex: `~/.codex`
  - Claude: `~/.claude` and `~/.claude.json`
  - OpenCode: `~/.config/opencode`, `~/.local/share/opencode`, `~/.cache/opencode`
- `initializeCommand` creates these paths so first-run mounts succeed.

## Image and tooling

- Base image: Ubuntu 24.04 (chosen as a reasonable default).
- Installs system tools: `git`, `curl`, `make`, `g++`, `mold`, `ccache`, `z3`, `gtkwave`, `npm`, `openssh-client`, `bash-completion`.
- Installs Verilator at `/opt/verilator` for RTL/cocotb workflows.
- Installs `slang-server` at `/opt/slang-server` for SystemVerilog language services.
- Installs CLI agents (`@openai/codex`, Claude Code, OpenCode) for out-of-box access.
- Installs `uv` for Python tooling in `~/.local/bin`.
- Extends `PATH` with `~/.local/bin`, Verilator, and slang-server.

## Container behavior

- Uses host networking (`--network=host`) so host VPN routing works.
- Runs as `ubuntu` and keeps UID/GID aligned with the host.
- Marks the workspace as a safe Git directory on create.
- Runs `make bootstrap` on start to install Python via `uv`, sync deps, and set pre-commit hooks.

## VS Code extensions

Recommends extensions for Python, Ruff, TOML, YAML, Markdown, Slang, and OpenCode.