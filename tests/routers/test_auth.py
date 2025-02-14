#!/usr/bin/env python3

"""This module tests the authentication endpoints to ensure users can create
account, login, and update their profile as needed."""


import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models.user import User
from app.schemas.base import Token
from app.schemas.user import UserResponse


@pytest.mark.anyio
class TestSignUpEndpoint:
    """Tests the /api/v1/auth/signup endpoint."""

    auth_endpoint = "/api/v1/auth/signup"

    async def test_that_valid_data_creates_a_user(
        self, api_client: AsyncClient, session
    ):
        """Test that valid user creation works."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={
                "name": "John Doe",
                "email": "jdoe@email.com",
                "password": "password1234",
                "role": "Doctor",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        user_response = UserResponse(**response.json())

        assert user_response.message == "User created successfully"
        assert user_response.data.name == "John Doe"

        assert User.count(db=session) == 1

    async def test_that_password_hash_is_not_returned_in_response(
        self, api_client: AsyncClient
    ):
        """Test that the password hash is not returned in the response after a
        successful user sign up action."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={
                "name": "John Doe",
                "email": "jdoe@email.com",
                "password": "password1234",
                "role": "Doctor",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        user_response = UserResponse(**response.json())

        assert not hasattr(user_response.data, "password_hash")
        assert not hasattr(user_response.data, "password")

    async def test_invalid_data_raises_error_422(
        self, api_client: AsyncClient
    ):
        """Test that invalid request bodies raises error 422."""
        response: Response = await api_client.post(
            self.auth_endpoint, json={"email": "jdoe@email.com"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_that_emails_are_unique_on_account_creation(
        self, api_client: AsyncClient, session
    ):
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={
                "name": "John Doe",
                "email": "jdoe@email.com",
                "password": "password1234",
                "role": "Doctor",
            },
        )

        # the first time should pass without errors
        assert response.status_code == status.HTTP_201_CREATED
        assert User.count(db=session) == 1

        # the second time must fail
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={
                "name": "John Doe",
                "email": "jdoe@email.com",
                "password": "password1234",
                "role": "Doctor",
            },
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        error = response.json()["detail"]

        assert error.get("error") == "Sorry, this email is already taken"
        assert error.get("success") is False
        assert error.get("status_code") == 409

        # ensure that the number of users is the same and didn't change
        assert User.count(db=session) == 1

    async def test_signup_with_invalid_role_type(
        self, api_client: AsyncClient
    ):
        """Test that invalid roles are not allowed to create accounts."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={
                "name": "John Doe",
                "email": "jdoe@email.com",
                "password": "password1234",
                "role": "Bad Role",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error = response.json()["detail"][0]

        assert error.get("msg") == "Input should be 'Doctor' or 'Patient'"

    async def test_patient_signup_works(
        self, session, api_client: AsyncClient
    ):
        """Test that patient account creations work as well."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={
                "name": "John Doe",
                "email": "jdoe@email.com",
                "password": "password1234",
                "role": "Patient",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert User.count(db=session) == 1

        user = UserResponse(**response.json())

        assert user.data.role == "Patient"


@pytest.mark.anyio
class TestLoginEndpoint:
    """Tests for the /api/v1/login endpoint."""

    auth_endpoint = "/api/v1/auth/login"

    async def test_login_without_available_user(self, api_client: AsyncClient):
        """Test that login fails when no user has been created in the database.

        For this test no user exists and therefore must fail.
        """
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={"email": "jdoe@email.com", "password": "password1234"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_works_for_existing_user(
        self, api_client: AsyncClient, doc_jdoe: User
    ):
        """Test that login works for an existing user with valid
        credentials."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={"email": doc_jdoe.email, "password": "password1234"},
        )
        token_response = Token(**response.json())

        assert token_response.status_code == status.HTTP_200_OK
        assert token_response.message == "Logged in successfully"

        token = token_response.data

        assert token.access_token is not None

    async def test_login_with_invalid_password(
        self, api_client: AsyncClient, doc_jdoe: User
    ):
        """Test that login fails for incorrect passwords."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={"email": doc_jdoe.email, "password": "WRONG PASSWORD"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_failed_login_has_www_authenticate_header(
        self, api_client: AsyncClient
    ):
        """Test that a failed login response includes the WWW-Authenticate
        header."""
        response: Response = await api_client.post(
            self.auth_endpoint,
            json={"email": "bad@email.com", "password": "WRONG PASSWORD"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        assert "www-authenticate" in response.headers.keys()
        assert response.headers.get("www-authenticate") == "Bearer"
