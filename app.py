from __future__ import annotations

import sqlite3
from functools import wraps
from pathlib import Path
from typing import Optional

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "library.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-key-change-me"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def search_books(
    conn: sqlite3.Connection,
    title: str = "",
    author: str = "",
    isbn: str = "",
    publisher: str = "",
    publication_year: str = "",
) -> list[sqlite3.Row]:
    query = """
        SELECT id, title, author, isbn, publisher, publication_year, total_copies, available_copies
        FROM books
    """
    clauses: list[str] = []
    params: list[str] = []

    if title:
        clauses.append("title LIKE ?")
        params.append(f"%{title}%")
    if author:
        clauses.append("author LIKE ?")
        params.append(f"%{author}%")
    if isbn:
        clauses.append("isbn LIKE ?")
        params.append(f"%{isbn}%")
    if publisher:
        clauses.append("publisher LIKE ?")
        params.append(f"%{publisher}%")
    if publication_year:
        clauses.append("CAST(publication_year AS TEXT) LIKE ?")
        params.append(f"%{publication_year}%")

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY publication_year DESC, title ASC"
    return conn.execute(query, tuple(params)).fetchall()


def init_db() -> None:
    with get_db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE,
                publisher TEXT,
                publication_year INTEGER,
                total_copies INTEGER NOT NULL CHECK(total_copies >= 0),
                available_copies INTEGER NOT NULL CHECK(available_copies >= 0)
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                user_type TEXT NOT NULL DEFAULT 'adherent',
                role TEXT NOT NULL DEFAULT 'user',
                password_hash TEXT
            );

            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                loan_date TEXT NOT NULL DEFAULT (date('now')),
                due_date TEXT,
                return_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS loan_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                request_date TEXT NOT NULL DEFAULT (date('now')),
                status TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                reservation_date TEXT NOT NULL DEFAULT (date('now')),
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            );
            """
        )

        if not _column_exists(conn, "users", "role"):
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

        if not _column_exists(conn, "users", "password_hash"):
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

        if not _column_exists(conn, "books", "publisher"):
            conn.execute("ALTER TABLE books ADD COLUMN publisher TEXT")

        if not _column_exists(conn, "books", "publication_year"):
            conn.execute("ALTER TABLE books ADD COLUMN publication_year INTEGER")

        admin = conn.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()
        if admin is None:
            conn.execute(
                """
                INSERT INTO users(full_name, email, phone, user_type, role, password_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "Administrateur",
                    "admin@bibliotheque.local",
                    None,
                    "administrateur",
                    "admin",
                    generate_password_hash("admin1234"),
                ),
            )


def get_current_user() -> Optional[sqlite3.Row]:
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Veuillez vous connecter.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None or user["role"] != "admin":
            flash("Acces reserve a l'administrateur.", "error")
            return redirect(url_for("user_dashboard"))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_user():
    return {"session_user": get_current_user()}


@app.route("/")
def home():
    user = get_current_user()
    if user is None:
        return redirect(url_for("login"))
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("user_dashboard"))


