#!/usr/bin/env python3

"""This module defines the endpoints used by doctors to add patient notes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from starlette.status import HTTP_200_OK

from app.core.dependencies import DBSessionDependency
from app.crud.base import APICrudBase
from app.exceptions import BadRequestError, ForbiddenActionError
from app.models.note import Note
from app.routers import CurrentUserDependency
from app.schemas.note import (
    NoteBaseResponse,
    NoteCreate,
    NoteResponse,
    NotesFilterParams,
    NotesResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Doctor & Patient Notes"])

crud_note = APICrudBase(model=Note)


def is_my_patient(patient_id: UUID, doctor: CurrentUserDependency):
    """Verifies that a patient belongs to a doctor."""
    return patient_id in [patient.patient_id for patient in doctor.patients]


@router.post(
    "/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note for a patient by an authenticated doctor",
    operation_id="add_note",
)
async def add_node(
    note: NoteCreate, db: DBSessionDependency, user: CurrentUserDependency
):
    """## Add Note

    ### POST /notes

    #### Summary
    Create a new note for a patient by an authenticated doctor.

    #### Description
    This endpoint allows an authenticated doctor to create a new note for one of their patients. The doctor must be authorized to add notes for the specified patient.

    #### Request Body
    - **note**: `NoteCreate` (required)
      - **patient_id**: `int` (required) - The ID of the patient.
      - **content**: `str` (required) - The content of the note.

    #### Responses

    - **201 Created**
      - **Content**: `application/json`
      - **Example**:
        ```json
        {
          "message": "Note created successfully",
          "status_code": 201,
          "success": true,
          "data": {
            "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
            "doctor": {
              "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
              "name": "Dr. John Doe"
            },
            "patient": {
              "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
              "name": "Jane Smith"
            },
            "content": "Patient's note content",
            "created_at": "2019-08-24T14:15:22Z"
          }
        }
        ```

    - **403 Forbidden**
      - **Content**: `application/json`
      - **Schema**: `ErrorResponse`
      - **Example**:
        ```json
        {
          "error": "You are unauthorized to perform this action"
          "success": false,
          "status_code": 403
        }
        ```

    - **400 Bad Request**
      - **Content**: `application/json`
      - **Schema**: `ErrorResponse`
      - **Example**:
        ```json
        {
          "error": "content cannot be empty"
          "success": false,
          "status_code": 400
        }
        ```

    #### Security
    - Requires authentication.
    - The user must be a doctor.

    #### Tags
    - Notes
    """
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
    db_note.save(db=db, created=True, content=note.content)

    return NoteResponse(
        message="Note retrieved successfully",
        status_code=status.HTTP_200_OK,
        data=NoteBaseResponse.model_validate(db_note),
    )


@router.get(
    "/notes/{note_id}",
    summary="Retrieve the details of a single note",
    response_model=NoteResponse,
    status_code=HTTP_200_OK,
    operation_id="get_note",
)
def get_note(
    note_id: UUID, db: DBSessionDependency, user: CurrentUserDependency
):
    """Retrieve a single note's details."""
    note = crud_note.get_by_id(db=db, obj_id=str(note_id))

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
    summary="List all the notes for the authenticated doctor or patient",
    response_model=NotesResponse,
    operation_id="list_notes",
    tags=["Patients", "Doctors"],
)
async def list_notes(
    db: DBSessionDependency,
    user: CurrentUserDependency,
    filter_query: Annotated[NotesFilterParams, Query()],
):
    """## List Notes

    ### Endpoint: GET /api/v1/notes

    #### Summary
    List all the notes for the authenticated doctor or patient.

    #### Description
    This endpoint retrieves all notes associated with the authenticated user.
    If the user is a doctor, it will return notes related to the doctor's
    patients. If the user is a patient, it will return notes related to the patient.

    #### Responses

    - **200 OK**
      - **Content**: `application/json`
      - **Example**:
        ```json
        {
          "message": "Notes retrieved successfully",
          "status_code": 200,
          "success": true,
          "data": [
            {
              "id": "1d74d030-ad4d-4af3-8f33-cd54514ab1c9",
              "content": "Note content",
              "doctor": {
                "id": "006e444c-6a08-4c4b-b40d-2ae62c81338c",
                "name": "John Doe"
              },
              "patient": {
                "id": "902d1837-4b6c-44c7-8fdb-f044048ff0a5",
                "name": "Sally Banks"
              },
              "created_at": "2023-10-01T12:00:00Z",
            },
            ...
          ]
        }
        ```

    #### Security
    - Requires authentication.
    - The user must be either a doctor or a patient.

    #### Tags
    - Doctor Notes
    """
    if user.role == "Doctor":
        if filter_query.patient_id:
            notes = crud_note.get_all(
                db=db,
                filter_by={
                    "doctor_id": user.id,
                    "patient_id": filter_query.patient_id,
                },
            )
        else:
            notes = crud_note.get_all(db=db, filter_by={"doctor_id": user.id})

    else:
        if filter_query.doctor_id:
            notes = crud_note.get_all(
                db=db,
                filter_by={
                    "patient_id": user.id,
                    "doctor_id": filter_query.doctor_id,
                },
            )
        else:
            notes = crud_note.get_all(db=db, filter_by={"patient_id": user.id})

    return NotesResponse(
        message="Notes retrieved successfully",
        status_code=status.HTTP_200_OK,
        data=[NoteBaseResponse.model_validate(note) for note in notes],
    )
