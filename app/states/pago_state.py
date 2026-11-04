import logging
from decimal import Decimal
import reflex as rx
from pydantic import BaseModel
from typing import List, Optional, Union

from app.database import SessionLocal
from app.services.pago_service import PagoService
from app.states.auth_state import AppState
from app.models import Estudiante, Profesor
from app.services import monedero_service
from app.config.precios import RECARGA_MINIMA, RECARGA_MAXIMA, METODOS_RECARGA, euros

logger = logging.getLogger(__name__)

ESTADOS_PAGO = {"pendiente", "completado", "fallido", "reembolsado"}


class PagoSchema(BaseModel):
    id_pago: int
    id_usuario: int
    id_reserva: Optional[int] = None
    monto: float
    monto_str: str = ""
    metodo: str
    fecha_pago: str
    estado: str
    correo: str


class PagoState(rx.State):

    # ====================================================
    # ESTADO GENERAL Y ADMIN
    # ====================================================
    pagos: List[PagoSchema] = []
    search_text: str = ""
    filtro_metodo: str = "todos"
    is_loading: bool = False

    # Métricas agregadas Admin (KPIs)
    kpi_ingresos: float = 0.0
    kpi_operaciones: int = 0
    kpi_tui_bono: int = 0
    kpi_visitantes: int = 0

    # ====================================================
    # ESTADO MONEDERO USUARIOS (ESTUDIANTE / PROFESOR)
    # ====================================================
    saldo_actual: float = 0.00
    numero_tui: str = "TUI-UNILEON"
    monto_recarga: str = "10"
    metodo_recarga: str = "tarjeta"

    @rx.var
    def saldo_actual_str(self) -> str:
        return euros(Decimal(str(self.saldo_actual)))

    @rx.var
    def kpi_ingresos_str(self) -> str:
        return euros(Decimal(str(self.kpi_ingresos)))

    # ====================================================
    # SETTERS
    # ====================================================
    def set_search_text(self, value: str):
        self.search_text = value

    def set_monto_recarga(self, value: str):
        self.monto_recarga = value

    def set_metodo_recarga(self, value: str):
        self.metodo_recarga = value

    def set_filtro_metodo(self, value: Union[str, list[str]]):
        if isinstance(value, list):
            self.filtro_metodo = value[0] if value else "todos"
        else:
            self.filtro_metodo = value

    # ====================================================
    # CARGA DE DATOS (CON SINCRONIZACIÓN DE SIDEBAR)
    # ====================================================
    @rx.event
    async def load_pagos(self):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in:
            self.pagos = []
            return rx.redirect("/")

        self.is_loading = True
        with SessionLocal() as db:
            # 1. Cargar saldo y TUI del usuario
            if app_state.user_id:
                est = db.query(Estudiante).filter(Estudiante.id_usuario == app_state.user_id).first()
                if est:
                    self.saldo_actual = float(est.saldo or 0.0)
                    self.numero_tui = getattr(est, "tui_numero", None) or f"TUI-{app_state.user_id:06d}"
                else:
                    prof = db.query(Profesor).filter(Profesor.id_usuario == app_state.user_id).first()
                    if prof:
                        self.saldo_actual = float(prof.saldo or 0.0)
                        self.numero_tui = getattr(prof, "tui_numero", None) or f"TUI-{app_state.user_id:06d}"

                # Actualizamos el saldo en AppState para mantener sincronizado el Sidebar
                app_state.user_saldo = self.saldo_actual

            # 2. Cargar historial de pagos
            resultados = PagoService.get_all(db, self.search_text, self.filtro_metodo)
            
            # Si no es admin, solo ve sus propios pagos (los visitantes, id 0, ninguno)
            if not app_state.is_admin:
                resultados = [
                    p for p in resultados
                    if app_state.user_id and p.id_usuario == app_state.user_id
                ]

            self.pagos = [
                PagoSchema(
                    id_pago=p.id_pago,
                    id_usuario=p.id_usuario or 0,
                    id_reserva=p.id_reserva,
                    monto=float(p.monto or 0.0),
                    monto_str=euros(Decimal(p.monto or 0)),
                    metodo=(p.metodo or "tarjeta").lower(),
                    fecha_pago=p.fecha_pago.strftime("%Y-%m-%d %H:%M") if hasattr(p.fecha_pago, "strftime") else str(p.fecha_pago),
                    estado=(p.estado or "completado").lower(),
                    correo=p.usuario.email if (p.usuario and p.id_usuario != 0) else (p.correo or "Visitante"),
                )
                for p in resultados
            ]

            # KPIs globales: solo para administración
            if not app_state.is_admin:
                self.is_loading = False
                return
            kpis = PagoService.get_kpis(db)
            self.kpi_ingresos = kpis["total_ingresos"]
            self.kpi_operaciones = kpis["total_operaciones"]
            self.kpi_tui_bono = kpis["tui_bonos"]
            self.kpi_visitantes = kpis["visitantes"]

        self.is_loading = False

    # ====================================================
    # ACCIONES
    # ====================================================
    @rx.event
    async def realizar_recarga(self):
        app_state = await self.get_state(AppState)
        if not app_state._tiene_rol("estudiante", "profesor") or not app_state.user_id:
            return rx.window_alert("Solo estudiantes y profesores pueden recargar el monedero TUI.")

        monto = monedero_service.parse_importe(self.monto_recarga)
        if monto is None:
            return rx.window_alert("El importe introducido no es un número válido.")
        if not (RECARGA_MINIMA <= monto <= RECARGA_MAXIMA):
            return rx.window_alert(
                f"El importe debe estar entre {euros(RECARGA_MINIMA)} y {euros(RECARGA_MAXIMA)}."
            )
        if self.metodo_recarga not in METODOS_RECARGA:
            return rx.window_alert("Método de recarga no válido.")

        try:
            with SessionLocal() as db:
                exito = PagoService.recargar_saldo_usuario(
                    db, app_state.user_id, app_state.user_role, monto, self.metodo_recarga
                )
                nuevo_saldo = monedero_service.obtener_saldo(db, app_state.user_id, app_state.user_role)
        except Exception:
            logger.exception("Error al recargar el monedero del usuario %s", app_state.user_id)
            return rx.window_alert("Ha ocurrido un error al procesar la recarga. Inténtalo de nuevo.")

        if not exito:
            return rx.window_alert("No se pudo completar la recarga. Perfil de monedero no encontrado.")

        # Sincronizar Sidebar y Vista Monedero
        app_state.user_saldo = float(nuevo_saldo or 0)
        self.saldo_actual = app_state.user_saldo
        app_state.agregar_notificacion(f"🎉 ¡Recarga de {euros(monto)} realizada con éxito!")
        self.monto_recarga = "10"
        return [
            PagoState.load_pagos,
            rx.window_alert(f"¡Recarga completada! Tu nuevo saldo es: {euros(nuevo_saldo or Decimal(0))}"),
        ]

    @rx.event
    async def cambiar_estado_pago(self, id_pago: int, nuevo_estado: str):
        app_state = await self.get_state(AppState)
        if not app_state._tiene_rol("administrador"):
            return rx.window_alert("No tienes permisos para realizar esta acción.")
        if nuevo_estado not in ESTADOS_PAGO:
            return rx.window_alert("Estado de pago no válido.")

        with SessionLocal() as db:
            PagoService.cambiar_estado(db, id_pago, nuevo_estado)

        app_state.agregar_notificacion(
            f"El pago #{id_pago} ha cambiado a estado {nuevo_estado.upper()}."
        )

        return PagoState.load_pagos