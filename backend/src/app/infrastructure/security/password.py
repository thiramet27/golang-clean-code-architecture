import bcrypt
from anyio import to_thread


class BcryptPasswordHasher:
    def __init__(self, rounds: int = 10) -> None:
        self._rounds = rounds

    # bcrypt takes ~50-100 ms of CPU per call and releases the GIL, so it runs in worker threads.
    # Called directly from async code it would freeze every other request while it hashes.

    async def hash(self, password: str) -> str:
        salt = bcrypt.gensalt(self._rounds)
        hashed: bytes = await to_thread.run_sync(bcrypt.hashpw, password.encode(), salt)
        return hashed.decode()

    async def verify(self, password: str, password_hash: str) -> bool:
        try:
            ok: bool = await to_thread.run_sync(bcrypt.checkpw, password.encode(), password_hash.encode())
            return ok
        except ValueError:  # malformed hash
            return False
