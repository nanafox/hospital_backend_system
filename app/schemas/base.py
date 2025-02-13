#!/usr/bin/env python3

"""This module defines base schemas."""

from datetime import datetime, timezone
from typing import Generic, TypeVar

from fastapi import status
from pydantic import UUID4, EmailStr, HttpUrl, model_validator
from sqlmodel import Field, SQLModel

ResponseModel = TypeVar("ResponseModel")


class BaseResponse(SQLModel, Generic[ResponseModel]):
    message: str
    status_code: int
    success: bool = True
    url: HttpUrl | None = Field(default=None, exclude=True)
    count: int | None = Field(
        default=None, description="The number of items.", exclude=True
    )
    data: ResponseModel

    @model_validator(mode="before")
    @classmethod
    def compute_count(cls, values):
        """Computes the number of items in the data list.

        Args:
            values (dict): The values passed to the model.

        Returns:
            dict: The updated values with the correct count.
        """
        if "data" in values and isinstance(values["data"], list):
            values["count"] = len(values["data"])

        return values


class Timestamp(SQLModel):
    created_at: datetime = Field(
        default=datetime.now(timezone.utc),
        sa_column_kwargs={"nullable": False},
    )
    updated_at: datetime = Field(
        default=datetime.now(timezone.utc),
        sa_column_kwargs={
            "onupdate": datetime.now(timezone.utc),
            "nullable": False,
        },
    )


class TokenBase(SQLModel):
    """Represents the schema for a token."""

    access_token: str
    token_type: str = "bearer"
    expires: datetime


class Token(BaseResponse[TokenBase]):
    """Represents the schema for a token."""

    message: str = "Token created successfully."
    status_code: int = status.HTTP_201_CREATED
    data: TokenBase


class TokenPayload(SQLModel):
    """Represents the payload of a token."""

    user_id: UUID4
    email: EmailStr
