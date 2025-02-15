#!/usr/bin/env python3

"""This module contains tests to validate that the Patient-Doctor API endpoints
are working as they should.

It will test that users can view doctors, choose the doctors they want
and view the doctors they've chosen. Also, users may want to remove
previous doctors, so tests will be made available for those as well
"""

import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models.patient_doctor import PatientDoctor
from app.models.user import User
from app.schemas.base import Token
from app.schemas.patient_doctor import DoctorPatientRead, PatientDoctorRead


@pytest.mark.anyio
class TestPatientDoctorCreationEndpoint:
    """Tests the POST /api/v1/me/doctors/ endpoint.

    This endpoint allows the user (a patient) to select from the
    available list of doctors.
    """

    async def test_create_with_unauthenticated_user(
        self, api_client: AsyncClient
    ):
        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={
                "doctor_ids": [
                    "bcb28c34-07a4-456c-953c-f8e80125a3c2",
                    "d2521f3c-87be-48d4-8a94-9d0af53df4ee",
                ]
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_doctor_selection_with_a_doctor(
        self, api_client: AsyncClient, doc_jdoe: User
    ):
        """Test that doctors are forbidden from selecting doctors."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={
                "doctor_ids": [
                    "bcb28c34-07a4-456c-953c-f8e80125a3c2",
                    "d2521f3c-87be-48d4-8a94-9d0af53df4ee",
                ]
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        expected_error_msg = (
            "You are unauthorized to perform this action. "
            "Only patients can perform this action."
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail").get("error") == expected_error_msg

    async def test_doctor_assignment_with_patient_user(
        self,
        api_client: AsyncClient,
        patient_sally: User,
        doc_jdoe: User,
        session,
    ):
        """Test that the doctor assignment works for the patient."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={"doctor_ids": [str(doc_jdoe.id)]},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify that exactly one instance was created
        assert PatientDoctor.count(db=session) == 1

        data = PatientDoctorRead(**response.json()).data
        doctors = data.doctors

        # Verify patient ID is the authenticated user's ID
        assert data.patient_id == patient_sally.id

        # Verify that the Doctor ID assigned is the same the patient requested
        assert doctors[0].doctor_id == doc_jdoe.id

    async def test_doctor_assignment_with_empty_doctor_ids(
        self,
        api_client: AsyncClient,
        patient_sally: User,
        session,
    ):
        """Test that the doctor assignment without any IDs in the array
        fails."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={"doctor_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify that the instance was NOT created
        assert PatientDoctor.count(db=session) == 0

    async def test_doctor_unassignment_with_a_doctor(
        self, api_client: AsyncClient, doc_jdoe: User
    ):
        """Test that doctors are forbidden from accessing the POST
        /api/v1/me/doctors/remove endpoint.

        This ensures that only patients can assign and remove their
        doctors.
        """
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/me/doctors/remove",
            json={
                "doctor_ids": [
                    "bcb28c34-07a4-456c-953c-f8e80125a3c2",
                    "d2521f3c-87be-48d4-8a94-9d0af53df4ee",
                ]
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        expected_error_msg = (
            "You are unauthorized to perform this action. "
            "Only patients can perform this action."
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail").get("error") == expected_error_msg

    async def test_doctor_selection_with_non_existent_doctor_ids(
        self, api_client: AsyncClient, patient_sally: User
    ):
        """Test that non-existent doctor IDs fail."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={
                "username": patient_sally.email,
                "password": "password1234",
            },
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={
                "doctor_ids": [
                    "bcb28c34-07a4-456c-953c-f8e80125a3c2",
                    "d2521f3c-87be-48d4-8a94-9d0af53df4ee",
                ]
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.anyio
class TestPatientDoctorDeletionEndpoint:
    """Tests that the POST /api/v1/me/doctors/remove.

    This endpoint takes te IDs of the Doctors to remove from the
    patient. Valid doctors who are part of the current user's list will
    be removed, an error is thrown when anything goes wrong.
    """

    async def test_deletion_with_doctor_user_fails(
        self, api_client: AsyncClient, doc_jdoe: User
    ):
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.get(
            "/api/v1/me/doctors",
            headers={"Authorization": f"Bearer {token}"},
        )

        expected_error_msg = (
            "You are unauthorized to perform this action. "
            "Only patients can perform this action."
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail").get("error") == expected_error_msg

    async def test_delete_non_existent_assigment(
        self, api_client: AsyncClient, patient_sally: User
    ):
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.post(
            "/api/v1/me/doctors/remove",
            json={
                "doctor_ids": [
                    "bcb28c34-07a4-456c-953c-f8e80125a3c2",
                    "d2521f3c-87be-48d4-8a94-9d0af53df4ee",
                ]
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_valid_assigned_doctor(
        self,
        api_client: AsyncClient,
        patient_sally: User,
        doc_jdoe: User,
        session,
    ):
        """Test that patients can remove doctors they assigned to
        themselves."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        # assign doctor to patient
        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={"doctor_ids": [str(doc_jdoe.id)]},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify that exactly one instance was created
        assert PatientDoctor.count(db=session) == 1

        response: Response = await api_client.post(
            "/api/v1/me/doctors/remove",
            json={"doctor_ids": [str(doc_jdoe.id)]},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.json().get("message") == "Doctors unassigned successfully"
        )

        # Verify that the association instance was deleted
        assert PatientDoctor.count(db=session) == 0


@pytest.mark.anyio
class TestAssignedDoctorsListingEndpoint:
    """Tests the GET /api/v1/me/doctors to ensure doctors are retrieved when
    requested."""

    async def test_with_unauthenticated_user(self, api_client: AsyncClient):
        """Test that unauthenticated users are not granted access."""
        response: Response = await api_client.get("/api/v1/me/doctors")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_with_existing_doctor_assignment(
        self, api_client: AsyncClient, patient_sally: User, doc_jdoe: User
    ):
        """Test that authenticated users can view their selected doctors."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        # assign doctor to patient
        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={"doctor_ids": [str(doc_jdoe.id)]},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        assigned_doctors_response: Response = await api_client.get(
            "/api/v1/me/doctors", headers={"Authorization": f"Bearer {token}"}
        )

        assert assigned_doctors_response.status_code == status.HTTP_200_OK

        # verify that the doctor's ID is in the response
        doctors = PatientDoctorRead(
            **assigned_doctors_response.json()
        ).data.doctors

        assert doc_jdoe.id == doctors[0].doctor_id


@pytest.mark.anyio
class TestDoctorPatientsListingEndpoint:
    """Tests the GET /api/v1/me/patients endpoint.

    This endpoint is only accessible to doctors.
    """

    async def test_listing_with_unauthenticated_user(
        self, api_client: AsyncClient
    ):
        """Test that unauthenticated users are not granted access."""
        response: Response = await api_client.get("/api/v1/me/patients")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_forbidden_for_patient_users(
        self, api_client: AsyncClient, patient_sally: User
    ):
        """Tests that this endpoint is only accessible to doctors."""
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        response: Response = await api_client.get(
            "/api/v1/me/patients",
            headers={"Authorization": f"Bearer {token}"},
        )

        expected_error_msg = (
            "You are unauthorized to perform this action. "
            "Only doctors can perform this action."
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail").get("error") == expected_error_msg

    async def test_doctor_can_list_patients(
        self,
        api_client: AsyncClient,
        patient_sally: User,
        doc_jdoe: User,
    ):
        """Test that authenticated doctors can view their patients."""
        # sign in as patient and select the doctor
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": patient_sally.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        # assign doctor to patient
        response: Response = await api_client.post(
            "/api/v1/me/doctors",
            json={"doctor_ids": [str(doc_jdoe.id)]},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # now sign in as the doctor and verify the patient has selected you
        sign_in_response: Response = await api_client.post(
            "/api/v1/auth/login",
            data={"username": doc_jdoe.email, "password": "password1234"},
        )

        assert sign_in_response.status_code == status.HTTP_200_OK

        token = Token(**sign_in_response.json()).data.access_token

        assigned_patients_response: Response = await api_client.get(
            "/api/v1/me/patients", headers={"Authorization": f"Bearer {token}"}
        )

        assert assigned_patients_response.status_code == status.HTTP_200_OK

        # verify that the patient is in the doctors list of of patients
        patients = DoctorPatientRead(
            **assigned_patients_response.json()
        ).data.patients

        assert patients[0].patient_id == patient_sally.id
