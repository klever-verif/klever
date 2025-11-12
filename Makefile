# Use bash and fail fast
.DEFAULT_GOAL := help

## Bootstrap project env from lockfile
bootstrap:
	uv python install
	uv sync --locked --all-extras --dev
	uv run pre-commit install --hook-type commit-msg --hook-type pre-commit

## Format with Ruff
format:
	uv run ruff format .

## Check formatting
format-check:
	uv run ruff check --fix .

## Lint (Ruff)
lint:
	uv run ruff check .

## Fix linting
lint-fix:
	uv run ruff check --fix .

## Type check (Pyright via PyPI wrapper)
type-check:
	uv run pyright

## Run tests
test:
	uv run pytest -n auto

## Run tests with coverage
test-coverage:
	uv run pytest -n auto --cov=src --no-cov-on-fail --cov-report term-missing --cov-report html

## Pre-commit on all files
pre-commit:
	uv run pre-commit run --all-files

## Check commit messages
check-commit:
	uv run cz check --commit-msg-file .git/COMMIT_EDITMSG

## Check everything
check: format-check lint type-check check-commit

## Update UV lockfile
lock:
	uv lock

## Fix everything
fix: format lint-fix lock

## Clean up
clean:
	rm -rf .cache .ruff_cache .pytest_cache **/__pycache__ dist htmlcov .coverage site

## Show targets
help:
	@awk 'BEGIN{tabstop=8;targetcol=32} /^##/{desc=$$0;sub(/^##[ ]*/,"",desc);next} /^[a-zA-Z0-9_-]+:/{name=$$1;sub(/:.*/,"",name);col=length(name);pos=col;ntabs=0;while(pos<targetcol){ntabs++;pos=int(pos/tabstop+1)*tabstop}printf "%s",name;for(i=0;i<ntabs;i++)printf "\t";printf "%s\n",desc;desc=""}' Makefile
