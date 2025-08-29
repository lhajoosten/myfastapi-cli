from __future__ import annotations

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Email(str):
    def __new__(cls, value: str):  # noqa: D401
        if not EMAIL_RE.match(value):
            raise ValueError("Invalid email format")
        return str.__new__(cls, value)
