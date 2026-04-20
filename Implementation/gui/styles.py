"""
gui/styles.py
-------------
Color palette and reusable widget helpers.
"""
import tkinter as tk
from tkinter import ttk

# ── Color Palette ──────────────────────────────────────────────
BG_DARK    = "#1A1F36"   # sidebar / header
BG_LIGHT   = "#F4F6FB"   # main content area
ACCENT     = "#4F6EF7"   # primary blue accent
ACCENT2    = "#22D3A5"   # green accent
DANGER     = "#EF4444"   # red / delete
WARNING    = "#F59E0B"   # orange / fine
SUCCESS    = "#10B981"   # green / success
TEXT_LIGHT = "#FFFFFF"
TEXT_DARK  = "#1F2937"
TEXT_MID   = "#6B7280"
CARD_BG    = "#FFFFFF"
SIDEBAR_HOVER = "#2D3555"

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_LABEL  = ("Segoe UI", 10, "bold")

BTN_OPTS = dict(
    relief="flat", cursor="hand2",
    font=("Segoe UI", 10, "bold"),
    padx=14, pady=6
)


def configure_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background=CARD_BG,
                    foreground=TEXT_DARK,
                    fieldbackground=CARD_BG,
                    rowheight=26,
                    font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
                    background=BG_DARK,
                    foreground=TEXT_LIGHT,
                    font=("Segoe UI", 10, "bold"),
                    relief="flat")
    style.map("Treeview", background=[("selected", ACCENT)])


def make_btn(parent, text, command, color=ACCENT, fg=TEXT_LIGHT, **kw):
    b = tk.Button(parent, text=text, command=command,
                  bg=color, fg=fg, activebackground=color,
                  activeforeground=fg, **BTN_OPTS, **kw)
    return b


def make_entry(parent, **kw) -> tk.Entry:
    e = tk.Entry(parent, font=FONT_BODY, relief="solid", bd=1,
                 bg=CARD_BG, fg=TEXT_DARK, **kw)
    return e


def labeled_entry(parent, label_text, row, col=0, show=None) -> tk.Entry:
    tk.Label(parent, text=label_text, font=FONT_LABEL,
             bg=CARD_BG, fg=TEXT_DARK).grid(row=row, column=col, sticky="w", pady=(6, 0), padx=6)
    e = tk.Entry(parent, font=FONT_BODY, relief="solid", bd=1,
                 bg="#F9FAFB", fg=TEXT_DARK, show=show or "")
    e.grid(row=row + 1, column=col, sticky="ew", padx=6, pady=(0, 4))
    return e


def section_header(parent, text, bg=BG_LIGHT):
    tk.Label(parent, text=text, font=FONT_TITLE,
             bg=bg, fg=BG_DARK).pack(anchor="w", padx=20, pady=(18, 4))
    tk.Frame(parent, height=2, bg=ACCENT).pack(fill="x", padx=20, pady=(0, 10))
