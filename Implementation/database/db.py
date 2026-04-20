"""
database/db.py
--------------
Handles SQLite database connection and schema initialization.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table (base for Librarian & Member)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            phone       TEXT,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL CHECK(role IN ('librarian','member'))
        )
    """)

    # Books / Catalog
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            author          TEXT    NOT NULL,
            isbn            TEXT    NOT NULL UNIQUE,
            category        TEXT,
            total_copies    INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Loan Records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS loan_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id   INTEGER NOT NULL REFERENCES users(id),
            book_id     INTEGER NOT NULL REFERENCES books(id),
            loan_date   TEXT    NOT NULL,
            due_date    TEXT    NOT NULL,
            return_date TEXT,
            status      TEXT    NOT NULL DEFAULT 'active' CHECK(status IN ('active','returned','overdue'))
        )
    """)

    # Fine Records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fine_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id     INTEGER NOT NULL REFERENCES loan_records(id),
            member_id   INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            paid        INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Payment Transactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fine_id     INTEGER NOT NULL REFERENCES fine_records(id),
            member_id   INTEGER NOT NULL REFERENCES users(id),
            amount_paid REAL    NOT NULL,
            payment_date TEXT   NOT NULL
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_db()
    print("Database initialized.")
