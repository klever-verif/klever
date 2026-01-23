#!/usr/bin/env python3
"""Review CLI for managing code review sessions."""

from __future__ import annotations

import argparse
import io
import os
import re
import select
import sqlite3
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator


EVENT_THREAD_CREATED = "thread_created"
EVENT_COMMENT = "comment"
EVENT_THREAD_RESOLVED = "thread_resolved"
EVENT_ALL_THREADS_RESOLVED = "all_threads_resolved"
EVENT_REVIEW_CLOSED = "review_closed"

EVENT_LOG_PREFIX = "events-"
EVENT_LOG_SUFFIX = ".log"

REVIEWCTL_HOME_ENV = "REVIEWCTL_HOME"
DB_FILENAME = "review.db"
LOG_ROTATION_LIMIT = 2


class ReviewError(Exception):
    """Raised for user-facing review errors."""


def now_timestamp() -> str:
    """Return a local timestamp for storage/printing."""
    return datetime.now(tz=UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def eprint(message: str) -> None:
    """Print a message to stderr."""
    sys.stderr.write(f"{message}\n")


def get_home_dir() -> Path:
    """Return the review storage directory."""
    override = os.environ.get(REVIEWCTL_HOME_ENV)
    if override:
        return Path(override)
    return Path("~/.klever-review").expanduser()


def open_db() -> sqlite3.Connection:
    """Open the SQLite database, creating it if needed."""
    home = get_home_dir()
    home.mkdir(parents=True, exist_ok=True)
    path = home / DB_FILENAME
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    init_db(conn)
    return conn


def log_event(home: Path, line: str) -> None:
    """Write an event log line with rotation."""
    timestamp = datetime.now(tz=UTC).astimezone().strftime("%Y-%m-%d")
    log_path = home / f"{EVENT_LOG_PREFIX}{timestamp}{EVENT_LOG_SUFFIX}"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
    logs = sorted(home.glob(f"{EVENT_LOG_PREFIX}*{EVENT_LOG_SUFFIX}"))
    if len(logs) <= LOG_ROTATION_LIMIT:
        return
    for old_log in logs[:-LOG_ROTATION_LIMIT]:
        old_log.unlink(missing_ok=True)


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Return True when a table exists."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True when a table has a column."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def migrate_legacy_schema(conn: sqlite3.Connection) -> None:
    """Rename legacy tables from older schemas."""
    if not table_exists(conn, "reviews"):
        return
    if table_has_column(conn, "reviews", "scope"):
        return
    suffix = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
    for table in ["events", "comments", "threads", "participants", "reviews"]:
        if table_exists(conn, table):
            conn.execute(f"ALTER TABLE {table} RENAME TO {table}_legacy_{suffix}")
    for index in [
        "reviews_issue_open_idx",
        "participants_review_idx",
        "threads_review_idx",
        "comments_thread_idx",
        "events_review_idx",
    ]:
        conn.execute(f"DROP INDEX IF EXISTS {index}")


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they do not exist."""
    migrate_legacy_schema(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            scope TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('open', 'closed')),
            created_at TEXT NOT NULL,
            closed_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('reviewer', 'reviewee')),
            last_event_id INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(review_id, name)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS participants_review_idx ON participants(review_id)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
            thread_no INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('open', 'resolved')),
            author_token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            UNIQUE(review_id, thread_no)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS threads_review_idx ON threads(review_id)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
            author_token TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS comments_thread_idx ON comments(thread_id)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            thread_no INTEGER,
            author_token TEXT,
            count INTEGER,
            with_comment INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS events_review_idx ON events(review_id)")


@contextmanager
def write_transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """Run a write transaction with immediate locking."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def validate_non_negative(value: int, label: str) -> None:
    """Reject negative integer values."""
    if value < 0:
        raise ReviewError(f"{label} must be a non-negative integer")


def validate_review_id(review_id: str) -> None:
    """Validate review ID format (alphanumeric, underscores, dashes only)."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", review_id):
        raise ReviewError("review ID must contain only alphanumeric characters, underscores, or dashes")


def fetch_review(conn: sqlite3.Connection, review_id: str) -> sqlite3.Row | None:
    """Fetch a review by ID."""
    return conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()


def fetch_participant(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    """Fetch a participant by token."""
    return conn.execute("SELECT * FROM participants WHERE token = ?", (token,)).fetchone()


def resolve_review_from_args(
    conn: sqlite3.Connection,
    user: str | None,
    review_id: str | None,
) -> sqlite3.Row:
    """Resolve a review based on user id or review ID."""
    if user and review_id is not None:
        raise ReviewError("use either --user or --id")
    if user is None and review_id is None:
        raise ReviewError("--id is required when --user is not used")
    if user:
        participant = fetch_participant(conn, user)
        if not participant:
            raise ReviewError("invalid user id")
        review = fetch_review(conn, participant["review_id"])
    else:
        if review_id is None:
            raise ReviewError("--id is required when --user is not used")
        review = fetch_review(conn, review_id)
    if not review:
        raise ReviewError("review does not exist")
    return review


def fetch_thread(conn: sqlite3.Connection, review_id: str, thread_no: int) -> sqlite3.Row | None:
    """Fetch a thread by review and thread number."""
    return conn.execute(
        "SELECT * FROM threads WHERE review_id = ? AND thread_no = ?",
        (review_id, thread_no),
    ).fetchone()


def count_threads(conn: sqlite3.Connection, review_id: str) -> int:
    """Count threads for a review."""
    row = conn.execute("SELECT COUNT(*) AS count FROM threads WHERE review_id = ?", (review_id,)).fetchone()
    return int(row["count"])


def count_threads_by_status(conn: sqlite3.Connection, review_id: str, status: str) -> int:
    """Count threads for a review by status."""
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM threads WHERE review_id = ? AND status = ?",
        (review_id, status),
    ).fetchone()
    return int(row["count"])


def list_thread_numbers(conn: sqlite3.Connection, review_id: str, status: str | None = None) -> list[int]:
    """Return thread numbers for a review."""
    if status:
        rows = conn.execute(
            "SELECT thread_no FROM threads WHERE review_id = ? AND status = ? ORDER BY thread_no ASC",
            (review_id, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT thread_no FROM threads WHERE review_id = ? ORDER BY thread_no ASC",
            (review_id,),
        ).fetchall()
    return [int(row["thread_no"]) for row in rows]


def count_participants(conn: sqlite3.Connection, review_id: str, role: str | None = None) -> int:
    """Count participants for a review."""
    if role:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM participants WHERE review_id = ? AND role = ?",
            (review_id, role),
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) AS count FROM participants WHERE review_id = ?", (review_id,)).fetchone()
    return int(row["count"])


def count_comments_for_thread(conn: sqlite3.Connection, thread_id: int) -> int:
    """Count comments for a thread."""
    row = conn.execute("SELECT COUNT(*) AS count FROM comments WHERE thread_id = ?", (thread_id,)).fetchone()
    return int(row["count"])


def has_reviewee_comment(conn: sqlite3.Connection, thread_id: int) -> bool:
    """Check if any reviewee has commented on the thread."""
    row = conn.execute(
        """
        SELECT 1 FROM comments
        JOIN participants ON participants.token = comments.author_token
        WHERE comments.thread_id = ? AND participants.role = 'reviewee'
        LIMIT 1
        """,
        (thread_id,),
    ).fetchone()
    return row is not None


def count_comments_for_review(conn: sqlite3.Connection, review_id: str) -> int:
    """Count comments for a review."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM comments
        JOIN threads ON comments.thread_id = threads.id
        WHERE threads.review_id = ?
        """,
        (review_id,),
    ).fetchone()
    return int(row["count"])


@dataclass(frozen=True)
class EventPayload:
    """Data used when recording an event."""

    event_type: str
    thread_no: int | None
    author_token: str | None
    count: int | None
    with_comment: int = 0


def add_event(
    conn: sqlite3.Connection,
    review_id: str,
    payload: EventPayload,
) -> None:
    """Insert an event for the review."""
    cursor = conn.execute(
        """
        INSERT INTO events (review_id, event_type, thread_no, author_token, count, with_comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            payload.event_type,
            payload.thread_no,
            payload.author_token,
            payload.count,
            payload.with_comment,
            now_timestamp(),
        ),
    )
    event_id = cursor.lastrowid
    if event_id is None:
        return
    event_row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if event_row is None:
        return
    log_event(get_home_dir(), format_event(conn, event_row))


