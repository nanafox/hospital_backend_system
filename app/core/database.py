#!/usr/bin/env python3

"""This module defines the database connections."""

from sqlalchemy.sql import func
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import settings

if settings.db_type == "sqlite":
    engine = create_engine(
        settings.db_url, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.db_url)


def get_session():
    """Yields the database session."""
    SQLModel.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        yield session


def save(model_instance, *, db: Session):
    """Saves an instance of any object to the database."""
    db.add(model_instance)
    db.commit()
    db.refresh(model_instance)

    return model_instance


def delete(model_instance, *, db: Session):
    """Delete an instance of an object from the database."""
    db.delete(model_instance)
    db.commit()


def count(model, *, db: Session) -> int:
    """Returns the number of records for a specific model."""
    return db.exec(select(func.count()).select_from(model)).one()
