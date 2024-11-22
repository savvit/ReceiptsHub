from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import get_user_or_none
from src.config import Config


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashes the given password using bcrypt.

    This function takes a plain text password and returns a hashed version of the password.
    It uses the bcrypt hashing algorithm via the passlib library.

    Args:
        password (str): The plain text password to be hashed.
    """

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if the provided plain password matches the hashed password.

    This function compares a plain text password with a previously hashed password using bcrypt.
    It returns `True` if the passwords match, otherwise `False`.

    Args:
        plain_password (str): The plain text password to be verified.
        hashed_password (str): The hashed password to compare against.
    """

    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Creates a JWT (JSON Web Token) for user authentication.

    This function generates a JWT token with the provided data and includes an expiration time.
    The token is encoded using the specified secret key and algorithm from the configuration.

    Args:
        data (dict): The data to be encoded in the JWT token.
    """

    to_encode = data.copy()
    expire = datetime.now() + timedelta(
        minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        Config.SECRET_KEY,
        algorithm=Config.ALGORITHM
    )


async def authenticate_user(
        session: AsyncSession, username: str, password: str
):
    """
    Authenticates a user by verifying their username and password.

    This function looks up a user by their username, and if found, verifies their password.
    If both the username and password are valid, the user object is returned.
    If authentication fails, it returns `None`.

    Args:
        session (AsyncSession): The database session used to query user data.
        username (str): The username of the user trying to authenticate.
        password (str): The plain text password provided by the user.
    """

    user = await get_user_or_none(session, username=username)

    if user and verify_password(password, user.password):
        return user

    return None