def read_stdin_text() -> str | None:
    """Return text from stdin if available."""
    if sys.stdin is None or sys.stdin.closed:
        return None
    if sys.stdin.isatty():
        return None
    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
    except (OSError, ValueError):
        try:
            content = sys.stdin.read()
        except (OSError, io.UnsupportedOperation):
            return None
        return content.strip() if content else None
    if not ready:
        return None
    content = sys.stdin.read()
    return content.strip() if content else None


def parse_scope(parts: list[str]) -> str:
    """Return the scope text from args or stdin."""
    text = " ".join(parts).strip()
    if not text:
        stdin_text = read_stdin_text()
        if stdin_text:
            text = stdin_text
    if not text:
        raise ReviewError("scope text is required")
    return text


def scope_header(scope: str) -> str:
    """Return the first line of the scope."""
    lines = scope.splitlines()
    return lines[0] if lines else ""


def format_event(conn: sqlite3.Connection, event: sqlite3.Row) -> str:
    """Format an event line for output."""
    thread_value = "-" if event["thread_no"] is None else str(event["thread_no"])
    count_value = "-" if event["count"] is None else str(event["count"])
    author_name = "-"
    author_role = "-"
    if event["author_token"]:
        author = fetch_participant(conn, event["author_token"])
        if author:
            author_name = author["name"]
            author_role = author["role"]
    line = (
        f"event: {event['event_type']} thread:{thread_value} author:{author_name} "
        f"author_role:{author_role} count:{count_value}"
    )
    if event["event_type"] == EVENT_THREAD_RESOLVED:
        line += f" with_comment:{event['with_comment']}"
    return line


