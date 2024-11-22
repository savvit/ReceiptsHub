from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette.responses import PlainTextResponse

from src.checks.models import Check
from src.checks.schemas import (
    CreateCheckResponse, CheckCreate, PaymentResponse, GetDetailCheckResponse,
    CheckFilterParams
)
from src.checks.service import (
    get_filtered_checks_query, get_check_by_id_from_db
)
from src.checks.utils import (
    add_products_to_check, calculate_totals, create_check_record,
    fetch_check_with_products, apply_filters
)
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.products.schemas import ProductResponse
from src.users.models import User


router = APIRouter(prefix="/checks", tags=["Check processing"])


@router.post("/create", response_model=CreateCheckResponse)
async def create_check(
    check_data: CheckCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Create a new check and associate it with the current user.

    Args:
        check_data (CheckCreate): The data required to create a new check,
        including payment and product details.
        user (User): The currently authenticated user, injected via `Depends`.
        session (AsyncSession): The database session, injected via `Depends`.

    Returns:
        CreateCheckResponse: A detailed response containing the newly created
        check and associated products.
    """

    total, rest = await calculate_totals(check_data)

    new_check = await create_check_record(
        session=session,
        user_id=user.id,
        total=total,
        rest=rest,
        payment_type=check_data.payment.type,
        payment_amount=check_data.payment.amount,
    )

    await add_products_to_check(session, new_check.id, check_data.products)
    await session.commit()

    check_with_products = await fetch_check_with_products(session, new_check.id)

    return CreateCheckResponse(
        id=check_with_products.id,
        user_id=check_with_products.user_id,
        created_at=check_with_products.created_at,
        total=check_with_products.total,
        rest=check_with_products.rest,
        payment=PaymentResponse(
            type=check_with_products.payment_type,
            amount=check_with_products.payment_amount
        ),
        products=[
            ProductResponse(
                name=product.name,
                price=product.price,
                quantity=product.quantity,
                total=product.total
            )
            for product in check_with_products.products
        ]
    )


@router.get("/list", response_model=List[CreateCheckResponse])
async def list_checks(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    filters: CheckFilterParams = Depends(),
    skip: int = 0,
    per_page: int = 10
):
    """
    Retrieve a list of checks filtered by various criteria.

    Args:
        session (AsyncSession): The database session dependency.
        user (User): The currently authenticated user.
        filters (CheckFilterParams): The filters to apply to the query.
        skip (int): The number of records to skip. Default is 0.
        per_page (int): The maximum number of records to return. Default is 10.

    Returns:
        List[CreateCheckResponse]: A list of filtered checks with their details.
    """

    query_filters = apply_filters(filters, user.id)

    checks = await get_filtered_checks_query(
        session=session,
        filters=query_filters,
        user_id=user.id,
        skip=skip,
        per_page=per_page
    )

    response = [
        CreateCheckResponse(
            id=check.id,
            user_id=check.user_id,
            total=check.total,
            rest=check.rest,
            created_at=check.created_at,
            payment=PaymentResponse(
                type=check.payment_type,
                amount=check.payment_amount
            ),
            products=[
                ProductResponse.from_orm(prod) for prod in check.products
            ]
        )
        for check in checks
    ]

    return response


@router.get("/{check_id}")
async def get_check_by_id(
        check_id: int,
        request: Request,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Retrieves a check by its ID and returns detailed information,
    including products.

    Args:
        check_id (int): The ID of the check to retrieve.
        user (User): The currently authenticated user.
        session (AsyncSession): The database session dependency.

    Returns:
        GetDetailCheckResponse: A response model containing the details
        of the check.
    """

    check = await get_check_by_id_from_db(check_id, user.id, session)

    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    return GetDetailCheckResponse(
        id=check.id,
        user_id=check.user_id,
        created_at=check.created_at,
        total=check.total,
        payment=PaymentResponse(
            type=check.payment_type,
            amount=check.payment_amount
        ),
        rest=check.rest,
        products=[
            ProductResponse(
                name=product.name,
                price=product.price,
                quantity=product.quantity,
                total=product.total
            )
            for product in check.products
        ],
        receipt_url=f"{request.url}/text"
    )


@router.get("/{check_id}/text", response_model=str)
async def get_check_text(
        check_id: int,
        session: AsyncSession = Depends(get_db),
        fop_width: int = 10,
        qty_width: int = 6,
        price_width: int = 12,
        name_width: int = 20,
        total_width: int = 12,
        sum_width: int = 20,
        payment_width: int = 15,
        date_width: int = 20
):
    """
    Generates a formatted text representation of a check.

    This endpoint retrieves a check by its ID, including its user and products,
    and returns a formatted string with the check details. The text includes:
    - The FOP (Full Name) of the user.
    - A list of products with their quantity, price, and total.
    - The total amount, payment amount, and remaining amount.
    - The creation date of the check.
    The width of the columns in the text can be customized using the provided query parameters.

    Args:
        check_id (int): The ID of the check to retrieve.
        session (AsyncSession): The database session used to query the check and related data.
        fop_width (int): The width for the FOP (user's full name) column. Default is 10.
        qty_width (int): The width for the quantity column. Default is 6.
        price_width (int): The width for the price column. Default is 12.
        name_width (int): The width for the product name column. Default is 20.
        total_width (int): The width for the total column. Default is 12.
        sum_width (int): The width for the sum column. Default is 20.
        payment_width (int): The width for the payment column. Default is 15.
        date_width (int): The width for the date column. Default is 20.
    """

    result = await session.execute(
        select(Check)
        .options(selectinload(Check.products), selectinload(
            Check.user))
        .where(Check.id == check_id)
    )
    check = result.scalars().first()

    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    check_text = f"{'ФОП':>{fop_width}} {check.user.full_name}\n"
    check_text += "=" * (fop_width + len(
        check.user.full_name) + 1) + "\n"

    for product in check.products:
        check_text += f"{product.quantity:>{qty_width}.2f} x {product.price:>{price_width},.2f}\n"
        check_text += f"{product.name:<{name_width}} {product.total:>{total_width},.2f}\n"

    check_text += "-" * (fop_width + len(
        check.user.full_name) + 1) + "\n"

    check_text += f"{'СУМА':<{sum_width}} {check.total:>{total_width},.2f}\n"
    check_text += f"{'Картка':<{payment_width}} {check.payment_amount:>{total_width},.2f}\n"
    check_text += f"{'Решта':<{payment_width}} {check.rest:>{total_width},.2f}\n"
    check_text += "=" * (fop_width + len(
        check.user.full_name) + 1) + "\n"

    check_text += f"{check.created_at.strftime('%d.%m.%Y %H:%M'):<{date_width}}\n"
    check_text += "Дякуємо за покупку!"

    return PlainTextResponse(content=check_text)
