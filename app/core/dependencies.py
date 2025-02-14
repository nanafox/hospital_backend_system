#!/usr/bin/env python3

"""This module defines the dependencies for the API."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.database import Session, get_session

DBSessionDependency = Annotated[Session, Depends(get_session)]

OAuth2SchemeDependency = Annotated[
    str, Depends(OAuth2PasswordBearer(tokenUrl=settings.login_route))
]
