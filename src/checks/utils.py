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


def format_header(user_full_name: str, line_width: int) -> str:
    """
    Formats the header with the FOP (user's full name) centered.

    Args:
        user_full_name (str): The full name of the user.
        line_width (int): The total width of the line.

    Returns:
        str: The formatted header.
    """

    header = f"ФОП {user_full_name}"

    return f"{header:^{line_width}}\n" + "=" * line_width + "\n"


def format_products(products, line_width: int) -> str:
    """
    Formats the list of products with their details.

    Args:
        products (list): The list of products to format.
        line_width (int): The total width of the line.

    Returns:
        str: The formatted string for all products.
    """

    sum_label_width = line_width // 2
    sum_value_width = line_width - sum_label_width
    product_lines = ""

    for product in products:
        product_lines += (
            f"{product.name:<{sum_label_width}}"
            f"{f'{product.quantity:.2f} x {product.price:,.2f}':>{sum_value_width}}\n"
        )
        product_lines += f"{'':<{sum_label_width}}{product.total:>{sum_value_width},.2f}\n"

    return product_lines


def format_summary(check, line_width: int) -> str:
    """
    Formats the summary section, including total, payment amount, and remaining amount.

    Args:
        check: The check object containing summary details.
        line_width (int): The total width of the line.

    Returns:
        str: The formatted summary section.
    """

    sum_label_width = line_width // 2
    sum_value_width = line_width - sum_label_width

    summary = ""
    summary += f"{'СУМА':<{sum_label_width}}{check.total:>{sum_value_width},.2f}\n"
    summary += f"{'Картка':<{sum_label_width}}{check.payment_amount:>{sum_value_width},.2f}\n"
    summary += f"{'Решта':<{sum_label_width}}{check.rest:>{sum_value_width},.2f}\n"

    return summary


def format_footer(created_at, line_width: int) -> str:
    """
    Formats the footer section with the creation date and thank-you message.

    Args:
        created_at (datetime): The creation date of the receipt.
        line_width (int): The total width of the line.

    Returns:
        str: The formatted footer.
    """

    footer = f"{created_at.strftime('%d.%m.%Y %H:%M'):^{line_width}}\n"
    footer += "Дякуємо за покупку!".center(line_width)

    return footer
