"""
gui/member_dashboard.py
-----------------------
Member dashboard: Search books, Borrow, View loans, Pay fines, History.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from models.book import Catalog
from models.transaction import LoanRecord, FineRecord, PaymentTransaction, TransactionHistory
from gui.styles import *


class MemberDashboard(tk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, bg=BG_LIGHT)
        self.pack(fill="both", expand=True)
        self.user = user
        self.on_logout = on_logout
        self._build()
        self._show_section("search")

    def _build(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG_DARK, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="📚 LMS", font=("Segoe UI", 16, "bold"),
                 bg=BG_DARK, fg=TEXT_LIGHT).pack(pady=(24, 4))
        tk.Label(self.sidebar, text="Member Portal",
                 font=FONT_SMALL, bg=BG_DARK, fg="#8B9CC7").pack(pady=(0, 16))
        tk.Frame(self.sidebar, height=1, bg="#2D3555").pack(fill="x", padx=16, pady=4)

        self._nav_btns = {}
        nav_items = [
            ("🔍  Search Books", "search"),
            ("🔄  My Loans", "loans"),
            ("💰  My Fines", "fines"),
            ("📜  History", "history"),
        ]
        for label, key in nav_items:
            b = tk.Button(self.sidebar, text=label, anchor="w",
                          font=("Segoe UI", 11), relief="flat", cursor="hand2",
                          bg=BG_DARK, fg="#C4CDE8", activebackground=SIDEBAR_HOVER,
                          padx=20, pady=10,
                          command=lambda k=key: self._show_section(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        tk.Frame(self.sidebar, height=1, bg="#2D3555").pack(fill="x", padx=16, pady=8, side="bottom")
        tk.Button(self.sidebar, text=f"👋  {self.user.name}", anchor="w",
                  font=("Segoe UI", 10), relief="flat",
                  bg=BG_DARK, fg="#8B9CC7", padx=20, pady=8,
                  state="disabled").pack(fill="x", side="bottom")
        make_btn(self.sidebar, "Logout", self.on_logout,
                 color=DANGER).pack(side="bottom", fill="x", padx=16, pady=8)

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
        self._set_active_nav(key)
        self._clear_main()
        {
            "search":  self._section_search,
            "loans":   self._section_loans,
            "fines":   self._section_fines,
            "history": self._section_history,
        }[key]()

    # ── Search & Borrow ───────────────────────────────────────────────────
    def _section_search(self):
        section_header(self.main, "🔍 Search & Borrow Books")

        sf = tk.Frame(self.main, bg=BG_LIGHT)
        sf.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(sf, text="Keyword:", font=FONT_BODY, bg=BG_LIGHT).pack(side="left")
        search_var = tk.StringVar()
        tk.Entry(sf, textvariable=search_var, font=FONT_BODY, width=28,
                 relief="solid", bd=1).pack(side="left", padx=6)
        field_var = tk.StringVar(value="title")
        for f in ["title", "author", "category"]:
            tk.Radiobutton(sf, text=f.capitalize(), variable=field_var,
                           value=f, font=FONT_SMALL, bg=BG_LIGHT).pack(side="left")

        configure_treeview_style()
        cols = ("ID", "Title", "Author", "ISBN", "Category", "Available")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=90 if c in ("ID", "Available") else 155, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=4)

        def refresh(keyword="", field="title"):
            tree.delete(*tree.get_children())
            books = Catalog.search_books(keyword, field) if keyword else Catalog.get_all_books()
            for b in books:
                row = (b.id, b.title, b.author, b.isbn, b.category, b.available_copies)
                tag = "available" if b.is_available() else "unavail"
                tree.insert("", "end", values=row, tags=(tag,))
            tree.tag_configure("available", foreground=SUCCESS)
            tree.tag_configure("unavail", foreground=DANGER)

        tk.Button(sf, text="🔍 Search",
                  command=lambda: refresh(search_var.get(), field_var.get()),
                  font=FONT_SMALL, relief="flat", bg=ACCENT, fg=TEXT_LIGHT,
                  cursor="hand2", padx=8).pack(side="left", padx=4)
        tk.Button(sf, text="⟳ All", command=lambda: refresh(),
                  font=FONT_SMALL, relief="flat", bg=TEXT_MID, fg=TEXT_LIGHT,
                  cursor="hand2", padx=8).pack(side="left")

        af = tk.Frame(self.main, bg=BG_LIGHT)
        af.pack(fill="x", padx=20, pady=6)

        def borrow():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Please select a book to borrow.")
                return
            book_id = tree.item(sel[0])["values"][0]
            ok, msg = LoanRecord.borrow_book(self.user.id, book_id)
            messagebox.showinfo("Borrow Result", msg)
            if ok:
                refresh()

        make_btn(af, "📥 Borrow Selected", borrow, color=ACCENT2, fg=TEXT_DARK).pack(side="left", padx=4)
        refresh()

    # ── Active Loans ──────────────────────────────────────────────────────
    def _section_loans(self):
        section_header(self.main, "🔄 My Active Loans")
        configure_treeview_style()
        cols = ("Loan ID", "Member", "Book Title", "Loan Date", "Due Date", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=16)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        for row in LoanRecord.get_active_loans_for_member(self.user.id):
            tree.insert("", "end", values=row)

    # ── Fines ─────────────────────────────────────────────────────────────
    def _section_fines(self):
        section_header(self.main, "💰 My Unpaid Fines")
        configure_treeview_style()
        cols = ("Fine ID", "Book", "Amount ($)", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=160, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=4)

        def refresh():
            tree.delete(*tree.get_children())
            for row in FineRecord.get_unpaid_fines_for_member(self.user.id):
                tree.insert("", "end", values=row, tags=("unpaid",))
            tree.tag_configure("unpaid", foreground=DANGER)

        af = tk.Frame(self.main, bg=BG_LIGHT)
        af.pack(fill="x", padx=20, pady=6)

        def pay_fine():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select a fine to pay.")
                return
            fine_id = tree.item(sel[0])["values"][0]
            ok, msg = PaymentTransaction.pay_fine(fine_id, self.user.id)
            messagebox.showinfo("Payment", msg)
            if ok:
                refresh()

        make_btn(af, "💳 Pay Selected Fine", pay_fine, color=ACCENT2, fg=TEXT_DARK).pack(side="left", padx=4)
        make_btn(af, "⟳ Refresh", refresh).pack(side="left", padx=4)
        refresh()

    # ── History ───────────────────────────────────────────────────────────
    def _section_history(self):
        section_header(self.main, "📜 My Borrowing History")
        configure_treeview_style()
        cols = ("Loan ID", "Book Title", "Loan Date", "Due Date", "Return Date", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=16)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        for row in TransactionHistory.get_member_history(self.user.id):
            tag = "returned" if row[-1] == "returned" else ("overdue" if row[-1] == "overdue" else "active")
            tree.insert("", "end", values=row, tags=(tag,))
        tree.tag_configure("returned", foreground=SUCCESS)
        tree.tag_configure("overdue", foreground=DANGER)
        tree.tag_configure("active", foreground=ACCENT)
