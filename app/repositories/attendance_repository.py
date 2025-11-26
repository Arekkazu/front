from datetime import date
from typing import Iterable, Optional

from app import db
from app.models.attendance import Attendance
from app.models.user import User


class AttendanceRepository:
    """
    Implementación de repositorio para `Attendance` usando SQLAlchemy.

    Responsable de:
    - Crear, persistir, leer y eliminar registros de asistencia.
    - Consultas específicas como historial del usuario y asistencia por fecha.

    Nota: la actualización de registros de asistencia no está permitida por reglas de negocio.
    """

    def create(self, **data) -> Attendance:
        """
        Crea y persiste un nuevo registro de asistencia.
        Data esperada:
            - user_id: int (obligatorio, debe existir)
        Opcional:
            - date: datetime.date (por defecto, la fecha del sistema)
            - timestamp: datetime (por defecto, se usa default del modelo)
        """
        user_id = data.get("user_id")
        attendance_date: Optional[date] = data.get("date")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id es obligatorio y debe ser un entero positivo")

        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuario no existe")

        # Si no se provee fecha, usar la lógica por defecto del modelo (date.today) al crear
        # Validar unicidad diaria (user_id, date)
        target_date = attendance_date or date.today()
        existing = Attendance.query.filter_by(user_id=user_id, date=target_date).first()
        if existing:
            raise ValueError(
                "Ya se registró asistencia para este usuario en la fecha indicada"
            )

        attendance = Attendance(user_id=user_id)
        # Si se pasa 'date', setear explícitamente
        if attendance_date:
            attendance.date = attendance_date

        db.session.add(attendance)
        db.session.commit()
        return attendance

    def save(self, entity: Attendance) -> Attendance:
        """
        Persiste la entidad (insert/update según corresponda) y retorna la entidad.
        """
        db.session.add(entity)
        db.session.commit()
        return entity

    def find_by_id(self, entity_id: int) -> Optional[Attendance]:
        """
        Retorna el registro de asistencia por ID o None si no existe.
        """
        return Attendance.query.get(entity_id)

    def find_all(
        self, *, offset: int = 0, limit: Optional[int] = None
    ) -> Iterable[Attendance]:
        """
        Retorna todos los registros de asistencia, con soporte de paginación.
        Ordena por fecha descendente y luego por ID.
        """
        query = Attendance.query.order_by(Attendance.date.desc(), Attendance.id.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def update(self, entity_id: int, **data) -> Attendance:
        """
        Actualización no permitida por reglas de negocio.
        """
        raise NotImplementedError(
            "Los registros de asistencia no pueden ser actualizados"
        )

    def delete(self, entity_id: int) -> None:
        """
        Elimina el registro de asistencia por ID. Lanza error si no existe.
        """
        attendance = self.find_by_id(entity_id)
        if not attendance:
            raise ValueError("Registro de asistencia no encontrado")
        db.session.delete(attendance)
        db.session.commit()

    # ---- Consultas específicas del dominio ----

    def get_for_user_on_date(
        self, user_id: int, date_obj: date
    ) -> Optional[Attendance]:
        """
        Retorna el registro de asistencia de un usuario en una fecha específica.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id debe ser un entero positivo")
        if not isinstance(date_obj, date):
            raise ValueError("date_obj debe ser una fecha válida (datetime.date)")
        return Attendance.query.filter_by(user_id=user_id, date=date_obj).first()

    def get_user_attendance(
        self, user_id: int, *, offset: int = 0, limit: Optional[int] = None
    ) -> Iterable[Attendance]:
        """
        Retorna el historial de asistencias de un usuario, ordenado por fecha descendente.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id debe ser un entero positivo")
        query = Attendance.query.filter_by(user_id=user_id).order_by(
            Attendance.date.desc(), Attendance.id.desc()
        )
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
