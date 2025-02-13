#!/usr/bin/env python3

"""This module defines the User model."""


from pydantic import EmailStr
from sqlmodel import Field

from app.models.base import BaseModel


class User(BaseModel, table=True):
    """Defines User Model."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True, nullable=False)
    role: str
    name: str = Field(nullable=False, description="The name of the user")
    password_hash: str
