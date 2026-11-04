import bcrypt
from sqlalchemy.orm import Session
from app.models import Usuario


class AuthService:

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return (
            db.query(Usuario)
            .filter(Usuario.email == email.strip().lower())
            .first()
        )

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        if not password_hash:
            return False
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except ValueError:
            # Hash con formato inválido (p. ej. contraseña guardada en texto plano):
            # nunca se acepta. Usa scripts/hash_plaintext_passwords.py para migrarlas.
            return False

    @staticmethod
    def login(db: Session, email: str, password: str):
        user = AuthService.get_user_by_email(db, email)

        # La cuenta genérica de visitantes (id 0) no admite inicio de sesión
        if user is None or user.credencial_activa is False or user.tipo == "visitante":
            return None

        if not AuthService.verify_password(
            password,
            user.contrasena_hash,
        ):
            return None

        return user