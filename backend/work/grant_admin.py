"""Grant administrator access to an existing account from a trusted shell.

Usage: python grant_admin.py user@company.com
"""
import sys

from db import get_database, init_db


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python grant_admin.py user@company.com")
    email = sys.argv[1].strip().lower()
    init_db()
    result = get_database().users.update_one({"email": email, "active": True}, {"$set": {"role": "admin"}})
    if result.matched_count != 1:
        raise SystemExit("No active account found for that email.")
    print(f"Granted administrator access to {email}. Sign out and back in for it to take effect.")


if __name__ == "__main__":
    main()
