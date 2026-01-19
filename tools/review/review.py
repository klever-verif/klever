#!/usr/bin/env python3
"""Review CLI for managing code review sessions."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


NAME_POOL = [
    "john",
    "dan",
    "dave",
    "mark",
    "paul",
    "luke",
    "tom",
    "alex",
    "max",
    "emma",
    "lucy",
    "kate",
    "nina",
    "rose",
    "mike",
    "zane",
]

EVENT_THREAD_CREATED = "thread_created"
EVENT_COMMENT = "comment"
EVENT_THREAD_RESOLVED = "thread_resolved"
EVENT_REVIEW_CLOSED = "review_closed"

REVIEWCTL_HOME_ENV = "REVIEWCTL_HOME"
DB_FILENAME = "review.db"


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


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they do not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue INTEGER NOT NULL,
            task INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('open', 'closed')),
            created_at TEXT NOT NULL,
            closed_at TEXT,
            UNIQUE(issue, task)
        )
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS reviews_issue_open_idx ON reviews(issue) WHERE status='open'")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('reviewer', 'reviewee')),
            last_event_id INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS participants_review_idx ON participants(review_id)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
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
            review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
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


def fetch_review(conn: sqlite3.Connection, issue: int, task: int) -> sqlite3.Row | None:
    """Fetch a review by issue/task."""
    return conn.execute("SELECT * FROM reviews WHERE issue = ? AND task = ?", (issue, task)).fetchone()


def fetch_review_by_id(conn: sqlite3.Connection, review_id: int) -> sqlite3.Row | None:
    """Fetch a review by ID."""
    return conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()


def fetch_participant(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    """Fetch a participant by token."""
    return conn.execute("SELECT * FROM participants WHERE token = ?", (token,)).fetchone()


def fetch_thread(conn: sqlite3.Connection, review_id: int, thread_no: int) -> sqlite3.Row | None:
    """Fetch a thread by review and thread number."""
    return conn.execute(
        "SELECT * FROM threads WHERE review_id = ? AND thread_no = ?",
        (review_id, thread_no),
    ).fetchone()


def count_threads(conn: sqlite3.Connection, review_id: int) -> int:
    """Count threads for a review."""
    row = conn.execute("SELECT COUNT(*) AS count FROM threads WHERE review_id = ?", (review_id,)).fetchone()
    return int(row["count"])


def count_participants(conn: sqlite3.Connection, review_id: int, role: str | None = None) -> int:
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


def count_comments_for_review(conn: sqlite3.Connection, review_id: int) -> int:
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
    review_id: int,
    payload: EventPayload,
) -> None:
    """Insert an event for the review."""
    conn.execute(
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


def select_available_name(conn: sqlite3.Connection, review_id: int) -> str | None:
    """Return the next available name for a review."""
    rows = conn.execute("SELECT name FROM participants WHERE review_id = ?", (review_id,)).fetchall()
    used = {row["name"] for row in rows}
    for name in NAME_POOL:
        if name not in used:
            return name
    return None


def ensure_review(conn: sqlite3.Connection, issue: int, task: int, allow_create: bool) -> sqlite3.Row:
    """Get or create a review based on flags."""
    review = fetch_review(conn, issue, task)
    if review:
        if review["status"] == "closed":
            raise ReviewError("review is already closed for this issue/task")
        return review
    if not allow_create:
        raise ReviewError("review does not exist")
    open_review = conn.execute("SELECT task FROM reviews WHERE issue = ? AND status = 'open'", (issue,)).fetchone()
    if open_review:
        raise ReviewError(f"issue {issue} already has an active review for task {open_review['task']}")
    cursor = conn.execute(
        "INSERT INTO reviews(issue, task, status, created_at) VALUES (?, ?, 'open', ?)",
        (issue, task, now_timestamp()),
    )
    review_id = cursor.lastrowid
    if review_id is None:
        raise ReviewError("failed to create review")
    review = fetch_review_by_id(conn, review_id)
    if review is None:
        raise ReviewError("failed to load review")
    return review


def format_event(event: sqlite3.Row) -> str:
    """Format an event line for output."""
    thread_value = "-" if event["thread_no"] is None else str(event["thread_no"])
    author_value = "-" if event["author_token"] is None else event["author_token"]
    count_value = "-" if event["count"] is None else str(event["count"])
    line = f"event: {event['event_type']} thread:{thread_value} author:{author_value} count:{count_value}"
    if event["event_type"] == EVENT_THREAD_RESOLVED:
        line += f" with_comment:{event['with_comment']}"
    return line


def parse_comment(parts: list[str], required: bool) -> str | None:
    """Return a normalized comment or None."""
    text = " ".join(parts).strip()
    if required and not text:
        raise ReviewError("comment text is required")
    return text if text else None


def cmd_create(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Create a review if allowed."""
    validate_non_negative(args.issue, "issue")
    validate_non_negative(args.task, "task")
    with write_transaction(conn):
        review = fetch_review(conn, args.issue, args.task)
        if review:
            if review["status"] == "closed":
                raise ReviewError("review is already closed for this issue/task")
        else:
            open_review = conn.execute(
                "SELECT task FROM reviews WHERE issue = ? AND status = 'open'", (args.issue,)
            ).fetchone()
            if open_review:
                raise ReviewError(f"issue {args.issue} already has an active review for task {open_review['task']}")
            conn.execute(
                "INSERT INTO reviews(issue, task, status, created_at) VALUES (?, ?, 'open', ?)",
                (args.issue, args.task, now_timestamp()),
            )
    sys.stdout.write(f"review: issue={args.issue} task={args.task} status=open\n")


