import subprocess

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.core.config import settings
from app.core.database import get_session
from app.crud.user import crud_user
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate, UserRoleEnum


@pytest.fixture(scope="package", autouse=True)
def setup_teardown_test_db():
    """Performs setup and tear-down for the test database."""
    print("Setting up test database")
    subprocess.run(["./setup_test_db.sh"])

    yield

    print("Tearing down test database")
    subprocess.run(["./teardown_test_db.sh"])


@pytest.fixture
def session():
    """Sets up the session for the test database connection."""
    engine = create_engine(settings.db_test_url)

    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
async def api_client(session: Session):
    """Yields a client object to be used for API testing."""

    def override_get_session():
        """A fixture to override the default database session used in tests.

        Explanation:
        This fixture yields the provided session for testing purposes and
        ensures that the session is properly closed after the test.

        Returns:
            The database session for testing.
        """
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    yield AsyncClient(
        base_url="http://api.test.com", transport=ASGITransport(app=app)
    )


@pytest.fixture
def doc_jdoe(session: Session) -> User:
    """Fixture to create a doctor user.

    User Details:
        email: jdoe@email.com
        password: password1234

    Args:
        session (Session): The database session to use for creating the user.

    Returns:
        models.User: The created user object in the database.
    """
    user = UserCreate(
        email="jdoe@email.com",
        password="password1234",
        role=UserRoleEnum.doctor,
        name="John Doe",
    )
    return crud_user.create(db=session, user=user)


@pytest.fixture
def patient_sally(session: Session) -> User:
    """Fixture to create a patient user.

    User Details:
        email: sally@email.com
        password: password1234

    Args:
        session (Session): The database session to use for creating the user.

    Returns:
        models.User: The created user object in the database.
    """
    user = UserCreate(
        email="sally@email.com",
        password="password1234",
        role=UserRoleEnum.patient,
        name="Sally Banks",
    )
    return crud_user.create(db=session, user=user)


@pytest.fixture
def patient_bob(session: Session) -> User:
    user = UserCreate(
        email="bob@email.com",
        password="password1234",
        role=UserRoleEnum.patient,
        name="Bob Manny",
    )

    return crud_user.create(db=session, user=user)
