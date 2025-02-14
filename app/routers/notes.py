#!/usr/bin/env python3

"""This module defines the endpoints used by doctors to add patient notes."""

from uuid import UUID

from fastapi import APIRouter, status
from sqlmodel import select
from starlette.status import HTTP_200_OK

from app.core.dependencies import DBSessionDependency
from app.crud.base import APICrudBase
from app.exceptions import BadRequestError, ForbiddenActionError, NotFoundError
from app.models.note import Note
from app.routers import CurrentUserDependency
from app.schemas.note import (
    NoteBaseResponse,
    NoteCreate,
    NoteResponse,
    NotesResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Doctor Notes"])

crud_note = APICrudBase(model=Note)


def is_my_patient(patient_id: UUID, doctor: CurrentUserDependency):
    """Verifies that a patient belongs to a doctor."""
    return patient_id in [patient.patient_id for patient in doctor.patients]


@router.post(
    "/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_node(
    note: NoteCreate, db: DBSessionDependency, user: CurrentUserDependency
):
    if user.role != "Doctor":
        raise ForbiddenActionError(
            error="You are unauthorized to perform this action"
        )

    # Ensure that doctors can only notes for their patients
    if not is_my_patient(patient_id=note.patient_id, doctor=user):
        raise ForbiddenActionError(error="This is not a patient of yours")

    if note.content == "":
        raise BadRequestError(error="content cannot be empty")

    db_note = Note(**note.model_dump(), doctor_id=user.id)
    db_note.set_content(note.content)
    db_note.save(db=db, created=True)

    return NoteResponse.model_validate(db_note)


@router.get(
    "/notes/{note_id}",
    summary="Retrieve the details of a single note",
    response_model=NoteResponse,
    status_code=HTTP_200_OK,
)
def get_note(
    note_id: UUID, db: DBSessionDependency, user: CurrentUserDependency
):
    """Retrieve a single note's details."""
    query = select(Note).where(Note.id == note_id)
    note = db.exec(query).first()

    if not note:
        raise NotFoundError(error="Note not found")

    # Ensure the correct user can access the note
    if (user.role == "Doctor" and note.doctor_id != user.id) or (
        user.role == "Patient" and note.patient_id != user.id
    ):
        raise ForbiddenActionError(
            error="You are not authorized to read this note"
        )

    return NoteResponse(
        message="Note retrieved successfully",
        status_code=status.HTTP_200_OK,
        data=NoteBaseResponse.model_validate(note),
    )


@router.get(
    "/notes",
    summary="List all the notes for the authenticated doctor",
    response_model=NotesResponse,
)
async def list_notes(db: DBSessionDependency, user: CurrentUserDependency):
    if user.role == "Doctor":
        notes = crud_note.get_all(db=db, filter_by={"doctor_id": user.id})
    else:
        notes = crud_note.get_all(db=db, filter_by={"patient_id": user.id})

    return NotesResponse(
        message="Notes retrieved successfully",
        status_code=status.HTTP_200_OK,
        data=[NoteBaseResponse.model_validate(note) for note in notes],
    )
