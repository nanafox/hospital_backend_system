#!/usr/bin/env python3

"""This module defines security functions."""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlmodel import select

from app.core.config import settings
from app.core.dependencies import DBSessionDependency, OAuth2SchemeDependency
from app.exceptions import UnauthorizedError
from app.models.user import User
from app.schemas.base import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(*, password: str) -> str:
    """Hashes the given password using the pwd_context.

    Args:
        password (str): The password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def is_valid_password(*, plain_password: str, hashed_password: str) -> bool:
    """Verify that the plain password matches the hashed_password in the DB."""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(
    db: DBSessionDependency, email: EmailStr, password: str
) -> User | None:
    """Authenticate the user using their email and password."""
    user: User | None = db.exec(select(User).where(User.email == email)).first()

    if not user:
        return None

    if not is_valid_password(
        plain_password=password, hashed_password=user.password_hash
    ):
        return None

    return user


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Generate the access token for the user."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.secret_key,
        algorithm=settings.hashing_algorithm,
    )

    settings.access_token_duration = expire
    return encoded_jwt


async def verify_access_token(
    *,
    token: OAuth2SchemeDependency,
) -> TokenPayload:
    """Verifies that the token being used is valid."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.hashing_algorithm]
        )
        user_id = payload.get("sub")
        email = payload.get("email")

        if user_id is None or email is None:
            raise UnauthorizedError()

        token_data = TokenPayload(user_id=user_id, email=email)
    except InvalidTokenError as error:
        raise UnauthorizedError() from error

    return token_data


async def get_current_user(
    token: OAuth2SchemeDependency, db: DBSessionDependency
) -> User:
    """Returns the current authenticated user."""
    token_data = await verify_access_token(token=token)

    if user := db.get(User, token_data.user_id):
        return user
    else:
        raise UnauthorizedError()
