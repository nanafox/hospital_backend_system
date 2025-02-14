#!/usr/bin/env python3

"""This module defines the schema for User operations."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr, Field, computed_field
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.security import hash_password
from app.schemas.base import BaseResponse


class UserRoleEnum(str, Enum):
    """Defines the User roles."""

    doctor = "Doctor"
    patient = "Patient"


class UserBase(SQLModel):
    id: uuid.UUID = Field(description="The ID of the user")
    name: str = Field(description="The name of the user")
    email: EmailStr = Field(description="The user's email")
    role: UserRoleEnum = Field(description="The user's role")
    created_at: datetime
    updated_at: datetime


class User(UserBase):
    """User schema."""


class UserResponse(BaseResponse[UserBase]):
    """Schema for user response."""

    message: str = Field(
        examples=["User retrieved successfully", "User created successfully"]
    )
    status_code: int = Field(examples=[200, 201])
    data: User


class UserCreate(SQLModel):
    """Schema for new user account."""

    name: str = Field(description="The name of the user")
    email: EmailStr = Field(description="The user's email")
    role: UserRoleEnum = Field(description="The user's role")
    password: str = Field(
        description="The user's password",
        min_length=settings.minimum_password_length,
        max_length=settings.maximum_password_length,
    )

    @computed_field
    @property
    def password_hash(self) -> str:
        return hash_password(password=self.password)


class UserLogin(SQLModel):
    """Schema for user login."""

    email: EmailStr = Field(description="The user's email")
    password: str = Field(
        description="The user's password",
        min_length=settings.minimum_password_length,
        max_length=settings.maximum_password_length,
    )
