#!/usr/bin/env python3

"""This module defines the encryption and decryption functions for the doctors
notes."""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

fernet = Fernet(settings.encryption_key)


def decrypt(content: str) -> str:
    return fernet.decrypt(content.encode()).decode()


def encrypt(content: str) -> str:
    return fernet.encrypt(content.encode()).decode()


def is_encrypted(content: str) -> bool:
    """Check if the content is already encrypted."""
    try:
        decrypt(content)
        return True
    except InvalidToken:
        return False
