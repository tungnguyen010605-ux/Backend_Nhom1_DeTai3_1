from __future__ import annotations

import argparse
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = Path("Bend/data/app.db")


def _cleanup_basic(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TEMP TABLE cleanup_users AS
        SELECT id
        FROM user_profiles
        WHERE LOWER(name) IN ('test user', 'second user', 'string')
           OR name GLOB 'User *'
        """
    )

    cur.execute("DELETE FROM body_measurements WHERE user_id IN (SELECT id FROM cleanup_users)")
    cur.execute(
        """
        DELETE FROM clothing_items
        WHERE user_id IN (SELECT id FROM cleanup_users)
           OR LOWER(category) = 'string'
           OR LOWER(size_label) = 'string'
           OR LOWER(color) = 'string'
        """
    )
    cur.execute("DELETE FROM user_profiles WHERE id IN (SELECT id FROM cleanup_users)")


def _cleanup_strict(cur: sqlite3.Cursor) -> None:
    # Remove users that have no body measurements; these are usually incomplete/test profiles.
    cur.execute(
        """
        DELETE FROM clothing_items
        WHERE user_id IN (
            SELECT u.id
            FROM user_profiles u
            LEFT JOIN body_measurements bm ON bm.user_id = u.id
            GROUP BY u.id
            HAVING COUNT(bm.id) = 0
        )
        """
    )
    cur.execute(
        """
        DELETE FROM user_profiles
        WHERE id IN (
            SELECT u.id
            FROM user_profiles u
            LEFT JOIN body_measurements bm ON bm.user_id = u.id
            GROUP BY u.id
            HAVING COUNT(bm.id) = 0
        )
        """
    )

    # Deduplicate same-name users by keeping only the highest id (newest row).
    cur.execute(
        """
        CREATE TEMP TABLE duplicate_users AS
        SELECT u.id
        FROM user_profiles u
        JOIN (
            SELECT name, MAX(id) AS keep_id
            FROM user_profiles
            GROUP BY name
            HAVING COUNT(*) > 1
        ) g ON g.name = u.name
        WHERE u.id <> g.keep_id
        """
    )
    cur.execute("DELETE FROM body_measurements WHERE user_id IN (SELECT id FROM duplicate_users)")
    cur.execute("DELETE FROM clothing_items WHERE user_id IN (SELECT id FROM duplicate_users)")
    cur.execute("DELETE FROM user_profiles WHERE id IN (SELECT id FROM duplicate_users)")

    # Remove placeholder colors like 'Color 5'.
    cur.execute("DELETE FROM clothing_items WHERE color GLOB 'Color *'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cleanup test/trash records from Bend/data/app.db")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Apply stronger cleanup: remove users without measurements and deduplicate by name.",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    backup_path = DB_PATH.with_name(f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy2(DB_PATH, backup_path)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print(f"backup: {backup_path}")
    for table_name in ("user_profiles", "clothing_items", "body_measurements"):
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        print("before", table_name, cur.fetchone()[0])

    _cleanup_basic(cur)
    if args.strict:
        _cleanup_strict(cur)

    conn.commit()

    for table_name in ("user_profiles", "clothing_items", "body_measurements"):
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        print("after", table_name, cur.fetchone()[0])

    print("remaining users:")
    for user_id, name in cur.execute("SELECT id, name FROM user_profiles ORDER BY id"):
        print(user_id, name)

    conn.close()


if __name__ == "__main__":
    main()
