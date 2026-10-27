"""Copy the current SQLite data into the configured MongoDB database.

This is safe to run more than once: documents are upserted by their existing IDs.
The original SQLite file is not modified or deleted.
"""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from db import get_database, init_db, store_job_sheets


SQLITE_PATH = Path(__file__).resolve().with_name("job_store.db")


def parse_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def parse_created_at(value):
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy users, sessions, password resets, and jobs from SQLite to MongoDB.")
    parser.add_argument("--sqlite-path", type=Path, default=SQLITE_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Report source row counts without writing to MongoDB.")
    args = parser.parse_args()
    if not args.sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {args.sqlite_path}")

    sqlite_conn = sqlite3.connect(args.sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    tables = {row[0] for row in sqlite_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts = {table: sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("users", "sessions", "password_resets", "jobs") if table in tables}
    if args.dry_run:
        print(f"SQLite source: {args.sqlite_path}")
        print(f"Rows to copy: {counts}")
        sqlite_conn.close()
        return

    init_db()
    mongo = get_database()

    if "users" in tables:
        for row in sqlite_conn.execute("SELECT * FROM users"):
            doc = dict(row)
            doc.setdefault("role", "member")
            doc.setdefault("active", 1)
            doc["active"] = bool(doc["active"])
            doc["created_at"] = parse_created_at(doc.get("created_at"))
            mongo.users.replace_one({"id": doc["id"]}, doc, upsert=True)

    if "sessions" in tables:
        for row in sqlite_conn.execute("SELECT token_hash,user_id,expires_at FROM sessions"):
            doc = dict(row)
            mongo.sessions.replace_one({"token_hash": doc["token_hash"]}, doc, upsert=True)

    if "password_resets" in tables:
        for row in sqlite_conn.execute("SELECT token_hash,user_id,expires_at FROM password_resets"):
            doc = dict(row)
            mongo.password_resets.replace_one({"token_hash": doc["token_hash"]}, doc, upsert=True)

    if "jobs" in tables:
        for row in sqlite_conn.execute("SELECT * FROM jobs"):
            source = dict(row)
            doc = {
                "id": source["id"],
                "jobCode": source.get("job_code"),
                "fileName": source.get("file_name"),
                "date": source.get("date"),
                "timeUTC": source.get("time_utc"),
                "fileSize": source.get("file_size"),
                "fileType": source.get("file_type"),
                "status": source.get("status"),
                "operator": source.get("operator"),
                "recordsCount": source.get("records_count"),
                "sha256Seal": source.get("sha256_seal"),
                "sourceFiles": parse_json(source.get("source_files"), []),
                "previewRows": parse_json(source.get("preview_rows"), []),
                "metrics": parse_json(source.get("metrics"), {}),
                "createdAt": parse_created_at(source.get("created_at")),
            }
            store_job_sheets(doc["id"], parse_json(source.get("sheet_data"), {}))
            mongo.jobs.replace_one({"id": doc["id"]}, doc, upsert=True)

    sqlite_conn.close()
    print(f"Copied SQLite rows to MongoDB: {counts}")
    print("The SQLite source was left unchanged. Verify the app against MongoDB before archiving it.")


if __name__ == "__main__":
    main()
