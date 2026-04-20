"""
models/transaction.py
---------------------
LoanRecord, FineRecord, PaymentTransaction, TransactionHistory
"""
from database.db import get_connection
from datetime import date, timedelta

LOAN_DAYS = 14          # default borrowing period
FINE_PER_DAY = 0.50    # fine rate in dollars


class LoanRecord:
    """Tracks a single borrowing event."""

    def __init__(self, record_id, member_id, book_id, loan_date, due_date,
                 return_date, status):
        self._id = record_id
        self._member_id = member_id
        self._book_id = book_id
        self._loan_date = loan_date
        self._due_date = due_date
        self._return_date = return_date
        self._status = status

    @property
    def id(self): return self._id

    @property
    def member_id(self): return self._member_id

    @property
    def book_id(self): return self._book_id

    @property
    def loan_date(self): return self._loan_date

    @property
    def due_date(self): return self._due_date

    @property
    def return_date(self): return self._return_date

    @property
    def status(self): return self._status

    def to_tuple(self):
        return (self._id, self._member_id, self._book_id, self._loan_date,
                self._due_date, self._return_date or "—", self._status)

    # --- Static helpers ---
    @staticmethod
    def borrow_book(member_id: int, book_id: int) -> tuple[bool, str]:
        conn = get_connection()
        try:
            book = conn.execute(
                "SELECT available_copies FROM books WHERE id=?", (book_id,)
            ).fetchone()
            if not book or book["available_copies"] < 1:
                return False, "No copies available."

            today = date.today().isoformat()
            due = (date.today() + timedelta(days=LOAN_DAYS)).isoformat()

            conn.execute(
                "INSERT INTO loan_records (member_id,book_id,loan_date,due_date,status) VALUES (?,?,?,?,'active')",
                (member_id, book_id, today, due)
            )
            conn.execute(
                "UPDATE books SET available_copies=available_copies-1 WHERE id=?",
                (book_id,)
            )
            conn.commit()
            return True, f"Book borrowed! Due date: {due}"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def return_book(loan_id: int) -> tuple[bool, str, float]:
        """Returns (success, message, fine_amount)."""
        conn = get_connection()
        try:
            loan = conn.execute(
                "SELECT * FROM loan_records WHERE id=?", (loan_id,)
            ).fetchone()
            if not loan:
                return False, "Loan record not found.", 0.0
            if loan["status"] == "returned":
                return False, "Book already returned.", 0.0

            today = date.today()
            due = date.fromisoformat(loan["due_date"])
            fine_amount = 0.0
            if today > due:
                fine_amount = (today - due).days * FINE_PER_DAY

            conn.execute(
                "UPDATE loan_records SET return_date=?, status='returned' WHERE id=?",
                (today.isoformat(), loan_id)
            )
            conn.execute(
                "UPDATE books SET available_copies=available_copies+1 WHERE id=?",
                (loan["book_id"],)
            )

            if fine_amount > 0:
                conn.execute(
                    "INSERT INTO fine_records (loan_id,member_id,amount,paid) VALUES (?,?,?,0)",
                    (loan_id, loan["member_id"], fine_amount)
                )

            conn.commit()
            msg = f"Book returned. Fine: ${fine_amount:.2f}" if fine_amount else "Book returned. No fine."
            return True, msg, fine_amount
        except Exception as e:
            return False, str(e), 0.0
        finally:
            conn.close()

    @staticmethod
    def get_active_loans_for_member(member_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT lr.id, u.name, b.title, lr.loan_date, lr.due_date, lr.status
               FROM loan_records lr
               JOIN users u ON u.id = lr.member_id
               JOIN books b ON b.id = lr.book_id
               WHERE lr.member_id=? AND lr.status='active'""",
            (member_id,)
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]

    @staticmethod
    def get_all_loans() -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT lr.id, u.name, b.title, lr.loan_date, lr.due_date,
                      COALESCE(lr.return_date,'—'), lr.status
               FROM loan_records lr
               JOIN users u ON u.id = lr.member_id
               JOIN books b ON b.id = lr.book_id
               ORDER BY lr.id DESC"""
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]


class FineRecord:
    """Tracks fines owed by members."""

    @staticmethod
    def get_unpaid_fines_for_member(member_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT fr.id, b.title, fr.amount, fr.paid
               FROM fine_records fr
               JOIN loan_records lr ON lr.id = fr.loan_id
               JOIN books b ON b.id = lr.book_id
               WHERE fr.member_id=? AND fr.paid=0""",
            (member_id,)
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]

    @staticmethod
    def get_all_fines() -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT fr.id, u.name, b.title, fr.amount,
                      CASE fr.paid WHEN 1 THEN 'Paid' ELSE 'Unpaid' END
               FROM fine_records fr
               JOIN users u ON u.id = fr.member_id
               JOIN loan_records lr ON lr.id = fr.loan_id
               JOIN books b ON b.id = lr.book_id
               ORDER BY fr.id DESC"""
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]


class PaymentTransaction:
    """Records payment of fines."""

    @staticmethod
    def pay_fine(fine_id: int, member_id: int) -> tuple[bool, str]:
        conn = get_connection()
        try:
            fine = conn.execute(
                "SELECT * FROM fine_records WHERE id=? AND member_id=?",
                (fine_id, member_id)
            ).fetchone()
            if not fine:
                return False, "Fine not found."
            if fine["paid"]:
                return False, "Fine already paid."

            today = date.today().isoformat()
            conn.execute(
                "INSERT INTO payment_transactions (fine_id,member_id,amount_paid,payment_date) VALUES (?,?,?,?)",
                (fine_id, member_id, fine["amount"], today)
            )
            conn.execute("UPDATE fine_records SET paid=1 WHERE id=?", (fine_id,))
            conn.commit()
            return True, f"Fine of ${fine['amount']:.2f} paid successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()


class TransactionHistory:
    """Aggregates loan history for a member or all members."""

    @staticmethod
    def get_member_history(member_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT lr.id, b.title, lr.loan_date, lr.due_date,
                      COALESCE(lr.return_date,'—'), lr.status
               FROM loan_records lr
               JOIN books b ON b.id = lr.book_id
               WHERE lr.member_id=?
               ORDER BY lr.id DESC""",
            (member_id,)
        ).fetchall()
        conn.close()
        return [tuple(r) for r in rows]
