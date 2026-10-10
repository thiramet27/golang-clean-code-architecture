"""What the user use case needs from the outside world. Implementations live in infrastructure."""

from datetime import datetime
from typing import Protocol

from app.domain.entities.user import TokenClaims, TokenType


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenService(Protocol):
    def issue(self, user_id: int, token_type: TokenType, expires_at: datetime | None = None) -> str:
        """expires_at=None uses the configured lifetime of token_type."""
        ...

    def parse(self, token: str) -> TokenClaims:
        """Raises InvalidTokenError / TokenExpiredError."""
        ...