@app.route("/catalog")
@login_required
def catalog():
    filters = {
        "title": request.args.get("title", "").strip(),
        "author": request.args.get("author", "").strip(),
        "isbn": request.args.get("isbn", "").strip(),
        "publisher": request.args.get("publisher", "").strip(),
        "publication_year": request.args.get("publication_year", "").strip(),
    }
    with get_db_connection() as conn:
        filtered_books = search_books(conn, **filters)

    return render_template("catalog.html", books=filtered_books, filters=filters)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip() or None
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not full_name or not email or not password:
            flash("Tous les champs obligatoires doivent etre remplis.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caracteres.", "error")
            return redirect(url_for("register"))

        if password != password_confirm:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for("register"))

        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users(full_name, email, phone, user_type, role, password_hash)
                    VALUES (?, ?, ?, 'adherent', 'user', ?)
                    """,
                    (full_name, email, phone, generate_password_hash(password)),
                )
            flash("Compte cree. Connectez-vous.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Cet email est deja utilise.", "error")
            return redirect(url_for("register"))

    return render_template("register.html", title="Inscription")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not user["password_hash"]:
            flash("Identifiants invalides.", "error")
            return redirect(url_for("login"))

        if not check_password_hash(user["password_hash"], password):
            flash("Identifiants invalides.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))

    return render_template("login.html", title="Connexion")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Session fermee.", "success")
    return redirect(url_for("login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db_connection() as conn:
        stats = {
            "books": conn.execute("SELECT COUNT(*) AS c FROM books").fetchone()["c"],
            "users": conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'user'").fetchone()["c"],
            "active_loans": conn.execute(
                "SELECT COUNT(*) AS c FROM loans WHERE return_date IS NULL"
            ).fetchone()["c"],
            "pending_requests": conn.execute(
                "SELECT COUNT(*) AS c FROM loan_requests WHERE status = 'pending'"
            ).fetchone()["c"],
            "active_reservations": conn.execute(
                "SELECT COUNT(*) AS c FROM reservations WHERE status = 'active'"
            ).fetchone()["c"],
        }

        recent_loans = conn.execute(
            """
            SELECT l.id, b.title AS book_title, u.full_name AS user_name,
                   l.loan_date, l.return_date
            FROM loans l
            JOIN books b ON b.id = l.book_id
            JOIN users u ON u.id = l.user_id
            ORDER BY l.id DESC
            LIMIT 10
            """
        ).fetchall()

    return render_template("dashboard.html", stats=stats, recent_loans=recent_loans)


@app.route("/me")
@login_required
def user_dashboard():
    user = get_current_user()
    if user and user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    with get_db_connection() as conn:
        my_active_loans = conn.execute(
            """
            SELECT l.id, l.loan_date, l.due_date, b.title AS book_title
            FROM loans l
            JOIN books b ON b.id = l.book_id
            WHERE l.user_id = ? AND l.return_date IS NULL
            ORDER BY l.id DESC
            """,
            (user["id"],),
        ).fetchall()

        my_history = conn.execute(
            """
            SELECT l.id, l.loan_date, l.return_date, b.title AS book_title
            FROM loans l
            JOIN books b ON b.id = l.book_id
            WHERE l.user_id = ?
            ORDER BY l.id DESC
            LIMIT 20
            """,
            (user["id"],),
        ).fetchall()

        my_requests = conn.execute(
            """
            SELECT r.id, r.request_date, r.status, b.title AS book_title
            FROM loan_requests r
            JOIN books b ON b.id = r.book_id
            WHERE r.user_id = ?
            ORDER BY r.id DESC
            """,
            (user["id"],),
        ).fetchall()

        my_reservations = conn.execute(
            """
            SELECT r.id, r.reservation_date, r.status, b.title AS book_title
            FROM reservations r
            JOIN books b ON b.id = r.book_id
            WHERE r.user_id = ?
            ORDER BY r.id DESC
            """,
            (user["id"],),
        ).fetchall()

        books_list = conn.execute(
            "SELECT id, title, author, publication_year, available_copies FROM books ORDER BY title"
        ).fetchall()

    return render_template(
        "user_dashboard.html",
        my_active_loans=my_active_loans,
        my_history=my_history,
        my_requests=my_requests,
        my_reservations=my_reservations,
        books=books_list,
    )


@app.post("/me/loan-requests")
@login_required
def create_loan_request():
    user = get_current_user()
    if user and user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    book_id = request.form.get("book_id")
    if not book_id:
        flash("Selectionnez un ouvrage.", "error")
        return redirect(url_for("catalog"))

    with get_db_connection() as conn:
        existing = conn.execute(
            """
            SELECT id FROM loan_requests
            WHERE user_id = ? AND book_id = ? AND status = 'pending'
            """,
            (user["id"], book_id),
        ).fetchone()
        if existing:
            flash("Vous avez deja une demande en attente pour cet ouvrage.", "error")
            return redirect(url_for("catalog"))

        conn.execute(
            "INSERT INTO loan_requests(user_id, book_id) VALUES (?, ?)",
            (user["id"], book_id),
        )

    flash("Demande d'emprunt envoyee a l'administrateur.", "success")
    return redirect(url_for("catalog"))


@app.post("/me/reservations")
@login_required
def create_reservation():
    user = get_current_user()
    if user and user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    book_id = request.form.get("book_id")
    if not book_id:
        flash("Selectionnez un ouvrage.", "error")
        return redirect(url_for("catalog"))

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO reservations(user_id, book_id) VALUES (?, ?)",
            (user["id"], book_id),
        )

    flash("Reservation enregistree.", "success")
    return redirect(url_for("catalog"))


@app.post("/me/reservations/<int:reservation_id>/cancel")
@login_required
def cancel_own_reservation(reservation_id: int):
    user = get_current_user()
    if user and user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE reservations
            SET status = 'closed'
            WHERE id = ? AND user_id = ? AND status = 'active'
            """,
            (reservation_id, user["id"]),
        )

    flash("Reservation annulee.", "success")
    return redirect(url_for("user_dashboard"))


