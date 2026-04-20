"""
utils/overdue_updater.py
------------------------
Feature 1: Overdue Status Auto-Update
Runs on app startup and can be triggered manually.
Scans all active loans, marks overdue ones, auto-creates fine records.
"""
from database.db import get_connection
from datetime import date
from models.transaction import FINE_PER_DAY


def update_overdue_statuses() -> dict:
    """
    Scans all active loans. If due_date < today:
      - Sets status = 'overdue'
      - Creates a fine_record if one doesn't exist yet
    Returns a summary dict.
    """
    conn = get_connection()
    today = date.today().isoformat()

    # Find all active loans that are past due date
    overdue_loans = conn.execute("""
        SELECT lr.id, lr.member_id, lr.book_id, lr.due_date
        FROM loan_records lr
        WHERE lr.status = 'active'
          AND lr.due_date < ?
    """, (today,)).fetchall()

    newly_overdue = 0
    fines_created = 0

    for loan in overdue_loans:
        loan_id   = loan["id"]
        member_id = loan["member_id"]
        due_date  = loan["due_date"]

        # Update status to overdue
        result = conn.execute("""
            UPDATE loan_records SET status = 'overdue'
            WHERE id = ? AND status = 'active'
        """, (loan_id,))
        if result.rowcount > 0:
            newly_overdue += 1

        # Calculate running fine (days overdue × rate)
        days_overdue = (date.today() - date.fromisoformat(due_date)).days
        fine_amount  = days_overdue * FINE_PER_DAY

        # Create fine record only if one doesn't exist yet for this loan
        existing_fine = conn.execute(
            "SELECT id FROM fine_records WHERE loan_id = ?", (loan_id,)
        ).fetchone()

        if not existing_fine and fine_amount > 0:
            conn.execute("""
                INSERT INTO fine_records (loan_id, member_id, amount, paid)
                VALUES (?, ?, ?, 0)
            """, (loan_id, member_id, fine_amount))
            fines_created += 1
        elif existing_fine and fine_amount > 0:
            # Update fine amount as days increase (only if unpaid)
            conn.execute("""
                UPDATE fine_records SET amount = ?
                WHERE loan_id = ? AND paid = 0
            """, (fine_amount, loan_id))

    conn.commit()
    conn.close()

    return {
        "total_overdue":   len(overdue_loans),
        "newly_marked":    newly_overdue,
        "fines_created":   fines_created,
        "checked_on":      today,
    }


def get_overdue_summary() -> list:
    """Returns list of overdue loans with member and book details."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.name AS member, u.email, b.title AS book,
               lr.due_date,
               CAST(julianday('now') - julianday(lr.due_date) AS INTEGER) AS days_overdue,
               ROUND(
                 CAST(julianday('now') - julianday(lr.due_date) AS REAL) * ?, 2
               ) AS fine_amount
        FROM loan_records lr
        JOIN users u ON u.id = lr.member_id
        JOIN books b ON b.id = lr.book_id
        WHERE lr.status IN ('active', 'overdue')
          AND lr.due_date < date('now')
        ORDER BY days_overdue DESC
    """, (FINE_PER_DAY,)).fetchall()
    conn.close()
    return [tuple(r) for r in rows]
