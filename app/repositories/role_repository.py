from typing import Iterable, Optional

from app import db
from app.models.role import Role


class RoleRepository:
    """
    Implementación de repositorio para `Role` usando SQLAlchemy.

    Responsable de:
    - Crear, persistir, leer, actualizar y eliminar roles.
    - Consultas específicas como buscar por nombre.
    """

    def create(self, **data) -> Role:
        """
        Crea y persiste un nuevo rol.
        Data esperada:
            - name: str (obligatorio, único)
        """
        name: Optional[str] = data.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("name es obligatorio y debe ser un string no vacío")

        name = name.strip()

        # Validar unicidad
        if Role.query.filter_by(name=name).first():
            raise ValueError(f"El rol '{name}' ya existe")

        role = Role(name=name)
        db.session.add(role)
        db.session.commit()
        return role

    def save(self, entity: Role) -> Role:
        """
        Persiste la entidad (insert/update según corresponda) y retorna la entidad.
        """
        if not isinstance(entity, Role):
            raise ValueError("entity debe ser instancia de Role")
        db.session.add(entity)
        db.session.commit()
        return entity

    def find_by_id(self, entity_id: int) -> Optional[Role]:
        """
        Retorna el rol por ID o None si no existe.
        """
        if not isinstance(entity_id, int) or entity_id <= 0:
            raise ValueError("entity_id debe ser un entero positivo")
        return Role.query.get(entity_id)

    def find_all(
        self, *, offset: int = 0, limit: Optional[int] = None
    ) -> Iterable[Role]:
        """
        Retorna todos los roles, con soporte de paginación.
        """
        query = Role.query.order_by(Role.id.asc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def update(self, entity_id: int, **data) -> Role:
        """
        Actualiza un rol existente con los datos proporcionados.
        Data soportada:
            - name: str (único)
        """
        role = self.find_by_id(entity_id)
        if not role:
            raise ValueError("Rol no encontrado")

        if "name" in data and data["name"]:
            name = data["name"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError("name debe ser un string no vacío")
            name = name.strip()

            # Validar unicidad (excluyendo el propio rol)
            existing = Role.query.filter(
                Role.name == name, Role.id != entity_id
            ).first()
            if existing:
                raise ValueError(f"El nombre de rol '{name}' ya está en uso")

            role.name = name

        db.session.commit()
        return role

    def delete(self, entity_id: int) -> None:
        """
        Elimina el rol por ID. Lanza error si no existe.
        """
        role = self.find_by_id(entity_id)
        if not role:
            raise ValueError("Rol no encontrado")

        db.session.delete(role)
        db.session.commit()

    # ---- Métodos específicos del dominio ----

    def find_by_name(self, name: str) -> Optional[Role]:
        """
        Retorna el rol por su nombre, o None si no existe.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name debe ser un string no vacío")
        return Role.query.filter_by(name=name.strip()).first()
