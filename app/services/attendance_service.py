from datetime import date

from app.models.attendance import Attendance
from app.repositories.attendance_repository import AttendanceRepository
from app.services.base_service import BaseService


class AttendanceService(BaseService):
    """
    Servicio de asistencia que delega el acceso a datos al repositorio de asistencias.
    Mantiene la interfaz de alto nivel y reglas de negocio específicas.
    """

    def __init__(self, repo: AttendanceRepository | None = None) -> None:
        self._repo = repo if repo is not None else AttendanceRepository()

    def create(self, user_id: int) -> Attendance:
        """Crear un nuevo registro de asistencia"""
        return self._repo.create(user_id=user_id)

    def get(self, attendance_id: int) -> Attendance | None:
        """Obtener un registro de asistencia por ID"""
        return self._repo.find_by_id(attendance_id)

    def get_all(self) -> list[Attendance]:
        """Obtener todos los registros de asistencia"""
        return list(self._repo.find_all())

    def update(self, attendance_id: int, **kwargs) -> None:
        """Actualizar un registro de asistencia existente"""
        # No se permite actualizar un registro de asistencia
        raise NotImplementedError(
            "Los registros de asistencia no pueden ser actualizados"
        )

    def delete(self, attendance_id: int) -> None:
        """Eliminar un registro de asistencia"""
        self._repo.delete(attendance_id)

    def get_for_user_on_date(self, user_id: int, date_obj: date) -> Attendance | None:
        """Obtener asistencia de un usuario en una fecha específica"""
        return self._repo.get_for_user_on_date(user_id, date_obj)

    def get_user_attendance(self, user_id: int) -> list[Attendance]:
        """Obtener historial de asistencias de un usuario"""
        return list(self._repo.get_user_attendance(user_id))
