"""Provision a named user from a trusted administrator shell.

Usage: python create_user.py user@company.com "Full Name"
"""
import getpass
import re
import sys
from uuid import uuid4

from api import _password_hash
from db import get_database, init_db


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python create_user.py user@company.com "Full Name"')
    email, name = sys.argv[1].strip().lower(), sys.argv[2].strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not name:
        raise SystemExit("Enter a valid email address and a name.")
    password = getpass.getpass("Temporary password (12+ chars, upper/lowercase and number): ")
    if len(password) < 12 or not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        raise SystemExit("Password does not meet the requirements.")
    init_db()
    database = get_database()
    try:
        database.users.insert_one({"id": str(uuid4()), "email": email, "name": name, "password_hash": _password_hash(password), "role": "member", "active": True})
    except Exception as exc:
        raise SystemExit(f"Could not create account: {exc}") from exc
    print(f"Created account for {name} ({email}). Share the temporary password securely.")


if __name__ == "__main__":
    main()