def maybe_add_all_threads_resolved(conn: sqlite3.Connection, review_id: str, author_token: str) -> None:
    """Record an all-threads-resolved event when appropriate."""
    open_threads = count_threads_by_status(conn, review_id, "open")
    total_threads = count_threads(conn, review_id)
    if open_threads == 0 and total_threads > 0:
        add_event(
            conn,
            review_id,
            EventPayload(
                event_type=EVENT_ALL_THREADS_RESOLVED,
                thread_no=None,
                author_token=author_token,
                count=total_threads,
            ),
        )


def parse_comment(parts: list[str], required: bool) -> str | None:
    """Return a normalized comment or None."""
    text = " ".join(parts).strip()
    if not text:
        stdin_text = read_stdin_text()
        if stdin_text:
            text = stdin_text
    if required and not text:
        raise ReviewError("comment text is required")
    return text if text else None


def cmd_create(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Create a review if allowed."""
    review_id = args.review_id
    validate_review_id(review_id)
    scope = parse_scope(args.scope)
    with write_transaction(conn):
        if fetch_review(conn, review_id):
            raise ReviewError("review with this ID already exists")
        conn.execute(
            "INSERT INTO reviews(id, scope, status, created_at) VALUES (?, ?, 'open', ?)",
            (review_id, scope, now_timestamp()),
        )
    sys.stdout.write(f"{review_id}\n")


def cmd_join(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Join a review and allocate a token."""
    review_id = args.review_id
    name = args.name.strip()
    if not name:
        raise ReviewError("name is required")
    with write_transaction(conn):
        review = fetch_review(conn, review_id)
        if not review:
            raise ReviewError("review does not exist")
        if review["status"] == "closed":
            raise ReviewError("review is closed")
        existing = conn.execute(
            "SELECT 1 FROM participants WHERE review_id = ? AND name = ?",
            (review_id, name),
        ).fetchone()
        if existing:
            raise ReviewError("name is already taken")
        token = f"{name}-{review_id}"
        max_event = conn.execute(
            "SELECT COALESCE(MAX(id), 0) AS max_id FROM events WHERE review_id = ?",
            (review_id,),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO participants(review_id, token, name, role, last_event_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (review_id, token, name, args.role, int(max_event["max_id"]), now_timestamp()),
        )
    sys.stdout.write(f"{token}\n")


def cmd_threads_create(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Create a new thread for a review."""
    with write_transaction(conn):
        participant = fetch_participant(conn, args.user)
        if not participant:
            raise ReviewError("invalid user id")
        review = fetch_review(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        if participant["role"] != "reviewer":
            raise ReviewError("reviewee cannot create a new thread")
        next_thread = conn.execute(
            "SELECT COALESCE(MAX(thread_no), -1) + 1 AS next_no FROM threads WHERE review_id = ?",
            (review["id"],),
        ).fetchone()
        thread_no = int(next_thread["next_no"])
        cursor = conn.execute(
            """
            INSERT INTO threads(review_id, thread_no, status, author_token, created_at)
            VALUES (?, ?, 'open', ?, ?)
            """,
            (review["id"], thread_no, participant["token"], now_timestamp()),
        )
        if cursor.lastrowid is None:
            raise ReviewError("failed to create thread")
        add_event(
            conn,
            review["id"],
            EventPayload(
                event_type=EVENT_THREAD_CREATED,
                thread_no=thread_no,
                author_token=participant["token"],
                count=0,
            ),
        )
    sys.stdout.write(f"thread-{thread_no}\n")


def cmd_threads_comment(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Add a comment to a thread."""
    comment_text = parse_comment(args.comment, required=True)
    if comment_text is None:
        raise ReviewError("comment text is required")
    validate_non_negative(args.thread, "thread")
    with write_transaction(conn):
        participant = fetch_participant(conn, args.user)
        if not participant:
            raise ReviewError("invalid user id")
        review = fetch_review(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        thread = fetch_thread(conn, review["id"], args.thread)
        if not thread:
            raise ReviewError("thread does not exist")
        if thread["status"] == "resolved":
            raise ReviewError("thread is resolved")
        conn.execute(
            """
            INSERT INTO comments(thread_id, author_token, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (thread["id"], participant["token"], comment_text, now_timestamp()),
        )
        comment_count = count_comments_for_thread(conn, thread["id"])
        if args.resolve:
            if thread["author_token"] != participant["token"]:
                raise ReviewError("user cannot resolve this thread")
            if not args.force and not has_reviewee_comment(conn, thread["id"]):
                raise ReviewError("cannot resolve thread without reviewee response")
            conn.execute(
                "UPDATE threads SET status = 'resolved', resolved_at = ? WHERE id = ?",
                (now_timestamp(), thread["id"]),
            )
            add_event(
                conn,
                review["id"],
                EventPayload(
                    event_type=EVENT_THREAD_RESOLVED,
                    thread_no=thread["thread_no"],
                    author_token=participant["token"],
                    count=comment_count,
                    with_comment=1,
                ),
            )
            maybe_add_all_threads_resolved(conn, review["id"], participant["token"])
        else:
            add_event(
                conn,
                review["id"],
                EventPayload(
                    event_type=EVENT_COMMENT,
                    thread_no=thread["thread_no"],
                    author_token=participant["token"],
                    count=comment_count,
                ),
            )
    sys.stdout.write(f"thread: {thread['thread_no']} comments: {comment_count}\n")


def cmd_threads_resolve(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Resolve a thread."""
    validate_non_negative(args.thread, "thread")
    with write_transaction(conn):
        participant = fetch_participant(conn, args.user)
        if not participant:
            raise ReviewError("invalid user id")
        review = fetch_review(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        thread = fetch_thread(conn, review["id"], args.thread)
        if not thread:
            raise ReviewError("thread does not exist")
        if thread["status"] == "resolved":
            raise ReviewError("thread is resolved")
        if thread["author_token"] != participant["token"]:
            raise ReviewError("user cannot resolve this thread")
        if not args.force and not has_reviewee_comment(conn, thread["id"]):
            raise ReviewError("cannot resolve thread without reviewee response")
        comment_count = count_comments_for_thread(conn, thread["id"])
        conn.execute(
            "UPDATE threads SET status = 'resolved', resolved_at = ? WHERE id = ?",
            (now_timestamp(), thread["id"]),
        )
        add_event(
            conn,
            review["id"],
            EventPayload(
                event_type=EVENT_THREAD_RESOLVED,
                thread_no=thread["thread_no"],
                author_token=participant["token"],
                count=comment_count,
                with_comment=0,
            ),
        )
        maybe_add_all_threads_resolved(conn, review["id"], participant["token"])
    sys.stdout.write(f"thread: {thread['thread_no']} comments: {comment_count}\n")


def cmd_close(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Close a review if all threads are resolved."""
    with write_transaction(conn):
        participant = fetch_participant(conn, args.user)
        if not participant:
            raise ReviewError("invalid user id")
        if participant["role"] != "reviewer":
            raise ReviewError("user cannot close the review")
        review = fetch_review(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        open_threads = list_thread_numbers(conn, review["id"], status="open")
        if open_threads:
            joined = " ".join(str(thread_no) for thread_no in open_threads)
            raise ReviewError(
                "all threads must be resolved before closing the review"
                + (f" (open threads: {joined})" if joined else "")
            )
        conn.execute(
            "UPDATE reviews SET status = 'closed', closed_at = ? WHERE id = ?",
            (now_timestamp(), review["id"]),
        )
        add_event(
            conn,
            review["id"],
            EventPayload(
                event_type=EVENT_REVIEW_CLOSED,
                thread_no=None,
                author_token=participant["token"],
                count=None,
            ),
        )
        threads_count = count_threads(conn, review["id"])
        comments_count = count_comments_for_review(conn, review["id"])
        reviewers = count_participants(conn, review["id"], "reviewer")
        reviewees = count_participants(conn, review["id"], "reviewee")
    sys.stdout.write(
        "\n".join(
            [
                f"review: id={review['id']} status=closed",
                (f"threads: {threads_count} comments: {comments_count} reviewers: {reviewers} reviewees: {reviewees}"),
            ]
        )
        + "\n"
    )


def cmd_status(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Show review status and counts."""
    review = resolve_review_from_args(conn, args.user, args.review_id)
    open_threads = count_threads_by_status(conn, review["id"], "open")
    resolved_threads = count_threads_by_status(conn, review["id"], "resolved")
    comments_count = count_comments_for_review(conn, review["id"])
    reviewers = count_participants(conn, review["id"], "reviewer")
    reviewees = count_participants(conn, review["id"], "reviewee")
    sys.stdout.write(
        "\n".join(
            [
                f"review: id={review['id']} status={review['status']}",
                f"threads: open={open_threads} resolved={resolved_threads} comments={comments_count}",
                f"participants: reviewers={reviewers} reviewees={reviewees}",
            ]
        )
        + "\n"
    )


def render_thread(conn: sqlite3.Connection, thread: sqlite3.Row) -> list[str]:
    """Render a thread as Markdown lines."""
    status_label = "open" if thread["status"] == "open" else "resolved"
    lines: list[str] = ["", f"## thread-{thread['thread_no']} {status_label}"]
    comments = conn.execute(
        """
        SELECT comments.body, comments.created_at, participants.role, participants.name
        FROM comments
        JOIN participants ON participants.token = comments.author_token
        WHERE comments.thread_id = ?
        ORDER BY comments.id ASC
        """,
        (thread["id"],),
    ).fetchall()
    for comment in comments:
        lines.append(f"### [{comment['role']}][{comment['name']}] @ {comment['created_at']}")
        lines.append(comment["body"])
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def cmd_view(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Print review content as Markdown."""
    thread_no = getattr(args, "thread", None)
    if thread_no is not None:
        validate_non_negative(thread_no, "thread")
    review = resolve_review_from_args(conn, args.user, args.review_id)
    lines = [f"# review-{review['id']} {review['status']}"]
    lines.extend(review["scope"].splitlines())
    if thread_no is not None:
        thread = fetch_thread(conn, review["id"], thread_no)
        if not thread:
            raise ReviewError("thread does not exist")
        lines.extend(render_thread(conn, thread))
    else:
        threads = conn.execute(
            "SELECT * FROM threads WHERE review_id = ? ORDER BY thread_no ASC",
            (review["id"],),
        ).fetchall()
        for thread in threads:
            lines.extend(render_thread(conn, thread))
    sys.stdout.write("\n".join(lines).rstrip("\n") + "\n")


def cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """List reviews."""
    if args.all:
        reviews = conn.execute("SELECT id, status, scope FROM reviews ORDER BY created_at ASC").fetchall()
    else:
        reviews = conn.execute(
            "SELECT id, status, scope FROM reviews WHERE status = 'open' ORDER BY created_at ASC"
        ).fetchall()
    if not reviews:
        eprint("no reviews" if args.all else "no active reviews")
        return
    for review in reviews:
        open_threads = count_threads_by_status(conn, review["id"], "open")
        comments = count_comments_for_review(conn, review["id"])
        header = scope_header(review["scope"].strip())
        line = (
            f"review: id={review['id']} status={review['status']} "
            f"open_threads={open_threads} comments={comments} scope={header or '-'}"
        )
        sys.stdout.write(f"{line}\n")


def cmd_threads_list(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """List threads for a review."""
    review = resolve_review_from_args(conn, args.user, args.review_id)
    threads = conn.execute(
        "SELECT * FROM threads WHERE review_id = ? ORDER BY thread_no ASC",
        (review["id"],),
    ).fetchall()
    if not threads:
        eprint("no threads")
        return
    for thread in threads:
        author = fetch_participant(conn, thread["author_token"])
        author_name = author["name"] if author else "-"
        comments_count = count_comments_for_thread(conn, thread["id"])
        sys.stdout.write(
            "thread-{thread_no}: status={status} comments={comments} author={author}\n".format(
                thread_no=thread["thread_no"],
                status=thread["status"],
                comments=comments_count,
                author=author_name,
            )
        )


def cmd_threads_view(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """View a single thread."""
    validate_non_negative(args.thread, "thread")
    review = resolve_review_from_args(conn, args.user, args.review_id)
    thread = fetch_thread(conn, review["id"], args.thread)
    if not thread:
        raise ReviewError("thread does not exist")
    lines = [f"# review-{review['id']} {review['status']}"]
    lines.extend(review["scope"].splitlines())
    lines.extend(render_thread(conn, thread))
    sys.stdout.write("\n".join(lines).rstrip("\n") + "\n")


def cmd_wait(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Wait for review events for a participant."""
    participant = fetch_participant(conn, args.user)
    if not participant:
        raise ReviewError("invalid user id")
    review = fetch_review(conn, participant["review_id"])
    if review is None or review["status"] == "closed":
        raise ReviewError("review is closed")
    while True:
        participant = fetch_participant(conn, args.user)
        if not participant:
            raise ReviewError("invalid user id")
        events = conn.execute(
            """
            SELECT * FROM events
            WHERE review_id = ? AND id > ?
            ORDER BY id ASC
            """,
            (participant["review_id"], participant["last_event_id"]),
        ).fetchall()
        if events:
            with write_transaction(conn):
                conn.execute(
                    "UPDATE participants SET last_event_id = ? WHERE id = ?",
                    (events[-1]["id"], participant["id"]),
                )
            for event in events:
                sys.stdout.write(f"{format_event(conn, event)}\n")
            return
        review = fetch_review(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        time.sleep(0.5)


def add_create_parser(subparsers: Any) -> None:
    """Register the create command."""
    create_parser = subparsers.add_parser(
        "create",
        help="Create a review",
        description=(
            "Create a new review session with the specified ID and scope. "
            "The scope defines what is being reviewed (e.g., a feature, a file, or a set of changes). "
            "On success, the review ID is printed to stdout and can be used to join or manage the review."
        ),
    )
    create_parser.add_argument(
        "--id",
        dest="review_id",
        required=True,
        help="Unique review identifier (alphanumeric, underscores, dashes; no spaces)",
    )
    create_parser.add_argument(
        "scope",
        nargs=argparse.REMAINDER,
        help="Description of what is being reviewed; can also be piped via stdin",
    )
    create_parser.set_defaults(func=cmd_create)


def add_join_parser(subparsers: Any) -> None:
    """Register the join command."""
    join_parser = subparsers.add_parser(
        "join",
        help="Join a review",
        description=(
            "Join an existing review session as a participant. "
            "Requires a unique name and a role (reviewer or reviewee). "
            "On success, a participant token is printed to stdout. "
            "This token is used for all subsequent operations (creating threads, commenting, etc.)."
        ),
    )
    join_parser.add_argument(
        "review_id",
        metavar="REVIEW_ID",
        help="ID of the review session to join",
    )
    join_parser.add_argument(
        "--name",
        required=True,
        help="Participant name (must be unique within the review)",
    )
    join_parser.add_argument(
        "--role",
        choices=["reviewer", "reviewee"],
        required=True,
        help="Participant role in the review session",
    )
    join_parser.set_defaults(func=cmd_join)


def add_close_parser(subparsers: Any) -> None:
    """Register the close command."""
    close_parser = subparsers.add_parser(
        "close",
        help="Close a review",
        description=(
            "Close a review session. Only a reviewer can close the review, "
            "and all threads must be resolved before closing. "
            "The review ID is derived from the participant token. "
            "On success, prints review statistics."
        ),
    )
    close_parser.add_argument(
        "--user",
        required=True,
        help="Participant token (must be a reviewer)",
    )
    close_parser.set_defaults(func=cmd_close)


def add_status_parser(subparsers: Any) -> None:
    """Register the status command."""
    status_parser = subparsers.add_parser(
        "status",
        help="Show review status",
        description=(
            "Show the current status of a review session including thread counts, "
            "comment counts, and participant information. "
            "Specify either --user (participant token) or --id (review ID), but not both."
        ),
    )
    status_parser.add_argument(
        "--user",
        help="Participant token to identify the review",
    )
    status_parser.add_argument(
        "--id",
        dest="review_id",
        help="Review ID to show status for",
    )
    status_parser.set_defaults(func=cmd_status)


def add_view_parser(subparsers: Any) -> None:
    """Register the view command."""
    view_parser = subparsers.add_parser("view", help="View review contents")
    view_parser.add_argument("--user")
    view_parser.add_argument("--id", dest="review_id")
    view_parser.set_defaults(func=cmd_view)


def add_list_parser(subparsers: Any) -> None:
    """Register the list command."""
    list_parser = subparsers.add_parser(
        "list",
        help="List reviews",
        description=(
            "List review sessions. "
            "By default, only open reviews are shown. Use --all to include closed reviews. "
            "Shows review ID, status, number of open threads, total comments, and scope summary."
        ),
    )
    list_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all reviews, including closed ones",
    )
    list_parser.set_defaults(func=cmd_list)


def add_threads_parsers(subparsers: Any) -> None:
    """Register thread subcommands."""
    threads_parser = subparsers.add_parser("threads", help="Manage threads")
    threads_subparsers = threads_parser.add_subparsers(dest="threads_command", required=True)

    threads_create = threads_subparsers.add_parser("create", help="Create a thread")
    threads_create.add_argument("--user", required=True)
    threads_create.set_defaults(func=cmd_threads_create)

    threads_comment = threads_subparsers.add_parser("comment", help="Add a comment to a thread")
    threads_comment.add_argument("--user", required=True)
    threads_comment.add_argument("-n", "--thread", type=int, required=True)
    threads_comment.add_argument("--resolve", action="store_true")
    threads_comment.add_argument("--force", action="store_true", help="Resolve even without reviewee response")
    threads_comment.add_argument("comment", nargs=argparse.REMAINDER)
    threads_comment.set_defaults(func=cmd_threads_comment)

    threads_resolve = threads_subparsers.add_parser("resolve", help="Resolve a thread")
    threads_resolve.add_argument("--user", required=True)
    threads_resolve.add_argument("-n", "--thread", type=int, required=True)
    threads_resolve.add_argument("--force", action="store_true", help="Resolve even without reviewee response")
    threads_resolve.set_defaults(func=cmd_threads_resolve)

    threads_list = threads_subparsers.add_parser("list", help="List threads")
    threads_list.add_argument("--user")
    threads_list.add_argument("--id", dest="review_id")
    threads_list.set_defaults(func=cmd_threads_list)

    threads_view = threads_subparsers.add_parser("view", help="View a thread")
    threads_view.add_argument("--user")
    threads_view.add_argument("--id", dest="review_id")
    threads_view.add_argument("-n", "--thread", type=int, required=True)
    threads_view.set_defaults(func=cmd_threads_view)


def add_wait_parser(subparsers: Any) -> None:
    """Register the wait command."""
    wait_parser = subparsers.add_parser("wait", help="Wait for review events")
    wait_parser.add_argument("--user", required=True)
    wait_parser.set_defaults(func=cmd_wait)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="reviewctl.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_create_parser(subparsers)
    add_join_parser(subparsers)
    add_close_parser(subparsers)
    add_status_parser(subparsers)
    add_view_parser(subparsers)
    add_list_parser(subparsers)
    add_threads_parsers(subparsers)
    add_wait_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for CLI execution."""
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = open_db()
    try:
        args.func(conn, args)
    except ReviewError as exc:
        eprint(str(exc))
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
