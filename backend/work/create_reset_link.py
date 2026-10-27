"""Generate a single-use password reset link from a trusted admin shell.

Usage: python create_reset_link.py user@company.com
Share the printed link with the user through a private channel.
"""
import secrets
import sys
import time

from api import FRONTEND_URL, _token_hash
from db import get_database, init_db


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python create_reset_link.py user@company.com")
    email = sys.argv[1].strip().lower()
    init_db()
    database = get_database()
    user = database.users.find_one({"email": email, "active": True}, {"_id": 0, "id": 1})
    if not user:
        raise SystemExit("No active account found for that email.")

    token = secrets.token_urlsafe(32)
    database.password_resets.delete_many({"user_id": user["id"]})
    database.password_resets.insert_one({"token_hash": _token_hash(token), "user_id": user["id"], "expires_at": int(time.time()) + 1800})

    base_url = FRONTEND_URL.rstrip("/")
    print(f"One-time reset link (expires in 30 minutes):\n{base_url}/?reset={token}")


if __name__ == "__main__":
    main()
