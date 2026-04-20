# Library Management System
## CSCI 6234 — Object-Oriented Design | Prof. Walt Melo | Spring 2026 | Group G25

---

## Project Structure

```
library_management_system/
│
├── main.py                        # Entry point — run this
│
├── database/
│   ├── __init__.py
│   └── db.py                      # SQLite schema + connection
│
├── models/
│   ├── __init__.py
│   ├── user.py                    # User (abstract), Librarian, Member
│   ├── book.py                    # Book, Catalog
│   ├── transaction.py             # LoanRecord, FineRecord, PaymentTransaction, TransactionHistory
│   └── report.py                  # Report (summary, top books, overdue)
│
├── gui/
│   ├── __init__.py
│   ├── styles.py                  # Colors, fonts, shared widgets
│   ├── login_window.py            # Login + Registration screen
│   ├── librarian_dashboard.py     # Full librarian UI
│   └── member_dashboard.py        # Full member UI
│
├── requirements.txt               # No pip installs needed!
└── README.md
```

---

## How to Run

### Prerequisites
- Python 3.10 or higher (download from https://python.org)
- That's it! No external packages needed.

### Steps

1. **Open VS Code**
2. Open the folder `library_management_system`
3. Open a terminal: `Terminal → New Terminal`
4. Run:
   ```
   python main.py
   ```

The app will:
- Auto-create `library.db` (SQLite database)
- Seed a default admin account

---

## Default Login Credentials

| Role       | Email                 | Password  |
|------------|-----------------------|-----------|
| Librarian  | admin@library.com     | admin123  |

You can register new Member accounts from the login screen.

---

## OOD Principles Demonstrated

| Principle         | Where Applied |
|-------------------|---------------|
| **Encapsulation** | All model classes use `_private` attributes with `@property` accessors |
| **Inheritance**   | `User` → `Librarian`, `Member` · Polymorphic `get_dashboard_label()` |
| **Polymorphism**  | `Report` generates different report types; search strategies by field |
| **Abstraction**   | `User` is an ABC (Abstract Base Class) using Python's `abc` module |

---

## Entity Classes (from Domain Model)

1. `User` — abstract base (name, email, phone, password)
2. `Librarian` — extends User
3. `Member` — extends User
4. `Book` — title, author, ISBN, category, copies
5. `Catalog` — manages book CRUD
6. `LoanRecord` — tracks borrow/return with due dates
7. `FineRecord` — calculates late fees ($0.50/day)
8. `PaymentTransaction` — records fine payments
9. `TransactionHistory` — aggregates member history
10. `Report` — summary stats, overdue report, top books

---

## Features

### Librarian
- Add / Edit / Delete books in catalog
- Search books by title, author, category, ISBN
- View all members
- View all loan records; return books
- View all fine records
- Generate reports: summary dashboard, top borrowed books, overdue list

### Member
- Search & borrow available books
- View active loans
- Pay unpaid fines
- View full borrowing history
