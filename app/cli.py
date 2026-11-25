"""Administrative command line: create the first administrator account."""
import argparse
import getpass
import os
import sys

from sqlalchemy import select

from app.db.models import User
from app.db.session import transaction
from app.security import hash_password


def create_admin(login: str, password: str) -> int:
    login = login.strip()
    if not login:
        print("Ошибка: укажите логин.", file=sys.stderr)
        return 2
    if len(password) < 8:
        print("Ошибка: пароль должен быть не короче 8 символов.", file=sys.stderr)
        return 2
    with transaction() as session:
        if session.scalar(select(User.id).where(User.login == login)) is not None:
            print(f"Ошибка: пользователь {login!r} уже существует.", file=sys.stderr)
            return 1
        session.add(User(login=login, password_hash=hash_password(password),
                         role="administrator"))
    print(f"Администратор {login!r} создан.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli",
                                     description="Служебные команды StudentLedger")
    sub = parser.add_subparsers(dest="command", required=True)
    admin = sub.add_parser("create-admin", help="создать администратора")
    admin.add_argument("--login", required=True)
    admin.add_argument("--password", help="необязательно; иначе ADMIN_PASSWORD или запрос")
    args = parser.parse_args(argv)

    if args.command == "create-admin":
        password = args.password or os.environ.get("ADMIN_PASSWORD")
        if not password:
            password = getpass.getpass("Пароль администратора: ")
            confirm = getpass.getpass("Повторите пароль: ")
            if password != confirm:
                print("Ошибка: пароли не совпадают.", file=sys.stderr)
                return 2
        return create_admin(args.login, password)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
