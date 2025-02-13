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

    def __init__(self, *, model_name):
        self.status_code = status.HTTP_403_FORBIDDEN
        self.detail = {
            "error": f"You are not authorized to delete this {self.model_name}",
            "success": False,
            "status_code": self.status_code,
        }
