#!/usr/bin/env python3

"""This module is the entry for the Hospital backend API."""

from typing import Dict

from fastapi import FastAPI

from app.docs import docs
from app.routers.auth import router as auth_router
from app.routers.notes import router as notes_router
from app.routers.patient_doctor import router as patient_doctor_router

app = FastAPI(
    version="v1",
    description=docs,
    title="Hospital Backend System",
    docs_url="/api/swagger-docs",
    redoc_url="/api/docs",
    contact={
        "name": "Maxwell Nana Forson",
        "website": "https://mnforson.live",
        "email": "nanaforsonjnr@gmail.com",
    },
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(patient_doctor_router)
app.include_router(notes_router)


@app.get("/", tags=["API Info & Status"], summary="Shows a welcome message")
async def root():
    """This endpoint returns a welcome message when hit."""
    return {"message": "Hello, welcome to the Hospital Backend System"}


@app.get(
    "/status",
    tags=["API Info & Status"],
    summary="Returns the status of API",
    responses={
        200: {
            "description": "API is up!",
            "model": Dict,
        }
    },
)
async def status():
    """This endpoint returns the current status of the API."""
    return {"status": "OK"}
