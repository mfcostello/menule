from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import String, cast
from app.config.precios import PRECIO_MENU_VISITANTE
from app.models import Reserva, Usuario, Pago, Plato


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

    @staticmethod
    def actualizar_estado(db: Session, id_reserva: int, estado: str, estado_bit: int) -> Optional[Reserva]:
        """Actualiza el estado y el estado_bit de una reserva."""
        reserva = db.query(Reserva).filter(Reserva.id_reserva == id_reserva).first()
        if reserva:
            reserva.estado = estado
            reserva.estado_bit = bool(estado_bit)
            db.commit()
            db.refresh(reserva)
        return reserva

    @staticmethod
    def crear_reserva_usuario(
        db: Session,
        id_usuario: int,
        id_menu: int,
        platos_ids: List[int],
        monto: float,
        metodo: str = "tui",
    ) -> Reserva:
        """
        Crea una reserva confirmada para un usuario registrado, asigna platos y
        genera el registro de Pago completado correspondiente para coherencia estadística.
        """
        platos_objetos = []
        if platos_ids:
            platos_objetos = db.query(Plato).filter(Plato.id_plato.in_(platos_ids)).all()

        nueva_reserva = Reserva(
            id_usuario=id_usuario,
            id_menu=id_menu,
            fecha_reserva=datetime.now(),
            estado="confirmada",
            estado_bit=False,  # 0 = Pendiente de recogida en cocina
            platos=platos_objetos,
        )
        db.add(nueva_reserva)
        db.flush()

        nuevo_pago = Pago(
            id_usuario=id_usuario,
            id_reserva=nueva_reserva.id_reserva,
            monto=monto,
            metodo=metodo,
            fecha_pago=datetime.now(),
            estado="completado",
        )
        db.add(nuevo_pago)
        db.commit()
        db.refresh(nueva_reserva)

        return nueva_reserva

    @staticmethod
    def crear_reserva_visitante(
        db: Session,
        id_menu: int,
        platos_ids: List[int],
        email_visitante: str,
    ) -> int:
        """Crea una reserva anónima vinculada al id_usuario = 0 y registra su pago por tarjeta (7,50 €)."""
        platos_objetos = []
        if platos_ids:
            platos_objetos = db.query(Plato).filter(Plato.id_plato.in_(platos_ids)).all()

        nueva_reserva = Reserva(
            id_usuario=0,  # ID reservado para visitantes
            id_menu=id_menu,
            fecha_reserva=datetime.now(),
            estado="confirmada",
            estado_bit=False,  # 0 = Pendiente de recogida en cocina
            platos=platos_objetos,
        )
        db.add(nueva_reserva)
        db.flush()

        nuevo_pago = Pago(
            id_reserva=nueva_reserva.id_reserva,
            id_usuario=0,
            monto=PRECIO_MENU_VISITANTE,
            metodo="tarjeta",
            estado="completado",
            correo=email_visitante,
            fecha_pago=datetime.now(),
        )
        db.add(nuevo_pago)
        db.commit()

        return nueva_reserva.id_reserva