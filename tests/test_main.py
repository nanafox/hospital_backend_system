#!/usr/bin/env python3

"""This module contains tests for the root and status endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient, Response


@pytest.mark.anyio
async def test_root_endpoint(api_client: AsyncClient):
    """Test that the root endpoint is working and returns the right message."""
    response: Response = await api_client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "Hello, welcome to the Hospital Backend System"
    }


@pytest.mark.anyio
async def test_status_endpoint(api_client: AsyncClient):
    """Test that the status endpoint is up and running."""
    response = await api_client.get("/status")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "OK"}
