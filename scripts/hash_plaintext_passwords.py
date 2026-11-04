"""Migra a bcrypt las contraseñas guardadas en texto plano.

El login ya no acepta contraseñas sin hashear. Si en tu base de datos hay
usuarios insertados a mano con la contraseña en claro, ejecuta una vez:

    python scripts/hash_plaintext_passwords.py          # muestra qué cambiaría
    python scripts/hash_plaintext_passwords.py --apply  # aplica los cambios
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models import Usuario  # noqa: E402
from app.services.register_service import RegisterService  # noqa: E402

BCRYPT_PREFIJOS = ("$2a$", "$2b$", "$2y$")


def main(aplicar: bool) -> None:
    with SessionLocal() as db:
        usuarios = db.query(Usuario).all()
        pendientes = [
            u for u in usuarios
            if u.contrasena_hash and not u.contrasena_hash.startswith(BCRYPT_PREFIJOS)
        ]

        for u in pendientes:
            print(f"{'Hasheando' if aplicar else 'Pendiente'}: #{u.id_usuario} {u.email}")
            if aplicar:
                u.contrasena_hash = RegisterService.hash_password(u.contrasena_hash)

        if aplicar:
            db.commit()
        print(f"{len(pendientes)} contraseña(s) en texto plano encontradas.")
        if pendientes and not aplicar:
            print("Vuelve a ejecutar con --apply para hashearlas.")


if __name__ == "__main__":
    main(aplicar="--apply" in sys.argv)