def cmd_join(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Join a review and allocate a token."""
    validate_non_negative(args.issue, "issue")
    validate_non_negative(args.task, "task")
    with write_transaction(conn):
        review = ensure_review(conn, args.issue, args.task, args.create)
        name = select_available_name(conn, review["id"])
        if not name:
            raise ReviewError("name pool exhausted for this review")
        token = f"{name}-{review['issue']}-{review['task']}"
        max_event = conn.execute(
            "SELECT COALESCE(MAX(id), 0) AS max_id FROM events WHERE review_id = ?",
            (review["id"],),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO participants(review_id, token, name, role, last_event_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (review["id"], token, name, args.role, int(max_event["max_id"]), now_timestamp()),
        )
        threads_count = count_threads(conn, review["id"])
        reviewers = count_participants(conn, review["id"], "reviewer")
        reviewees = count_participants(conn, review["id"], "reviewee")
    sys.stdout.write(
        "\n".join(
            [
                f"token: {token}",
                f"threads: {threads_count}",
                f"reviewers: {reviewers}",
                f"reviewees: {reviewees}",
            ]
        )
        + "\n"
    )


def cmd_comment(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Add a comment or create a thread."""
    comment_text = parse_comment(args.comment, required=True)
    if comment_text is None:
        raise ReviewError("comment text is required")
    if args.thread is not None:
        validate_non_negative(args.thread, "thread")
    with write_transaction(conn):
        participant = fetch_participant(conn, args.token)
        if not participant:
            raise ReviewError("invalid token")
        review = fetch_review_by_id(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        if args.thread is None:
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
            thread_id = cursor.lastrowid
            if thread_id is None:
                raise ReviewError("failed to create thread")
            conn.execute(
                """
                INSERT INTO comments(thread_id, author_token, body, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (thread_id, participant["token"], comment_text, now_timestamp()),
            )
            comment_count = count_comments_for_thread(conn, thread_id)
            add_event(
                conn,
                review["id"],
                EventPayload(
                    event_type=EVENT_THREAD_CREATED,
                    thread_no=thread_no,
                    author_token=participant["token"],
                    count=comment_count,
                ),
            )
        else:
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
    sys.stdout.write(f"comments: {comment_count}\n")


def cmd_resolve(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Resolve a thread, optionally with a comment."""
    validate_non_negative(args.thread, "thread")
    comment_text = parse_comment(args.comment, required=False)
    with write_transaction(conn):
        participant = fetch_participant(conn, args.token)
        if not participant:
            raise ReviewError("invalid token")
        review = fetch_review_by_id(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        thread = fetch_thread(conn, review["id"], args.thread)
        if not thread:
            raise ReviewError("thread does not exist")
        if thread["status"] == "resolved":
            raise ReviewError("thread is resolved")
        if thread["author_token"] != participant["token"]:
            raise ReviewError("token cannot resolve this thread")
        if comment_text:
            conn.execute(
                """
                INSERT INTO comments(thread_id, author_token, body, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (thread["id"], participant["token"], comment_text, now_timestamp()),
            )
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
                with_comment=1 if comment_text else 0,
            ),
        )
    sys.stdout.write(f"comments: {comment_count}\n")


def cmd_close(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Close a review if all threads are resolved."""
    with write_transaction(conn):
        participant = fetch_participant(conn, args.token)
        if not participant:
            raise ReviewError("invalid token")
        if participant["role"] != "reviewer":
            raise ReviewError("token cannot close the review")
        review = fetch_review_by_id(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        open_threads = conn.execute(
            "SELECT COUNT(*) AS count FROM threads WHERE review_id = ? AND status = 'open'",
            (review["id"],),
        ).fetchone()
        if int(open_threads["count"]) > 0:
            raise ReviewError("all threads must be resolved before closing the review")
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
                f"review: issue={review['issue']} task={review['task']} status=closed",
                (f"threads: {threads_count} comments: {comments_count} reviewers: {reviewers} reviewees: {reviewees}"),
            ]
        )
        + "\n"
    )


def render_thread(conn: sqlite3.Connection, thread: sqlite3.Row) -> list[str]:
    """Render a thread as Markdown lines."""
    lines: list[str] = [f"## thread-{thread['thread_no']}"]
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
    if args.token and (args.issue is not None or args.task is not None):
        raise ReviewError("use either --token or --issue/--task")
    if args.token is None and (args.issue is None or args.task is None):
        raise ReviewError("--issue and --task are required when --token is not used")
    if args.thread is not None:
        validate_non_negative(args.thread, "thread")
    if args.token:
        participant = fetch_participant(conn, args.token)
        if not participant:
            raise ReviewError("invalid token")
        review = fetch_review_by_id(conn, participant["review_id"])
    else:
        validate_non_negative(args.issue, "issue")
        validate_non_negative(args.task, "task")
        review = fetch_review(conn, args.issue, args.task)
    if not review:
        raise ReviewError("review does not exist")
    lines = [f"# issue-{review['issue']}: task-{review['task']}"]
    if args.thread is not None:
        thread = fetch_thread(conn, review["id"], args.thread)
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
    sys.stdout.write("\n".join(lines) + "\n")


def cmd_list(conn: sqlite3.Connection, _args: argparse.Namespace) -> None:
    """List active reviews."""
    reviews = conn.execute(
        "SELECT id, issue, task FROM reviews WHERE status = 'open' ORDER BY issue ASC, task ASC"
    ).fetchall()
    if not reviews:
        eprint("no active reviews")
        return
    for review in reviews:
        threads_count = count_threads(conn, review["id"])
        participants_count = count_participants(conn, review["id"])
        sys.stdout.write(
            "review: issue={issue} task={task} threads={threads} participants={participants}\n".format(
                issue=review["issue"],
                task=review["task"],
                threads=threads_count,
                participants=participants_count,
            )
        )


def cmd_wait(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Wait for review events for a participant."""
    participant = fetch_participant(conn, args.token)
    if not participant:
        raise ReviewError("invalid token")
    review = fetch_review_by_id(conn, participant["review_id"])
    if review is None or review["status"] == "closed":
        raise ReviewError("review is closed")
    while True:
        participant = fetch_participant(conn, args.token)
        if not participant:
            raise ReviewError("invalid token")
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
                sys.stdout.write(f"{format_event(event)}\n")
            return
        review = fetch_review_by_id(conn, participant["review_id"])
        if review is None or review["status"] == "closed":
            raise ReviewError("review is closed")
        time.sleep(0.5)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="review.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a review")
    create_parser.add_argument("--issue", type=int, required=True)
    create_parser.add_argument("--task", type=int, required=True)
    create_parser.set_defaults(func=cmd_create)

    join_parser = subparsers.add_parser("join", help="Join a review")
    join_parser.add_argument("--issue", type=int, required=True)
    join_parser.add_argument("--task", type=int, required=True)
    join_parser.add_argument("--role", choices=["reviewer", "reviewee"], required=True)
    join_parser.add_argument("--create", action="store_true")
    join_parser.set_defaults(func=cmd_join)

    comment_parser = subparsers.add_parser("comment", help="Add a comment")
    comment_parser.add_argument("--token", required=True)
    comment_parser.add_argument("--thread", type=int)
    comment_parser.add_argument("comment", nargs=argparse.REMAINDER)
    comment_parser.set_defaults(func=cmd_comment)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a thread")
    resolve_parser.add_argument("--token", required=True)
    resolve_parser.add_argument("--thread", type=int, required=True)
    resolve_parser.add_argument("comment", nargs=argparse.REMAINDER)
    resolve_parser.set_defaults(func=cmd_resolve)

    close_parser = subparsers.add_parser("close", help="Close a review")
    close_parser.add_argument("--token", required=True)
    close_parser.set_defaults(func=cmd_close)

    view_parser = subparsers.add_parser("view", help="View review contents")
    view_parser.add_argument("--token")
    view_parser.add_argument("--issue", type=int)
    view_parser.add_argument("--task", type=int)
    view_parser.add_argument("--thread", type=int)
    view_parser.set_defaults(func=cmd_view)

    list_parser = subparsers.add_parser("list", help="List active reviews")
    list_parser.set_defaults(func=cmd_list)

    wait_parser = subparsers.add_parser("wait", help="Wait for review events")
    wait_parser.add_argument("--token", required=True)
    wait_parser.set_defaults(func=cmd_wait)

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
