"""
models/book.py
--------------
Book entity class and Catalog management class.
"""
from database.db import get_connection


class Book:
    """Represents a book in the library catalog."""

    def __init__(self, book_id, title, author, isbn, category, total_copies, available_copies):
        self._id = book_id
        self._title = title
        self._author = author
        self._isbn = isbn
        self._category = category
        self._total_copies = total_copies
        self._available_copies = available_copies

    # --- Properties ---
    @property
    def id(self): return self._id

    @property
    def title(self): return self._title

    @property
    def author(self): return self._author

    @property
    def isbn(self): return self._isbn

    @property
    def category(self): return self._category

    @property
    def total_copies(self): return self._total_copies

    @property
    def available_copies(self): return self._available_copies

    def is_available(self) -> bool:
        return self._available_copies > 0

    def to_tuple(self):
        """Returns row data for display in a Treeview."""
        return (self._id, self._title, self._author, self._isbn,
                self._category, self._total_copies, self._available_copies)

    def __repr__(self):
        return f"Book(id={self._id}, title={self._title!r}, isbn={self._isbn!r})"


class Catalog:
    """Manages the library book catalog (CRUD operations)."""

    @staticmethod
    def add_book(title, author, isbn, category, total_copies) -> tuple[bool, str]:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO books (title,author,isbn,category,total_copies,available_copies) VALUES (?,?,?,?,?,?)",
                (title, author, isbn, category, int(total_copies), int(total_copies))
            )
            conn.commit()
            return True, "Book added successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update_book(book_id, title, author, isbn, category, total_copies) -> tuple[bool, str]:
        conn = get_connection()
        try:
            conn.execute(
                """UPDATE books SET title=?,author=?,isbn=?,category=?,total_copies=?
                   WHERE id=?""",
                (title, author, isbn, category, int(total_copies), book_id)
            )
            conn.commit()
            return True, "Book updated successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete_book(book_id) -> tuple[bool, str]:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM books WHERE id=?", (book_id,))
            conn.commit()
            return True, "Book deleted."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_books() -> list[Book]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
        conn.close()
        return [Book(*row) for row in rows]

    @staticmethod
    def search_books(keyword: str, field: str = "title") -> list[Book]:
        """Search by title, author, or category."""
        allowed = {"title", "author", "category", "isbn"}
        if field not in allowed:
            field = "title"
        conn = get_connection()
        rows = conn.execute(
            f"SELECT * FROM books WHERE {field} LIKE ? ORDER BY title",
            (f"%{keyword}%",)
        ).fetchall()
        conn.close()
        return [Book(*row) for row in rows]

    @staticmethod
    def get_book_by_id(book_id) -> Book | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
        conn.close()
        return Book(*row) if row else None
