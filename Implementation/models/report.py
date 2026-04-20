"""
models/report.py
----------------
Report class — generates summary statistics.
"""
from database.db import get_connection


class Report:
    """Generates library reports (Polymorphism: different report types)."""

    @staticmethod
    def summary() -> dict:
        conn = get_connection()
        total_books      = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        total_members    = conn.execute("SELECT COUNT(*) FROM users WHERE role='member'").fetchone()[0]
        active_loans     = conn.execute("SELECT COUNT(*) FROM loan_records WHERE status='active'").fetchone()[0]
        overdue_loans    = conn.execute(
            "SELECT COUNT(*) FROM loan_records WHERE status='active' AND due_date < date('now')"
        ).fetchone()[0]
        total_fines      = conn.execute("SELECT COALESCE(SUM(amount),0) FROM fine_records WHERE paid=0").fetchone()[0]
        total_collected  = conn.execute("SELECT COALESCE(SUM(amount_paid),0) FROM payment_transactions").fetchone()[0]
        conn.close()
        return {
            "Total Books":          total_books,
            "Total Members":        total_members,
            "Active Loans":         active_loans,
            "Overdue Loans":        overdue_loans,
            "Unpaid Fines ($)":     f"{total_fines:.2f}",
            "Collected Fines ($)":  f"{total_collected:.2f}",
        }

    @staticmethod
    def top_borrowed_books(limit: int = 10) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT b.title, b.author, COUNT(lr.id) AS times_borrowed
               FROM loan_records lr JOIN books b ON b.id=lr.book_id
               GROUP BY lr.book_id ORDER BY times_borrowed DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]

    @staticmethod
    def overdue_report() -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT u.name, b.title, lr.due_date,
                      CAST(julianday('now') - julianday(lr.due_date) AS INTEGER) AS days_overdue
               FROM loan_records lr
               JOIN users u ON u.id=lr.member_id
               JOIN books b ON b.id=lr.book_id
               WHERE lr.status='active' AND lr.due_date < date('now')
               ORDER BY days_overdue DESC"""
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]
