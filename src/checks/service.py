from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

from src.checks.models import Check


async def get_filtered_checks_query(
    session: AsyncSession,
    filters: list,
    user_id: int,
    skip: int = 0,
    per_page: int = 10
):
    """
    Constructs and executes an SQL query to retrieve filtered checks from the database.

    Args:
        session (AsyncSession): The database session used for executing queries.
        filters (list): A list of filters to apply to the query.
        user_id (int): The ID of the current user.
        skip (int): The number of results to skip (used for pagination).
        per_page (int): The maximum number of results to return.

    Returns:
        list: A list of checks that match the filtering criteria.
    """

    query = (
        select(Check)
        .options(selectinload(Check.products))
        .where(and_(*filters, Check.user_id == user_id))
        .offset(skip)
        .limit(per_page)
    )

    result = await session.execute(query)

    return result.scalars().all()


async def get_check_by_id_from_db(
        check_id: int, user_id: int,
        session: AsyncSession
):
    """
    Retrieves a check from the database by its ID for a specific user.

    Args:
        check_id (int): The ID of the check.
        user_id (int): The ID of the user.
        session (AsyncSession): The database session dependency.

    Returns:
        Check: The check object retrieved from the database or None if not found.
    """

    result = await session.execute(
        select(
            Check
        ).options(
            selectinload(Check.products)
        ).where(
            and_(
                Check.id == check_id,
                Check.user_id == user_id
            )
        )
    )

    return result.scalars().first()
