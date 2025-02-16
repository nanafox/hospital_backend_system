#!/usr/bin/env python3

"""This module defines the routes for user authentication and management."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core import security
from app.core.config import settings
from app.core.dependencies import DBSessionDependency
from app.crud.user import crud_user
from app.exceptions import UnauthorizedError
from app.schemas.base import Token, TokenBase, UnauthorizedErrorResponse
from app.schemas.user import User, UserCreate, UserResponse

router = APIRouter(tags=["Authentication"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Sign up: Create a New Doctor or Patient",
    operation_id="signup",
)
async def signup(user: UserCreate, db: DBSessionDependency):
    """## Sign Up Endpoint

    ### Endpoint
    `POST /api/v1/auth/signup`

    ### Summary
    Sign up: Create a new doctor or patient account.

    ### Operation ID
    `signup`

    ### Request Body
    - `user` (UserCreate): The user details required to create a new account.
      - `email` (str): The email address of the user.
      - `password` (str): The password for the user account.
      - `first_name` (str): The first name of the user.
      - `last_name` (str): The last name of the user.
      - `role` (str): The role of the user, either "Doctor" or "Patient".

    ### Responses

    #### 201 Created
    - **Description**: User created successfully.
    - **Response Model**: `UserResponse`
      - `message` (str): A message indicating the user was created successfully.
      - `status_code` (int): The HTTP status code.
      - `data` (User): The details of the created user.
        - `id` (UUID): The unique identifier of the user.
        - `email` (str): The email address of the user.
        - `name` (str): The name of the user.
        - `role` (str): The role of the user, either "doctor" or "patient".
        - `created_at` (datetime): The timestamp when the user was created.
        - `updated_at` (datetime): The timestamp when the user was last updated.

    #### 422 Unprocessable Entity
    - **Description**: Validation Error

    ### Request Example
    ```http
    POST /api/v1/auth/signup HTTP/1.1
    Host: example.com
    Content-Type: application/json

    {
      "email": "user@example.com",
      "password": "securepassword",
      "name": "John Doe"
      "role": "Doctor"
    }
    ```

    ### Response Example

    #### 201 Created
    ```json
    {
      "message": "User created successfully",
      "status_code": 201,
      "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "doctor",
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z"
      }
    }
    ```

    ### Security
    - No authentication required to access this endpoint.
    """
    new_user = crud_user.create(db=db, user=user)

    return UserResponse(
        message="User created successfully",
        data=User(**new_user.model_dump()),
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Login: Works for both patients and doctors",
    operation_id="login",
    response_model=Token,
    responses={
        200: {"description": "Log in successful", "model": Token},
        401: {
            "description": "Invalid credentials",
            "model": UnauthorizedErrorResponse,
        },
    },
)
async def login(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSessionDependency,
):
    """## Login Endpoint

    ### Endpoint
    `POST /api/v1/auth/login`

    ### Summary
    Login endpoint for both patients and doctors.

    ### Operation ID
    `login`

    ### Request Body
    - `credentials` (OAuth2PasswordRequestForm): The form containing
      the username (email) and password. Be sure to provide the user's email
      even though the field is `username`.

    ### Responses

    #### 200 OK
    - **Description**: Successfully logged in.
    - **Response Model**: `Token`
      - `message` (str): A message indicating successful login.
      - `status_code` (int): The HTTP status code.
      - `success` (bool): Always `true` on success.
      - `data` (TokenBase): The token data.
        - `access_token` (str): The JWT access token.
        - `token_type` (str): The type of the token, typically "bearer".
        - `expires` (int): The duration in seconds for which the token is valid.

    #### 401 Unauthorized
    - **Description**: Invalid credentials provided.
    - **Response Model**: `UnauthorizedError`
      - `detail` (dict): A dictionary / hash map containing the error details
        - `error`: A message indicating the credentials are invalid.
        - `success`: Always false.
        - `status_code`: Error 401 (Unauthorized)

    ### Request Example
    ```http
    POST /login HTTP/1.1
    Host: example.com
    Content-Type: application/x-www-form-urlencoded

    username=user@example.com&password=yourpassword
    ```

    ### Response Example

    #### 200 OK
    ```json
    {
      "message": "Logged in successfully",
      "status_code": 200,
      "success": true,
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires": 2025-02-16T00:14:35.125080Z
      }
    }
    ```

    #### 401 Unauthorized
    ```json
    {
      "detail": {
        "error": "Invalid email or password",
        "success": false,
        "status_code": 401
      }
    }
    ```

    ### Security
    - No authentication required to access this endpoint.
    - Provides a JWT token upon successful login which can be used for authenticated requests.
    """
    user = security.authenticate_user(
        db=db, email=credentials.username, password=credentials.password
    )

    if user is None:
        raise UnauthorizedError()

    access_token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return Token(
        message="Logged in successfully",
        status_code=status.HTTP_200_OK,
        data=TokenBase(
            access_token=access_token,
            token_type="bearer",
            expires=settings.access_token_duration,
        ),
    )
