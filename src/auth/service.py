from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User


async def get_user_or_none(session: AsyncSession, **filter_by):
    """
    Retrieves a user from the database based on the provided filters.

    This function executes a query to find a user that matches the filter criteria.
    It uses SQLAlchemy's `filter_by` method to filter users by the provided arguments.
    If no user is found, it returns `None`.

    Args:
        session (AsyncSession): The database session used to execute the query.
        **filter_by: Dynamic keyword arguments that are used to filter users
        in the database. For example, `username="john_doe"` or `user_id=1`.

    """

    query = select(User).filter_by(**filter_by)

    result = await session.execute(query)

    return result.scalars().first()
