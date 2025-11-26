from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService


class UserService(BaseService):
    """
    Servicio de usuarios que delega el acceso a datos al repositorio de usuarios.
    Mantiene la interfaz de alto nivel y reglas de negocio específicas.
    """

    def __init__(self, repo: UserRepository | None = None) -> None:
        self._repo = repo if repo is not None else UserRepository()

    def create(self, username: str, password: str, role_name: str) -> User:
        """Crear un nuevo usuario"""
        return self._repo.create(
            username=username, password=password, role_name=role_name
        )

    def get(self, user_id: int) -> User | None:
        """Obtener un usuario por ID"""
        return self._repo.find_by_id(user_id)

    def get_all(self) -> list[User]:
        """Obtener todos los usuarios"""
        return list(self._repo.find_all())

    def update(self, user_id: int, **kwargs) -> User:
        """Actualizar un usuario existente"""
        return self._repo.update(user_id, **kwargs)

    def delete(self, user_id: int) -> None:
        """Eliminar un usuario"""
        self._repo.delete(user_id)

    def find_by_username(self, username: str) -> User | None:
        """Buscar usuario por nombre de usuario"""
        return self._repo.find_by_username(username)

    def is_last_admin(self, user_id: int) -> bool:
        """Verificar si el usuario es el único administrador"""
        return self._repo.is_last_admin(user_id)
