from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date, datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "library_secret_key_2024"

DB_PATH = "library.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT,
        genre TEXT,
        total_copies INTEGER DEFAULT 1,
        available_copies INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        joined_on TEXT DEFAULT CURRENT_DATE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id TEXT NOT NULL,
        book_id INTEGER NOT NULL,
        issued_on TEXT NOT NULL,
        due_date TEXT NOT NULL,
        returned_on TEXT,
        status TEXT DEFAULT 'issued',
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    )''')

    # Sample data
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ("Wings of Fire", "A.P.J. Abdul Kalam", "978-81-7371-146-6", "Biography", 3, 3),
            ("The God of Small Things", "Arundhati Roy", "978-0-8129-7217-5", "Fiction", 2, 2),
            ("Godan", "Munshi Premchand", "978-81-7009-154-3", "Fiction", 4, 4),
            ("Discovery of India", "Jawaharlal Nehru", "978-0-14-013353-0", "History", 2, 2),
            ("Python Programming", "Mark Lutz", "978-1-4493-5573-9", "Technology", 3, 3),
        ]
        c.executemany(
            "INSERT INTO books (title, author, isbn, genre, total_copies, available_copies) VALUES (?,?,?,?,?,?)",
            sample_books
        )

    c.execute("SELECT COUNT(*) FROM members")
    if c.fetchone()[0] == 0:
        sample_members = [
            ("MEM001", "Priya Verma", "9876543210", "priya@email.com"),
            ("MEM002", "Arjun Singh", "9123456780", "arjun@email.com"),
        ]
        c.executemany(
            "INSERT INTO members (id, name, phone, email) VALUES (?,?,?,?)",
            sample_members
        )

    conn.commit()
    conn.close()


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_db()
    stats = {
        "total_books": conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "total_members": conn.execute("SELECT COUNT(*) FROM members").fetchone()[0],
        "total_issued": conn.execute("SELECT COUNT(*) FROM issues WHERE status='issued'").fetchone()[0],
        "overdue": conn.execute(
            "SELECT COUNT(*) FROM issues WHERE status='issued' AND due_date < ?", (str(date.today()),)
        ).fetchone()[0],
    }
    recent = conn.execute('''
        SELECT i.*, m.name AS member_name, b.title AS book_title
        FROM issues i
        JOIN members m ON i.member_id = m.id
        JOIN books b ON i.book_id = b.id
        ORDER BY i.id DESC LIMIT 5
    ''').fetchall()
    conn.close()
    return render_template("index.html", stats=stats, recent=recent, today=str(date.today()))


# ─── BOOKS ────────────────────────────────────────────────────────────────────

@app.route("/books")
def books():
    conn = get_db()
    search = request.args.get("q", "")
    genre = request.args.get("genre", "")
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if genre:
        query += " AND genre = ?"
        params.append(genre)
    query += " ORDER BY title"
    books_list = conn.execute(query, params).fetchall()
    genres = conn.execute("SELECT DISTINCT genre FROM books ORDER BY genre").fetchall()
    conn.close()
    return render_template("books.html", books=books_list, genres=genres, search=search, selected_genre=genre)


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        isbn = request.form.get("isbn", "").strip()
        genre = request.form.get("genre", "Other")
        copies = int(request.form.get("copies", 1))

        if not title or not author:
            flash("Title and Author are required!", "error")
            return redirect(url_for("add_book"))

        conn = get_db()
        conn.execute(
            "INSERT INTO books (title, author, isbn, genre, total_copies, available_copies) VALUES (?,?,?,?,?,?)",
            (title, author, isbn, genre, copies, copies)
        )
        conn.commit()
        conn.close()
        flash(f'"{title}" successfully added!', "success")
        return redirect(url_for("books"))

    return render_template("add_book.html")


@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = get_db()
    active = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE book_id=? AND status='issued'", (book_id,)
    ).fetchone()[0]
    if active:
        flash("This book is currently issued and cannot be deleted!", "error")
    else:
        conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        flash("Book deleted successfully.", "success")
    conn.close()
    return redirect(url_for("books"))


# ─── MEMBERS ──────────────────────────────────────────────────────────────────

@app.route("/members")
def members():
    conn = get_db()
    search = request.args.get("q", "")
    query = "SELECT * FROM members WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR id LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY name"
    members_list = conn.execute(query, params).fetchall()

    issued_counts = {}
    for row in conn.execute("SELECT member_id, COUNT(*) as cnt FROM issues WHERE status='issued' GROUP BY member_id"):
        issued_counts[row["member_id"]] = row["cnt"]

    conn.close()
    return render_template("members.html", members=members_list, issued_counts=issued_counts, search=search)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        mid = request.form["id"].strip().upper()
        name = request.form["name"].strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not mid or not name:
            flash("Member ID and Name are required!", "error")
            return redirect(url_for("add_member"))

        conn = get_db()
        existing = conn.execute("SELECT id FROM members WHERE id=?", (mid,)).fetchone()
        if existing:
            flash("This Member ID already exists!", "error")
            conn.close()
            return redirect(url_for("add_member"))

        conn.execute(
            "INSERT INTO members (id, name, phone, email) VALUES (?,?,?,?)",
            (mid, name, phone, email)
        )
        conn.commit()
        conn.close()
        flash(f"{name} successfully registered!", "success")
        return redirect(url_for("members"))

    return render_template("add_member.html")


@app.route("/members/delete/<member_id>", methods=["POST"])
def delete_member(member_id):
    conn = get_db()
    active = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE member_id=? AND status='issued'", (member_id,)
    ).fetchone()[0]
    if active:
        flash("This member currently has issued books and cannot be deleted!", "error")
    else:
        conn.execute("DELETE FROM members WHERE id=?", (member_id,))
        conn.commit()
        flash("Member Removed.", "success")
    conn.close()
    return redirect(url_for("members"))


# ─── ISSUE / RETURN ───────────────────────────────────────────────────────────

@app.route("/issue", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        member_id = request.form["member_id"]
        book_id = int(request.form["book_id"])
        due_date = request.form["due_date"]
        today = str(date.today())

        if due_date <= today:
            flash("Due date must be in the future!", "error")
            return redirect(url_for("issue_book"))

        conn = get_db()
        already = conn.execute(
            "SELECT id FROM issues WHERE member_id=? AND book_id=? AND status='issued'",
            (member_id, book_id)
        ).fetchone()
        if already:
            flash("This member has already issued this book!", "error")
            conn.close()
            return redirect(url_for("issue_book"))

        conn.execute(
            "INSERT INTO issues (member_id, book_id, issued_on, due_date, status) VALUES (?,?,?,?,'issued')",
            (member_id, book_id, today, due_date)
        )
        conn.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id=?", (book_id,)
        )
        book = conn.execute("SELECT title FROM books WHERE id=?", (book_id,)).fetchone()
        conn.commit()
        conn.close()
        flash(f'"{book["title"]}" successfully issued!', "success")
        return redirect(url_for("issue_book"))

    conn = get_db()
    members_list = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    books_list = conn.execute(
        "SELECT * FROM books WHERE available_copies > 0 ORDER BY title"
    ).fetchall()
    default_due = str(date.today() + timedelta(days=14))
    conn.close()
    return render_template("issue.html", members=members_list, books=books_list, default_due=default_due)


@app.route("/return", methods=["GET", "POST"])
def return_book():
    if request.method == "POST":
        issue_id = int(request.form["issue_id"])
        today = str(date.today())

        conn = get_db()
        issue = conn.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone()
        if not issue:
            flash("Record not found!", "error")
            conn.close()
            return redirect(url_for("return_book"))

        conn.execute(
            "UPDATE issues SET status='returned', returned_on=? WHERE id=?", (today, issue_id)
        )
        conn.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id=?", (issue["book_id"],)
        )
        book = conn.execute("SELECT title FROM books WHERE id=?", (issue["book_id"],)).fetchone()
        conn.commit()
        conn.close()
        flash(f'"{book["title"]}"successfully returned!', "success")
        return redirect(url_for("return_book"))

    conn = get_db()
    active_issues = conn.execute('''
        SELECT i.id, i.due_date, i.issued_on, m.name AS member_name, b.title AS book_title
        FROM issues i
        JOIN members m ON i.member_id = m.id
        JOIN books b ON i.book_id = b.id
        WHERE i.status = 'issued'
        ORDER BY i.due_date
    ''').fetchall()
    today = str(date.today())
    conn.close()
    return render_template("return.html", active_issues=active_issues, today=today)


# ─── RECORDS ──────────────────────────────────────────────────────────────────

@app.route("/records")
def records():
    conn = get_db()
    status_filter = request.args.get("status", "")
    query = '''
        SELECT i.*, m.name AS member_name, b.title AS book_title, b.author
        FROM issues i
        JOIN members m ON i.member_id = m.id
        JOIN books b ON i.book_id = b.id
        WHERE 1=1
    '''
    params = []
    if status_filter:
        query += " AND i.status = ?"
        params.append(status_filter)
    query += " ORDER BY i.id DESC"
    all_records = conn.execute(query, params).fetchall()
    today = str(date.today())
    conn.close()
    return render_template("records.html", records=all_records, today=today, status_filter=status_filter)


if __name__ == "__main__":
    init_db()
    print("\n✅ Library Management System started successfully!")
    print("🌐 open in browser: http://127.0.0.1:5000\n")
    app.run(debug=True)
