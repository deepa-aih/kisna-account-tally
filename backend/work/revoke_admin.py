"""Remove administrator access from an account via a trusted backend shell.

Usage: python revoke_admin.py user@company.com
"""
import sys

from db import get_database, init_db


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python revoke_admin.py user@company.com")
    email = sys.argv[1].strip().lower()
    init_db()
    database = get_database()
    user = database.users.find_one({"email": email, "active": True})
    if not user:
        raise SystemExit("No active account found for that email.")
    if user["role"] != "admin":
        raise SystemExit("This account does not currently have administrator access.")

    admin_count = database.users.count_documents({"role": "admin", "active": True})
    if admin_count <= 1:
        raise SystemExit("Cannot remove access from the last active administrator. Grant admin access to another account first.")

    database.users.update_one({"id": user["id"]}, {"$set": {"role": "member"}})
    database.sessions.delete_many({"user_id": user["id"]})
    print(f"Removed administrator access from {email} and ended their active sessions. They can sign in again as a member.")


if __name__ == "__main__":
    main()
