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
    get_filtered_checks_query, get_check_by_id_from_db, fetch_check_data
)
from src.checks.utils import (
    add_products_to_check, calculate_totals, create_check_record,
    fetch_check_with_products, apply_filters, format_footer, format_summary,
    format_products, format_header
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


@router.get("/{check_id}/text", response_class=PlainTextResponse)
async def get_check_text(
        check_id: int,
        session: AsyncSession = Depends(get_db),
        line_width: int = 40
):
    """
    Generates a text-based receipt with the structure shown in the image.
    The product name is aligned to the left, while the quantity, price, and total are aligned to the right.

    Args:
        check_id (int): The ID of the receipt.
        session (AsyncSession): The database session used to retrieve data.
        line_width (int): The total width of the line. Default is 40.
    """

    check = await fetch_check_data(check_id, session)

    check_text = format_header(check.user.full_name, line_width)
    check_text += format_products(check.products, line_width)
    check_text += "-" * line_width + "\n"
    check_text += format_summary(check, line_width)
    check_text += "=" * line_width + "\n"
    check_text += format_footer(check.created_at, line_width)

    return PlainTextResponse(content=check_text)
