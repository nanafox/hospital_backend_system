#!/usr/bin/env python3

"""This modules defines the schemas for Patient Doctor selection."""

from datetime import datetime
from typing import List
from uuid import UUID

from sqlmodel import Field, SQLModel

from app.schemas.base import BaseResponse


class PatientDoctorBase(SQLModel):
    doctor_ids: List[UUID] = Field(
        description="List of doctor IDs to assign to the patient"
    )


class PatientDoctorCreate(PatientDoctorBase):
    pass


class PatientDoctor(SQLModel):
    doctor_id: UUID
    doctor_name: str
    assigned_at: datetime


class PatientDoctorReadBase(SQLModel):
    patient_id: UUID
    doctors: List[PatientDoctor]

    class Config:
        from_attributes = True


class PatientDoctorRead(BaseResponse[PatientDoctorReadBase]):
    data: PatientDoctorReadBase


class PatientDoctorDelete(PatientDoctorBase):
    doctor_ids: List[UUID] = Field(
        description="List of doctor IDs to remove from the patient"
    )


class DoctorPatient(SQLModel):
    patient_id: UUID
    patient_name: str
    assigned_at: datetime


class DoctorPatientReadBase(SQLModel):
    doctor_id: UUID
    patients: List[DoctorPatient]

    class Config:
        from_attributes = True


class DoctorPatientRead(BaseResponse[DoctorPatientReadBase]):
    data: DoctorPatientReadBase


class DoctorRead(SQLModel):
    """Schema for reading basic doctor details."""

    id: UUID
    name: str


class Doctors(BaseResponse[List[DoctorRead]]):
    """Response schema for retrieving multiple doctors."""

    data: List[DoctorRead]
    count: int
