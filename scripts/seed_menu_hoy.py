"""Crea un catálogo de platos de ejemplo y los menús de un día.

Es idempotente: los platos/ingredientes que ya existen (por nombre) y los menús
que ya existen para esa fecha y turno no se duplican.

    python scripts/seed_menu_hoy.py               # menús de hoy
    python scripts/seed_menu_hoy.py 2026-11-05    # menús de otra fecha
"""
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models import Ingrediente, Menu, Plato  # noqa: E402

# nombre: (tipo, alérgenos)
CATALOGO = {
    # Primeros
    "Lentejas estofadas": ("primero", "Ninguno"),
    "Crema de calabaza": ("primero", "Lácteos"),
    "Ensalada mixta": ("primero", "Huevo"),
    "Sopa de cocido": ("primero", "Gluten"),
    "Macarrones con tomate": ("primero", "Gluten"),
    "Gazpacho": ("primero", "Ninguno"),
    # Segundos
    "Pollo asado con patatas": ("segundo", "Ninguno"),
    "Merluza a la plancha": ("segundo", "Pescado"),
    "Albóndigas en salsa": ("segundo", "Gluten, Huevo"),
    "Tortilla de patatas": ("segundo", "Huevo"),
    "Lomo a la plancha con pimientos": ("segundo", "Ninguno"),
    "Hamburguesa vegetal": ("segundo", "Gluten, Soja"),
    # Postres
    "Flan casero": ("postre", "Huevo, Lácteos"),
    "Fruta de temporada": ("postre", "Ninguno"),
    "Yogur natural": ("postre", "Lácteos"),
    "Arroz con leche": ("postre", "Lácteos"),
}

MENUS_DEL_DIA = {
    "almuerzo": [
        "Lentejas estofadas", "Ensalada mixta", "Macarrones con tomate",
        "Pollo asado con patatas", "Merluza a la plancha", "Albóndigas en salsa",
        "Flan casero", "Fruta de temporada", "Arroz con leche",
    ],
    "cena": [
        "Crema de calabaza", "Sopa de cocido", "Gazpacho",
        "Tortilla de patatas", "Lomo a la plancha con pimientos", "Hamburguesa vegetal",
        "Yogur natural", "Fruta de temporada",
    ],
}


def main(fecha: date) -> None:
    with SessionLocal() as db:
        platos = {p.nombre: p for p in db.query(Plato).all()}
        for nombre, (tipo, alergenos) in CATALOGO.items():
            if nombre not in platos:
                platos[nombre] = Plato(nombre=nombre, tipo=tipo, alergenos=alergenos, activo=True)
                db.add(platos[nombre])

        # El stock se descuenta buscando un ingrediente con el nombre del plato
        ingredientes = {i.nombre for i in db.query(Ingrediente.nombre).all()}
        for nombre, (_, alergenos) in CATALOGO.items():
            if nombre not in ingredientes:
                db.add(Ingrediente(
                    nombre=nombre, unidad_medida="Raciones",
                    stock_actual=Decimal("100"), stock_minimo=Decimal("20"),
                    alergeno=alergenos != "Ninguno", tipo_alergeno=alergenos,
                ))

        for tipo, nombres in MENUS_DEL_DIA.items():
            existe = db.query(Menu).filter(Menu.fecha == fecha, Menu.tipo == tipo).first()
            if existe:
                print(f"Ya existe el menú de {tipo} del {fecha} (#{existe.id_menu}).")
                continue
            menu = Menu(fecha=fecha, tipo=tipo, max_reservas=150, disponible=True,
                        platos=[platos[n] for n in nombres])
            db.add(menu)
            db.flush()
            print(f"Creado menú de {tipo} del {fecha} (#{menu.id_menu}) con {len(nombres)} platos.")

        db.commit()


if __name__ == "__main__":
    main(date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today())