@app.route("/books", methods=["GET", "POST"])
@admin_required
def books():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip() or None
        publisher = request.form.get("publisher", "").strip() or None
        publication_year_raw = request.form.get("publication_year", "").strip()
        publication_year = int(publication_year_raw) if publication_year_raw.isdigit() else None

        try:
            total_copies = int(request.form.get("total_copies", "1"))
        except ValueError:
            total_copies = -1

        if not title or not author or total_copies < 1:
            flash("Titre, auteur et nombre d'exemplaires valides sont requis.", "error")
            return redirect(url_for("books"))

        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO books(
                        title, author, isbn, publisher, publication_year, total_copies, available_copies
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, author, isbn, publisher, publication_year, total_copies, total_copies),
                )
            flash("Ouvrage ajoute.", "success")
        except sqlite3.IntegrityError:
            flash("ISBN deja existant ou donnees invalides.", "error")

        return redirect(url_for("books"))

    filters = {
        "title": request.args.get("title", "").strip(),
        "author": request.args.get("author", "").strip(),
        "isbn": request.args.get("isbn", "").strip(),
        "publisher": request.args.get("publisher", "").strip(),
        "publication_year": request.args.get("publication_year", "").strip(),
    }

    with get_db_connection() as conn:
        all_books = search_books(conn, **filters)

    return render_template("books.html", books=all_books, filters=filters)


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip() or None
        user_type = request.form.get("user_type", "adherent").strip() or "adherent"
        role = request.form.get("role", "user").strip() or "user"
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("Nom, email et mot de passe sont obligatoires.", "error")
            return redirect(url_for("users"))

        if role not in {"user", "admin"}:
            flash("Role invalide.", "error")
            return redirect(url_for("users"))

        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users(full_name, email, phone, user_type, role, password_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (full_name, email, phone, user_type, role, generate_password_hash(password)),
                )
            flash("Compte cree.", "success")
        except sqlite3.IntegrityError:
            flash("Email deja utilise.", "error")

        return redirect(url_for("users"))

    with get_db_connection() as conn:
        all_users = conn.execute(
            "SELECT id, full_name, email, phone, user_type, role FROM users ORDER BY id DESC"
        ).fetchall()

    return render_template("users.html", users=all_users)


