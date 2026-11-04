"""Ciclo de vida de las reservas: creación, recogida y cancelación.

Todas las operaciones que cambian el estado de una reserva pasan por aquí para
que las reglas de negocio se apliquen siempre igual:

- No se puede superar ``Menu.max_reservas`` ni reservar un menú no disponible.
- Un usuario registrado solo puede tener una reserva activa por menú.
- Solo se pueden elegir platos que pertenecen al menú.
- Cancelar una reserva devuelve el importe al monedero TUI (y marca el pago
  como ``reembolsado``); una reserva recogida o cancelada ya no cambia.

Cada función confirma (commit) su propia transacción o la deshace entera.
Los errores que debe ver el usuario se lanzan como ``ReservaError``.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List

from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session, joinedload

from app.config.precios import PRECIO_MENU_POR_ROL, PRECIO_MENU_VISITANTE
from app.models import Menu, Pago, Reserva, Usuario
from app.services import monedero_service
from app.services.stock_service import StockService

# Estados desde los que una reserva aún puede recogerse o cancelarse
ESTADOS_ACTIVOS = ("pendiente", "confirmada")

ID_USUARIO_VISITANTE = 0


class ReservaError(Exception):
    """Error de negocio con un mensaje apto para mostrar al usuario."""


def _bloquear_menu_reservable(db: Session, id_menu: int) -> Menu:
    """Bloquea la fila del menú (SELECT ... FOR UPDATE) y comprueba que admite reservas.

    El bloqueo serializa las reservas simultáneas del mismo menú, de forma que
    el recuento de plazas no puede quedarse desfasado entre dos peticiones.
    """
    menu = db.query(Menu).filter(Menu.id_menu == id_menu).with_for_update().first()
    if menu is None or not menu.disponible:
        raise ReservaError("Este menú ya no está disponible.")
    if menu.fecha != date.today():
        raise ReservaError("Solo se puede reservar el menú del día.")

    if menu.max_reservas is not None:
        ocupadas = (
            db.query(func.count(Reserva.id_reserva))
            .filter(Reserva.id_menu == id_menu, Reserva.estado != "cancelada")
            .scalar()
        )
        if ocupadas >= menu.max_reservas:
            raise ReservaError("Lo sentimos, este menú ya está completo.")
    return menu


def _platos_elegidos(menu: Menu, nombres_platos: List[str]):
    """Devuelve los platos del menú que corresponden a los nombres elegidos."""
    nombres = {n for n in nombres_platos if n}
    disponibles = {p.nombre: p for p in menu.platos if p.activo is not False}
    if not nombres or not nombres.issubset(disponibles):
        raise ReservaError("Los platos seleccionados no pertenecen al menú de hoy.")
    return [disponibles[n] for n in nombres]


class ReservaService:

    @staticmethod
    def get_all(db: Session, search_text: str = "") -> List[Reserva]:
        """Obtiene todas las reservas cargando sus usuarios, menú y platos específicos seleccionados."""
        query = db.query(Reserva).options(
            joinedload(Reserva.usuario),
            joinedload(Reserva.menu),
            joinedload(Reserva.platos),
        )

        if search_text.strip():
            patron = f"%{search_text.strip()}%"
            query = query.join(Usuario, isouter=True).filter(
                (cast(Reserva.id_reserva, String).ilike(patron)) |
                (Usuario.email.ilike(patron))
            )

        return query.order_by(Reserva.fecha_reserva.desc()).all()

    # ------------------------------------------------------------------
    # CREACIÓN
    # ------------------------------------------------------------------
    @staticmethod
    def crear_reserva_tui(
        db: Session,
        id_usuario: int,
        rol: str,
        id_menu: int,
        nombres_platos: List[str],
    ) -> Reserva:
        """Reserva pagada con el monedero TUI (estudiantes y profesores)."""
        precio = PRECIO_MENU_POR_ROL.get(rol)
        if precio is None:
            raise ReservaError("Solo estudiantes y profesores pueden reservar con el monedero TUI.")

        try:
            menu = _bloquear_menu_reservable(db, id_menu)

            ya_reservado = (
                db.query(Reserva.id_reserva)
                .filter(
                    Reserva.id_menu == id_menu,
                    Reserva.id_usuario == id_usuario,
                    Reserva.estado != "cancelada",
                )
                .first()
            )
            if ya_reservado:
                raise ReservaError("Ya tienes una reserva para este menú.")

            platos = _platos_elegidos(menu, nombres_platos)

            if not monedero_service.descontar(db, id_usuario, rol, precio):
                raise ReservaError("Saldo TUI insuficiente. Por favor, recarga tu monedero.")

            reserva = Reserva(
                id_usuario=id_usuario,
                id_menu=id_menu,
                fecha_reserva=datetime.now(),
                estado="confirmada",
                estado_bit=False,  # 0 = Pendiente de recogida en cocina
                platos=platos,
            )
            db.add(reserva)
            db.flush()

            db.add(Pago(
                id_usuario=id_usuario,
                id_reserva=reserva.id_reserva,
                monto=precio,
                metodo="tui",
                fecha_pago=datetime.now(),
                estado="completado",
            ))
            db.commit()
            return reserva
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def crear_reserva_visitante(
        db: Session,
        id_menu: int,
        nombres_platos: List[str],
        email_visitante: str,
    ) -> int:
        """Reserva anónima (id_usuario = 0) pagada con tarjeta."""
        try:
            menu = _bloquear_menu_reservable(db, id_menu)
            platos = _platos_elegidos(menu, nombres_platos)

            reserva = Reserva(
                id_usuario=ID_USUARIO_VISITANTE,
                id_menu=id_menu,
                fecha_reserva=datetime.now(),
                estado="confirmada",
                estado_bit=False,  # 0 = Pendiente de recogida en cocina
                platos=platos,
            )
            db.add(reserva)
            db.flush()

            db.add(Pago(
                id_reserva=reserva.id_reserva,
                id_usuario=ID_USUARIO_VISITANTE,
                monto=PRECIO_MENU_VISITANTE,
                metodo="tarjeta",
                estado="completado",
                correo=email_visitante,
                fecha_pago=datetime.now(),
            ))
            db.commit()
            return reserva.id_reserva
        except Exception:
            db.rollback()
            raise

    # ------------------------------------------------------------------
    # CAMBIOS DE ESTADO
    # ------------------------------------------------------------------
    @staticmethod
    def _bloquear_reserva_activa(db: Session, id_reserva: int) -> Reserva:
        reserva = (
            db.query(Reserva)
            .filter(Reserva.id_reserva == id_reserva)
            .with_for_update()
            .first()
        )
        if reserva is None:
            raise ReservaError(f"La reserva #{id_reserva} no existe.")
        if reserva.estado not in ESTADOS_ACTIVOS:
            raise ReservaError(f"La reserva #{id_reserva} ya está {reserva.estado}.")
        return reserva

    @staticmethod
    def marcar_recogida(db: Session, id_reserva: int) -> None:
        """Entrega la comanda y descuenta el stock (una sola vez)."""
        try:
            reserva = ReservaService._bloquear_reserva_activa(db, id_reserva)
            reserva.estado = "recogida"
            reserva.estado_bit = True
            StockService.descontar_stock_por_reserva(db, reserva)
            db.commit()
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def cancelar_reserva(db: Session, id_reserva: int) -> Decimal:
        """Cancela la reserva y reembolsa sus pagos.

        Los pagos con monedero TUI se devuelven al saldo del usuario; los de
        tarjeta (visitantes) se marcan como reembolsados. Devuelve el importe
        abonado al monedero.
        """
        try:
            reserva = ReservaService._bloquear_reserva_activa(db, id_reserva)
            reserva.estado = "cancelada"
            reserva.estado_bit = False

            devuelto = Decimal("0")
            for pago in reserva.pagos:
                if pago.estado != "completado":
                    continue
                if pago.metodo == "tui" and pago.id_usuario:
                    rol = (
                        db.query(Usuario.tipo)
                        .filter(Usuario.id_usuario == pago.id_usuario)
                        .scalar()
                    )
                    monto = Decimal(pago.monto)
                    if not monedero_service.abonar(db, pago.id_usuario, rol, monto):
                        raise ReservaError(
                            "No se pudo devolver el importe: el usuario no tiene monedero TUI."
                        )
                    devuelto += monto
                pago.estado = "reembolsado"

            db.commit()
            return devuelto
        except Exception:
            db.rollback()
            raise
