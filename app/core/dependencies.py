#!/usr/bin/env python3

"""This module defines the dependencies for the API."""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.core.database import Session, get_session

DBSessionDependency = Annotated[Session, Depends(get_session)]
