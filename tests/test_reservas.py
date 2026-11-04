from decimal import Decimal as D

import pytest

from app.models import Ingrediente, Menu, Pago, Reserva
from app.services import monedero_service as m
from app.services.reserva_service import ReservaError, ReservaService as R

from tests.conftest import PLATOS_OK


def stock_pollo(db):
    return db.query(Ingrediente).filter_by(nombre="Pollo").one().stock_actual


# ---------------------------------------------------------------- creación
def test_reserva_tui_cobra_y_registra_pago(datos):
    reserva = R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)

    assert m.obtener_saldo(datos, 1, "estudiante") == D("14.50")
    assert (reserva.estado, reserva.estado_bit) == ("confirmada", False)
    assert sorted(p.nombre for p in reserva.platos) == sorted(PLATOS_OK)
    pago = datos.query(Pago).filter_by(id_reserva=reserva.id_reserva).one()
    assert (pago.monto, pago.metodo, pago.estado) == (D("5.50"), "tui", "completado")


def test_profesor_paga_su_tarifa(datos):
    R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)
    assert m.obtener_saldo(datos, 3, "profesor") == D("13.50")


@pytest.mark.parametrize(
    "id_usuario, rol, id_menu, platos, mensaje",
    [
        (2, "estudiante", 1, PLATOS_OK, "Saldo"),
        (1, "estudiante", 1, ["Sopa", "Caviar", "Flan"], "no pertenecen"),
        (1, "estudiante", 1, [], "no pertenecen"),
        (1, "estudiante", 2, PLATOS_OK, "menú del día"),
        (1, "estudiante", 99, PLATOS_OK, "no está disponible"),
        (4, "administrador", 1, PLATOS_OK, "Solo estudiantes y profesores"),
    ],
)
def test_reserva_rechazada_no_cobra(datos, id_usuario, rol, id_menu, platos, mensaje):
    saldo_antes = m.obtener_saldo(datos, id_usuario, rol)
    with pytest.raises(ReservaError, match=mensaje):
        R.crear_reserva_tui(datos, id_usuario, rol, id_menu, platos)
    assert m.obtener_saldo(datos, id_usuario, rol) == saldo_antes
    assert datos.query(Reserva).count() == 0
    assert datos.query(Pago).count() == 0


def test_menu_no_disponible(datos):
    datos.get(Menu, 1).disponible = False
    datos.commit()
    with pytest.raises(ReservaError, match="no está disponible"):
        R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)


def test_una_reserva_activa_por_usuario_y_menu(datos):
    R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    with pytest.raises(ReservaError, match="Ya tienes"):
        R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    assert m.obtener_saldo(datos, 1, "estudiante") == D("14.50")


def test_se_puede_volver_a_reservar_tras_cancelar(datos):
    reserva = R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    R.cancelar_reserva(datos, reserva.id_reserva)
    R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)


def test_aforo_maximo(datos):
    R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)
    with pytest.raises(ReservaError, match="completo"):
        R.crear_reserva_visitante(datos, 1, PLATOS_OK, "v@v.es")
    assert datos.query(Reserva).count() == 2


def test_las_recogidas_ocupan_plaza_y_las_canceladas_no(datos):
    r1 = R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    r2 = R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)
    R.marcar_recogida(datos, r1.id_reserva)
    R.cancelar_reserva(datos, r2.id_reserva)
    R.crear_reserva_visitante(datos, 1, PLATOS_OK, "v@v.es")  # 1 plaza libre
    with pytest.raises(ReservaError, match="completo"):
        R.crear_reserva_visitante(datos, 1, PLATOS_OK, "v2@v.es")


def test_reserva_visitante(datos):
    id_reserva = R.crear_reserva_visitante(datos, 1, PLATOS_OK, "v@v.es")
    pago = datos.query(Pago).filter_by(id_reserva=id_reserva).one()
    assert (pago.id_usuario, pago.monto, pago.metodo, pago.correo) == (0, D("7.50"), "tarjeta", "v@v.es")


# ---------------------------------------------------------------- recogida
def test_recogida_descuenta_stock_una_sola_vez(datos):
    reserva = R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    R.marcar_recogida(datos, reserva.id_reserva)
    assert stock_pollo(datos) == D("9")
    assert datos.get(Reserva, reserva.id_reserva).estado_bit is True

    with pytest.raises(ReservaError, match="ya está recogida"):
        R.marcar_recogida(datos, reserva.id_reserva)
    assert stock_pollo(datos) == D("9")


def test_recoger_reserva_inexistente(datos):
    with pytest.raises(ReservaError, match="no existe"):
        R.marcar_recogida(datos, 123)


# ---------------------------------------------------------------- cancelación
def test_cancelar_reembolsa_al_monedero(datos):
    reserva = R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)
    assert R.cancelar_reserva(datos, reserva.id_reserva) == D("6.50")
    assert m.obtener_saldo(datos, 3, "profesor") == D("20.00")
    assert datos.query(Pago).filter_by(id_reserva=reserva.id_reserva).one().estado == "reembolsado"


def test_no_se_reembolsa_dos_veces(datos):
    reserva = R.crear_reserva_tui(datos, 3, "profesor", 1, PLATOS_OK)
    R.cancelar_reserva(datos, reserva.id_reserva)
    with pytest.raises(ReservaError, match="ya está cancelada"):
        R.cancelar_reserva(datos, reserva.id_reserva)
    assert m.obtener_saldo(datos, 3, "profesor") == D("20.00")


def test_no_se_cancela_una_reserva_recogida(datos):
    reserva = R.crear_reserva_tui(datos, 1, "estudiante", 1, PLATOS_OK)
    R.marcar_recogida(datos, reserva.id_reserva)
    with pytest.raises(ReservaError, match="ya está recogida"):
        R.cancelar_reserva(datos, reserva.id_reserva)
    assert m.obtener_saldo(datos, 1, "estudiante") == D("14.50")


def test_cancelar_visitante_marca_reembolsado_sin_monedero(datos):
    id_reserva = R.crear_reserva_visitante(datos, 1, PLATOS_OK, "v@v.es")
    assert R.cancelar_reserva(datos, id_reserva) == D("0")
    assert datos.query(Pago).filter_by(id_reserva=id_reserva).one().estado == "reembolsado"
