"""
models/user.py
--------------
Implements the User abstract base class, Librarian, and Member
following OOD principles: Encapsulation, Inheritance, Polymorphism.
"""
from abc import ABC, abstractmethod
from database.db import get_connection
import hashlib


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class User(ABC):
    """Abstract base class for all system users."""

    def __init__(self, user_id: int, name: str, email: str, phone: str, role: str):
        self._id = user_id
        self._name = name
        self._email = email
        self._phone = phone
        self._role = role

    # --- Properties (Encapsulation) ---
    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

    @property
    def phone(self):
        return self._phone

    @property
    def role(self):
        return self._role

    @abstractmethod
    def get_dashboard_label(self) -> str:
        """Polymorphic: each subclass returns its own label."""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, name={self._name!r})"

    # --- Static / Class helpers ---
    @staticmethod
    def authenticate(email: str, password: str):
        """Returns a User subclass instance if credentials are valid, else None."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        conn.close()
        if row and row["password"] == _hash_password(password):
            if row["role"] == "librarian":
                return Librarian(row["id"], row["name"], row["email"], row["phone"])
            else:
                return Member(row["id"], row["name"], row["email"], row["phone"])
        return None

    @staticmethod
    def register(name: str, email: str, phone: str, password: str, role: str):
        """Registers a new user. Returns (True, user_id) or (False, error_msg)."""
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)",
                (name, email, phone, _hash_password(password), role)
            )
            conn.commit()
            return True, cur.lastrowid
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()


class Librarian(User):
    def __init__(self, user_id, name, email, phone):
        super().__init__(user_id, name, email, phone, "librarian")

    def get_dashboard_label(self) -> str:
        return "Librarian Dashboard"


class Member(User):
    def __init__(self, user_id, name, email, phone):
        super().__init__(user_id, name, email, phone, "member")

    def get_dashboard_label(self) -> str:
        return "Member Dashboard"
