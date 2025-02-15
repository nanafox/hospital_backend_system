from sqlmodel import Session, select

from app.crud.base import APICrudBase
from app.exceptions import InternalServerError, NotFoundError
from app.models.user import User
from app.schemas import user as schemas


class UserCrud(APICrudBase[User, schemas.User]):
    """CRUD operations for the User model.

    This class provides methods to create, retrieve, update, and delete
    User objects. It inherits from the APICrudBase class and specifies
    the User model and UserBase schema as type parameters.
    """

    def __init__(self, model: User = User):
        """Initialize the UserCrud class.

        Args:
            model (User, optional): The User model. Defaults to
            User.
        """
        super().__init__(model)

    def get_by_email(self, *, email: str, db: Session) -> User:
        """Get a user by email.

        Args:
            email (str): The email of the user.
            db (Session): The database session.

        Returns:
            User: The user with the specified email.

        Raises:
            self.not_found_error: If the user is not found.
        """
        if user := db.exec(select(User).where(User.email == email)).first():
            return user

        raise NotFoundError(error="User not found")

    def create(
        self,
        *,
        db: Session,
        user: schemas.UserCreate,
    ) -> User:
        """Create a new user.

        Args:
            db (Session): The database session.
            user (schemas.UserCreate): The user data to create.

        Returns:
            User: The created user.

        Raises:
            HTTPException: If the user already exists.
        """
        return super().create(db=db, schema=user)

    def __get_user(self, *, by: str, identifier: str, db: Session) -> User:
        """Retrieves a user by their ID or username.

        Args:
            by (str): The type of data to use for the search.
            identifier (str): A unique value that identifiers a user.
            db (Session): The database session instance.

        Raises:
            HTTPException: Error 404 is raised if the user does not exist.
            Error 500 is raised if the search type is not recognized.

        Returns:
            User: The user with the requested ID or username.
        """
        match by:
            case "id":
                return self.get_by_id(obj_id=identifier, db=db)
            case "email":
                return self.get_by_email(email=identifier, db=db)
            case _:
                raise InternalServerError()

    get = __get_user


crud_user = UserCrud()
