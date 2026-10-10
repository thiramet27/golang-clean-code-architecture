import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.domain.entities.user import TokenClaims, TokenType
from app.domain.errors import InvalidTokenError, TokenExpiredError

# Same claim layout as the Go version: {"claims": {"id": 1}, "sub": "access-token", ...}
SUBJECTS = {TokenType.ACCESS: "access-token", TokenType.REFRESH: "refresh-token"}
AUDIENCE = ["user", "admin"]
CLOCK_SKEW = timedelta(seconds=30)


class JwtTokenService:
    def __init__(
        self,
        secret: str,
        issuer: str,
        access_ttl: timedelta,
        refresh_ttl: timedelta,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._secret = secret
        self._issuer = issuer
        self._ttl = {TokenType.ACCESS: access_ttl, TokenType.REFRESH: refresh_ttl}
        self._now = now

    def issue(self, user_id: int, token_type: TokenType, expires_at: datetime | None = None) -> str:
        now = self._now()
        payload: dict[str, Any] = {
            "claims": {"id": user_id},
            "iss": self._issuer,
            "sub": SUBJECTS[token_type],
            "aud": AUDIENCE,
            "exp": expires_at or now + self._ttl[token_type],
            "nbf": now,
            "iat": now,
            "jti": uuid.uuid4().hex,  # two tokens issued in the same second must still differ
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def parse(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience="user",
                issuer=self._issuer,
                # Time claims are checked below against self._now, so tests can control the clock.
                options={
                    "require": ["exp", "sub", "claims"],
                    "verify_exp": False,
                    "verify_nbf": False,
                    "verify_iat": False,
                },
            )
        except jwt.DecodeError as e:
            raise InvalidTokenError("token format is invalid") from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"parse token failed: {e}") from e

        now = self._now().timestamp()
        if now >= payload["exp"]:
            raise TokenExpiredError()
        if now + CLOCK_SKEW.total_seconds() < payload.get("nbf", 0):
            raise InvalidTokenError("token is not valid yet")

        token_type = next((t for t, sub in SUBJECTS.items() if sub == payload["sub"]), None)
        user_id = payload["claims"].get("id") if isinstance(payload["claims"], dict) else None
        if token_type is None or not isinstance(user_id, int):
            raise InvalidTokenError("claims type is invalid")
        return TokenClaims(
            user_id=user_id,
            token_type=token_type,
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
