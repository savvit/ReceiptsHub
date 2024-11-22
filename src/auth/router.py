from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import RegistrationResponse, Registration, Login
from src.auth.service import get_user_or_none
from src.auth.utils import (
    hash_password, authenticate_user, create_access_token
)
from src.database import get_db
from src.users.models import User

router = APIRouter(prefix="/auth", tags=["Registration and Login"])


@router.post("/register", response_model=RegistrationResponse)
async def register_user(
        user_data: Registration,
        session: AsyncSession = Depends(get_db)
):
    """
    Registers a new user.

    This endpoint receives the user data (full name, username, and password),
    checks if the username is already taken, hashes the password, and creates
    a new user in the database.

    Args:
        user_data (Registration): The user information to register.
        session (AsyncSession): The database session.
    """

    user_exist = await get_user_or_none(
        session,
        username=user_data.username
    )

    if user_exist:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        full_name=user_data.full_name,
        username=user_data.username,
        password=hashed_password
    )

    session.add(new_user)

    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post("/login")
async def login_user(
        response: Response,
        user: Login,
        session: AsyncSession = Depends(get_db)
):
    """
   Authenticates the user and generates a JWT token.

   This endpoint checks if the provided username and password are valid,
   authenticates the user, and returns a JWT token that can be used for
   authenticated requests.

   Args:
       response (Response): The response object to set the authentication token as a cookie.
       user (Login): The user's login information (username and password).
       session (AsyncSession): The database session.
   """

    user = await authenticate_user(
        session,
        user.username,
        user.password
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {"sub": user.username}
    )
    response.set_cookie(
        "receipthub_access_token",
        token,
        httponly=True
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
