#!/usr/bin/env python3

"""This module defines the encryption and decryption functions for the doctors
notes."""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

fernet = Fernet(settings.encryption_key)


def decrypt(content: str) -> str:
    """Return the decrypted version of the `content` received.

    Args:
        content (str): The content to decrypt

    Returns:
        str: The decrypted content.
    """
    return fernet.decrypt(content.encode()).decode()


def encrypt(content: str) -> str:
    """Return the encrypted version of the `content` passed to it.

    Primarily, this is meant to encrypt the doctor's notes but it can also be
    used for other things that require encryption of its contents.

    Args:
        content (str): The content to encrypt

    Returns:
        str: The encrypted version of the content
    """
    return fernet.encrypt(content.encode()).decode()


def is_encrypted(content: str) -> bool:
    """Check if the content is already encrypted."""
    try:
        decrypt(content)
        return True
    except InvalidToken:
        return False
