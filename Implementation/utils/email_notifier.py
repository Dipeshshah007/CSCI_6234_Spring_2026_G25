"""
utils/email_notifier.py
-----------------------
Feature 2: Email Notifications
Sends overdue reminders and fine alerts to members via Gmail SMTP.
Uses Python's built-in smtplib — no pip install needed.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.db import get_connection
from datetime import date
from models.transaction import FINE_PER_DAY


# ── Email Configuration (set these before using) ──────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SENDER_EMAIL  = ""   # e.g. libraryg25@gmail.com
SENDER_PASSWORD = "" # Gmail App Password (not your login password)
LIBRARY_NAME  = "GWU Library — CSCI 6234 G25"


def _is_configured() -> bool:
    return bool(SENDER_EMAIL and SENDER_PASSWORD)


def send_email(to_email: str, subject: str, body_html: str) -> tuple[bool, str]:
    """Core email sender. Returns (success, message)."""
    if not _is_configured():
        return False, "Email not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in utils/email_notifier.py"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{LIBRARY_NAME} <{SENDER_EMAIL}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(body_html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True, f"Email sent to {to_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your Gmail App Password."
    except Exception as e:
        return False, str(e)


def _overdue_email_body(member_name: str, book_title: str,
                         due_date: str, days_overdue: int, fine: float) -> str:
    return f"""
    <html><body style="font-family:Segoe UI,sans-serif;color:#1F2937;max-width:600px;margin:auto">
      <div style="background:#4F6EF7;padding:24px;border-radius:8px 8px 0 0">
        <h2 style="color:#fff;margin:0">📚 {LIBRARY_NAME}</h2>
        <p style="color:#D0D9FF;margin:4px 0 0">Overdue Book Notice</p>
      </div>
      <div style="background:#fff;padding:24px;border:1px solid #E5E7EB;border-top:none">
        <p>Dear <strong>{member_name}</strong>,</p>
        <p>This is a reminder that the following book is <strong style="color:#EF4444">overdue</strong>:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr style="background:#F4F6FB">
            <td style="padding:10px;font-weight:bold">Book Title</td>
            <td style="padding:10px">{book_title}</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold">Due Date</td>
            <td style="padding:10px;color:#EF4444">{due_date}</td>
          </tr>
          <tr style="background:#F4F6FB">
            <td style="padding:10px;font-weight:bold">Days Overdue</td>
            <td style="padding:10px">{days_overdue} days</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold">Current Fine</td>
            <td style="padding:10px;color:#EF4444"><strong>${fine:.2f}</strong>
              (${FINE_PER_DAY:.2f}/day)</td>
          </tr>
        </table>
        <p>Please return the book as soon as possible to stop accruing fines.</p>
        <p style="color:#6B7280;font-size:13px;margin-top:32px">
          This is an automated message from {LIBRARY_NAME}.<br>
          Please do not reply to this email.
        </p>
      </div>
    </html>
    """


def _fine_paid_email_body(member_name: str, book_title: str, amount: float) -> str:
    return f"""
    <html><body style="font-family:Segoe UI,sans-serif;color:#1F2937;max-width:600px;margin:auto">
      <div style="background:#10B981;padding:24px;border-radius:8px 8px 0 0">
        <h2 style="color:#fff;margin:0">📚 {LIBRARY_NAME}</h2>
        <p style="color:#D1FAE5;margin:4px 0 0">Payment Confirmation</p>
      </div>
      <div style="background:#fff;padding:24px;border:1px solid #E5E7EB;border-top:none">
        <p>Dear <strong>{member_name}</strong>,</p>
        <p>Your fine has been <strong style="color:#10B981">paid successfully</strong>.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr style="background:#F4F6FB">
            <td style="padding:10px;font-weight:bold">Book</td>
            <td style="padding:10px">{book_title}</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold">Amount Paid</td>
            <td style="padding:10px;color:#10B981"><strong>${amount:.2f}</strong></td>
          </tr>
          <tr style="background:#F4F6FB">
            <td style="padding:10px;font-weight:bold">Date</td>
            <td style="padding:10px">{date.today().isoformat()}</td>
          </tr>
        </table>
        <p>Thank you! Your account is now clear.</p>
      </div>
    </html>
    """


def send_overdue_reminders() -> list[dict]:
    """
    Sends overdue reminder emails to all members with overdue books.
    Returns list of results.
    """
    conn = get_connection()
    overdue = conn.execute("""
        SELECT u.name, u.email, b.title, lr.due_date,
               CAST(julianday('now') - julianday(lr.due_date) AS INTEGER) AS days_overdue,
               ROUND(CAST(julianday('now') - julianday(lr.due_date) AS REAL) * ?, 2) AS fine
        FROM loan_records lr
        JOIN users u ON u.id = lr.member_id
        JOIN books b ON b.id = lr.book_id
        WHERE lr.status IN ('active','overdue') AND lr.due_date < date('now')
    """, (FINE_PER_DAY,)).fetchall()
    conn.close()

    results = []
    for row in overdue:
        body = _overdue_email_body(row["name"], row["title"],
                                   row["due_date"], row["days_overdue"], row["fine"])
        ok, msg = send_email(row["email"],
                             f"⚠️ Overdue Book: {row['title']}", body)
        results.append({"member": row["name"], "email": row["email"],
                        "book": row["title"], "success": ok, "message": msg})
    return results


def send_fine_paid_notification(member_id: int, fine_id: int) -> tuple[bool, str]:
    """Sends payment confirmation after a fine is paid."""
    conn = get_connection()
    row = conn.execute("""
        SELECT u.name, u.email, b.title, fr.amount
        FROM fine_records fr
        JOIN users u ON u.id = fr.member_id
        JOIN loan_records lr ON lr.id = fr.loan_id
        JOIN books b ON b.id = lr.book_id
        WHERE fr.id = ? AND fr.member_id = ?
    """, (fine_id, member_id)).fetchone()
    conn.close()
    if not row:
        return False, "Record not found."
    body = _fine_paid_email_body(row["name"], row["title"], row["amount"])
    return send_email(row["email"], "✅ Fine Payment Confirmed", body)
