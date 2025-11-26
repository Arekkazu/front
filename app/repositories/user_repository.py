from typing import Iterable, Optional

from app import db
from app.models.role import Role
from app.models.user import User


class UserRepository:
    """
    Implementación de repositorio para `User` usando SQLAlchemy.

    Responsable de:
    - Crear, persistir, leer, actualizar y eliminar usuarios.
    - Consultas específicas como buscar por username y contar admins.
    """

    def create(self, **data) -> User:
        """
        Crea un nuevo usuario en memoria (sin commit) y lo persiste.
        Data esperada:
            - username: str (obligatorio, único)
            - password: str (obligatorio)
            - role_name: str (obligatorio, debe existir en tabla roles)
        """
        username: Optional[str] = data.get("username")
        password: Optional[str] = data.get("password")
        role_name: Optional[str] = data.get("role_name")

        if not username or not isinstance(username, str):
            raise ValueError("username es obligatorio y debe ser string")
        if not password or not isinstance(password, str):
            raise ValueError("password es obligatorio y debe ser string")
        if not role_name or not isinstance(role_name, str):
            raise ValueError("role_name es obligatorio y debe ser string")

        # Validar unicidad de username
        if User.query.filter_by(username=username).first():
            raise ValueError(f"El usuario '{username}' ya existe")

        # Obtener rol
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"El rol '{role_name}' no existe")

        # Crear entidad
        user = User(username=username, role_id=role.id)
        user.set_password(password)

        # Persistir
        db.session.add(user)
        db.session.commit()
        return user

    def save(self, entity: User) -> User:
        """
        Persiste la entidad (insert/update según corresponda) y retorna la entidad.
        """
        db.session.add(entity)
        db.session.commit()
        return entity

    def find_by_id(self, entity_id: int) -> Optional[User]:
        """
        Retorna el usuario por ID o None si no existe.
        """
        return User.query.get(entity_id)

    def find_all(
        self, *, offset: int = 0, limit: Optional[int] = None
    ) -> Iterable[User]:
        """
        Retorna todos los usuarios, con soporte de paginación.
        """
        query = User.query.order_by(User.id.asc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def update(self, entity_id: int, **data) -> User:
        """
        Actualiza un usuario existente con los datos proporcionados.
        Data soportada:
            - username: str (único)
            - password: str
            - role_name: str (debe existir)
        """
        user = self.find_by_id(entity_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        if "username" in data and data["username"]:
            username = data["username"]
            # Validar unicidad (excluyendo el propio usuario)
            existing = User.query.filter(
                User.username == username, User.id != entity_id
            ).first()
            if existing:
                raise ValueError(f"El nombre de usuario '{username}' ya está en uso")
            user.username = username

        if "password" in data and data["password"]:
            user.set_password(data["password"])

        if "role_name" in data and data["role_name"]:
            role_name = data["role_name"]
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"El rol '{role_name}' no existe")
            user.role_id = role.id

        db.session.commit()
        return user

    def delete(self, entity_id: int) -> None:
        """
        Elimina el usuario por ID. Lanza error si no existe.
        """
        user = self.find_by_id(entity_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        db.session.delete(user)
        db.session.commit()

    # ---- Métodos específicos del dominio ----

    def find_by_username(self, username: str) -> Optional[User]:
        """
        Retorna el usuario por su nombre de usuario, o None si no existe.
        """
        if not username or not isinstance(username, str):
            raise ValueError("username debe ser un string no vacío")
        return User.query.filter_by(username=username).first()

    def count_admins(self) -> int:
        """
        Cuenta cuántos usuarios con rol 'Admin' existen.
        """
        return User.query.join(Role).filter(Role.name == "Admin").count()

    def is_last_admin(self, entity_id: int) -> bool:
        """
        Verifica si el usuario dado es el único administrador del sistema.
        """
        user = self.find_by_id(entity_id)
        if not user:
            return False
        # Asegurar que el usuario es admin
        if not user.role or user.role.name != "Admin":
            return False
        return self.count_admins() == 1