@app.route("/loans", methods=["GET", "POST"])
@admin_required
def loans():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "approve_request":
            request_id = request.form.get("request_id")
            due_date = request.form.get("due_date", "").strip() or None
            if not request_id:
                flash("Demande invalide.", "error")
                return redirect(url_for("loans"))

            with get_db_connection() as conn:
                req = conn.execute(
                    """
                    SELECT id, user_id, book_id, status
                    FROM loan_requests
                    WHERE id = ?
                    """,
                    (request_id,),
                ).fetchone()
                if req is None or req["status"] != "pending":
                    flash("Demande introuvable ou deja traitee.", "error")
                    return redirect(url_for("loans"))

                book = conn.execute(
                    "SELECT id, available_copies FROM books WHERE id = ?",
                    (req["book_id"],),
                ).fetchone()
                if book is None or book["available_copies"] < 1:
                    flash("Aucun exemplaire disponible.", "error")
                    return redirect(url_for("loans"))

                conn.execute(
                    "UPDATE loan_requests SET status = 'approved' WHERE id = ?",
                    (request_id,),
                )
                conn.execute(
                    """
                    INSERT INTO loans(user_id, book_id, loan_date, due_date)
                    VALUES (?, ?, date('now'), ?)
                    """,
                    (req["user_id"], req["book_id"], due_date),
                )
                conn.execute(
                    "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
                    (req["book_id"],),
                )

            flash("Demande approuvee et emprunt cree.", "success")
            return redirect(url_for("loans"))

        if action == "reject_request":
            request_id = request.form.get("request_id")
            if not request_id:
                flash("Demande invalide.", "error")
                return redirect(url_for("loans"))

            with get_db_connection() as conn:
                conn.execute(
                    """
                    UPDATE loan_requests
                    SET status = 'rejected'
                    WHERE id = ? AND status = 'pending'
                    """,
                    (request_id,),
                )

            flash("Demande rejetee.", "success")
            return redirect(url_for("loans"))

        if action == "return":
            loan_id = request.form.get("loan_id")
            if not loan_id:
                flash("Emprunt invalide.", "error")
                return redirect(url_for("loans"))

            with get_db_connection() as conn:
                loan = conn.execute(
                    "SELECT id, book_id, return_date FROM loans WHERE id = ?",
                    (loan_id,),
                ).fetchone()

                if loan is None:
                    flash("Emprunt introuvable.", "error")
                    return redirect(url_for("loans"))

                if loan["return_date"] is not None:
                    flash("Cet emprunt est deja retourne.", "error")
                    return redirect(url_for("loans"))

                conn.execute(
                    "UPDATE loans SET return_date = date('now') WHERE id = ?",
                    (loan_id,),
                )
                conn.execute(
                    "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
                    (loan["book_id"],),
                )

            flash("Retour enregistre.", "success")
            return redirect(url_for("loans"))

    with get_db_connection() as conn:
        pending_requests = conn.execute(
            """
            SELECT r.id, r.request_date, r.status,
                   u.full_name AS user_name,
                   b.title AS book_title,
                   b.available_copies AS available_copies
            FROM loan_requests r
            JOIN users u ON u.id = r.user_id
            JOIN books b ON b.id = r.book_id
            WHERE r.status = 'pending'
            ORDER BY r.id DESC
            """
        ).fetchall()

        active_loans = conn.execute(
            """
            SELECT l.id, l.loan_date, l.due_date,
                   b.title AS book_title,
                   u.full_name AS user_name
            FROM loans l
            JOIN books b ON b.id = l.book_id
            JOIN users u ON u.id = l.user_id
            WHERE l.return_date IS NULL
            ORDER BY l.loan_date DESC, l.id DESC
            """
        ).fetchall()

        loan_history = conn.execute(
            """
            SELECT l.id, l.loan_date, l.return_date,
                   b.title AS book_title,
                   u.full_name AS user_name
            FROM loans l
            JOIN books b ON b.id = l.book_id
            JOIN users u ON u.id = l.user_id
            ORDER BY l.id DESC
            LIMIT 30
            """
        ).fetchall()

    return render_template(
        "loans.html",
        pending_requests=pending_requests,
        active_loans=active_loans,
        loan_history=loan_history,
    )


@app.route("/reservations")
@admin_required
def reservations():
    with get_db_connection() as conn:
        reservations_list = conn.execute(
            """
            SELECT r.id, r.reservation_date, r.status,
                   b.title AS book_title,
                   u.full_name AS user_name
            FROM reservations r
            JOIN books b ON b.id = r.book_id
            JOIN users u ON u.id = r.user_id
            ORDER BY r.id DESC
            """
        ).fetchall()

    return render_template("reservations.html", reservations=reservations_list)


@app.post("/reservations/<int:reservation_id>/close")
@admin_required
def close_reservation(reservation_id: int):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE reservations SET status = 'closed' WHERE id = ?",
            (reservation_id,),
        )
    flash("Reservation cloturee.", "success")
    return redirect(url_for("reservations"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
