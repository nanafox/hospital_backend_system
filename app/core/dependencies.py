#!/usr/bin/env python3

"""This module defines the dependencies for the API."""

from typing import Annotated, Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param

from app.core.config import settings
from app.core.database import Session, get_session
from app.exceptions import UnauthorizedError

DBSessionDependency = Annotated[Session, Depends(get_session)]


class OAuth2PasswordBearer2(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise UnauthorizedError()
            else:
                return None
        return param


OAuth2SchemeDependency = Annotated[
    str,
    Depends(
        OAuth2PasswordBearer2(
            tokenUrl=settings.login_route,
            scheme_name="Bearer Token Authentication",
        )
    ),
]
