#!/usr/bin/env python3

"""This module tests the Notes endpoints."""


import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models.patient_doctor import PatientDoctor
from app.models.user import User
from app.schemas.base import Token


@pytest.mark.anyio
class TestCreationEndpoint:
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
            json={"email": doc_jdoe.email, "password": "password1234"},
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
            json={"email": patient_sally.email, "password": "password1234"},
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
            json={"email": doc_jdoe.email, "password": "password1234"},
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
            json={"email": doc_jdoe.email, "password": "password1234"},
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
    def test_can_fetch_existing_note(
        self, api_client: AsyncClient, doc_jdoe: User, patient_sally: User
    ):
        pass
