#!/usr/bin/env python3

"""This module defines the schema for notes."""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field
from sqlmodel import SQLModel

from app.models.note import Note
from app.schemas.base import BaseResponse


class NoteCreate(SQLModel):
    content: str = Field(description="The contents of the note")
    patient_id: UUID = Field(description="The patient receiving the note")


class Base(SQLModel):
    id: UUID
    name: str


class Patient(Base):
    pass


class Doctor(Base):
    pass


class Note(SQLModel):
    id: UUID
    doctor: Doctor
    patient: Patient
    content: str
    created_at: datetime

    @classmethod
    def model_validate(cls, note: Note):
        """Converts DB model to response schema with decrypted content."""
        return cls(
            id=note.id,
            doctor=note.doctor,
            patient=note.patient,
            content=note.content,
            created_at=note.created_at,
        )


class NoteResponse(BaseResponse[Note]):
    data: Note


class NotesResponse(BaseResponse[List[Note]]):
    data: List[Note]
    count: int


class NotesFilterParams(SQLModel):
    doctor_id: UUID | None = Field(
        default=None,
        description=(
            "The doctor to filter by, used only when the user is a patient."
        ),
    )
    patient_id: UUID | None = Field(
        default=None,
        description=(
            "The patient to filter by, used only when the user is a doctor."
        ),
    )
