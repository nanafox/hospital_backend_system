#!/usr/bin/env python3

"""This module tests the Notes endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models.note import Note
from app.models.patient_doctor import PatientDoctor
from app.models.user import User
from app.schemas.base import Token
from app.schemas.note import NotesResponse, NoteResponse
from app.services import encryption


@pytest.mark.anyio
class TestCreationEndpoint:
    """Test the POST /api/v1/notes endpoint used by doctors to add patient
    notes."""

    async def test_valid_creation_works(
        self,
        api_client: AsyncClient,
        doc_jdoe: User,
        patient_sally: User,
        session,
    ):
        """Test that a doctor can create a note when logged in."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        # Add doctor-patient relationship to DB
        patient_doctor_relation = PatientDoctor(
            patient_id=patient_sally.id, doctor_id=doc_jdoe.id
        )

        session.add(patient_doctor_relation)
        session.commit()  # Ensure it's persisted

        # Send note creation request
        response: Response = await api_client.post(
            "/api/v1/notes",
            json={
                "content": "The patient needs long rests and sleep.",
                "patient_id": str(patient_sally.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

    async def test_fails_when_user_is_not_a_doctor(
        self, api_client: AsyncClient, patient_sally: User
    ):
        """Test that note creation fails when the user is not a doctor."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/notes",
            json={
                "content": "The patient needs long rests and sleep.",
                "patient_id": str(patient_sally.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_fails_when_patient_does_not_belong_to_doctor(
        self, api_client: AsyncClient, doc_jdoe: User, patient_sally: User
    ):
        """Test that note creation fails when the user is not a doctor."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/notes",
            json={
                "content": "The patient needs long rests and sleep.",
                "patient_id": str(patient_sally.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response

    async def test_fails_if_content_is_empty(
        self,
        api_client: AsyncClient,
        doc_jdoe: User,
        patient_sally: User,
        session,
    ):
        """❌ Should fail if the note content is empty."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )
        assert sign_in_response.status_code == status.HTTP_200_OK

        token = sign_in_response.json()["data"]["access_token"]

        # Assign doctor to patient
        patient_doctor_relation = PatientDoctor(
            patient_id=patient_sally.id, doctor_id=doc_jdoe.id
        )
        session.add(patient_doctor_relation)
        session.commit()

        response: Response = await api_client.post(
            "/api/v1/notes",
            json={
                "content": "",  # Empty content
                "patient_id": str(patient_sally.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"]["error"] == "content cannot be empty"


@pytest.mark.anyio
class TestSingleNoteFetchEndpoint:
    async def test_can_fetch_existing_note(
        self,
        api_client: AsyncClient,
        doc_jdoe: User,
        patient_sally: User,
        session,
    ):
        """Test that a doctor can fetch an existing note."""
        # create a new note for the patient.
        note = Note(
            patient_id=patient_sally.id,
            doctor_id=doc_jdoe.id,
            encrypted_content="Patient needs medications to treat rashes",
        )

        note.save(db=session, created=True)

        # ensure the note was saved
        assert Note.count(db=session) == 1

        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )
        assert sign_in_response.status_code == status.HTTP_200_OK

        token = sign_in_response.json()["data"]["access_token"]
        response: Response = await api_client.get(
            f"/api/v1/notes/{note.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        note_response: NoteResponse = NoteResponse(**response.json())
        assert note_response.message == "Note retrieved successfully"
        assert note_response.data.id == note.id

    async def test_throws_404_when_not_is_missing(
        self,
        api_client: AsyncClient,
        doc_jdoe: User,
    ):
        """Test that error 404 is raised when the note doesn't exist."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )
        assert sign_in_response.status_code == status.HTTP_200_OK

        token = sign_in_response.json()["data"]["access_token"]
        response: Response = await api_client.get(
            "/api/v1/notes/726d12d1-3ef1-48d6-8045-d878a9c54cfc",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
class TestNotesListingEndpoint:
    """Tests the GET /api/v1/notes endpoint used by doctors and patient to
    retrieve their notes."""

    async def test_authorized_access_fails(self, api_client: AsyncClient):
        response: Response = await api_client.get("/api/v1/notes")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_authenticated_patient_can_view_their_notes(
        self,
        api_client: AsyncClient,
        patient_bob: User,
        doc_jdoe: User,
        patient_sally: User,
        session,
    ):
        """Tests that patients can see only their notes given by their
        doctor."""
        # add doc_joe as the doctor for each of the users
        PatientDoctor(patient_id=patient_bob.id, doctor_id=doc_jdoe.id).save(db=session)

        PatientDoctor(patient_id=patient_sally.id, doctor_id=doc_jdoe.id).save(
            db=session
        )

        assert PatientDoctor.count(db=session) == 2

        # now create a note for each user
        #
        # note for patient Bob
        Note(
            doctor_id=doc_jdoe.id,
            patient_id=patient_bob.id,
            encrypted_content=encryption.encrypt("The user needs lots of rest"),
        ).save(db=session, created=True)

        # note for patient Sally
        Note(
            doctor_id=doc_jdoe.id,
            patient_id=patient_sally.id,
            encrypted_content=encryption.encrypt(
                "The patient is suffering from tubercolosis"
            ),
        ).save(db=session, created=True)

        assert Note.count(db=session) == 2

        # Now as the doctor retrieve the notes
        response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert response.status_code == status.HTTP_200_OK
        token = response.json()["data"]["access_token"]

        # now retrieve the notes as the doctor (Doctor John Doe)
        response: Response = await api_client.get(
            "/api/v1/notes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        # ensure it follows the schema
        doctor_notes = NotesResponse(**response.json())

        assert doctor_notes.count == 2

        # verify that the IDs match correctly for Bob and Sally
        assert doctor_notes.data[0].patient.id == patient_bob.id
        assert doctor_notes.data[1].patient.id == patient_sally.id

        # Now as patient Bob retrieve the notes, must be 1
        response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": "bob@email.com", "password": "password1234"},
        )

        assert response.status_code == status.HTTP_200_OK
        token = response.json()["data"]["access_token"]

        # now retrieve the notes as patient (Patient Bob Manny)
        response: Response = await api_client.get(
            "/api/v1/notes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        bob_notes = NotesResponse(**response.json())

        assert bob_notes.count == 1
        assert bob_notes.data[0].patient.id == patient_bob.id
