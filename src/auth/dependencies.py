from datetime import datetime

from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import get_user_or_none
from src.config import Config
from src.database import get_db


def get_token(request: Request):
    """
        Retrieves the JWT token from the cookies in the incoming request.

        This function looks for the `receipthub_access_token` cookie in the request.
        If the token is not found, an HTTP 401 Unauthorized error is raised.

        Args:
            request (Request): The incoming HTTP request object.
    """

    token = request.cookies.get("receipthub_access_token")

    if not token:
        raise HTTPException(status_code=401)
    return token


async def get_current_user(
        session: AsyncSession = Depends(get_db), token: str = Depends(get_token)
):
    """
    Retrieves the currently authenticated user based on the provided JWT token.

    This function decodes the JWT token, validates its expiration time, and checks
    if the token is valid. If the token is valid, it retrieves the user from the
    database based on the `username` contained in the token's payload.

    Args:
        session (AsyncSession): The database session used to query user data.
        token (str): The JWT token to be validated and decoded.
    """

    try:
        payload = jwt.decode(
            token,
            Config.SECRET_KEY,
            algorithms=Config.ALGORITHM
        )
    except JWTError:
        raise HTTPException(status_code=401)

    expire: str = payload.get("exp")

    if not expire or int(expire) < datetime.utcnow().timestamp():
        raise HTTPException(status_code=401)

    username = payload.get("sub")

    user = await get_user_or_none(session, username=username)

    return user
