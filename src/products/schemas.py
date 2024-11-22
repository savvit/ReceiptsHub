from decimal import Decimal

from pydantic import BaseModel, field_validator


class ProductResponse(BaseModel):
    """
        A model representing a product in the check.

        Attributes:
            name (str): The name of the product.
            price (Decimal): The price of the product.
            quantity (int): The quantity of the product.
            total (int): The total amount for the product (price * quantity).

        Validation:
            Ensures that price, quantity, and total are not negative.
    """

    name: str
    price: Decimal
    quantity: int
    total: int

    @field_validator("price", "quantity", "total")
    def check_non_negative(cls, value, field):
        """
        Validate that the value is not negative. Applied to price, quantity, and total fields.

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

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """
    A model for creating a product within a check.

    This model represents the details of a product that is part of a check,
    including the product's name, price, and quantity. It also includes a
    calculated property for the total price of the product.

    Attributes:
        name (str): The name of the product.
        price (Decimal): The price per unit of the product.
        quantity (Decimal): The quantity of the product.

    Properties:
        total (Decimal): The total cost for this product (price * quantity).
    """

    name: str
    price: Decimal
    quantity: Decimal

    @property
    def total(self):
        """
        Calculate the total cost of the product.

        This property multiplies the price per unit by the quantity to calculate
        the total cost of the product.

        Returns:
            Decimal: The total cost of the product.
        """

        return self.price * self.quantity


class PaymentCreate(BaseModel):
    """
    A model for creating payment details.

    This model represents the details of a payment, including the payment type
    and the amount paid.

    Attributes:
        type (str): The type of payment (e.g., 'cash', 'card').
        amount (Decimal): The amount paid by the customer.
    """

    type: str
    amount: Decimal
