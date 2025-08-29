from __future__ import annotations

from typing import Protocol, runtime_checkable, Dict, List, Optional

from app.domain.entities.user import User


@runtime_checkable
class UserRepositoryProtocol(Protocol):
    def create(self, username: str, password_hash: str, roles: List[str]) -> User: ...  # noqa: D401,E701
    def get_by_username(self, username: str) -> Optional[User]: ...  # noqa: D401,E701
    def get_by_id(self, user_id: int) -> Optional[User]: ...  # noqa: D401,E701


class InMemoryUserRepository(UserRepositoryProtocol):
    def __init__(self) -> None:
        self._by_id: Dict[int, User] = {}
        self._by_username: Dict[str, int] = {}
        self._next_id = 1

    def create(self, username: str, password_hash: str, roles: List[str]) -> User:
        user = User(id=self._next_id, username=username, password_hash=password_hash, roles=roles)
        self._by_id[self._next_id] = user
        self._by_username[username] = self._next_id
        self._next_id += 1
        return user

    def get_by_username(self, username: str) -> Optional[User]:
        _id = self._by_username.get(username)
        if _id is None:
            return None
        return self._by_id.get(_id)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._by_id.get(user_id)
