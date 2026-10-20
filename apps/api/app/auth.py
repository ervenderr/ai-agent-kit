from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.models import User

_bearer = HTTPBearer(auto_error=False)


async def current_user(
    request: Request, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> User:
    """PLACEHOLDER AUTH: the bearer token is looked up in users.api_token.

    Swap this dependency for real authentication (OIDC/session/JWT with hashed or signed credentials).
    Everything downstream only needs a `User` with `id` and `scopes`.
    """
    if creds is None:
        raise HTTPException(401, "Missing bearer token")
    async with request.app.state.db() as s:
        user = await s.scalar(select(User).where(User.api_token == creds.credentials))
    if user is None:
        raise HTTPException(401, "Invalid token")
    return user
