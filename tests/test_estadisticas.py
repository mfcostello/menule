from decimal import Decimal as D

from app.services.estadistica_service import EstadisticaService
from app.services.pago_service import PagoService
from app.services.reserva_service import ReservaService as R

from tests.conftest import PLATOS_OK


def test_recargas_no_cuentan_como_ingresos(datos):
    PagoService.recargar_saldo_usuario(datos, 1, "estudiante", D("50"))
    R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)

    kpis = PagoService.get_kpis(datos)
    assert kpis["total_ingresos"] == 5.5
    assert kpis["total_operaciones"] == 2  # la recarga sí es una transacción


def test_reembolsos_no_cuentan_como_ingresos(datos):
    r1 = R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)
    R.cancelar_reserva(datos, r1.id_reserva)

    assert PagoService.get_kpis(datos)["total_ingresos"] == 6.5


def test_ingresos_por_rol(datos):
    PagoService.recargar_saldo_usuario(datos, 3, "profesor", D("100"))
    R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)

    por_rol = {d["rol"]: d["total_pagado"] for d in EstadisticaService.obtener_pagos_por_rol(datos)}
    assert por_rol == {"Estudiante": 5.5, "Profesor": 6.5}
