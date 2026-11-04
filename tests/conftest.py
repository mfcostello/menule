"""Fixtures compartidas: una base de datos SQLite en memoria por test.

Los servicios solo usan SQLAlchemy genérico, así que se pueden probar sin
MySQL. (SQLite ignora ``SELECT ... FOR UPDATE``; la lógica de negocio que se
prueba aquí no depende del bloqueo.)
"""
from datetime import date, timedelta
from decimal import Decimal

import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Estudiante,
    Ingrediente,
    Menu,
    Plato,
    Profesor,
    Usuario,
)

PASSWORD = "secreta123"
PLATOS_OK = ["Sopa", "Pollo", "Flan"]

# Hash calculado una vez y con coste bajo: bcrypt a coste 12 en cada test
# multiplica por 10 la duración de la suite.
PASSWORD_HASH = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _usuario(id_usuario, tipo, password_hash, email=None):
    return Usuario(
        id_usuario=id_usuario,
        nombre="Test",
        apellido=str(id_usuario),
        email=email or f"user{id_usuario}@test.es",
        contrasena_hash=password_hash,
        tipo=tipo,
    )


@pytest.fixture
def datos(db):
    """Usuarios con monedero, platos y un menú de hoy con 2 plazas.

    - #0 visitante genérico, #1 estudiante (20 €), #2 estudiante (3 €),
      #3 profesor (20 €), #4 administrador.
    - Menú #1: hoy, max 2 reservas, platos Sopa/Pollo/Flan.
    - Menú #2: ayer. Plato "Caviar" existe pero no está en ningún menú.
    """
    pw_hash = PASSWORD_HASH
    db.add_all([
        _usuario(0, "visitante", pw_hash, "visitante@menule.com"),
        _usuario(1, "estudiante", pw_hash),
        _usuario(2, "estudiante", pw_hash),
        _usuario(3, "profesor", pw_hash),
        _usuario(4, "administrador", pw_hash),
        Estudiante(id_usuario=1, saldo=Decimal("20.00")),
        Estudiante(id_usuario=2, saldo=Decimal("3.00")),
        Profesor(id_usuario=3, saldo=Decimal("20.00")),
    ])
    sopa = Plato(nombre="Sopa", tipo="primero")
    pollo = Plato(nombre="Pollo", tipo="segundo")
    flan = Plato(nombre="Flan", tipo="postre")
    db.add_all([
        sopa, pollo, flan,
        Plato(nombre="Caviar", tipo="segundo"),
        Ingrediente(nombre="Pollo", stock_actual=Decimal("10")),
        Menu(id_menu=1, fecha=date.today(), tipo="almuerzo", max_reservas=2,
             disponible=True, platos=[sopa, pollo, flan]),
        Menu(id_menu=2, fecha=date.today() - timedelta(days=1), tipo="almuerzo",
             max_reservas=10, disponible=True, platos=[sopa, pollo, flan]),
    ])
    db.commit()
    return db
