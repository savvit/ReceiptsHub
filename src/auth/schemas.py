import re

from pydantic import BaseModel, field_validator


class Registration(BaseModel):
    """
    A model for user registration, including validation for the full name and username.

    Attributes:
        full_name (str): The user"s full name. Must contain only letters (no digits or special characters).
        username (str): The username for the user. Must contain only letters (no digits or special characters).
        password (str): The password for the user. Must meet security requirements.
    """
    
    full_name: str
    username: str
    password: str

    @field_validator("username")
    def validate_username(cls, value):
        """
        Validate that the username contains only letters and digits (no special characters).

        Args:
            value (str): The value of the username to be validated.
        """

        if len(value) > 20:
            raise ValueError("Username cannot be longer than 20 characters")

        if not re.match(r"^[A-Za-z0-9]+$", value):
            raise ValueError(
                "Username must contain only letters and digits "
                "(no special characters)"
            )

        return value

    @field_validator("full_name")
    def validate_full_name(cls, value):
        """
        Validate that the full name contains only letters
        (no digits or special characters).

        Args:
            value (str): The value of the full name to be validated.
        """

        if len(value) > 50:
            raise ValueError("Full name cannot be longer than 50 characters")

        if not re.match(r"^[A-Za-z ]+$", value):
            raise ValueError(
                "Full name must contain only letters "
                "(no digits or special characters)"
            )

        return value

    @field_validator("password")
    def validate_password(cls, value):
        """
        Password check:
         - Must be at least 6 characters
         - Must contain at least one capital letter
         - Must contain at least one lowercase letter
         - Must contain at least one digit
        """

        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")

        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")

        return value


class Login(BaseModel):
    """
    A model for user login validation.

    This model validates the username and password for login.
    Both fields must not be empty.
    """

    username: str
    password: str

    @field_validator("username", "password")
    def not_empty(cls, value, field):
        """
        Validate that the field value is not empty or just whitespace.
        """

        if not value.strip():
            raise ValueError(
                f"{field.field_name} cannot be empty or contain only spaces"
            )

        return value


class RegistrationResponse(BaseModel):
    """
    This model is used to return the data when a user successfully registers.
    """
    
    full_name: str
    username: str

    class Config:
        from_attributes = True
