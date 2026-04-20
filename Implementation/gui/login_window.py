"""
gui/login_window.py
-------------------
Login and Registration screen.
"""
import tkinter as tk
from tkinter import messagebox
from models.user import User
from gui.styles import *


class LoginWindow(tk.Frame):
    def __init__(self, master, on_login_success):
        super().__init__(master, bg=BG_DARK)
        self.pack(fill="both", expand=True)
        self.on_login_success = on_login_success
        self._build()

    def _build(self):
        # Left decorative panel
        left = tk.Frame(self, bg=ACCENT, width=340)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="📚", font=("Segoe UI", 60),
                 bg=ACCENT, fg=TEXT_LIGHT).pack(pady=(80, 10))
        tk.Label(left, text="Library\nManagement\nSystem",
                 font=("Segoe UI", 22, "bold"),
                 bg=ACCENT, fg=TEXT_LIGHT, justify="center").pack()
        tk.Label(left, text="CSCI 6234 · Group G25",
                 font=FONT_SMALL, bg=ACCENT, fg="#D0D9FF").pack(pady=(30, 0))
        tk.Label(left, text="Prof. Walt Melo · Spring 2026",
                 font=FONT_SMALL, bg=ACCENT, fg="#D0D9FF").pack()

        # Right login form
        right = tk.Frame(self, bg=BG_LIGHT)
        right.pack(side="left", fill="both", expand=True)

        card = tk.Frame(right, bg=CARD_BG, bd=0, relief="flat",
                        highlightthickness=1, highlightbackground="#E5E7EB")
        card.place(relx=0.5, rely=0.5, anchor="center", width=380)

        tk.Label(card, text="Welcome Back", font=("Segoe UI", 22, "bold"),
                 bg=CARD_BG, fg=BG_DARK).pack(pady=(30, 4))
        tk.Label(card, text="Sign in to your account",
                 font=FONT_BODY, bg=CARD_BG, fg=TEXT_MID).pack(pady=(0, 20))

        form = tk.Frame(card, bg=CARD_BG)
        form.pack(padx=30, fill="x")
        form.columnconfigure(0, weight=1)

        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        tk.Label(form, text="Email", font=FONT_LABEL, bg=CARD_BG, fg=TEXT_DARK
                 ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        tk.Entry(form, textvariable=self.email_var, font=FONT_BODY,
                 relief="solid", bd=1, bg="#F9FAFB"
                 ).grid(row=1, column=0, sticky="ew", ipady=5)

        tk.Label(form, text="Password", font=FONT_LABEL, bg=CARD_BG, fg=TEXT_DARK
                 ).grid(row=2, column=0, sticky="w", pady=(10, 2))
        tk.Entry(form, textvariable=self.pass_var, show="•", font=FONT_BODY,
                 relief="solid", bd=1, bg="#F9FAFB"
                 ).grid(row=3, column=0, sticky="ew", ipady=5)

        make_btn(card, "Sign In", self._login, color=ACCENT).pack(
            fill="x", padx=30, pady=(18, 6), ipady=4)
        make_btn(card, "Create Account", self._show_register,
                 color=BG_LIGHT, fg=ACCENT).pack(fill="x", padx=30, pady=(0, 24), ipady=4)

        # Demo hint
        tk.Label(card, text="Default admin: admin@library.com / admin123",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MID).pack(pady=(0, 16))

    def _login(self):
        email = self.email_var.get().strip()
        pw = self.pass_var.get().strip()
        if not email or not pw:
            messagebox.showwarning("Missing Fields", "Please enter email and password.")
            return
        user = User.authenticate(email, pw)
        if user:
            self.on_login_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")

    def _show_register(self):
        reg = tk.Toplevel(self)
        reg.title("Create Account")
        reg.geometry("420x500")
        reg.resizable(False, False)
        reg.configure(bg=CARD_BG)

        tk.Label(reg, text="Create Account", font=("Segoe UI", 18, "bold"),
                 bg=CARD_BG, fg=BG_DARK).pack(pady=(24, 4))

        form = tk.Frame(reg, bg=CARD_BG)
        form.pack(padx=30, fill="x")
        form.columnconfigure(0, weight=1)

        fields = {}
        for i, (label, show) in enumerate([
            ("Full Name", None), ("Email", None),
            ("Phone", None), ("Password", "•"), ("Confirm Password", "•")
        ]):
            tk.Label(form, text=label, font=FONT_LABEL, bg=CARD_BG
                     ).grid(row=i*2, column=0, sticky="w", pady=(8, 0))
            e = tk.Entry(form, font=FONT_BODY, relief="solid", bd=1,
                         bg="#F9FAFB", show=show or "")
            e.grid(row=i*2+1, column=0, sticky="ew", ipady=5)
            fields[label] = e

        role_var = tk.StringVar(value="member")
        rf = tk.Frame(reg, bg=CARD_BG)
        rf.pack(padx=30, anchor="w", pady=(10, 0))
        for r, v in [("Member", "member"), ("Librarian", "librarian")]:
            tk.Radiobutton(rf, text=r, variable=role_var, value=v,
                           font=FONT_BODY, bg=CARD_BG).pack(side="left", padx=8)

        def _do_register():
            name = fields["Full Name"].get().strip()
            email = fields["Email"].get().strip()
            phone = fields["Phone"].get().strip()
            pw = fields["Password"].get()
            pw2 = fields["Confirm Password"].get()
            if not all([name, email, pw]):
                messagebox.showwarning("Missing Fields", "Name, Email, and Password are required.", parent=reg)
                return
            if pw != pw2:
                messagebox.showerror("Error", "Passwords do not match.", parent=reg)
                return
            ok, result = User.register(name, email, phone, pw, role_var.get())
            if ok:
                messagebox.showinfo("Success", "Account created! Please log in.", parent=reg)
                reg.destroy()
            else:
                messagebox.showerror("Error", result, parent=reg)

        make_btn(reg, "Register", _do_register, color=ACCENT2, fg=TEXT_DARK
                 ).pack(fill="x", padx=30, pady=16, ipady=4)
