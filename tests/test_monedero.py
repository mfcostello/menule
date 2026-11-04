from decimal import Decimal as D

import pytest

from app.models import Pago
from app.services import monedero_service as m
from app.services.pago_service import PagoService


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("10", D("10.00")),
        ("2,505", D("2.51")),
        (" 3.1 ", D("3.10")),
        ("nan", None),
        ("inf", None),
        ("-inf", None),
        ("abc", None),
        ("", None),
    ],
)
def test_parse_importe(entrada, esperado):
    assert m.parse_importe(entrada) == esperado


def test_descontar_con_saldo_suficiente(datos):
    assert m.descontar(datos, 1, "estudiante", D("5.50"))
    datos.commit()
    assert m.obtener_saldo(datos, 1, "estudiante") == D("14.50")


def test_descontar_sin_saldo_no_cambia_nada(datos):
    assert not m.descontar(datos, 2, "estudiante", D("5.50"))
    assert m.obtener_saldo(datos, 2, "estudiante") == D("3.00")


def test_descontar_saldo_exacto_deja_cero(datos):
    assert m.descontar(datos, 2, "estudiante", D("3.00"))
    assert m.obtener_saldo(datos, 2, "estudiante") == D("0.00")


@pytest.mark.parametrize("importe", [D("0"), D("-5")])
def test_no_se_operan_importes_no_positivos(datos, importe):
    assert not m.descontar(datos, 1, "estudiante", importe)
    assert not m.abonar(datos, 1, "estudiante", importe)
    assert m.obtener_saldo(datos, 1, "estudiante") == D("20.00")


def test_roles_sin_monedero(datos):
    assert not m.tiene_monedero("administrador")
    assert not m.descontar(datos, 4, "administrador", D("1"))
    assert m.obtener_saldo(datos, 4, "administrador") is None


def test_recarga_suma_saldo_y_registra_pago(datos):
    assert PagoService.recargar_saldo_usuario(datos, 3, "profesor", D("10.10"))
    assert m.obtener_saldo(datos, 3, "profesor") == D("30.10")
    pago = datos.query(Pago).one()
    assert (pago.id_usuario, pago.estado, pago.id_reserva) == (3, "completado", None)


def test_recarga_sin_monedero_no_registra_pago(datos):
    assert not PagoService.recargar_saldo_usuario(datos, 4, "administrador", D("10"))
    assert datos.query(Pago).count() == 0
