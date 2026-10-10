from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.domain.entities.user import TokenType
from app.domain.errors import InvalidTokenError, TokenExpiredError
from app.infrastructure.security.jwt_tokens import JwtTokenService

SECRET = "unit-test-secret-0123456789abcdef-long-enough-for-hs512-0123456789"


def service(secret: str = SECRET, issuer: str = "golang-first-api-app") -> JwtTokenService:
    return JwtTokenService(secret, issuer, timedelta(hours=1), timedelta(days=2))


def test_claims_have_the_same_layout_as_the_go_version() -> None:
    token = service().issue(42, TokenType.ACCESS)
    payload = jwt.decode(token, SECRET, algorithms=["HS256"], audience="user")
    assert payload["claims"] == {"id": 42}
    assert payload["sub"] == "access-token"
    assert payload["aud"] == ["user", "admin"]
    assert payload["iss"] == "golang-first-api-app"


def test_round_trip() -> None:
    claims = service().parse(service().issue(7, TokenType.REFRESH))
    assert (claims.user_id, claims.token_type) == (7, TokenType.REFRESH)


def test_refresh_token_uses_refresh_lifetime() -> None:
    # Go bug: refresh tokens were signed with GOAPP_JWT_ACCESS_EXPIRES
    claims = service().parse(service().issue(1, TokenType.REFRESH))
    assert claims.expires_at - datetime.now(UTC) > timedelta(days=1)


def test_custom_expiry_is_kept() -> None:
    expires = datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=30)
    assert service().parse(service().issue(1, TokenType.REFRESH, expires_at=expires)).expires_at == expires


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        service(secret="another-secret-0123456789abcdef!!").issue(1, TokenType.ACCESS),
        service(issuer="someone-else").issue(1, TokenType.ACCESS),
        jwt.encode(
            {
                "claims": {"id": 1},
                "sub": "access-token",
                "aud": "user",
                "exp": 9999999999,
                "iss": "golang-first-api-app",
            },
            SECRET,
            algorithm="HS512",
        ),
    ],
    ids=["garbage", "wrong-secret", "wrong-issuer", "wrong-algorithm"],
)
def test_rejects_invalid_tokens(token: str) -> None:
    with pytest.raises(InvalidTokenError):
        service().parse(token)


def test_rejects_expired_token() -> None:
    past = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(TokenExpiredError):
        service().parse(service().issue(1, TokenType.ACCESS, expires_at=past))
