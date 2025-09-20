from typing import List, Set
from uuid import UUID

from sqlmodel import Session, select

from app.crud.base import APICrudBase
from app.exceptions import BadRequestError, NotFoundError
from app.models.patient_doctor import PatientDoctor
from app.models.user import User
from app.schemas import patient_doctor as schemas
from app.schemas.user import UserRoleEnum


class PatientDoctorCrud(APICrudBase[PatientDoctor, schemas.PatientDoctorBase]):
    """CRUD operations for the PatientDoctor model.

    This class provides methods to create, retrieve, and delete patient-
    doctor relationships. It inherits from APICrudBase.
    """

    def __init__(self, model: PatientDoctor = PatientDoctor):
        """Initialize the PatientDoctorCrud class."""
        super().__init__(model)

    @staticmethod
    def get_by_patient_and_doctor(
        *, patient_id: UUID, doctor_id: UUID, db: Session
    ) -> PatientDoctor:
        """Retrieve a specific patient-doctor relationship."""
        if record := db.exec(
            select(PatientDoctor)
            .where(PatientDoctor.patient_id == patient_id)
            .where(PatientDoctor.doctor_id == doctor_id)
        ).first():
            return record

        raise NotFoundError(
            error=f"The doctor with ID {str(doctor_id)} is not assigned to you"
        )

    def create(
        self, *, db: Session, patient_id: UUID, doctor_ids: List[UUID]
    ) -> List[PatientDoctor]:
        """Assign multiple doctors to a patient efficiently."""
        if not doctor_ids:
            raise BadRequestError(error="Doctor IDs list cannot be empty.")

        existing_doctor_ids = self._get_existing_assignments(db, patient_id)
        new_doctor_ids = set(doctor_ids) - existing_doctor_ids

        if not new_doctor_ids:
            raise BadRequestError(
                error="All selected doctors are already assigned to this patient."
            )

        valid_doctor_ids = self._validate_doctors(db, new_doctor_ids)
        return self._insert_assignments(db, patient_id, valid_doctor_ids)

    def delete(self, *, patient_id: UUID, doctor_ids: List[UUID], db: Session) -> None:
        """Delete multiple patient-doctor relationships.

        Args:
            patient_id (UUID): The patient's ID.
            doctor_ids (List[UUID]): List of doctor IDs to remove.
            db (Session): The database session.

        Raises:
            BadRequestError: If some doctor IDs are not assigned, an error is raised.
        """
        if not doctor_ids:
            raise BadRequestError(error="Doctor IDs list cannot be empty.")

        existing_records = [
            self.get_by_patient_and_doctor(
                patient_id=patient_id, doctor_id=doctor_id, db=db
            )
            for doctor_id in doctor_ids
        ]

        # Filter out None values (invalid relationships)
        valid_records = [record for record in existing_records if record]

        if valid_records:
            for record in valid_records:
                db.delete(record)
            db.commit()

    def _get_existing_assignments(self, db: Session, patient_id: UUID) -> Set[UUID]:
        """Fetch doctors already assigned to a patient."""
        return set(
            db.scalars(
                select(PatientDoctor.doctor_id).where(
                    PatientDoctor.patient_id == patient_id
                )
            ).all()
        )

    def _validate_doctors(self, db: Session, doctor_ids: Set[UUID]) -> Set[UUID]:
        """Ensure doctor IDs exist and belong to users with the role
        'doctor'."""
        valid_doctor_ids = set(
            db.scalars(
                select(User.id).where(
                    User.id.in_(doctor_ids),
                    User.role == UserRoleEnum.doctor,
                )
            ).all()
        )

        invalid_doctor_ids = doctor_ids - valid_doctor_ids
        if invalid_doctor_ids:
            raise BadRequestError(
                error=f"The following Doctor IDs do not exist or are not doctors: "
                f"[{', '.join(map(str, invalid_doctor_ids))}]"
            )

        return valid_doctor_ids

    def _insert_assignments(
        self, db: Session, patient_id: UUID, doctor_ids: Set[UUID]
    ) -> List[PatientDoctor]:
        """Bulk insert new patient-doctor assignments."""
        new_assignments = [
            PatientDoctor(patient_id=patient_id, doctor_id=doc_id)
            for doc_id in doctor_ids
        ]

        db.bulk_save_objects(new_assignments)
        db.commit()

        return new_assignments


crud_patient_doctor = PatientDoctorCrud()
