"""Business errors. Handlers map these to HTTP responses; the domain never knows about HTTP."""


class DomainError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    pass


class EmailAlreadyUsedError(DomainError):
    def __init__(self) -> None:
        super().__init__("email has already been used")


class InvalidCredentialsError(DomainError):
    def __init__(self) -> None:
        # Same message for "no such email" and "wrong password" so the API can't be used to find accounts.
        super().__init__("email or password is invalid")


class InvalidTokenError(DomainError):
    pass


class TokenExpiredError(InvalidTokenError):
    def __init__(self) -> None:
        super().__init__("token had expired")


class NotFoundError(DomainError):
    pass


class EntityModelNotFoundError(NotFoundError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"entity model not found: {slug}")


class PermissionDeniedError(DomainError):
    pass
