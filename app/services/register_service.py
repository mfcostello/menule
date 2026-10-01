import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Usuario
from app.services.user_service import UserService


class RegisterService:

    @staticmethod
    def hash_password(password_raw: str) -> str:
        """Genera el hash de la contraseña usando bcrypt."""
        pwd_bytes = password_raw.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def email_exists(db: Session, email: str) -> bool:
        """Comprueba si un correo ya existe en la BD."""
        return UserService.email_exists(db, email)

    @staticmethod
    def dni_exists(db: Session, dni: str) -> bool:
        """Comprueba si un DNI ya existe en la BD."""
        return UserService.dni_exists(db, dni)

    @staticmethod
    def register_user(
        db: Session,
        nombre: str,
        apellido: str,
        email: str,
        password: str,
        dni: str,
        telefono: str,
        tipo: str,
        grado: Optional[str] = None,
        especialidad: Optional[str] = None,
    ) -> Usuario:
        """Crea el usuario y su perfil institucional (Estudiante, Profesor, Personal de Comedor)."""
        password_hashed = RegisterService.hash_password(password)

        return UserService.create_user(
            db=db,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contrasena_hash=password_hashed,
            tipo=tipo,
            dni=dni,
            telefono=telefono,
            grado=grado,
            especialidad=especialidad,
        )