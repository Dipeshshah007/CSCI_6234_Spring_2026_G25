"""
main.py
-------
Application entry point. Initializes DB, seeds default admin, launches GUI.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from database.db import initialize_db, get_connection
from models.user import User
from gui.login_window import LoginWindow
from gui.librarian_dashboard import LibrarianDashboard
from gui.member_dashboard import MemberDashboard
import hashlib


def seed_default_admin():
    """Creates a default librarian account if none exists."""
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE role='librarian' LIMIT 1").fetchone()
    if not existing:
        pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute(
            "INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)",
            ("Admin Librarian", "admin@library.com", "555-0000", pw_hash, "librarian")
        )
        conn.commit()
        print("[seed] Default admin created: admin@library.com / admin123")
    conn.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System — CSCI 6234 | Group G25")
        self.geometry("1150x700")
        self.minsize(900, 600)
        self.configure(bg="#1A1F36")
        self._current_frame = None
        self._show_login()

    def _clear(self):
        if self._current_frame:
            self._current_frame.destroy()
            self._current_frame = None

    def _show_login(self):
        self._clear()
        self._current_frame = LoginWindow(self, on_login_success=self._on_login)

    def _on_login(self, user):
        self._clear()
        if user.role == "librarian":
            self._current_frame = LibrarianDashboard(self, user, on_logout=self._show_login)
        else:
            self._current_frame = MemberDashboard(self, user, on_logout=self._show_login)

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    initialize_db()
    seed_default_admin()
    # Feature 1: Auto-update overdue statuses silently on every startup
    from utils.overdue_updater import update_overdue_statuses
    update_overdue_statuses()
    App().run()
