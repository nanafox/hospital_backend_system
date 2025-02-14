#!/usr/bin/env python3

"""This module defines the routes for user authentication and management."""

from fastapi import APIRouter, status

from app.core import security
from app.core.config import settings
from app.core.dependencies import DBSessionDependency
from app.crud.user import crud_user
from app.exceptions import UnauthorizedError
from app.schemas.base import Token, TokenBase
from app.schemas.user import User, UserCreate, UserLogin, UserResponse

router = APIRouter(tags=["Authentication"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Sign up: Create a New Doctor or Patient",
    operation_id="signup",
)
async def signup(user: UserCreate, db: DBSessionDependency):
    data = crud_user.create(db=db, user=user)

    return UserResponse(
        message="User created successfully",
        data=User(**data.model_dump()),
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Login: Works for both patients and doctors",
    operation_id="login",
    response_model=Token,
)
async def login(
    credentials: UserLogin,
    db: DBSessionDependency,
):
    try:
        user = crud_user.get(by="email", identifier=credentials.email, db=db)
    except Exception:
        raise UnauthorizedError()

    if not security.is_valid_password(
        plain_password=credentials.password, hashed_password=user.password_hash
    ):
        raise UnauthorizedError()

    access_token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return Token(
        message="Logged in successfully",
        status_code=status.HTTP_200_OK,
        data=TokenBase(
            access_token=access_token,
            token_type="bearer",
            expires=settings.access_token_duration,
        ),
    )
