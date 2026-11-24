from __future__ import annotations

import argparse

from app.auth.service import auth_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first admin user for the demo app")
    parser.add_argument("username", help="Admin username")
    parser.add_argument("password", help="Admin password")
    args = parser.parse_args()

    try:
        user = auth_service.register_user(args.username, args.password, role="admin")
        print(f"Admin user created: {user.username} ({user.role})")
    except ValueError as exc:
        print(f"Failed: {exc}")


if __name__ == "__main__":
    main()
