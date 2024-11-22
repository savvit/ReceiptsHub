from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.checks.models import Check
from src.checks.schemas import CheckCreate, CheckFilterParams
from src.products.models import Product
from src.products.schemas import ProductResponse


async def calculate_totals(check_data: CheckCreate):
    """
    Calculate the total price of products and the remaining balance.

    Args:
        check_data (CheckCreate): Input data with product and payment details.

    Returns:
        tuple[float, float]: Total price and remaining balance.

    Raises:
        HTTPException: If the payment amount is insufficient.
    """

    total = sum(
        product.price * product.quantity for product in check_data.products)
    rest = check_data.payment.amount - total

    if rest < 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount is less than the total price"
        )

    return total, rest


async def create_check_record(
        session: AsyncSession, user_id: int, total: float, rest: float,
        payment_type: str, payment_amount: float
):
    """
    Create a new check record in the database.

    Args:
        session (AsyncSession): The database session.
        user_id (int): ID of the user creating the check.
        total (float): Total amount for the check.
        rest (float): Remaining balance.
        payment_type (str): Type of payment.
        payment_amount (float): Amount paid.

    Returns:
        Check: The created check object.
    """

    new_check = Check(
        user_id=user_id,
        total=total,
        payment_type=payment_type,
        payment_amount=payment_amount,
        rest=rest,
    )
    session.add(new_check)
    await session.flush()

    return new_check


async def add_products_to_check(
        session: AsyncSession, check_id: int, products_data: List[ProductResponse]
):
    """
    Add product records associated with a check in the database.

    Args:
        session (AsyncSession): The database session.
        check_id (int): The ID of the associated check.
        products_data (List[ProductResponse]): List of product data to add.
    """

    products = [
        Product(
            name=product_data.name,
            price=product_data.price,
            quantity=product_data.quantity,
            total=product_data.price * product_data.quantity,
            check_id=check_id,
        )
        for product_data in products_data
    ]
    session.add_all(products)


async def fetch_check_with_products(session: AsyncSession, check_id: int) -> Check:
    """
    Fetch a check record with associated products from the database.

    Args:
        session (AsyncSession): The database session.
        check_id (int): ID of the check to fetch.

    Returns:
        Check: The check record with products.
    """
    result = await session.execute(
        select(
            Check
        ).options(
            selectinload(Check.products)
        ).where(
            Check.id == check_id
        )
    )

    return result.scalars().first()


def apply_filters(filters: CheckFilterParams, user_id: int):
    """
    Applies filters to the Check query based on the provided filter parameters.

    Args:
        filters (CheckFilterParams): The filter parameters provided by the user.
        user_id (int): The ID of the currently authenticated user.

    Returns:
        list: A list of conditions to be applied to the SQL query.
    """

    query_filters: list = []

    if filters.created_from:
        query_filters.append(Check.created_at >= filters.created_from)
    if filters.created_to:
        query_filters.append(Check.created_at <= filters.created_to)
    if filters.min_total:
        query_filters.append(Check.total >= filters.min_total)
    if filters.max_total:
        query_filters.append(Check.total <= filters.max_total)
    if filters.payment_type:
        query_filters.append(Check.payment_type == filters.payment_type)

    query_filters.append(Check.user_id == user_id)

    return query_filters
