# Python Data Tasks: API → SQLite, Scores Visualization, CSV Import

## Setup
```bash
pip install -r requirements.txt
```
Python 3.9+ is required. `sqlite3`, `csv` and `json` are part of the standard library.

## Problem 1: Books API → SQLite
```bash
python problem1_books_api.py                          # query "python programming", 10 books
python problem1_books_api.py --query "tolkien" --limit 15
```
**Flow:** Open Library REST API → JSON parsing (`requests` + `.json()`) → `books.db` → `books` table →
parameterised `INSERT` → `SELECT` + formatted table output.

- Table: `books(id, ol_key UNIQUE, title, author, publication_year)`
- Running the script again doesn't create duplicates: `INSERT OR IGNORE` checks the Open Library work key.
- Missing authors become `Unknown`, a missing year becomes `NULL` and shows as `N/A`, and records with no title are skipped.
- Network errors, HTTP errors and invalid JSON exit with a clear message.

## Problem 2: Student scores + bar chart
```bash
python problem2_student_scores.py                     # uses the bundled mock API
python problem2_student_scores.py --url http://host/api/students
```
There isn't a public student-scores API, so `mock_scores_api.py` serves the data over real HTTP.
The script starts it automatically. You can also run it yourself with `python mock_scores_api.py`
(port 8000). Any endpoint that returns `[{"name":..., "score":...}]` or `{"students": [...]}` works.

**Output:** a per-student table, the highest and lowest scores, the **average score**, and
`student_scores.png`. The chart is sorted by score, shows a value on each bar, draws a dashed
average line, and colours bars by whether they're above or below the average. Non-numeric scores
are skipped with a warning.

## Problem 3: CSV → SQLite
```bash
python problem3_csv_import.py                         # users.csv -> users.db
python problem3_csv_import.py --csv other.csv --db other.db
```
- `users.csv` contains Rahul, Priya and Amit.
- Table: `users(id, name, email UNIQUE COLLATE NOCASE)`
- Each email is checked with a regex. Rows with an invalid email or an empty name are skipped and reported with their line number.
- Duplicate emails are caught by the `UNIQUE` constraint (`IntegrityError`), skipped and reported. The check ignores case, so `RAHUL@example.com` counts as a duplicate of `rahul@example.com`.
- Prints a summary of inserted, duplicate and invalid rows, then every stored record.
