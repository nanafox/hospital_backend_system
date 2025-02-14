#!/usr/bin/env python3

"""This module defines custom exceptions for the API."""


from fastapi import HTTPException, status


class UserExistsError(HTTPException):
    """Raises an HTTP Error 409 (conflict) when email unique violation
    occur."""

    def __init__(self):
        self.status_code = status.HTTP_409_CONFLICT
        self.detail = {
            "error": "Sorry, this email is already taken",
            "success": False,
            "status_code": self.status_code,
        }


class InternalServerError(HTTPException):
    """Raises an HTTP 500 (Internal Server Error)."""

    def __init__(self):
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.detail = {
            "error": "Sorry, the server failed to respond correctly",
            "next_steps": "Try again after some, if it "
            "persists please contact the system admin",
            "success": False,
            "status_code": self.status_code,
        }


class ForbiddenActionError(HTTPException):
    """Raises an HTTP 403 (forbidden) error."""

    def __init__(self, *, error: str = ""):
        if error == "":
            error = "You are not authorized to perform this action"

        self.status_code = status.HTTP_403_FORBIDDEN
        self.detail = {
            "error": error,
            "success": False,
            "status_code": self.status_code,
        }


class UnauthorizedError(HTTPException):
    """Raises an HTTP 401 (unauthorized) error."""

    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.headers = {"WWW-Authenticate": "Bearer"}
        self.detail = {
            "error": "Invalid email or password",
            "success": False,
            "status_code": self.status_code,
        }


class BadRequestError(HTTPException):
    """Raises HTTP 400 (Bad request) error."""

    def __init__(self, error: str = ""):
        if error == "":
            error = "Invalid request"

        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = {
            "error": error,
            "success": False,
            "status_code": self.status_code,
        }


class NotFoundError(HTTPException):
    """Raises HTTP 404 (Not Found) error."""

    def __init__(self, error: str = ""):
        if error == "":
            error = "Invalid request"

        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = {
            "error": error,
            "success": False,
            "status_code": self.status_code,
        }
