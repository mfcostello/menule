from datetime import date, datetime, time
from typing import Optional
from sqlalchemy import String, func
from sqlalchemy.orm import Session, joinedload
from app.models import Menu, Reserva

# Turnos de comida en orden y hora a la que termina cada uno
ORDEN_TURNOS = ["desayuno", "almuerzo", "cena"]
FIN_TURNO = {"desayuno": time(11, 0), "almuerzo": time(16, 30)}


def turno_para_hora(hora: time) -> str:
    """'desayuno' hasta las 11:00, 'almuerzo' hasta las 16:30 y luego 'cena'."""
    for turno in ("desayuno", "almuerzo"):
        if hora < FIN_TURNO[turno]:
            return turno
    return "cena"


class MenuService:

    @staticmethod
    def get_all(db: Session):
        return (
            db.query(Menu)
            .options(joinedload(Menu.platos))
            .order_by(Menu.fecha.desc())
            .all()
        )

    @staticmethod
    def search(db: Session, text: str):
        query = (
            db.query(Menu)
            .options(joinedload(Menu.platos))
        )

        if text.strip():
            pattern = f"%{text.strip()}%"
            query = query.filter(
                (Menu.tipo.ilike(pattern))
                | (Menu.fecha.cast(String).ilike(pattern))
            )

        return (
            query.order_by(Menu.fecha.desc())
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        id_menu: int,
    ):
        return (
            db.query(Menu)
            .options(joinedload(Menu.platos))
            .filter(Menu.id_menu == id_menu)
            .first()
        )

    @staticmethod
    def get_menu_del_dia(
        db: Session,
        fecha_consulta: Optional[date] = None,
        hora: Optional[time] = None,
    ) -> Optional[Menu]:
        """Menú disponible de hoy que corresponde al momento del día.

        Si hay varios menús ese día (desayuno, almuerzo, cena), se elige el del
        turno actual; si no existe, el siguiente turno del día y, si ya han
        pasado todos, el último.
        """
        target_date = fecha_consulta or date.today()
        menus = (
            db.query(Menu)
            .options(joinedload(Menu.platos))
            .filter(Menu.fecha == target_date, Menu.disponible == True)  # noqa: E712
            .all()
        )
        if not menus:
            return None

        menus.sort(key=lambda m: ORDEN_TURNOS.index(m.tipo) if m.tipo in ORDEN_TURNOS else 99)
        turno_actual = turno_para_hora(hora or datetime.now().time())
        indice_actual = ORDEN_TURNOS.index(turno_actual)
        for menu in menus:
            if menu.tipo in ORDEN_TURNOS and ORDEN_TURNOS.index(menu.tipo) >= indice_actual:
                return menu
        return menus[-1]

    @staticmethod
    def count_reservas_dia(db: Session, target_date: Optional[date] = None) -> int:
        """Cuenta las reservas confirmadas asociadas a menús de una fecha."""
        fecha_val = target_date or date.today()
        return (
            db.query(func.count(Reserva.id_reserva))
            .join(Menu, Reserva.id_menu == Menu.id_menu)
            .filter(Menu.fecha == fecha_val, Reserva.estado == "confirmada")
            .scalar() or 0
        )

    @staticmethod
    def create(
        db: Session,
        fecha: date,
        tipo: str,
        max_reservas: int,
        disponible: bool,
    ):
        menu = Menu(
            fecha=fecha,
            tipo=tipo,
            max_reservas=max_reservas,
            disponible=disponible,
        )

        db.add(menu)
        db.commit()
        db.refresh(menu)

        return menu

    @staticmethod
    def update(
        db: Session,
        id_menu: int,
        fecha: date,
        tipo: str,
        max_reservas: int,
        disponible: bool,
    ):
        menu = (
            db.query(Menu)
            .filter(Menu.id_menu == id_menu)
            .first()
        )

        if not menu:
            return None

        menu.fecha = fecha
        menu.tipo = tipo
        menu.max_reservas = max_reservas
        menu.disponible = disponible

        db.commit()

        return menu

    @staticmethod
    def delete(
        db: Session,
        id_menu: int,
    ):
        menu = (
            db.query(Menu)
            .filter(Menu.id_menu == id_menu)
            .first()
        )

        if not menu:
            return False

        db.delete(menu)
        db.commit()

        return True