from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import String, cast, func
from app.models import Pago, Usuario
from app.services import monedero_service


# Pagos que cuentan como venta: completados y asociados a una reserva
FILTRO_VENTAS = (Pago.estado == "completado", Pago.id_reserva.isnot(None))


class PagoService:

    @staticmethod
    def get_all(db: Session, search_text: str = "", metodo_filtro: str = "todos") -> List[Pago]:
        """Obtiene el historial de pagos con filtros aplicados."""
        query = db.query(Pago).options(
            joinedload(Pago.usuario),
            joinedload(Pago.reserva)
        )

        if metodo_filtro and metodo_filtro != "todos":
            query = query.filter(Pago.metodo == metodo_filtro)

        if search_text.strip():
            patron = f"%{search_text.strip()}%"
            query = query.join(Usuario, isouter=True).filter(
                (cast(Pago.id_pago, String).ilike(patron)) |
                (cast(Pago.id_reserva, String).ilike(patron)) |
                (Usuario.email.ilike(patron)) |
                (Pago.correo.ilike(patron))
            )

        return query.order_by(Pago.fecha_pago.desc()).all()

    @staticmethod
    def get_kpis(db: Session) -> Dict[str, Any]:
        """Calcula agregados y estadísticas de los pagos para el panel."""
        # Ingresos = menús vendidos. Las recargas del monedero no cuentan: ese
        # dinero se contabiliza cuando se gasta en una reserva (si no, se
        # sumaría dos veces).
        ingresos_completados = db.query(func.sum(Pago.monto)).filter(*FILTRO_VENTAS).scalar() or 0.0
        ingresos_pendientes = (
            db.query(func.sum(Pago.monto))
            .filter(Pago.estado == "pendiente", Pago.id_reserva.isnot(None))
            .scalar() or 0.0
        )
        total_operaciones = db.query(func.count(Pago.id_pago)).scalar() or 0
        tui_bonos = db.query(func.count(Pago.id_pago)).filter(Pago.metodo.in_(["tui", "bono"])).scalar() or 0
        visitantes = db.query(func.count(Pago.id_pago)).filter(Pago.id_usuario == 0).scalar() or 0

        return {
            "total_ingresos": float(ingresos_completados),
            "ingresos_pendientes": float(ingresos_pendientes),
            "total_operaciones": int(total_operaciones),
            "tui_bonos": int(tui_bonos),
            "visitantes": int(visitantes),
        }

    @staticmethod
    def cambiar_estado(db: Session, id_pago: int, nuevo_estado: str) -> Optional[Pago]:
        """Actualiza el estado de un pago en la base de datos."""
        pago = db.query(Pago).filter(Pago.id_pago == id_pago).first()
        if pago:
            pago.estado = nuevo_estado
            db.commit()
            db.refresh(pago)
        return pago

    @staticmethod
    def recargar_saldo_usuario(db: Session, user_id: int, rol: str, monto: Decimal, metodo: str = "tarjeta") -> bool:
        """Añade saldo al monedero y registra el pago, todo en una única transacción."""
        try:
            if not monedero_service.abonar(db, user_id, rol, monto):
                db.rollback()
                return False

            db.add(Pago(
                id_usuario=user_id,
                monto=monto,
                metodo=metodo,
                fecha_pago=datetime.now(),
                estado="completado",
            ))
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
