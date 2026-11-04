"""Tarifas y límites económicos del comedor.

Todos los importes son ``Decimal`` para evitar errores de redondeo con dinero.
"""
from decimal import Decimal

# Precio del menú completo según el rol del comensal (pago con monedero TUI)
PRECIO_MENU_POR_ROL = {
    "estudiante": Decimal("5.50"),
    "profesor": Decimal("6.50"),
}

# Precio del menú para visitantes sin cuenta (pago con tarjeta)
PRECIO_MENU_VISITANTE = Decimal("7.50")

# Límites de las recargas del monedero
RECARGA_MINIMA = Decimal("1.00")
RECARGA_MAXIMA = Decimal("200.00")
METODOS_RECARGA = {"tarjeta", "efectivo"}
