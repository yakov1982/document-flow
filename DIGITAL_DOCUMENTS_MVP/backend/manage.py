#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys

from lexima_dms.app_core.config import get_settings
from lexima_dms.app_core.security import hash_password
from lexima_dms.db.init_db import init_db
from lexima_dms.db.models import User, UserRole
from lexima_dms.db.session import db_session
from lexima_dms.services.license import activate_license, create_license


def cmd_init_db(_: argparse.Namespace) -> int:
    get_settings().ensure_dirs()
    init_db()
    print("OK: database initialized")
    return 0


def cmd_generate_license(args: argparse.Namespace) -> int:
    db = db_session()
    try:
        lic = create_license(db, expires_days=args.days)
        print(f"OK: License generated")
        print(f"  Key: {lic.license_key}")
        print(f"  Expires: {lic.expires_at.strftime('%Y-%m-%d')}")
        print(f"  Activate via: POST /license/activate with {{'license_key': '{lic.license_key}'}}")
        return 0
    finally:
        db.close()


def cmd_activate_license(args: argparse.Namespace) -> int:
    db = db_session()
    try:
        status = activate_license(db, args.key)
        if status.active:
            print(f"OK: {status.message}")
            return 0
        print(f"ERR: {status.message}", file=sys.stderr)
        return 2
    finally:
        db.close()


def cmd_create_user(args: argparse.Namespace) -> int:
    role = UserRole(args.role)
    db = db_session()
    try:
        existing = db.query(User).filter(User.username == args.username).one_or_none()
        if existing:
            print("ERR: user already exists", file=sys.stderr)
            return 2

        u = User(
            username=args.username,
            password_hash=hash_password(args.password),
            role=role,
        )
        db.add(u)
        db.commit()
        print(f"OK: user created id={u.id} username={u.username} role={u.role.value}")
        return 0
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="manage.py", description="DIGITAL DOCUMENTS MVP management CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-db", help="Create data dir and initialize sqlite schema")
    p_init.set_defaults(func=cmd_init_db)

    p_lic = sub.add_parser("generate-license", help="Generate a new license key")
    p_lic.add_argument("--days", type=int, default=365, help="License validity in days")
    p_lic.set_defaults(func=cmd_generate_license)

    p_act = sub.add_parser("activate-license", help="Activate license by key (CLI)")
    p_act.add_argument("--key", required=True, help="License key to activate")
    p_act.set_defaults(func=cmd_activate_license)

    p_user = sub.add_parser("create-user", help="Create a user")
    p_user.add_argument("--username", required=True)
    p_user.add_argument("--password", required=True)
    p_user.add_argument(
        "--role",
        default=UserRole.author.value,
        choices=[r.value for r in UserRole],
        help="User role",
    )
    p_user.set_defaults(func=cmd_create_user)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

