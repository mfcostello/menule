from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import Usuario, Estudiante, Profesor, PersonalComedor


class UserService:

    # =====================================================
    # READ
    # =====================================================

    @staticmethod
    def get_all_users(db: Session):
        """Obtener todos los usuarios."""
        return (
            db.query(Usuario)
            .order_by(Usuario.id_usuario.asc())
            .all()
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        """Buscar un usuario por ID."""
        return (
            db.query(Usuario)
            .filter(Usuario.id_usuario == user_id)
            .first()
        )

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Buscar un usuario por email."""
        return (
            db.query(Usuario)
            .filter(Usuario.email == email.strip().lower())
            .first()
        )

    @staticmethod
    def search_users(db: Session, search: str):
        """Buscar usuarios por nombre, apellido, email o DNI."""
        patron = f"%{search.strip()}%"
        return (
            db.query(Usuario)
            .filter(
                or_(
                    Usuario.nombre.ilike(patron),
                    Usuario.apellido.ilike(patron),
                    Usuario.email.ilike(patron),
                    Usuario.dni.ilike(patron),
                )
            )
            .order_by(Usuario.id_usuario.asc())
            .all()
        )

    @staticmethod
    def count_users(db: Session):
        """Número total de usuarios."""
        return db.query(Usuario).count()

    # =====================================================
    # CREATE
    # =====================================================

    @staticmethod
    def create_user(
        db: Session,
        nombre: str,
        apellido: str,
        email: str,
        contrasena_hash: str,
        tipo: str,
        dni: Optional[str] = None,
        telefono: Optional[str] = None,
        grado: Optional[str] = None,
        especialidad: Optional[str] = None,
    ) -> Usuario:
        """Crea un usuario y su perfil asociado (Estudiante, Profesor, PersonalComedor)."""
        clean_dni = dni.strip().upper() if dni and dni.strip() else None
        clean_telefono = telefono.strip() if telefono and telefono.strip() else None

        user = Usuario(
            dni=clean_dni,
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            email=email.strip().lower(),
            contrasena_hash=contrasena_hash,
            tipo=tipo,
            telefono=clean_telefono,
            fecha_alta=date.today(),
            credencial_activa=True,
        )

        db.add(user)
        db.flush()  # Obtiene el id_usuario asignado

        tui_num = f"TUI-{clean_dni}" if clean_dni else f"TUI-{user.id_usuario:06d}"

        if tipo == "estudiante":
            est = Estudiante(
                id_usuario=user.id_usuario,
                grado_academico=grado.strip() if grado else "Grado Universitario",
                tui_numero=tui_num,
                saldo=0.00,
            )
            db.add(est)
        elif tipo == "profesor":
            prof = Profesor(
                id_usuario=user.id_usuario,
                grado_academico=grado.strip() if grado else "Docente Universitario",
                tui_numero=tui_num,
                saldo=0.00,
            )
            db.add(prof)
        elif tipo == "personal_comedor":
            comedor = PersonalComedor(
                id_usuario=user.id_usuario,
                fecha_contratacion=date.today(),
                especialidad=especialidad.strip() if especialidad else "Personal de Cocina",
            )
            db.add(comedor)

        db.commit()
        db.refresh(user)

        return user

    # =====================================================
    # UPDATE
    # =====================================================

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        **kwargs,
    ):
        """Actualizar campos de un usuario."""
        user = UserService.get_user_by_id(db, user_id)

        if user is None:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        db.commit()
        db.refresh(user)

        return user

    # =====================================================
    # DELETE
    # =====================================================

    @staticmethod
    def delete_user(
        db: Session,
        user_id: int,
    ) -> bool:
        """Eliminar un usuario."""
        user = UserService.get_user_by_id(db, user_id)

        if user is None:
            return False

        db.delete(user)
        db.commit()

        return True

    # =====================================================
    # VALIDATIONS
    # =====================================================

    @staticmethod
    def email_exists(
        db: Session,
        email: str,
    ) -> bool:
        """Comprobar si un email ya existe."""
        return (
            db.query(Usuario)
            .filter(Usuario.email == email.strip().lower())
            .first()
            is not None
        )

    @staticmethod
    def dni_exists(
        db: Session,
        dni: str,
    ) -> bool:
        """Comprobar si un DNI ya existe."""
        if not dni or not dni.strip():
            return False
        return (
            db.query(Usuario)
            .filter(Usuario.dni == dni.strip().upper())
            .first()
            is not None
        )