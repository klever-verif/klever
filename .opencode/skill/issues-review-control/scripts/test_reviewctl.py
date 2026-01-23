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

REVIEW_PATH = Path(__file__).resolve().parent / "reviewctl.py"
REVIEW_SPEC = util.spec_from_file_location("reviewctl", REVIEW_PATH)
if REVIEW_SPEC is None or REVIEW_SPEC.loader is None:
    raise RuntimeError("Unable to load review module")
reviewctl = util.module_from_spec(REVIEW_SPEC)
sys.modules["reviewctl"] = reviewctl
REVIEW_SPEC.loader.exec_module(reviewctl)


@pytest.fixture
def review_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a temporary review home directory."""
    monkeypatch.setenv(reviewctl.REVIEWCTL_HOME_ENV, str(tmp_path))
    return tmp_path


def run_command(argv: list[str]) -> tuple[int, str, str]:
    """Run the CLI and capture stdout/stderr."""
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = reviewctl.main(argv)
    return code, stdout.getvalue().rstrip("\n"), stderr.getvalue().rstrip("\n")


_review_counter: list[int] = [0]


def create_review(scope: str, review_id: str | None = None) -> str:
    """Create a review and return its id."""
    if review_id is None:
        _review_counter[0] += 1
        review_id = f"test-{_review_counter[0]:04d}"
    code, stdout, stderr = run_command(["create", "--id", review_id, scope])
    assert code == 0
    assert stderr == ""
    return stdout


def join_review(review_id: str, name: str, role: str) -> str:
    """Join a review and return the token."""
    code, stdout, stderr = run_command(["join", review_id, "--name", name, "--role", role])
    assert code == 0
    assert stderr == ""
    return stdout


def test_create_and_join_flow(review_home: Path) -> None:
    """Create a review and join it."""
    code, stdout, stderr = run_command(["create", "--id", "my-review", "Review scope"])
    assert code == 0
    assert stderr == ""
    review_id = stdout
    assert review_id == "my-review"

    code, stdout, stderr = run_command(["join", review_id, "--name", "alex", "--role", "reviewer"])
    assert code == 0
    assert stderr == ""
    assert stdout == f"alex-{review_id}"


def test_create_rejects_duplicate_id(review_home: Path) -> None:
    """Reject creating a review with an existing ID."""
    create_review("Scope alpha", review_id="dup-test")
    code, _stdout, stderr = run_command(["create", "--id", "dup-test", "Scope beta"])
    assert code == 1
    assert "review with this ID already exists" in stderr


def test_create_requires_scope_text(review_home: Path) -> None:
    """Reject creating a review without scope text."""
    code, _stdout, stderr = run_command(["create", "--id", "no-scope"])
    assert code == 1
    assert "scope text is required" in stderr


def test_create_rejects_invalid_id_format(review_home: Path) -> None:
    """Reject creating a review with invalid ID format."""
    code, _stdout, stderr = run_command(["create", "--id", "invalid id!", "Scope"])
    assert code == 1
    assert "alphanumeric characters, underscores, or dashes" in stderr


def test_join_requires_create(review_home: Path) -> None:
    """Require review creation before joining."""
    code, _stdout, stderr = run_command(["join", "deadbeef", "--name", "alex", "--role", "reviewer"])
    assert code == 1
    assert "review does not exist" in stderr


def test_join_allows_unique_names(review_home: Path) -> None:
    """Allow joining with unique names."""
    review_id = create_review("Scope join")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    assert reviewer == f"alex-{review_id}"
    assert reviewee == f"sam-{review_id}"


def test_join_closed_review_errors(review_home: Path) -> None:
    """Reject joining closed reviews."""
    review_id = create_review("Scope closed")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["close", "--user", token])
    code, _stdout, stderr = run_command(["join", review_id, "--name", "sam", "--role", "reviewee"])
    assert code == 1
    assert "review is closed" in stderr


def test_join_name_taken(review_home: Path) -> None:
    """Reject joins when name is already taken."""
    review_id = create_review("Scope names")
    join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["join", review_id, "--name", "alex", "--role", "reviewee"])
    assert code == 1
    assert "name is already taken" in stderr


def test_comment_create_thread_by_reviewer(review_home: Path) -> None:
    """Allow reviewers to create threads."""
    review_id = create_review("Scope threads")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    code, stdout, _stderr = run_command(["threads", "comment", "--user", token, "-n", "0", "First comment"])
    assert code == 0
    assert stdout == "thread: 0 comments: 1"


def test_comment_rejects_reviewee_thread_creation(review_home: Path) -> None:
    """Reject reviewee thread creation."""
    review_id = create_review("Scope reviewee")
    token = join_review(review_id, "alex", "reviewee")
    code, _stdout, stderr = run_command(["threads", "create", "--user", token])
    assert code == 1
    assert "reviewee cannot create" in stderr


def test_comment_nonexistent_thread_errors(review_home: Path) -> None:
    """Reject comments to non-existent threads."""
    review_id = create_review("Scope missing thread")
    token = join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["threads", "comment", "--user", token, "-n", "2", "Missing"])
    assert code == 1
    assert "thread does not exist" in stderr


def test_comment_resolved_thread_errors(review_home: Path) -> None:
    """Reject comments on resolved threads."""
    review_id = create_review("Scope resolved")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "Thread open"])
    run_command(["threads", "resolve", "--user", token, "-n", "0", "--force"])
    code, _stdout, stderr = run_command(["threads", "comment", "--user", token, "-n", "0", "Nope"])
    assert code == 1
    assert "thread is resolved" in stderr


def test_comment_invalid_token_errors(review_home: Path) -> None:
    """Reject comments with invalid tokens."""
    code, _stdout, stderr = run_command(["threads", "comment", "--user", "nope", "-n", "0", "Hello"])
    assert code == 1
    assert "invalid user id" in stderr


def test_all_threads_resolved_event(review_home: Path) -> None:
    """Emit an all threads resolved event when closing threads."""
    review_id = create_review("Scope all resolved")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Note"])
    run_command(["threads", "comment", "--user", reviewee, "-n", "0", "Reply"])
    run_command(["threads", "resolve", "--user", reviewer, "-n", "0"])
    code, stdout, _stderr = run_command(["wait", "--user", reviewee])
    assert code == 0
    assert any("event: all_threads_resolved" in line for line in stdout.splitlines())


def test_resolve_requires_author(review_home: Path) -> None:
    """Only thread authors can resolve threads."""
    review_id = create_review("Scope author")
    reviewer_token = join_review(review_id, "alex", "reviewer")
    reviewee_token = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer_token])
    run_command(["threads", "comment", "--user", reviewer_token, "-n", "0", "Open thread"])
    code, _stdout, stderr = run_command(["threads", "resolve", "--user", reviewee_token, "-n", "0"])

    assert code == 1
    assert "cannot resolve" in stderr


def test_resolve_missing_thread_errors(review_home: Path) -> None:
    """Reject resolves for missing threads."""
    review_id = create_review("Scope missing resolve")
    token = join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["threads", "resolve", "--user", token, "-n", "1"])
    assert code == 1
    assert "thread does not exist" in stderr


def test_resolve_accepts_optional_comment(review_home: Path) -> None:
    """Allow resolving threads with a comment."""
    review_id = create_review("Scope resolve comment")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "comment", "--user", reviewee, "-n", "0", "Reply"])
    code, stdout, _stderr = run_command(
        ["threads", "comment", "--user", reviewer, "-n", "0", "--resolve", "Final note"]
    )
    assert code == 0
    assert stdout == "thread: 0 comments: 3"


def test_close_requires_resolved_threads(review_home: Path) -> None:
    """Reject closing when threads remain open."""
    review_id = create_review("Scope close threads")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "Open thread"])
    code, _stdout, stderr = run_command(["close", "--user", token])
    assert code == 1
    assert "all threads must be resolved" in stderr


def test_close_requires_reviewer(review_home: Path) -> None:
    """Allow only reviewers to close reviews."""
    review_id = create_review("Scope close reviewer")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "resolve", "--user", reviewer, "-n", "0"])
    code, _stdout, stderr = run_command(["close", "--user", reviewee])
    assert code == 1
    assert "user cannot close" in stderr


def test_close_success_summary(review_home: Path) -> None:
    """Report summary stats on close."""
    review_id = create_review("Scope close summary")
    reviewer = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "resolve", "--user", reviewer, "-n", "0", "--force"])
    code, stdout, _stderr = run_command(["close", "--user", reviewer])
    assert code == 0
    assert f"review: id={review_id} status=closed" in stdout
    assert "threads: 1 comments: 1 reviewers: 1 reviewees: 0" in stdout


def test_view_requires_token_or_id(review_home: Path) -> None:
    """Require an id when no token is provided."""
    code, _stdout, stderr = run_command(["view"])
    assert code == 1
    assert "--id is required" in stderr


def test_view_rejects_token_and_id(review_home: Path) -> None:
    """Reject using both token and id."""
    review_id = create_review("Scope view options")
    token = join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["view", "--user", token, "--id", review_id])
    assert code == 1
    assert "use either --user" in stderr


def test_view_shows_threads(review_home: Path) -> None:
    """Show threads and comments in view output."""
    scope = "Scope view threads"
    review_id = create_review(scope)
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "First"])
    _code, stdout, _stderr = run_command(["view", "--user", token])
    lines = stdout.splitlines()
    assert lines[0] == f"# review-{review_id} open"
    assert lines[1] == scope
    assert "## thread-0 open" in stdout
    assert "### [reviewer][" in stdout


def test_view_by_id_after_close(review_home: Path) -> None:
    """Allow view by id after close."""
    review_id = create_review("Scope view closed")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "First"])
    run_command(["threads", "resolve", "--user", token, "-n", "0", "--force"])
    run_command(["close", "--user", token])
    code, stdout, _stderr = run_command(["view", "--id", review_id])
    assert code == 0
    assert f"# review-{review_id} closed" in stdout


def test_view_thread_missing_errors(review_home: Path) -> None:
    """Reject viewing missing threads."""
    review_id = create_review("Scope view thread")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    code, _stdout, stderr = run_command(["threads", "view", "--user", token, "-n", "2"])
    assert code == 1
    assert "thread does not exist" in stderr


def test_list_outputs_active_reviews(review_home: Path) -> None:
    """List active reviews with status, thread count, comment count, and scope."""
    first_id = create_review("Scope 24\nDetails")
    second_id = create_review("Scope 25")
    code, stdout, _stderr = run_command(["list"])
    assert code == 0
    lines = stdout.splitlines()
    assert any(f"review: id={first_id} status=open open_threads=0 comments=0 scope=Scope 24" == line for line in lines)
    assert any(f"review: id={second_id} status=open open_threads=0 comments=0 scope=Scope 25" == line for line in lines)


def test_list_empty_writes_stderr(review_home: Path) -> None:
    """Write a message when no reviews exist."""
    code, stdout, stderr = run_command(["list"])
    assert code == 0
    assert stdout == ""
    assert "no active reviews" in stderr


def test_wait_errors_when_closed(review_home: Path) -> None:
    """Error when waiting on closed reviews."""
    review_id = create_review("Scope wait closed")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["close", "--user", token])
    code, _stdout, stderr = run_command(["wait", "--user", token])
    assert code == 1
    assert "review is closed" in stderr


def test_wait_receives_thread_event(review_home: Path) -> None:
    """Wait should return new thread events."""
    review_id = create_review("Scope wait thread")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")

    events: list[str] = []

    def wait_thread() -> None:
        code, stdout, _stderr = run_command(["wait", "--user", reviewee])
        assert code == 0
        events.extend(stdout.splitlines())

    thread = threading.Thread(target=wait_thread)
    thread.start()
    time.sleep(0.2)

    run_command(["threads", "create", "--user", reviewer])
    thread.join(timeout=2)

    assert any("event: thread_created" in line for line in events)


def test_wait_consumes_multiple_events(review_home: Path) -> None:
    """Consume multiple events in one wait call."""
    review_id = create_review("Scope wait events")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")

    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Follow up"])

    code, stdout, _stderr = run_command(["wait", "--user", reviewee])
    assert code == 0
    lines = stdout.splitlines()
    assert any("event: thread_created" in line for line in lines)
    assert any("event: comment" in line for line in lines)


def test_wait_rejects_invalid_token(review_home: Path) -> None:
    """Reject waiting with invalid tokens."""
    code, _stdout, stderr = run_command(["wait", "--user", "bad-token"])
    assert code == 1
    assert "invalid user id" in stderr


def test_view_includes_scope_lines(review_home: Path) -> None:
    """Include scope lines directly after the header."""
    scope = "Scope header\nDetails line"
    review_id = create_review(scope)
    code, stdout, _stderr = run_command(["view", "--id", review_id])
    assert code == 0
    lines = stdout.splitlines()
    assert lines[0] == f"# review-{review_id} open"
    assert lines[1] == "Scope header"
    assert lines[2] == "Details line"


def test_comment_requires_text(review_home: Path) -> None:
    """Reject empty comments."""
    review_id = create_review("Scope comment text")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    code, _stdout, stderr = run_command(["threads", "comment", "--user", token, "-n", "0"])
    assert code == 1
    assert "comment text is required" in stderr


def test_resolve_rejects_resolved_thread(review_home: Path) -> None:
    """Reject resolving an already resolved thread."""
    review_id = create_review("Scope resolve resolved")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "Open thread"])
    run_command(["threads", "resolve", "--user", token, "-n", "0", "--force"])
    code, _stdout, stderr = run_command(["threads", "resolve", "--user", token, "-n", "0", "--force"])
    assert code == 1
    assert "thread is resolved" in stderr


def test_status_reports_counts(review_home: Path) -> None:
    """Report status counts for a review."""
    review_id = create_review("Scope status")
    reviewer = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "First"])
    code, stdout, _stderr = run_command(["status", "--id", review_id])
    assert code == 0
    assert f"review: id={review_id} status=open" in stdout
    assert "threads: open=1 resolved=0 comments=1" in stdout
    assert "participants: reviewers=1 reviewees=0" in stdout


def test_threads_list_shows_status(review_home: Path) -> None:
    """List threads with status output."""
    review_id = create_review("Scope threads list")
    reviewer = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Note"])
    code, stdout, _stderr = run_command(["threads", "list", "--id", review_id])
    assert code == 0
    assert "thread-0:" in stdout
    assert "status=open" in stdout


def test_comment_rejects_closed_review(review_home: Path) -> None:
    """Reject comments on closed reviews."""
    review_id = create_review("Scope comment closed")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "Open thread"])
    run_command(["threads", "resolve", "--user", token, "-n", "0", "--force"])
    run_command(["close", "--user", token])
    code, _stdout, stderr = run_command(["threads", "comment", "--user", token, "-n", "0", "Nope"])
    assert code == 1
    assert "review is closed" in stderr


def test_view_rejects_invalid_token(review_home: Path) -> None:
    """Reject view with invalid tokens."""
    code, _stdout, stderr = run_command(["view", "--user", "missing"])
    assert code == 1
    assert "invalid user id" in stderr


def test_create_allows_multiword_scope(review_home: Path) -> None:
    """Preserve multi-word scope text."""
    scope = "Multi word scope"
    review_id = create_review(scope)
    code, stdout, _stderr = run_command(["view", "--id", review_id])
    assert code == 0
    assert f"# review-{review_id} open" in stdout
    assert scope in stdout


def test_join_allows_same_name_on_different_reviews(review_home: Path) -> None:
    """Allow the same name across different reviews."""
    first_id = create_review("Scope first")
    second_id = create_review("Scope second")
    first_token = join_review(first_id, "alex", "reviewer")
    second_token = join_review(second_id, "alex", "reviewer")
    assert first_token == f"alex-{first_id}"
    assert second_token == f"alex-{second_id}"


def test_join_token_format(review_home: Path) -> None:
    """Tokens include name and review id."""
    review_id = create_review("Scope token format")
    token = join_review(review_id, "alex", "reviewer")
    assert token == f"alex-{review_id}"


def test_join_rejects_empty_name(review_home: Path) -> None:
    """Reject join when name is empty."""
    review_id = create_review("Scope empty name")
    code, _stdout, stderr = run_command(["join", review_id, "--name", "", "--role", "reviewer"])
    assert code == 1
    assert "name is required" in stderr


def test_comment_allows_reviewee_reply(review_home: Path) -> None:
    """Allow reviewees to comment in existing threads."""
    review_id = create_review("Scope reviewee reply")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    code, stdout, _stderr = run_command(["threads", "comment", "--user", reviewee, "-n", "0", "Reply"])
    assert code == 0
    assert stdout == "thread: 0 comments: 2"


def test_comment_rejects_negative_thread(review_home: Path) -> None:
    """Reject comments with negative thread numbers."""
    review_id = create_review("Scope negative thread")
    token = join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["threads", "comment", "--user", token, "-n", "-1", "Nope"])
    assert code == 1
    assert "thread must be a non-negative integer" in stderr


def test_resolve_allows_no_comment(review_home: Path) -> None:
    """Allow resolving threads without a comment."""
    review_id = create_review("Scope resolve no comment")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "comment", "--user", reviewee, "-n", "0", "Reply"])
    code, stdout, _stderr = run_command(["threads", "resolve", "--user", reviewer, "-n", "0"])
    assert code == 0
    assert stdout == "thread: 0 comments: 2"


def test_resolve_rejects_invalid_token(review_home: Path) -> None:
    """Reject resolves with invalid tokens."""
    code, _stdout, stderr = run_command(["threads", "resolve", "--user", "bad-token", "-n", "0"])
    assert code == 1
    assert "invalid user id" in stderr


def test_resolve_rejects_negative_thread(review_home: Path) -> None:
    """Reject resolving with negative thread numbers."""
    review_id = create_review("Scope resolve negative")
    token = join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["threads", "resolve", "--user", token, "-n", "-1"])
    assert code == 1
    assert "thread must be a non-negative integer" in stderr


def test_view_rejects_negative_thread(review_home: Path) -> None:
    """Reject view with negative thread numbers."""
    review_id = create_review("Scope view negative")
    token = join_review(review_id, "alex", "reviewer")
    code, _stdout, stderr = run_command(["threads", "view", "--user", token, "-n", "-1"])
    assert code == 1
    assert "thread must be a non-negative integer" in stderr


def test_view_rejects_missing_review(review_home: Path) -> None:
    """Reject viewing a missing reviewctl."""
    code, _stdout, stderr = run_command(["view", "--id", "deadbeef"])
    assert code == 1
    assert "review does not exist" in stderr


def test_view_thread_filter(review_home: Path) -> None:
    """View should filter to a single thread."""
    review_id = create_review("Scope view filter")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "0", "First thread"])
    run_command(["threads", "create", "--user", token])
    run_command(["threads", "comment", "--user", token, "-n", "1", "Second thread"])
    code, stdout, _stderr = run_command(["threads", "view", "--user", token, "-n", "0"])
    assert code == 0
    assert "## thread-0 open" in stdout
    assert "## thread-1" not in stdout


def test_list_excludes_closed_reviews(review_home: Path) -> None:
    """Do not list closed reviews."""
    closed_id = create_review("Scope closed list")
    reviewer = join_review(closed_id, "alex", "reviewer")
    run_command(["close", "--user", reviewer])
    open_id = create_review("Scope open list")
    code, stdout, _stderr = run_command(["list"])
    assert code == 0
    assert f"review: id={open_id}" in stdout
    assert f"review: id={closed_id}" not in stdout


def test_list_all_includes_closed_reviews(review_home: Path) -> None:
    """List all reviews including closed ones with --all flag."""
    closed_id = create_review("Scope closed all")
    reviewer = join_review(closed_id, "alex", "reviewer")
    run_command(["close", "--user", reviewer])
    open_id = create_review("Scope open all")
    code, stdout, _stderr = run_command(["list", "--all"])
    assert code == 0
    assert f"review: id={open_id} status=open" in stdout
    assert f"review: id={closed_id} status=closed" in stdout


def test_close_rejects_already_closed(review_home: Path) -> None:
    """Reject closing an already closed reviewctl."""
    review_id = create_review("Scope close already")
    token = join_review(review_id, "alex", "reviewer")
    run_command(["close", "--user", token])
    code, _stdout, stderr = run_command(["close", "--user", token])
    assert code == 1
    assert "review is closed" in stderr


def test_wait_receives_resolve_event_with_comment(review_home: Path) -> None:
    """Wait returns resolved events with payload."""
    review_id = create_review("Scope wait resolve")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "comment", "--user", reviewee, "-n", "0", "Reply"])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "--resolve", "Done"])
    code, stdout, _stderr = run_command(["wait", "--user", reviewee])
    assert code == 0
    lines = stdout.splitlines()
    resolved_line = next(line for line in lines if "event: thread_resolved" in line)
    assert "thread:0" in resolved_line
    assert "author_role:reviewer" in resolved_line
    assert "count:3" in resolved_line
    assert "with_comment:1" in resolved_line


def test_wait_receives_review_closed_event(review_home: Path) -> None:
    """Wait returns review closed events."""
    review_id = create_review("Scope wait closed")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    events: list[str] = []

    def wait_for_close() -> None:
        code, stdout, _stderr = run_command(["wait", "--user", reviewee])
        assert code == 0
        events.extend(stdout.splitlines())

    thread = threading.Thread(target=wait_for_close)
    thread.start()
    time.sleep(0.2)
    run_command(["close", "--user", reviewer])
    thread.join(timeout=2)

    assert not thread.is_alive()
    closed_line = next(line for line in events if "event: review_closed" in line)
    assert "author_role:reviewer" in closed_line
    assert "thread:-" in closed_line
    assert "count:-" in closed_line


def test_resolve_requires_reviewee_response(review_home: Path) -> None:
    """Reject resolving thread without reviewee response."""
    review_id = create_review("Scope resolve no reviewee")
    reviewer = join_review(review_id, "alex", "reviewer")
    join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    code, _stdout, stderr = run_command(["threads", "resolve", "--user", reviewer, "-n", "0"])
    assert code == 1
    assert "cannot resolve thread without reviewee response" in stderr


def test_resolve_force_bypasses_reviewee_check(review_home: Path) -> None:
    """Allow resolving thread with --force without reviewee response."""
    review_id = create_review("Scope resolve force")
    reviewer = join_review(review_id, "alex", "reviewer")
    join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    code, stdout, _stderr = run_command(["threads", "resolve", "--user", reviewer, "-n", "0", "--force"])
    assert code == 0
    assert stdout == "thread: 0 comments: 1"


def test_resolve_with_comment_requires_reviewee_response(review_home: Path) -> None:
    """Reject resolving with comment without reviewee response."""
    review_id = create_review("Scope resolve comment no reviewee")
    reviewer = join_review(review_id, "alex", "reviewer")
    join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    code, _stdout, stderr = run_command(["threads", "comment", "--user", reviewer, "-n", "0", "--resolve", "Final"])
    assert code == 1
    assert "cannot resolve thread without reviewee response" in stderr


def test_resolve_with_comment_force_bypasses_check(review_home: Path) -> None:
    """Allow resolving with comment and --force without reviewee response."""
    review_id = create_review("Scope resolve comment force")
    reviewer = join_review(review_id, "alex", "reviewer")
    join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    code, stdout, _stderr = run_command(
        ["threads", "comment", "--user", reviewer, "-n", "0", "--resolve", "--force", "Final"]
    )
    assert code == 0
    assert stdout == "thread: 0 comments: 2"


def test_resolve_succeeds_after_reviewee_comment(review_home: Path) -> None:
    """Allow resolving thread after reviewee has commented."""
    review_id = create_review("Scope resolve after reviewee")
    reviewer = join_review(review_id, "alex", "reviewer")
    reviewee = join_review(review_id, "sam", "reviewee")
    run_command(["threads", "create", "--user", reviewer])
    run_command(["threads", "comment", "--user", reviewer, "-n", "0", "Open thread"])
    run_command(["threads", "comment", "--user", reviewee, "-n", "0", "Reply"])
    code, stdout, _stderr = run_command(["threads", "resolve", "--user", reviewer, "-n", "0"])
    assert code == 0
    assert stdout == "thread: 0 comments: 2"
