from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True)
class User:
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserCredentials:
    """User plus password hash. Only the login use case ever sees this."""

    user: User
    password_hash: str


@dataclass(frozen=True)
class NewUser:
    email: str
    password: str
    first_name: str
    last_name: str


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    token_type: TokenType
    expires_at: datetime


@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str


@dataclass(frozen=True)
class LoginResult:
    user: User
    token: TokenPair


@dataclass(frozen=True)
class UserSession:
    """The active session of a user (one per user, same as the Go version).

    Tokens are stored as SHA-256 digests, so a leaked database cannot be replayed as live sessions.
    """

    user_id: int
    access_digest: str
    refresh_digest: str
