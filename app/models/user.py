#!/usr/bin/env python3

"""This module defines the User model."""

from pydantic import EmailStr
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.models.base import BaseModel
from app.models.note import Note
from app.models.patient_doctor import PatientDoctor


class User(BaseModel, table=True):
    """Defines User Model."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True, nullable=False)
    role: str = Field(index=True)
    name: str = Field(nullable=False, description="The name of the user")
    password_hash: str

    doctors: Mapped[list["PatientDoctor"]] = Relationship(
        back_populates="patient",
        sa_relationship_kwargs={"foreign_keys": "[PatientDoctor.patient_id]"},
    )

    patients: Mapped[list["PatientDoctor"]] = Relationship(
        back_populates="doctor",
        sa_relationship_kwargs={"foreign_keys": "[PatientDoctor.doctor_id]"},
    )

    doctor_notes: Mapped[list["Note"]] = Relationship(
        back_populates="doctor",
        sa_relationship_kwargs={
            "foreign_keys": "Note.doctor_id",
            "lazy": "selectin",
        },
    )
    patient_notes: Mapped[list["Note"]] = Relationship(
        back_populates="patient",
        sa_relationship_kwargs={
            "foreign_keys": "Note.patient_id",
            "lazy": "selectin",
        },
    )
