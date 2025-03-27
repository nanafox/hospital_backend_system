#!/usr/bin/env python3

"""This module defines the Note model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.core.dependencies import DBSessionDependency
from app.exceptions import BadRequestError
from app.models.base import BaseModel
from app.services import encryption

if TYPE_CHECKING:
    from app.models.user import User


class Note(BaseModel, table=True):
    """Defines the Note model."""

    doctor_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    patient_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    encrypted_content: str = Field(nullable=False)

    doctor: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Note.doctor_id"}
    )
    patient: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Note.patient_id"}
    )

    @property
    def content(self) -> str:
        """Return the decrypted version of the doctor's note.

        The doctor's note is encrypted in the database for maximum
        security. In the API responses, ensure that the doctor or
        patient requesting this information has some form of
        relationship to it. If it's a doctor, then they must be owner,
        if it's a patient, then it must be for them.
        """
        return encryption.decrypt(content=self.encrypted_content)

    def save(
        self, *, db: DBSessionDependency, created: bool = False, **kwargs
    ) -> User:
        """Save the new note."""
        content = kwargs.get("content")

        if not content and not self.encrypted_content:
            raise BadRequestError(error="content can't be empty")

        if content:
            if not encryption.is_encrypted(content):
                self.encrypted_content = encryption.encrypt(content)
            else:
                raise BadRequestError(
                    error="content should not be pre-encrypted"
                )
        elif not encryption.is_encrypted(self.encrypted_content):
            self.encrypted_content = encryption.encrypt(self.encrypted_content)

        return super().save(db=db, created=created)
