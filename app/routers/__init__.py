#!/usr/bin/env python3

"""Defines user dependencies."""

from typing import Annotated

from fastapi import Depends

from app.core.security import get_current_user
from app.models.user import User

CurrentUserDependency = Annotated[User, Depends(get_current_user)]
UserDependency: User = Depends(get_current_user)
