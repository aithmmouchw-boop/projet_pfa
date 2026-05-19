"""Crée la base MySQL (variables DB_* dans .env à la racine de PROJET_PYTHON)."""

import os
import re
from pathlib import Path

import pymysql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def main() -> None:
    name = os.environ.get("DB_NAME", "aesculia_db")
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise SystemExit("DB_NAME invalide (autorisé : lettres, chiffres, _).")

    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "3306"))
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "")

    conn = pymysql.connect(host=host, port=port, user=user, password=password)
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.commit()
    conn.close()
    print(f"Base MySQL « {name} » prête.")


if __name__ == "__main__":
    main()
