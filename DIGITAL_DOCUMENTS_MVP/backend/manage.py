#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys

from lexima_dms.app_core.config import get_settings
from lexima_dms.app_core.security import hash_password
from lexima_dms.db.init_db import init_db
from lexima_dms.db.models import User, UserRole
from lexima_dms.db.session import db_session


def cmd_init_db(_: argparse.Namespace) -> int:
    get_settings().ensure_dirs()
    init_db()
    print("OK: database initialized")
    return 0


def cmd_create_user(args: argparse.Namespace) -> int:
    role = UserRole(args.role)
    db = db_session()
    try:
        existing = db.query(User).filter(User.username == args.username).one_or_none()
        if existing:
            print("ERR: user already exists", file=sys.stderr)
            return 2

        if getattr(args, "ad", False):
            # AD-only user: will authenticate via LDAP/AD DS
            password_hash = ""
        elif not args.password:
            print("ERR: password required for local users", file=sys.stderr)
            return 2
        else:
            password_hash = hash_password(args.password)

        u = User(
            username=args.username,
            password_hash=password_hash,
            role=role,
        )
        db.add(u)
        db.commit()
        auth_note = " (AD/LDAP)" if getattr(args, "ad", False) else ""
        print(f"OK: user created id={u.id} username={u.username} role={u.role.value}{auth_note}")
        return 0
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="manage.py", description="DIGITAL DOCUMENTS MVP management CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-db", help="Create data dir and initialize sqlite schema")
    p_init.set_defaults(func=cmd_init_db)

    p_user = sub.add_parser("create-user", help="Create a user")
    p_user.add_argument("--username", required=True)
    p_user.add_argument("--password", default="", help="Password (empty for --ad)")
    p_user.add_argument(
        "--role",
        default=UserRole.author.value,
        choices=[r.value for r in UserRole],
        help="User role",
    )
    p_user.add_argument(
        "--ad",
        action="store_true",
        help="AD/LDAP user: no local password, auth via Active Directory",
    )
    p_user.set_defaults(func=cmd_create_user)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

