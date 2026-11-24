import argparse
import csv
import re
import sqlite3
import sys

# Practical email check: local@domain.tld, no spaces, one @
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email)) and ".." not in email


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:   # utf-8-sig strips Excel BOM
        reader = csv.DictReader(f)
        # normalise headers so "name", "Name ", "EMAIL" all work
        reader.fieldnames = [h.strip().lower() for h in (reader.fieldnames or [])]
        if not {"name", "email"} <= set(reader.fieldnames):
            raise ValueError("CSV must have 'Name' and 'Email' columns")
        return list(reader)


def create_database(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE   -- duplicates rejected case-insensitively
        )
        """
    )
    conn.commit()
    return conn


def import_users(conn: sqlite3.Connection, rows: list[dict]) -> dict:
    stats = {"inserted": [], "invalid": [], "duplicate": []}
    for line_no, row in enumerate(rows, start=2):            # line 1 is the header
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip().lower()

        if not name or not is_valid_email(email):
            stats["invalid"].append((line_no, name, email))
            continue
        try:
            conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
            stats["inserted"].append((name, email))
        except sqlite3.IntegrityError:                        # UNIQUE(email) violated
            stats["duplicate"].append((line_no, name, email))
    conn.commit()
    return stats


def display_users(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT id, name, email FROM users ORDER BY id").fetchall()
    print(f"\n{'ID':>3}  {'Name':<15}  {'Email':<30}")
    print("-" * 52)
    for user_id, name, email in rows:
        print(f"{user_id:>3}  {name:<15}  {email:<30}")
    print(f"\nTotal users in database: {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import users from CSV into SQLite")
    parser.add_argument("--csv", default="users.csv", help="input CSV file")
    parser.add_argument("--db", default="users.db", help="SQLite database file")
    args = parser.parse_args()

    try:
        rows = read_csv(args.csv)
    except FileNotFoundError:
        sys.exit(f"CSV file not found: {args.csv}")
    except ValueError as exc:
        sys.exit(str(exc))

    print(f"Read {len(rows)} row(s) from {args.csv}")
    conn = create_database(args.db)
    try:
        stats = import_users(conn, rows)

        print(f"Inserted : {len(stats['inserted'])}")
        for name, email in stats["inserted"]:
            print(f"  + {name} <{email}>")
        print(f"Duplicate: {len(stats['duplicate'])}")
        for line_no, name, email in stats["duplicate"]:
            print(f"  ~ line {line_no}: {name} <{email}> already exists, skipped")
        print(f"Invalid  : {len(stats['invalid'])}")
        for line_no, name, email in stats["invalid"]:
            print(f"  ! line {line_no}: '{name}' <{email}> failed validation, skipped")

        display_users(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
