"""
gui/librarian_dashboard.py
--------------------------
Full Librarian dashboard with Book Management, Members, Loans, Fines, Reports.
Features: Overdue Auto-Update, Email Notifications, PDF/CSV Export.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from models.book import Catalog
from models.transaction import LoanRecord, FineRecord
from models.report import Report
from models.user import User
from gui.styles import *
from utils.overdue_updater import update_overdue_statuses, get_overdue_summary
from utils.email_notifier import send_overdue_reminders, send_fine_paid_notification
from utils.exporter import (export_full_report_pdf, export_overdue_pdf,
                             export_loans_csv, export_fines_csv, export_summary_csv)


class LibrarianDashboard(tk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, bg=BG_LIGHT)
        self.pack(fill="both", expand=True)
        self.user = user
        self.on_logout = on_logout
        self._active_section = None
        self._build()
        self._show_section("books")
        # Feature 1: Auto-update overdue statuses on every login
        self._run_overdue_update(silent=True)

    # ── Layout ───────────────────────────────────────────────────────────
    def _build(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG_DARK, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="📚 LMS", font=("Segoe UI", 16, "bold"),
                 bg=BG_DARK, fg=TEXT_LIGHT).pack(pady=(24, 4))
        tk.Label(self.sidebar, text="Librarian Portal",
                 font=FONT_SMALL, bg=BG_DARK, fg="#8B9CC7").pack(pady=(0, 16))
        tk.Frame(self.sidebar, height=1, bg="#2D3555").pack(fill="x", padx=16, pady=4)

        self._nav_btns = {}
        nav_items = [
            ("📖  Books", "books"),
            ("👥  Members", "members"),
            ("🔄  Loans", "loans"),
            ("💰  Fines", "fines"),
            ("📊  Reports", "reports"),
        ]
        for label, key in nav_items:
            b = tk.Button(self.sidebar, text=label, anchor="w",
                          font=("Segoe UI", 11), relief="flat", cursor="hand2",
                          bg=BG_DARK, fg="#C4CDE8", activebackground=SIDEBAR_HOVER,
                          padx=20, pady=10,
                          command=lambda k=key: self._show_section(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        # Logout at bottom
        tk.Frame(self.sidebar, height=1, bg="#2D3555").pack(fill="x", padx=16, pady=8, side="bottom")
        tk.Button(self.sidebar, text=f"👋  {self.user.name}", anchor="w",
                  font=("Segoe UI", 10), relief="flat",
                  bg=BG_DARK, fg="#8B9CC7", padx=20, pady=8,
                  state="disabled").pack(fill="x", side="bottom")
        make_btn(self.sidebar, "Logout", self.on_logout,
                 color=DANGER, fg=TEXT_LIGHT).pack(side="bottom", fill="x", padx=16, pady=8)

        # Main content area
        self.main = tk.Frame(self, bg=BG_LIGHT)
        self.main.pack(side="left", fill="both", expand=True)

    def _set_active_nav(self, key):
        for k, b in self._nav_btns.items():
            b.configure(bg=ACCENT if k == key else BG_DARK,
                        fg=TEXT_LIGHT if k == key else "#C4CDE8")

    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    def _show_section(self, key):
        self._active_section = key
        self._set_active_nav(key)
        self._clear_main()
        {
            "books":   self._section_books,
            "members": self._section_members,
            "loans":   self._section_loans,
            "fines":   self._section_fines,
            "reports": self._section_reports,
        }[key]()

    # ── Books Section ─────────────────────────────────────────────────────
    def _section_books(self):
        section_header(self.main, "📖 Book Catalog")

        # Search bar
        sf = tk.Frame(self.main, bg=BG_LIGHT)
        sf.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(sf, text="Search:", font=FONT_BODY, bg=BG_LIGHT).pack(side="left")
        search_var = tk.StringVar()
        tk.Entry(sf, textvariable=search_var, font=FONT_BODY, width=28,
                 relief="solid", bd=1).pack(side="left", padx=6)
        field_var = tk.StringVar(value="title")
        for f in ["title", "author", "category", "isbn"]:
            tk.Radiobutton(sf, text=f.capitalize(), variable=field_var,
                           value=f, font=FONT_SMALL, bg=BG_LIGHT).pack(side="left")

        configure_treeview_style()
        cols = ("ID", "Title", "Author", "ISBN", "Category", "Total", "Available")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=90 if c in ("ID","Total","Available") else 160, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=4)

        def refresh(keyword="", field="title"):
            tree.delete(*tree.get_children())
            books = Catalog.search_books(keyword, field) if keyword else Catalog.get_all_books()
            for b in books:
                tree.insert("", "end", values=b.to_tuple())

        tk.Button(sf, text="🔍 Search", command=lambda: refresh(search_var.get(), field_var.get()),
                  font=FONT_SMALL, relief="flat", bg=ACCENT, fg=TEXT_LIGHT, cursor="hand2", padx=8
                  ).pack(side="left", padx=4)
        tk.Button(sf, text="⟳ All", command=lambda: refresh(),
                  font=FONT_SMALL, relief="flat", bg=TEXT_MID, fg=TEXT_LIGHT, cursor="hand2", padx=8
                  ).pack(side="left")

        # Action bar
        af = tk.Frame(self.main, bg=BG_LIGHT)
        af.pack(fill="x", padx=20, pady=6)
        make_btn(af, "+ Add Book", lambda: self._book_form(refresh), color=ACCENT2, fg=TEXT_DARK).pack(side="left", padx=4)
        make_btn(af, "✏ Edit", lambda: self._edit_book(tree, refresh)).pack(side="left", padx=4)
        make_btn(af, "🗑 Delete", lambda: self._delete_book(tree, refresh), color=DANGER).pack(side="left", padx=4)

        refresh()

    def _book_form(self, refresh_cb, book=None):
        win = tk.Toplevel(self)
        win.title("Add Book" if not book else "Edit Book")
        win.geometry("420x440")
        win.configure(bg=CARD_BG)
        win.grab_set()

        tk.Label(win, text="Add Book" if not book else "Edit Book",
                 font=FONT_HEADER, bg=CARD_BG, fg=BG_DARK).pack(pady=(20, 10))

        form = tk.Frame(win, bg=CARD_BG)
        form.pack(padx=30, fill="x")
        form.columnconfigure(0, weight=1)

        fields = {}
        labels = [("Title", None), ("Author", None), ("ISBN", None),
                  ("Category", None), ("Total Copies", None)]
        for i, (lbl, _) in enumerate(labels):
            tk.Label(form, text=lbl, font=FONT_LABEL, bg=CARD_BG
                     ).grid(row=i*2, column=0, sticky="w", pady=(6, 0))
            e = tk.Entry(form, font=FONT_BODY, relief="solid", bd=1, bg="#F9FAFB")
            e.grid(row=i*2+1, column=0, sticky="ew", ipady=4)
            fields[lbl] = e

        if book:
            fields["Title"].insert(0, book.title)
            fields["Author"].insert(0, book.author)
            fields["ISBN"].insert(0, book.isbn)
            fields["Category"].insert(0, book.category or "")
            fields["Total Copies"].insert(0, str(book.total_copies))

        def submit():
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not vals["Title"] or not vals["ISBN"]:
                messagebox.showwarning("Missing", "Title and ISBN are required.", parent=win)
                return
            try:
                copies = int(vals["Total Copies"] or 1)
            except ValueError:
                messagebox.showerror("Error", "Copies must be a number.", parent=win)
                return
            if book:
                ok, msg = Catalog.update_book(book.id, vals["Title"], vals["Author"],
                                              vals["ISBN"], vals["Category"], copies)
            else:
                ok, msg = Catalog.add_book(vals["Title"], vals["Author"],
                                           vals["ISBN"], vals["Category"], copies)
            if ok:
                refresh_cb()
                win.destroy()
            else:
                messagebox.showerror("Error", msg, parent=win)

        make_btn(win, "Save", submit, color=ACCENT2, fg=TEXT_DARK
                 ).pack(fill="x", padx=30, pady=16, ipady=4)

    def _edit_book(self, tree, refresh_cb):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a book to edit.")
            return
        book_id = tree.item(sel[0])["values"][0]
        book = Catalog.get_book_by_id(book_id)
        if book:
            self._book_form(refresh_cb, book)

    def _delete_book(self, tree, refresh_cb):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a book to delete.")
            return
        book_id = tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", "Delete this book?"):
            ok, msg = Catalog.delete_book(book_id)
            if ok:
                refresh_cb()
            else:
                messagebox.showerror("Error", msg)

    # ── Members Section ───────────────────────────────────────────────────
    def _section_members(self):
        section_header(self.main, "👥 Members")
        configure_treeview_style()
        cols = ("ID", "Name", "Email", "Phone", "Role")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        conn = __import__("database.db", fromlist=["get_connection"]).get_connection()
        rows = conn.execute("SELECT id,name,email,phone,role FROM users ORDER BY id").fetchall()
        conn.close()
        for r in rows:
            tree.insert("", "end", values=tuple(r))

    # ── Loans Section ─────────────────────────────────────────────────────
    def _section_loans(self):
        section_header(self.main, "🔄 Loan Records")
        configure_treeview_style()
        cols = ("Loan ID", "Member", "Book Title", "Loan Date", "Due Date", "Return Date", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=16)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=4)

        def refresh():
            tree.delete(*tree.get_children())
            for row in LoanRecord.get_all_loans():
                tag = "overdue" if row[-1] == "overdue" else ("returned" if row[-1] == "returned" else "")
                tree.insert("", "end", values=row, tags=(tag,))
            tree.tag_configure("overdue", foreground=DANGER)
            tree.tag_configure("returned", foreground=SUCCESS)

        # Return selected loan
        af = tk.Frame(self.main, bg=BG_LIGHT)
        af.pack(fill="x", padx=20, pady=6)

        def return_loan():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select a loan record to return.")
                return
            loan_id = tree.item(sel[0])["values"][0]
            ok, msg, fine = LoanRecord.return_book(loan_id)
            messagebox.showinfo("Result", msg)
            if ok:
                refresh()

        make_btn(af, "✅ Return Selected Book", return_loan, color=ACCENT2, fg=TEXT_DARK).pack(side="left", padx=4)
        make_btn(af, "⟳ Refresh", refresh).pack(side="left", padx=4)
        refresh()

    # ── Fines Section ─────────────────────────────────────────────────────
    def _section_fines(self):
        section_header(self.main, "💰 Fine Records")
        configure_treeview_style()
        cols = ("Fine ID", "Member", "Book", "Amount ($)", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=16)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=130, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        for row in FineRecord.get_all_fines():
            tree.insert("", "end", values=row,
                        tags=("paid" if row[-1] == "Paid" else "unpaid",))
        tree.tag_configure("paid", foreground=SUCCESS)
        tree.tag_configure("unpaid", foreground=DANGER)

    # ── Feature 1: Overdue Auto-Update ────────────────────────────────────
    def _run_overdue_update(self, silent=False):
        result = update_overdue_statuses()
        if not silent:
            msg = (f"Overdue check complete!\n\n"
                   f"Total overdue loans : {result['total_overdue']}\n"
                   f"Newly marked overdue: {result['newly_marked']}\n"
                   f"Fine records created: {result['fines_created']}\n"
                   f"Checked on          : {result['checked_on']}")
            messagebox.showinfo("Overdue Status Updated", msg)

    # ── Reports Section ───────────────────────────────────────────────────
    def _section_reports(self):
        section_header(self.main, "📊 Reports")

        # ── Feature Buttons Row ──
        feat_frame = tk.Frame(self.main, bg=BG_LIGHT)
        feat_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Feature 1 button
        make_btn(feat_frame, "🔄 Update Overdue Status",
                 lambda: self._run_overdue_update(silent=False),
                 color=WARNING, fg=TEXT_DARK).pack(side="left", padx=4)

        # Feature 2 button
        make_btn(feat_frame, "📧 Send Overdue Emails",
                 self._send_overdue_emails, color=ACCENT).pack(side="left", padx=4)

        # Feature 3 buttons
        make_btn(feat_frame, "📄 Export PDF",
                 self._export_pdf, color="#8B5CF6").pack(side="left", padx=4)
        make_btn(feat_frame, "📊 Export CSV",
                 self._export_csv, color=SUCCESS, fg=TEXT_DARK).pack(side="left", padx=4)

        # Summary cards
        summary = Report.summary()
        cards_frame = tk.Frame(self.main, bg=BG_LIGHT)
        cards_frame.pack(fill="x", padx=20, pady=6)

        card_colors = [ACCENT, ACCENT2, WARNING, DANGER, SUCCESS, "#8B5CF6"]
        for i, (label, value) in enumerate(summary.items()):
            card = tk.Frame(cards_frame, bg=card_colors[i % len(card_colors)],
                            width=160, height=90)
            card.grid(row=0, column=i, padx=6, pady=6)
            card.pack_propagate(False)
            tk.Label(card, text=str(value), font=("Segoe UI", 22, "bold"),
                     bg=card_colors[i % len(card_colors)], fg=TEXT_LIGHT).pack(pady=(12, 0))
            tk.Label(card, text=label, font=FONT_SMALL,
                     bg=card_colors[i % len(card_colors)], fg=TEXT_LIGHT).pack()

        # Top borrowed books
        tk.Label(self.main, text="Top Borrowed Books",
                 font=FONT_HEADER, bg=BG_LIGHT, fg=BG_DARK).pack(anchor="w", padx=20, pady=(16, 4))
        configure_treeview_style()
        cols = ("Title", "Author", "Times Borrowed")
        t1 = ttk.Treeview(self.main, columns=cols, show="headings", height=5)
        for c in cols:
            t1.heading(c, text=c)
            t1.column(c, width=200, anchor="center")
        t1.pack(fill="x", padx=20)
        for row in Report.top_borrowed_books():
            t1.insert("", "end", values=row)

        # Overdue
        tk.Label(self.main, text="Overdue Loans",
                 font=FONT_HEADER, bg=BG_LIGHT, fg=DANGER).pack(anchor="w", padx=20, pady=(10, 4))
        cols2 = ("Member", "Email", "Book", "Due Date", "Days Overdue", "Fine ($)")
        t2 = ttk.Treeview(self.main, columns=cols2, show="headings", height=4)
        for c in cols2:
            t2.heading(c, text=c)
            t2.column(c, width=130, anchor="center")
        t2.pack(fill="x", padx=20)
        for row in get_overdue_summary():
            t2.insert("", "end", values=row, tags=("over",))
        t2.tag_configure("over", foreground=DANGER)

    # ── Feature 2: Send Email Notifications ───────────────────────────────
    def _send_overdue_emails(self):
        results = send_overdue_reminders()
        if not results:
            messagebox.showinfo("No Overdue", "No overdue loans found. No emails sent.")
            return
        win = tk.Toplevel(self)
        win.title("Email Results")
        win.geometry("520x340")
        win.configure(bg=CARD_BG)
        tk.Label(win, text="📧 Email Notification Results",
                 font=FONT_HEADER, bg=CARD_BG, fg=BG_DARK).pack(pady=(16, 8))
        configure_treeview_style()
        cols = ("Member", "Email", "Book", "Status")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=16, pady=4)
        for r in results:
            status = "✅ Sent" if r["success"] else f"❌ {r['message']}"
            tree.insert("", "end", values=(r["member"], r["email"], r["book"], status),
                        tags=("ok" if r["success"] else "fail",))
        tree.tag_configure("ok",   foreground=SUCCESS)
        tree.tag_configure("fail", foreground=DANGER)
        tk.Label(win, text="Note: Configure SENDER_EMAIL in utils/email_notifier.py to enable real sending.",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MID, wraplength=480).pack(pady=8)

    # ── Feature 3: Export PDF / CSV ───────────────────────────────────────
    def _export_pdf(self):
        try:
            summary  = Report.summary()
            top      = Report.top_borrowed_books()
            overdue  = Report.overdue_report()
            loans    = LoanRecord.get_all_loans()
            filepath = export_full_report_pdf(summary, top, overdue, loans)
            folder   = os.path.dirname(filepath)
            messagebox.showinfo("PDF Exported ✅",
                                f"Report saved to:\n{filepath}\n\n"
                                f"Check the 'exports' folder in your project directory.")
            # Auto-open the exports folder on Windows
            os.startfile(folder) if os.name == "nt" else None
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _export_csv(self):
        try:
            summary = Report.summary()
            loans   = LoanRecord.get_all_loans()
            fines   = FineRecord.get_all_fines()
            f1 = export_summary_csv(summary)
            f2 = export_loans_csv(loans)
            f3 = export_fines_csv(fines)
            folder = os.path.dirname(f1)
            messagebox.showinfo("CSV Exported ✅",
                                f"3 files saved to exports folder:\n\n"
                                f"• {os.path.basename(f1)}\n"
                                f"• {os.path.basename(f2)}\n"
                                f"• {os.path.basename(f3)}")
            os.startfile(folder) if os.name == "nt" else None
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
