#!/usr/bin/env python3

"""This module defines the model for associating patients and doctors."""

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.core import database as session
from app.core.dependencies import DBSessionDependency


class PatientDoctor(SQLModel, table=True):
    """Defines the Patient - Doctor association model"""

    patient_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    doctor_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    assigned_at: datetime = Field(
        default=datetime.now(timezone.utc),
        sa_column_kwargs={"nullable": False},
    )

    patient: "User" = Relationship(
        back_populates="patients",
        sa_relationship_kwargs={"foreign_keys": "PatientDoctor.patient_id"},
    )
    doctor: "User" = Relationship(
        back_populates="doctors",
        sa_relationship_kwargs={"foreign_keys": "PatientDoctor.doctor_id"},
    )

    __table_args__ = (
        UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor"),
    )

    @classmethod
    def count(cls, db: DBSessionDependency) -> int:
        """Counts the number of records in the table for this model."""
        return session.count(cls, db=db)
