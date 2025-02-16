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
from app.schemas import note as schema
from app.schemas.note import (
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
        data=schema.Note.model_validate(db_note),
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
    """## Retrieve Note Details

    ### Endpoint
    `GET /notes/{note_id}`

    ### Summary
    Retrieve the details of a single note.

    ### Parameters

    #### Path Parameters
    - `note_id` (UUID): The unique identifier of the note to retrieve.

    ### Responses

    #### 200 OK
    - **Description**: Note retrieved successfully.
    - **Response Model**: `NoteResponse`
      - `message` (str): A message indicating the note was retrieved successfully.
      - `status_code` (int): The HTTP status code.
      - `data` (Note): The details of the note.

    #### 403 Forbidden
    - **Description**: The user is not authorized to read this note.
    - **Response Model**: `ForbiddenActionError`
      - `error` (str): An error message indicating the user is not authorized.

    ### Request Example
    ```http
    GET /notes/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
    Host: example.com
    Authorization: Bearer <token>
    ```

    ### Response Example

    #### 200 OK
    ```json
    {
      "message": "Note retrieved successfully",
      "status_code": 200,
      "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Sample Note",
        "content": "This is a sample note.",
        "doctor_id": "a3c9ad01-0fbd-4083-b8e8-0b901c4ef227",
        "patient_id": "9b91ff9a-b373-4258-bfc2-f6e3d0e8ae0f",
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z"
      }
    }
    ```

    #### 403 Forbidden
    ```json
    {
      "error": "You are not authorized to read this note"
    }
    ```

    ### Security
    - Requires authentication via a Bearer token.
    - Access is restricted based on user roles:
      - Doctors can only access notes they created.
      - Patients can only access notes associated with their ID.
    """
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
        data=schema.Note.model_validate(note),
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
        data=[schema.Note.model_validate(note) for note in notes],
    )
