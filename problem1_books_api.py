import argparse
import sqlite3
import sys

import requests

API_URL = "https://openlibrary.org/search.json"
TIMEOUT_SECONDS = 15


# ---------- fetch and parse ----------
def fetch_books(query: str, limit: int, api_url: str = API_URL) -> list[dict]:
    """Call the REST API and return the raw JSON 'docs' list."""
    params = {
        "q": query,
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year",
    }
    response = requests.get(api_url, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()          # raise on 4xx / 5xx
    payload = response.json()            # JSON -> Python dict
    return payload.get("docs", [])


def parse_books(docs: list[dict]) -> list[tuple]:
    """Turn raw API records into clean (key, title, author, year) tuples."""
    books = []
    for doc in docs:
        title = (doc.get("title") or "").strip()
        if not title:
            continue                      # skip records with no title
        authors = doc.get("author_name") or ["Unknown"]
        year = doc.get("first_publish_year")   # may be missing -> NULL
        books.append((doc.get("key"), title, ", ".join(authors), year))
    return books


# ---------- database and table ----------
def create_database(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            ol_key           TEXT UNIQUE,          -- Open Library work id, prevents duplicates
            title            TEXT NOT NULL,
            author           TEXT NOT NULL,
            publication_year INTEGER
        )
        """
    )
    conn.commit()
    return conn


# ---------- 5: insert ----------
def insert_books(conn: sqlite3.Connection, books: list[tuple]) -> int:
    """Insert books with a parameterised query; re-runs skip existing rows."""
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO books (ol_key, title, author, publication_year) "
        "VALUES (?, ?, ?, ?)",
        books,
    )
    conn.commit()
    return conn.total_changes - before


# ---------- 6: retrieve and display ----------
def fetch_stored_books(conn: sqlite3.Connection) -> list[tuple]:
    cursor = conn.execute(
        "SELECT id, title, author, publication_year FROM books "
        "ORDER BY publication_year IS NULL, publication_year, title"
    )
    return cursor.fetchall()


def display_books(rows: list[tuple]) -> None:
    if not rows:
        print("No books stored.")
        return

    def cut(text, width):
        text = str(text)
        return text if len(text) <= width else text[: width - 3] + "..."

    header = f"{'ID':>3}  {'Title':<45}  {'Author':<28}  {'Year':>4}"
    print(header)
    print("-" * len(header))
    for book_id, title, author, year in rows:
        print(f"{book_id:>3}  {cut(title, 45):<45}  {cut(author, 28):<28}  {year or 'N/A':>4}")
    print(f"\nTotal books in database: {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch books from Open Library into SQLite")
    parser.add_argument("--query", default="python programming", help="search term")
    parser.add_argument("--limit", type=int, default=10, help="number of books to fetch")
    parser.add_argument("--db", default="books.db", help="SQLite database file")
    parser.add_argument("--api-url", default=API_URL, help=argparse.SUPPRESS)
    args = parser.parse_args()

    print(f"Fetching up to {args.limit} books for '{args.query}' from Open Library...")
    try:
        docs = fetch_books(args.query, args.limit, args.api_url)
    except requests.RequestException as exc:
        sys.exit(f"API request failed: {exc}")
    except ValueError:
        sys.exit("API returned a response that is not valid JSON.")

    books = parse_books(docs)
    print(f"Received {len(docs)} records, {len(books)} valid after parsing.")

    conn = create_database(args.db)
    try:
        inserted = insert_books(conn, books)
        print(f"Inserted {inserted} new books into '{args.db}' "
              f"({len(books) - inserted} already existed).\n")
        display_books(fetch_stored_books(conn))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
