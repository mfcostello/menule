"""Operaciones sobre el saldo del monedero TUI (Estudiantes y Profesores).

Las modificaciones de saldo se hacen con un único ``UPDATE`` atómico en la base
de datos (``saldo = saldo - x WHERE saldo >= x``), de modo que dos peticiones
simultáneas no pueden gastar el mismo dinero dos veces.

Estas funciones NO hacen commit: el llamante es responsable de la transacción,
para poder agrupar el cobro con la creación de la reserva/pago.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import Estudiante, Profesor

_MODELO_POR_ROL = {
    "estudiante": Estudiante,
    "profesor": Profesor,
}

CENTIMO = Decimal("0.01")


def parse_importe(valor) -> Optional[Decimal]:
    """Convierte la entrada del usuario en un importe válido con 2 decimales.

    Devuelve ``None`` si no es un número finito (rechaza 'nan', 'inf', texto...).
    Acepta coma o punto como separador decimal.
    """
    try:
        importe = Decimal(str(valor).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    if not importe.is_finite():
        return None
    return importe.quantize(CENTIMO, rounding=ROUND_HALF_UP)


def _modelo(rol: str):
    return _MODELO_POR_ROL.get((rol or "").lower())


def tiene_monedero(rol: str) -> bool:
    return _modelo(rol) is not None


def obtener_saldo(db: Session, id_usuario: int, rol: str) -> Optional[Decimal]:
    modelo = _modelo(rol)
    if modelo is None:
        return None
    saldo = db.execute(
        select(modelo.saldo).where(modelo.id_usuario == id_usuario)
    ).scalar_one_or_none()
    return None if saldo is None else Decimal(saldo)


def descontar(db: Session, id_usuario: int, rol: str, importe: Decimal) -> bool:
    """Resta ``importe`` del saldo solo si hay fondos suficientes.

    Devuelve True si se ha cobrado; False si no hay saldo o no existe monedero.
    """
    modelo = _modelo(rol)
    if modelo is None or importe <= 0:
        return False
    resultado = db.execute(
        update(modelo)
        .where(modelo.id_usuario == id_usuario, modelo.saldo >= importe)
        .values(saldo=modelo.saldo - importe)
    )
    return resultado.rowcount == 1


def abonar(db: Session, id_usuario: int, rol: str, importe: Decimal) -> bool:
    """Suma ``importe`` al saldo. Devuelve False si el usuario no tiene monedero."""
    modelo = _modelo(rol)
    if modelo is None or importe <= 0:
        return False
    resultado = db.execute(
        update(modelo)
        .where(modelo.id_usuario == id_usuario)
        .values(saldo=func.coalesce(modelo.saldo, 0) + importe)
    )
    return resultado.rowcount == 1
