#!/usr/bin/env python3

"""This module defines the base model for all other models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import declared_attr
from sqlmodel import Field

from app.core import database as session
from app.core.dependencies import DBSessionDependency
from app.schemas.base import Timestamp


class BaseModel(Timestamp):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )

    @classmethod
    def count(cls, db: DBSessionDependency) -> int:
        """Counts the number of records in the table for this model."""
        return session.count(cls, db=db)

    def save(self, *, db: DBSessionDependency, created: bool = False, **kwargs):
        """Saves the current object to the database."""
        self.updated_at = (
            self.created_at if created else datetime.now(timezone.utc)
        )
        return session.save(self, db=db, **kwargs)

    def delete(self, *, db: DBSessionDependency):
        """Deletes the current object from the database."""
        session.delete(self, db=db)
