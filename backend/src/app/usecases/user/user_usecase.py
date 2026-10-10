import hashlib
import hmac
from weakref import WeakKeyDictionary

from app.domain.entities.user import (
    LoginResult,
    NewUser,
    TokenClaims,
    TokenPair,
    TokenType,
    User,
    UserSession,
)
from app.domain.errors import InvalidCredentialsError, InvalidTokenError, NotFoundError, ValidationError
from app.domain.repositories.user_repository import UserRepository
from app.usecases.user.ports import PasswordHasher, TokenService

MIN_PASSWORD_LENGTH = 8


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class UserUsecase:
    # A use case is created per request, so the dummy hash is cached per hasher instead of per instance.
    _dummy_hashes: "WeakKeyDictionary[PasswordHasher, str]" = WeakKeyDictionary()

    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def register(self, new_user: NewUser) -> User:
        if len(new_user.password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
        return await self._users.insert(
            email=new_user.email.lower(),
            password_hash=await self._hasher.hash(new_user.password),
            first_name=new_user.first_name,
            last_name=new_user.last_name,
        )

    async def login(self, email: str, password: str) -> LoginResult:
        credentials = await self._users.get_by_email(email.lower())
        password_hash = credentials.password_hash if credentials else await self._get_dummy_hash()
        if not await self._hasher.verify(password, password_hash) or credentials is None:
            raise InvalidCredentialsError()

        user = credentials.user
        pair = TokenPair(
            access=self._tokens.issue(user.id, TokenType.ACCESS),
            refresh=self._tokens.issue(user.id, TokenType.REFRESH),
        )
        await self._save_session(user.id, pair)
        return LoginResult(user=user, token=pair)

    async def refresh_token(self, refresh_token: str) -> LoginResult:
        claims = await self._verify_session_token(refresh_token, TokenType.REFRESH)
        user = await self._require_user(claims.user_id)

        # Rotate both tokens, but the new refresh token keeps the original expiry,
        # so a session can't be extended forever by refreshing.
        pair = TokenPair(
            access=self._tokens.issue(user.id, TokenType.ACCESS),
            refresh=self._tokens.issue(user.id, TokenType.REFRESH, expires_at=claims.expires_at),
        )
        await self._save_session(user.id, pair)
        return LoginResult(user=user, token=pair)

    async def logout(self, refresh_token: str) -> None:
        claims = await self._verify_session_token(refresh_token, TokenType.REFRESH)
        await self._users.delete_session(claims.user_id)

    async def authenticate(self, access_token: str) -> tuple[User, str | None]:
        """Return the user and their permission for a valid, non-revoked access token."""
        claims = await self._verify_session_token(access_token, TokenType.ACCESS)
        user = await self._require_user(claims.user_id)
        return user, await self._users.get_permission(user.id)

    async def get_profile(self, user_id: int) -> User:
        return await self._require_user(user_id)

    # --- helpers ---

    async def _get_dummy_hash(self) -> str:
        """Checked against when the email doesn't exist, so login takes as long as with a real account."""
        cached = self._dummy_hashes.get(self._hasher)
        if cached is None:
            cached = self._dummy_hashes[self._hasher] = await self._hasher.hash("timing-equalizer")
        return cached

    async def _verify_session_token(self, token: str, expected: TokenType) -> TokenClaims:
        claims = self._tokens.parse(token)
        if claims.token_type is not expected:
            raise InvalidTokenError(f"expected {expected} token")

        session = await self._users.find_session(claims.user_id)
        stored = None
        if session is not None:
            stored = session.access_digest if expected is TokenType.ACCESS else session.refresh_digest
        # A valid signature is not enough: logout / re-login revokes old tokens.
        if stored is None or not hmac.compare_digest(stored, token_digest(token)):
            raise InvalidTokenError("user token not found")
        return claims

    async def _save_session(self, user_id: int, pair: TokenPair) -> None:
        await self._users.save_session(
            UserSession(
                user_id=user_id,
                access_digest=token_digest(pair.access),
                refresh_digest=token_digest(pair.refresh),
            )
        )

    async def _require_user(self, user_id: int) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("user not found")
        return user
