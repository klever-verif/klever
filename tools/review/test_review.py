"""Tests for the review CLI."""

from __future__ import annotations

import sys
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from importlib import util
from io import StringIO
from pathlib import Path

import pytest

REVIEW_PATH = Path(__file__).resolve().parent / "review.py"
REVIEW_SPEC = util.spec_from_file_location("review", REVIEW_PATH)
if REVIEW_SPEC is None or REVIEW_SPEC.loader is None:
    raise RuntimeError("Unable to load review module")
review = util.module_from_spec(REVIEW_SPEC)
sys.modules["review"] = review
REVIEW_SPEC.loader.exec_module(review)


@pytest.fixture
def review_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a temporary review home directory."""
    monkeypatch.setenv(review.REVIEWCTL_HOME_ENV, str(tmp_path))
    return tmp_path


def run_command(argv: list[str]) -> tuple[int, str, str]:
    """Run the CLI and capture stdout/stderr."""
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = review.main(argv)
    return code, stdout.getvalue().rstrip("\n"), stderr.getvalue().rstrip("\n")


def test_create_and_join_flow(review_home: Path) -> None:
    """Create a review and join it."""
    code, stdout, stderr = run_command(["create", "--issue", "1", "--task", "0"])
    assert code == 0
    assert stderr == ""
    assert stdout == "review: issue=1 task=0 status=open"

    code, stdout, stderr = run_command(["join", "--issue", "1", "--task", "0", "--role", "reviewer"])
    assert code == 0
    assert stderr == ""
    lines = stdout.splitlines()
    assert lines[0].startswith("token: ")
    assert lines[1] == "threads: 0"
    assert lines[2] == "reviewers: 1"
    assert lines[3] == "reviewees: 0"


def test_create_same_issue_requires_single_task(review_home: Path) -> None:
    """Reject multiple tasks for the same issue."""
    run_command(["create", "--issue", "2", "--task", "1"])
    code, _stdout, stderr = run_command(["create", "--issue", "2", "--task", "2"])
    assert code == 1
    assert "issue 2 already has an active review" in stderr


def test_create_rejects_closed_review(review_home: Path) -> None:
    """Reject creating a closed review."""
    run_command(["create", "--issue", "3", "--task", "0"])
    code, stdout, _stderr = run_command(["join", "--issue", "3", "--task", "0", "--role", "reviewer"])
    token = stdout.splitlines()[0].split(" ", 1)[1]
    run_command(["close", "--token", token])
    code, _stdout, stderr = run_command(["create", "--issue", "3", "--task", "0"])
    assert code == 1
    assert "review is already closed" in stderr


def test_join_requires_create(review_home: Path) -> None:
    """Require review creation before joining."""
    code, _stdout, stderr = run_command(["join", "--issue", "5", "--task", "0", "--role", "reviewer"])
    assert code == 1
    assert "review does not exist" in stderr


def test_join_can_create_review(review_home: Path) -> None:
    """Allow join with review creation."""
    code, stdout, stderr = run_command(["join", "--issue", "6", "--task", "0", "--role", "reviewee", "--create"])
    assert code == 0
    assert stderr == ""
    assert stdout.splitlines()[0].startswith("token: ")


def test_join_closed_review_errors(review_home: Path) -> None:
    """Reject joining closed reviews."""
    run_command(["create", "--issue", "7", "--task", "0"])
    code, stdout, _stderr = run_command(["join", "--issue", "7", "--task", "0", "--role", "reviewer"])
    token = stdout.splitlines()[0].split(" ", 1)[1]
    run_command(["close", "--token", token])
    code, _stdout, stderr = run_command(["join", "--issue", "7", "--task", "0", "--role", "reviewee"])
    assert code == 1
    assert "review is already closed" in stderr


def test_join_name_pool_exhausted(review_home: Path) -> None:
    """Reject joins when name pool is exhausted."""
    run_command(["create", "--issue", "8", "--task", "0"])
    for _ in range(len(review.NAME_POOL)):
        code, _stdout, _stderr = run_command(["join", "--issue", "8", "--task", "0", "--role", "reviewer"])
        assert code == 0
    code, _stdout, stderr = run_command(["join", "--issue", "8", "--task", "0", "--role", "reviewee"])
    assert code == 1
    assert "name pool exhausted" in stderr


def test_comment_create_thread_by_reviewer(review_home: Path) -> None:
    """Allow reviewers to create threads via comments."""
    run_command(["create", "--issue", "10", "--task", "0"])
    code, stdout, _stderr = run_command(["join", "--issue", "10", "--task", "0", "--role", "reviewer"])
    token = stdout.splitlines()[0].split(" ", 1)[1]
    code, stdout, _stderr = run_command(["comment", "--token", token, "First comment"])
    assert code == 0
    assert stdout == "comments: 1"


def test_comment_rejects_reviewee_thread_creation(review_home: Path) -> None:
    """Reject reviewee thread creation."""
    run_command(["create", "--issue", "11", "--task", "0"])
    code, stdout, _stderr = run_command(["join", "--issue", "11", "--task", "0", "--role", "reviewee"])
    token = stdout.splitlines()[0].split(" ", 1)[1]
    code, _stdout, stderr = run_command(["comment", "--token", token, "Need a thread"])
    assert code == 1
    assert "reviewee cannot create" in stderr


def test_comment_nonexistent_thread_errors(review_home: Path) -> None:
    """Reject comments to non-existent threads."""
    run_command(["create", "--issue", "12", "--task", "0"])
    code, stdout, _stderr = run_command(["join", "--issue", "12", "--task", "0", "--role", "reviewer"])
    token = stdout.splitlines()[0].split(" ", 1)[1]
    code, _stdout, stderr = run_command(["comment", "--token", token, "--thread", "2", "Missing"])
    assert code == 1
    assert "thread does not exist" in stderr


def test_comment_resolved_thread_errors(review_home: Path) -> None:
    """Reject comments on resolved threads."""
    run_command(["create", "--issue", "13", "--task", "0"])
    code, stdout, _stderr = run_command(["join", "--issue", "13", "--task", "0", "--role", "reviewer"])
    token = stdout.splitlines()[0].split(" ", 1)[1]
    run_command(["comment", "--token", token, "Thread open"])
    run_command(["resolve", "--token", token, "--thread", "0"])
    code, _stdout, stderr = run_command(["comment", "--token", token, "--thread", "0", "Nope"])
    assert code == 1
    assert "thread is resolved" in stderr


def test_comment_invalid_token_errors(review_home: Path) -> None:
    """Reject comments with invalid tokens."""
    code, _stdout, stderr = run_command(["comment", "--token", "nope", "Hello"])
    assert code == 1
    assert "invalid token" in stderr


def test_resolve_requires_author(review_home: Path) -> None:
    """Only thread authors can resolve threads."""
    run_command(["create", "--issue", "14", "--task", "0"])
    reviewer_token = (
        run_command(["join", "--issue", "14", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee_token = (
        run_command(["join", "--issue", "14", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", reviewer_token, "Open thread"])
    code, _stdout, stderr = run_command(["resolve", "--token", reviewee_token, "--thread", "0"])
    assert code == 1
    assert "cannot resolve" in stderr


def test_resolve_missing_thread_errors(review_home: Path) -> None:
    """Reject resolves for missing threads."""
    run_command(["create", "--issue", "15", "--task", "0"])
    token = (
        run_command(["join", "--issue", "15", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["resolve", "--token", token, "--thread", "1"])
    assert code == 1
    assert "thread does not exist" in stderr


def test_resolve_accepts_optional_comment(review_home: Path) -> None:
    """Allow resolves with optional comment."""
    run_command(["create", "--issue", "16", "--task", "0"])
    token = (
        run_command(["join", "--issue", "16", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "Open thread"])
    code, stdout, _stderr = run_command(["resolve", "--token", token, "--thread", "0", "Final note"])
    assert code == 0
    assert stdout == "comments: 2"


def test_close_requires_resolved_threads(review_home: Path) -> None:
    """Reject closing when threads remain open."""
    run_command(["create", "--issue", "17", "--task", "0"])
    token = (
        run_command(["join", "--issue", "17", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "Open thread"])
    code, _stdout, stderr = run_command(["close", "--token", token])
    assert code == 1
    assert "all threads must be resolved" in stderr


def test_close_requires_reviewer(review_home: Path) -> None:
    """Allow only reviewers to close reviews."""
    run_command(["create", "--issue", "18", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "18", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee = (
        run_command(["join", "--issue", "18", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", reviewer, "Open thread"])
    run_command(["resolve", "--token", reviewer, "--thread", "0"])
    code, _stdout, stderr = run_command(["close", "--token", reviewee])
    assert code == 1
    assert "token cannot close" in stderr


def test_close_success_summary(review_home: Path) -> None:
    """Report summary stats on close."""
    run_command(["create", "--issue", "19", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "19", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", reviewer, "Open thread"])
    run_command(["resolve", "--token", reviewer, "--thread", "0"])
    code, stdout, _stderr = run_command(["close", "--token", reviewer])
    assert code == 0
    assert "review: issue=19 task=0 status=closed" in stdout
    assert "threads: 1 comments: 1 reviewers: 1 reviewees: 0" in stdout


def test_view_requires_token_or_issue_task(review_home: Path) -> None:
    """Require issue/task when no token is provided."""
    code, _stdout, stderr = run_command(["view", "--issue", "1"])
    assert code == 1
    assert "--issue and --task" in stderr


def test_view_rejects_token_and_issue(review_home: Path) -> None:
    """Reject using both token and issue/task."""
    run_command(["create", "--issue", "20", "--task", "0"])
    token = (
        run_command(["join", "--issue", "20", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["view", "--token", token, "--issue", "20", "--task", "0"])
    assert code == 1
    assert "use either --token" in stderr


def test_view_shows_threads(review_home: Path) -> None:
    """Show threads and comments in view output."""
    run_command(["create", "--issue", "21", "--task", "0"])
    token = (
        run_command(["join", "--issue", "21", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "First"])
    _code, stdout, _stderr = run_command(["view", "--token", token])
    assert "# issue-21: task-0" in stdout
    assert "## thread-0" in stdout
    assert "### [reviewer][" in stdout


def test_view_by_issue_task_after_close(review_home: Path) -> None:
    """Allow view by issue/task after close."""
    run_command(["create", "--issue", "22", "--task", "0"])
    token = (
        run_command(["join", "--issue", "22", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "First"])
    run_command(["resolve", "--token", token, "--thread", "0"])
    run_command(["close", "--token", token])
    code, stdout, _stderr = run_command(["view", "--issue", "22", "--task", "0"])
    assert code == 0
    assert "# issue-22: task-0" in stdout


def test_view_thread_missing_errors(review_home: Path) -> None:
    """Reject viewing missing threads."""
    run_command(["create", "--issue", "23", "--task", "0"])
    token = (
        run_command(["join", "--issue", "23", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["view", "--token", token, "--thread", "2"])
    assert code == 1
    assert "thread does not exist" in stderr


def test_list_outputs_active_reviews(review_home: Path) -> None:
    """List active reviews with counts."""
    run_command(["create", "--issue", "24", "--task", "0"])
    run_command(["create", "--issue", "25", "--task", "0"])
    code, stdout, _stderr = run_command(["list"])
    assert code == 0
    lines = stdout.splitlines()
    assert any("issue=24" in line for line in lines)
    assert any("issue=25" in line for line in lines)


def test_list_empty_writes_stderr(review_home: Path) -> None:
    """Write a message when no reviews exist."""
    code, stdout, stderr = run_command(["list"])
    assert code == 0
    assert stdout == ""
    assert "no active reviews" in stderr


def test_wait_errors_when_closed(review_home: Path) -> None:
    """Error when waiting on closed reviews."""
    run_command(["create", "--issue", "26", "--task", "0"])
    token = (
        run_command(["join", "--issue", "26", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["close", "--token", token])
    code, _stdout, stderr = run_command(["wait", "--token", token])
    assert code == 1
    assert "review is closed" in stderr


def test_wait_receives_thread_event(review_home: Path) -> None:
    """Wait should return new thread events."""
    run_command(["create", "--issue", "27", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "27", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee = (
        run_command(["join", "--issue", "27", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )

    events: list[str] = []

    def wait_thread() -> None:
        code, stdout, _stderr = run_command(["wait", "--token", reviewee])
        assert code == 0
        events.extend(stdout.splitlines())

    thread = threading.Thread(target=wait_thread)
    thread.start()
    time.sleep(0.2)

    run_command(["comment", "--token", reviewer, "Open thread"])
    thread.join(timeout=2)

    assert any("event: thread_created" in line for line in events)


def test_wait_consumes_multiple_events(review_home: Path) -> None:
    """Consume multiple events in one wait call."""
    run_command(["create", "--issue", "28", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "28", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee = (
        run_command(["join", "--issue", "28", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )

    run_command(["comment", "--token", reviewer, "Open thread"])
    run_command(["comment", "--token", reviewer, "--thread", "0", "Follow up"])

    code, stdout, _stderr = run_command(["wait", "--token", reviewee])
    assert code == 0
    lines = stdout.splitlines()
    assert any("event: thread_created" in line for line in lines)
    assert any("event: comment" in line for line in lines)


def test_wait_rejects_invalid_token(review_home: Path) -> None:
    """Reject waiting with invalid tokens."""
    code, _stdout, stderr = run_command(["wait", "--token", "bad-token"])
    assert code == 1
    assert "invalid token" in stderr


@pytest.mark.parametrize(
    "argv", [["create", "--issue", "-1", "--task", "0"], ["create", "--issue", "0", "--task", "-1"]]
)
def test_create_rejects_negative_values(review_home: Path, argv: list[str]) -> None:
    """Reject negative issue/task values."""
    code, _stdout, stderr = run_command(argv)
    assert code == 1
    assert "must be a non-negative" in stderr


def test_comment_requires_text(review_home: Path) -> None:
    """Reject empty comments."""
    run_command(["create", "--issue", "30", "--task", "0"])
    token = (
        run_command(["join", "--issue", "30", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["comment", "--token", token])
    assert code == 1
    assert "comment text is required" in stderr


def test_resolve_rejects_resolved_thread(review_home: Path) -> None:
    """Reject resolving an already resolved thread."""
    run_command(["create", "--issue", "31", "--task", "0"])
    token = (
        run_command(["join", "--issue", "31", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "Open thread"])
    run_command(["resolve", "--token", token, "--thread", "0"])
    code, _stdout, stderr = run_command(["resolve", "--token", token, "--thread", "0"])
    assert code == 1
    assert "thread is resolved" in stderr


def test_comment_rejects_closed_review(review_home: Path) -> None:
    """Reject comments on closed reviews."""
    run_command(["create", "--issue", "32", "--task", "0"])
    token = (
        run_command(["join", "--issue", "32", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "Open thread"])
    run_command(["resolve", "--token", token, "--thread", "0"])
    run_command(["close", "--token", token])
    code, _stdout, stderr = run_command(["comment", "--token", token, "--thread", "0", "Nope"])
    assert code == 1
    assert "review is closed" in stderr


def test_view_rejects_invalid_token(review_home: Path) -> None:
    """Reject view with invalid tokens."""
    code, _stdout, stderr = run_command(["view", "--token", "missing"])
    assert code == 1
    assert "invalid token" in stderr


def test_create_idempotent(review_home: Path) -> None:
    """Creating an open review is idempotent."""
    code, stdout, stderr = run_command(["create", "--issue", "33", "--task", "0"])
    assert code == 0
    assert stderr == ""
    assert stdout == "review: issue=33 task=0 status=open"

    code, stdout, stderr = run_command(["create", "--issue", "33", "--task", "0"])
    assert code == 0
    assert stderr == ""
    assert stdout == "review: issue=33 task=0 status=open"


def test_join_create_rejects_active_issue_task(review_home: Path) -> None:
    """Reject join --create when issue already has a task."""
    run_command(["create", "--issue", "34", "--task", "0"])
    code, _stdout, stderr = run_command(["join", "--issue", "34", "--task", "1", "--role", "reviewer", "--create"])
    assert code == 1
    assert "issue 34 already has an active review for task 0" in stderr


def test_join_token_format(review_home: Path) -> None:
    """Tokens include pool name and issue/task."""
    run_command(["create", "--issue", "35", "--task", "2"])
    code, stdout, _stderr = run_command(["join", "--issue", "35", "--task", "2", "--role", "reviewer"])
    assert code == 0
    token = stdout.splitlines()[0].split(" ", 1)[1]
    parts = token.split("-")
    assert len(parts) == 3
    name, issue, task = parts
    assert name in review.NAME_POOL
    assert issue == "35"
    assert task == "2"


@pytest.mark.parametrize(
    "argv",
    [
        ["join", "--issue", "-1", "--task", "0", "--role", "reviewer"],
        ["join", "--issue", "0", "--task", "-1", "--role", "reviewer"],
    ],
)
def test_join_rejects_negative_values(review_home: Path, argv: list[str]) -> None:
    """Reject negative issue/task values on join."""
    code, _stdout, stderr = run_command(argv)
    assert code == 1
    assert "must be a non-negative" in stderr


def test_comment_allows_reviewee_reply(review_home: Path) -> None:
    """Allow reviewees to comment in existing threads."""
    run_command(["create", "--issue", "36", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "36", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee = (
        run_command(["join", "--issue", "36", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", reviewer, "Open thread"])
    code, stdout, _stderr = run_command(["comment", "--token", reviewee, "--thread", "0", "Reply"])
    assert code == 0
    assert stdout == "comments: 2"


def test_comment_rejects_negative_thread(review_home: Path) -> None:
    """Reject comments with negative thread numbers."""
    run_command(["create", "--issue", "37", "--task", "0"])
    token = (
        run_command(["join", "--issue", "37", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["comment", "--token", token, "--thread", "-1", "Nope"])
    assert code == 1
    assert "thread must be a non-negative integer" in stderr


def test_resolve_allows_no_comment(review_home: Path) -> None:
    """Allow resolving threads without a comment."""
    run_command(["create", "--issue", "38", "--task", "0"])
    token = (
        run_command(["join", "--issue", "38", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "Open thread"])
    code, stdout, _stderr = run_command(["resolve", "--token", token, "--thread", "0"])
    assert code == 0
    assert stdout == "comments: 1"


def test_resolve_rejects_invalid_token(review_home: Path) -> None:
    """Reject resolves with invalid tokens."""
    code, _stdout, stderr = run_command(["resolve", "--token", "bad-token", "--thread", "0"])
    assert code == 1
    assert "invalid token" in stderr


def test_resolve_rejects_negative_thread(review_home: Path) -> None:
    """Reject resolving with negative thread numbers."""
    run_command(["create", "--issue", "39", "--task", "0"])
    token = (
        run_command(["join", "--issue", "39", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["resolve", "--token", token, "--thread", "-1"])
    assert code == 1
    assert "thread must be a non-negative integer" in stderr


def test_view_rejects_negative_thread(review_home: Path) -> None:
    """Reject view with negative thread numbers."""
    run_command(["create", "--issue", "40", "--task", "0"])
    token = (
        run_command(["join", "--issue", "40", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    code, _stdout, stderr = run_command(["view", "--token", token, "--thread", "-1"])
    assert code == 1
    assert "thread must be a non-negative integer" in stderr


def test_view_rejects_missing_review(review_home: Path) -> None:
    """Reject viewing a missing review."""
    code, _stdout, stderr = run_command(["view", "--issue", "41", "--task", "0"])
    assert code == 1
    assert "review does not exist" in stderr


def test_view_thread_filter(review_home: Path) -> None:
    """View should filter to a single thread."""
    run_command(["create", "--issue", "42", "--task", "0"])
    token = (
        run_command(["join", "--issue", "42", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", token, "First thread"])
    run_command(["comment", "--token", token, "Second thread"])
    code, stdout, _stderr = run_command(["view", "--token", token, "--thread", "0"])
    assert code == 0
    assert "## thread-0" in stdout
    assert "## thread-1" not in stdout


def test_list_excludes_closed_reviews(review_home: Path) -> None:
    """Do not list closed reviews."""
    run_command(["create", "--issue", "43", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "43", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["close", "--token", reviewer])
    run_command(["create", "--issue", "44", "--task", "0"])
    code, stdout, _stderr = run_command(["list"])
    assert code == 0
    assert "issue=44" in stdout
    assert "issue=43" not in stdout


def test_close_rejects_already_closed(review_home: Path) -> None:
    """Reject closing an already closed review."""
    run_command(["create", "--issue", "45", "--task", "0"])
    token = (
        run_command(["join", "--issue", "45", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["close", "--token", token])
    code, _stdout, stderr = run_command(["close", "--token", token])
    assert code == 1
    assert "review is closed" in stderr


def test_wait_receives_resolve_event_with_comment(review_home: Path) -> None:
    """Wait returns resolved events with payload."""
    run_command(["create", "--issue", "46", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "46", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee = (
        run_command(["join", "--issue", "46", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )
    run_command(["comment", "--token", reviewer, "Open thread"])
    run_command(["resolve", "--token", reviewer, "--thread", "0", "Done"])
    code, stdout, _stderr = run_command(["wait", "--token", reviewee])
    assert code == 0
    lines = stdout.splitlines()
    resolved_line = next(line for line in lines if "event: thread_resolved" in line)
    assert "thread:0" in resolved_line
    assert f"author:{reviewer}" in resolved_line
    assert "count:2" in resolved_line
    assert "with_comment:1" in resolved_line


def test_wait_receives_review_closed_event(review_home: Path) -> None:
    """Wait returns review closed events."""
    run_command(["create", "--issue", "47", "--task", "0"])
    reviewer = (
        run_command(["join", "--issue", "47", "--task", "0", "--role", "reviewer"])[1].splitlines()[0].split(" ", 1)[1]
    )
    reviewee = (
        run_command(["join", "--issue", "47", "--task", "0", "--role", "reviewee"])[1].splitlines()[0].split(" ", 1)[1]
    )
    events: list[str] = []

    def wait_for_close() -> None:
        code, stdout, _stderr = run_command(["wait", "--token", reviewee])
        assert code == 0
        events.extend(stdout.splitlines())

    thread = threading.Thread(target=wait_for_close)
    thread.start()
    time.sleep(0.2)
    run_command(["close", "--token", reviewer])
    thread.join(timeout=2)

    assert not thread.is_alive()
    closed_line = next(line for line in events if "event: review_closed" in line)
    assert f"author:{reviewer}" in closed_line
    assert "thread:-" in closed_line
    assert "count:-" in closed_line
