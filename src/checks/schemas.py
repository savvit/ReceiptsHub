from decimal import Decimal
from fastapi import Query
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date, datetime

from src.products.schemas import ProductResponse, ProductCreate, PaymentCreate


class PaymentResponse(BaseModel):
    """
        A model representing payment details.

        Attributes:
            type (str): The type of payment (e.g., 'cash', 'card').
            amount (Decimal): The amount paid.
    """

    type: str
    amount: Decimal


class CreateCheckResponse(BaseModel):
    """
    A response model for a created check.

    Attributes:
        id (int): The ID of the check.
        user_id (int): The ID of the user who made the check.
        created_at (date): The date the check was created.
        total (int): The total amount of the check.
        payment (PaymentResponse): The payment details for the check.
        rest (Decimal): The remaining balance of the check.
        products (List[ProductResponse]): A list of products in the check.

    Validation:
        Ensures that the total and rest values are not negative.
    """

    id: int
    user_id: int
    created_at: date
    total: int
    payment: PaymentResponse
    rest: Decimal
    products: List[ProductResponse]

    @field_validator("total", "rest")
    def check_non_negative(cls, value, field):
        """
        Validate that the total and rest fields are not negative.

        Args:
            value (Any): The value to be validated.
            field (str): The name of the field being validated.

        Returns:
            value: The validated value.

        Raises:
            ValueError: If the value is negative, an error is raised with a specific message.
        """

        if value < 0:
            raise ValueError(f"{field.field_name} cannot be negative")
        return value


class GetDetailCheckResponse(CreateCheckResponse):
    """
    A detailed response model for a check.

    Inherits from `CreateCheckResponse` and adds the `receipt_url` field,
    which provides a link to the text representation of the check.

    Attributes:
        receipt_url (str): A URL pointing to the text representation of the check.
    """

    receipt_url: str


class PaginatedChecksResponse(BaseModel):
    """
    A paginated response model for a list of checks.

    This model is used to return a paginated list of checks,
    including metadata like the total number of checks, the current page, and the page size.

    Attributes:
        checks (List[CreateCheckResponse]): A list of checks for the current page.
        total_count (int): The total number of checks available.
        page (int): The current page number.
        page_size (int): The number of checks per page.
    """

    checks: List[CreateCheckResponse]
    total_count: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


class CheckCreate(BaseModel):
    """
    A model for creating a new check.

    This model includes the products and payment details required to create a new check.
    It also provides a `total` property to calculate the total amount of the check.

    Attributes:
        products (List[ProductCreate]): A list of products included in the check.
        payment (PaymentCreate): The payment details for the check.

    Properties:
        total (int): A calculated total amount for the check, based on the sum of all product totals.
    """

    products: List[ProductCreate]
    payment: PaymentCreate

    @property
    def total(self):
        """
        Calculate the total amount for the check.

        This property iterates over the products in the check and sums up their total values.

        Returns:
            int: The total amount of the check.
        """

        return sum(product.total for product in self.products)


class CheckFilterParams(BaseModel):
    """
    A model for filtering checks based on various parameters.

    Attributes:
        created_from (Optional[str]): Start date for filtering checks in ISO format.
        created_to (Optional[str]): End date for filtering checks in ISO format.
        min_total (Optional[float]): Minimum total amount for filtering checks.
        max_total (Optional[float]): Maximum total amount for filtering checks.
        payment_type (Optional[str]): Payment type for filtering checks ('cash' or 'card').
    """

    created_from: Optional[str] = Query(
        None,
        description="Start date in ISO format (e.g., '2023-01-01')"
    )
    created_to: Optional[str] = Query(
        None,
        description="End date in ISO format (e.g., '2023-01-01')"
    )
    min_total: Optional[float] = Query(
        None, ge=0, description="Minimum total amount"
    )
    max_total: Optional[float] = Query(
        None, ge=0, description="Maximum total amount"
    )
    payment_type: Optional[str] = Query(
        None, regex="^(cash|card)$",
        description="Payment type ('cash' or 'card')"
    )
