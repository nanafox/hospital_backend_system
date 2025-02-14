#!/usr/bin/env python3

"""This module defines the Note model."""

from uuid import UUID

from cryptography.fernet import Fernet
from sqlmodel import Field, Relationship

from app.core.config import settings
from app.models.base import BaseModel

fernet = Fernet(settings.encryption_key)


class Note(BaseModel, table=True):
    """Defines the Note model."""

    doctor_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    patient_id: UUID = Field(
        foreign_key="users.id", nullable=False, index=True
    )
    encrypted_content: str = Field(max_length=5000)

    doctor: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Note.doctor_id"}
    )
    patient: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Note.patient_id"}
    )

    def set_content(self, content: str):
        """Encrypts and stores the content."""
        self.encrypted_content = fernet.encrypt(content.encode()).decode()

    def get_content(self) -> str:
        """Decrypts and returns the content."""
        return (
            fernet.decrypt(self.encrypted_content.encode()).decode()
            if self.encrypted_content
            else ""
        )
