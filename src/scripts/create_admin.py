from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.auth.models import UserRole
from app.auth.service import AuthService, auth_service


def main(argv: list[str] | None = None, service: AuthService | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create an admin account or promote an existing user account."
    )
    parser.add_argument(
        "username",
        nargs="?",
        help="Admin username (prompted if omitted)",
    )
    args = parser.parse_args(argv)
    auth = service or auth_service

    username = (args.username or input("Admin username: ")).strip()
    try:
        auth._validate_username(username)
    except ValueError as exc:
        print(f"Could not create admin: {exc}", file=sys.stderr)
        return 1

    existing_user = auth.store.get_user(username)
    if existing_user is not None:
        if existing_user.role == UserRole.ADMIN.value:
            print(f"'{username}' is already an admin.")
            return 0

        print(f"'{username}' already has a regular user account.")
        password = getpass.getpass("Enter that account's password to promote it: ")
        if auth.authenticate_user(username, password) is None:
            print("Could not promote account: the password was not accepted.", file=sys.stderr)
            return 1
        auth.store.update_user(username, role=UserRole.ADMIN.value)
        print(f"Promoted '{username}' to admin.")
        return 0

    password = getpass.getpass("New admin password: ")
    confirmation = getpass.getpass("Confirm admin password: ")
    if password != confirmation:
        print("Could not create admin: passwords did not match.", file=sys.stderr)
        return 1

    try:
        user = auth.register_user(username, password, role=UserRole.ADMIN.value)
    except ValueError as exc:
        print(f"Could not create admin: {exc}", file=sys.stderr)
        return 1

    print(f"Admin account created for '{user.username}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
