#!/usr/bin/env python3

"""This module defines the routes for user authentication and management."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import DBSessionDependency
from app.crud.patient_doctor import crud_patient_doctor
from app.crud.user import crud_user
from app.exceptions import ForbiddenActionError
from app.models.patient_doctor import PatientDoctor as PatientDoctorModel
from app.routers import CurrentUserDependency, UserDependency
from app.schemas.patient_doctor import (
    DoctorPatient,
    DoctorPatientRead,
    DoctorPatientReadBase,
    DoctorRead,
    Doctors,
    PatientDoctor,
    PatientDoctorCreate,
    PatientDoctorDelete,
    PatientDoctorRead,
    PatientDoctorReadBase,
)

router = APIRouter(tags=["Patients & Doctors"], prefix="/api/v1")


@router.post(
    "/me/doctors",
    summary="Assign doctors as a Patient",
    operation_id="assign_doctors",
    status_code=status.HTTP_201_CREATED,
    response_model=PatientDoctorRead,
    tags=["Patients"],
)
async def assign_doctors(
    patient_doctor: PatientDoctorCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
):
    """**This endpoint is accessible only by patients.**

    It allows patients to add the doctors they prefer in order to
    receive treatment from them. Multiple doctors can be assigned to a
    patient at a time, simply provide a list of the doctor IDs
    """
    if user.role != "Patient":
        raise ForbiddenActionError(
            error="You are unauthorized to perform this action. "
            "Only patients can perform this action."
        )

    doctors = crud_patient_doctor.create(
        db=db, doctor_ids=patient_doctor.doctor_ids, patient_id=user.id
    )

    return __build_patient_doctors_response(
        patient_id=user.id,
        doctors=doctors,
        message="Doctors assigned successfully.",
    )


@router.post(
    "/me/doctors/remove",
    summary="Remove assigned doctors as a Patient",
    operation_id="remove_assigned_doctors",
    status_code=status.HTTP_200_OK,
    tags=["Patients"],
)
async def remove_assigned_doctors(
    patient_doctor: PatientDoctorDelete,
    db: DBSessionDependency,
    user: CurrentUserDependency,
):
    """Remove assigned doctors for the current authenticated user (patient)"""
    if user.role != "Patient":
        raise ForbiddenActionError(
            error=(
                "You are unauthorized to perform this action. "
                "Only patients can perform this action."
            )
        )

    crud_patient_doctor.delete(
        patient_id=user.id, doctor_ids=patient_doctor.doctor_ids, db=db
    )

    return {
        "message": "Doctors unassigned successfully",
        "status_code": status.HTTP_200_OK,
        "success": True,
    }


@router.get(
    "/me/doctors",
    summary="List assigned doctors",
    operation_id="list_assigned_doctors",
    status_code=status.HTTP_200_OK,
    response_model=PatientDoctorRead,
    tags=["Patients"],
)
async def list_assigned_doctors(user: CurrentUserDependency):
    """Returns all the doctors this patient has selected."""
    if user.role != "Patient":
        raise ForbiddenActionError(
            error=(
                "You are unauthorized to perform this action. "
                "Only patients can perform this action."
            )
        )
    return __build_patient_doctors_response(
        patient_id=user.id,
        doctors=user.doctors,
        message="Assigned Doctors retrieved successfully",
    )


@router.get(
    "/me/patients",
    tags=["Doctors"],
    summary="View Patients for authenticated Doctor",
    status_code=status.HTTP_200_OK,
    response_model=DoctorPatientRead,
)
async def list_patients(user: CurrentUserDependency):
    if user.role != "Doctor":
        raise ForbiddenActionError(
            error=(
                "You are unauthorized to perform this action. "
                "Only doctors can perform this action."
            )
        )

    return __build_doctor_patients_response(
        doctor_id=user.id,
        patients=user.patients,
        message="Assigned patients retrieved successfully",
    )


@router.get(
    "/doctors",
    summary="Retrieve all the doctors available",
    dependencies=[UserDependency],
    response_model=Doctors,
)
async def list_doctors(db: DBSessionDependency):
    doctors = crud_user.get_all(db=db, filter_by={"role": "Doctor"})

    return Doctors(
        message="Doctors retrieved successfully",
        status_code=status.HTTP_200_OK,
        success=True,
        data=[
            DoctorRead(id=doctor.id, name=doctor.name) for doctor in doctors
        ],
    )


def __build_patient_doctors_response(
    patient_id: UUID, doctors: List[PatientDoctorModel], message: str
):
    """Builds the response for patient-doctor records."""
    return PatientDoctorRead(
        message=message,
        status_code=status.HTTP_201_CREATED,
        data=PatientDoctorReadBase(
            patient_id=patient_id,
            doctors=[
                PatientDoctor(
                    doctor_name=doctor.doctor.name if doctor.doctor else "",
                    **doctor.model_dump()
                )
                for doctor in doctors
            ],
        ),
    )


def __build_doctor_patients_response(
    doctor_id: UUID, patients: List[PatientDoctorModel], message: str
):
    """Builds the response for patient-doctor records."""
    patient_data = [
        DoctorPatient(
            patient_id=patient.patient_id,
            assigned_at=patient.assigned_at,
            patient_name=patient.patient.name,
        )
        for patient in patients
    ]

    return DoctorPatientRead(
        message=message,
        status_code=status.HTTP_201_CREATED,
        data=DoctorPatientReadBase(
            doctor_id=doctor_id,
            patients=patient_data,
        ),
    )
