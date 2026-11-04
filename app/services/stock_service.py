from typing import List
from sqlalchemy.orm import Session
from app.models import Ingrediente, Reserva


class StockService:

    @staticmethod
    def get_ingredientes(db: Session, search_text: str = "") -> List[Ingrediente]:
        """Obtiene la lista de ingredientes con filtro de búsqueda."""
        query = db.query(Ingrediente)
        if search_text.strip():
            pattern = f"%{search_text.strip()}%"
            query = query.filter(Ingrediente.nombre.ilike(pattern))
        return query.order_by(Ingrediente.nombre.asc()).all()

    @staticmethod
    def reabastecer_stock(db: Session, id_ingrediente: int, cantidad: float) -> bool:
        """Añade unidades al stock actual de un ingrediente."""
        ingrediente = db.query(Ingrediente).filter(Ingrediente.id_ingrediente == id_ingrediente).first()
        if ingrediente and cantidad > 0:
            ingrediente.stock_actual = float(ingrediente.stock_actual or 0) + float(cantidad)
            db.commit()
            return True
        return False

    @staticmethod
    def descontar_stock_por_reserva(db: Session, reserva: Reserva) -> bool:
        """
        Al entregar una comanda, descuenta stock de los ingredientes asociados a los platos
        específicamente elegidos en la reserva.

        No hace commit: se llama desde ReservaService.marcar_recogida, que confirma
        el cambio de estado y el descuento de stock en la misma transacción.
        """

        # Usar los platos seleccionados en la reserva; si no tuviese asignados, fallback a los del menú
        platos = reserva.platos if reserva.platos else (reserva.menu.platos if reserva.menu else [])

        for plato in platos:
            pattern = f"%{plato.nombre.strip()}%"
            ingrediente = db.query(Ingrediente).filter(Ingrediente.nombre.ilike(pattern)).first()

            if ingrediente:
                actual = float(ingrediente.stock_actual or 0)
                ingrediente.stock_actual = max(0.0, actual - 1.0)

        return True

    @staticmethod
    def guardar_ingrediente(db: Session, datos: dict) -> bool:
        """Crea o actualiza un ingrediente a partir de un diccionario."""
        if datos.get("id_ingrediente"):
            ing = db.query(Ingrediente).filter(Ingrediente.id_ingrediente == datos["id_ingrediente"]).first()
            if ing:
                ing.nombre = datos.get("nombre", ing.nombre)
                ing.unidad_medida = datos.get("unidad_medida", ing.unidad_medida)
                ing.stock_actual = datos.get("stock_actual", ing.stock_actual)
                ing.stock_minimo = datos.get("stock_minimo", ing.stock_minimo)
                ing.alergeno = datos.get("alergeno", ing.alergeno)
                ing.tipo_alergeno = datos.get("tipo_alergeno", ing.tipo_alergeno)
        else:
            nuevo_ing = Ingrediente(**datos)
            db.add(nuevo_ing)
        db.commit()
        return True

    @staticmethod
    def crear_ingrediente(
        db: Session,
        nombre: str,
        unidad_medida: str,
        stock_actual: float,
        stock_minimo: float,
        alergeno: bool = False,
        tipo_alergeno: str = "Ninguno",
    ) -> Ingrediente:
        """Crea y persiste un nuevo ingrediente."""
        nuevo = Ingrediente(
            nombre=nombre.strip(),
            unidad_medida=unidad_medida.strip() if unidad_medida else "Kg",
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            alergeno=alergeno,
            tipo_alergeno=tipo_alergeno.strip() if tipo_alergeno else "Ninguno",
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
