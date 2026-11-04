"""Carga un conjunto de datos de demostración realista (para presentar la app).

Crea, sin tocar los datos existentes:
- ~110 usuarios (estudiantes, profesores y personal de comedor) con contraseña común.
- Catálogo de platos e ingredientes de stock (algunos por debajo del mínimo).
- Menús de almuerzo y cena de los días laborables del último mes, de hoy y de
  la próxima semana.
- Reservas históricas (recogidas, alguna cancelada y reembolsada), reservas de
  visitantes y las de hoy, con sus pagos.
- Recargas del monedero simuladas en el tiempo: el saldo final de cada usuario
  cuadra con sus recargas y consumos y nunca es negativo.
- Incidencias en distintos estados, prioridades y destinos.

    python scripts/seed_demo.py

Si los usuarios de demo ya existen, no hace nada (restaura una copia de
seguridad si quieres empezar de cero).
"""
import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config.precios import PRECIO_MENU_POR_ROL, PRECIO_MENU_VISITANTE  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Estudiante, Incidencia, Ingrediente, Menu, Pago, PersonalComedor, Plato,
    Profesor, Reserva, Usuario,
)
from app.services.register_service import RegisterService  # noqa: E402
from seed_menu_hoy import CATALOGO as CATALOGO_BASE  # noqa: E402

PASSWORD_DEMO = "Demo1234!"
DIAS_HISTORIAL = 30
DIAS_FUTUROS = 7
rng = random.Random(2026)

CATALOGO = {
    **CATALOGO_BASE,
    "Paella de verduras": ("primero", "Ninguno"),
    "Garbanzos con espinacas": ("primero", "Ninguno"),
    "Espaguetis carbonara": ("primero", "Gluten, Huevo, Lácteos"),
    "Sopa de pescado": ("primero", "Pescado, Crustáceos"),
    "Ensalada de pasta": ("primero", "Gluten"),
    "Puré de verduras": ("primero", "Ninguno"),
    "Filete de ternera con ensalada": ("segundo", "Ninguno"),
    "Salmón al horno": ("segundo", "Pescado"),
    "Pechuga de pavo a la plancha": ("segundo", "Ninguno"),
    "Bacalao a la vizcaína": ("segundo", "Pescado"),
    "Croquetas caseras": ("segundo", "Gluten, Lácteos, Huevo"),
    "Pollo al curry con arroz": ("segundo", "Lácteos"),
    "Natillas": ("postre", "Lácteos, Huevo"),
    "Tarta de queso": ("postre", "Lácteos, Gluten, Huevo"),
    "Macedonia de frutas": ("postre", "Ninguno"),
    "Manzana asada": ("postre", "Ninguno"),
}

NOMBRES = ["Lucía", "Hugo", "Martina", "Mateo", "Sofía", "Leo", "Julia", "Daniel", "Paula", "Pablo",
           "Valeria", "Álvaro", "Carmen", "Adrián", "Irene", "Diego", "Sara", "Javier", "Elena", "Marcos",
           "Laura", "Iván", "Claudia", "Sergio", "Noa", "Rubén", "Alba", "Raúl", "Nerea", "Andrés",
           "Marta", "Óscar", "Ainhoa", "Gonzalo", "Lorena", "Víctor", "Ana", "Jorge", "Cristina", "Héctor",
           "Beatriz", "Mario", "Patricia", "Alberto", "Rocío", "Fernando", "Teresa", "Luis", "Inés", "Carlos"]
APELLIDOS = ["García", "Fernández", "González", "Rodríguez", "López", "Martínez", "Sánchez", "Pérez",
             "Álvarez", "Gómez", "Díez", "Robles", "Prieto", "Fuertes", "Castro", "Blanco", "Llamazares",
             "Rey", "Alonso", "Gutiérrez", "Morán", "Pellitero", "Cuervo", "Valbuena", "Ordás", "Barrio"]
GRADOS = ["Grado en Ingeniería Informática", "Grado en Ingeniería Aeroespacial",
          "Grado en Ingeniería Mecánica", "Grado en Ingeniería Eléctrica",
          "Grado en Ingeniería Electrónica Industrial", "Máster en Ingeniería Informática"]
DEPARTAMENTOS = ["Ingeniería Eléctrica y de Sistemas", "Matemáticas", "Ingeniería Mecánica",
                 "Ciencias de la Computación", "Física Aplicada"]


def _sin_tildes(s: str) -> str:
    return s.lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))


def _dni(numero: int) -> str:
    return f"{numero:08d}{'TRWAGMYFPDXBNJZSQVHLCKE'[numero % 23]}"


def _dias_laborables(desde: date, hasta: date):
    d = desde
    while d <= hasta:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def crear_usuarios(db, password_hash):
    usuarios = []  # (Usuario, rol, perfil)
    usados = set()

    def nuevo(tipo, dominio, i):
        while True:
            nombre, ap1, ap2 = rng.choice(NOMBRES), rng.choice(APELLIDOS), rng.choice(APELLIDOS)
            email = f"{_sin_tildes(nombre)}.{_sin_tildes(ap1)}@{dominio}"
            if email not in usados:
                usados.add(email)
                break
        alta = date.today() - timedelta(days=rng.randint(40, 400))
        u = Usuario(nombre=nombre, apellido=f"{ap1} {ap2}", email=email, contrasena_hash=password_hash,
                    dni=_dni(71400000 + i * 7919 % 99999), telefono=f"6{rng.randint(10000000, 99999999)}",
                    fecha_alta=alta, credencial_activa=True, tipo=tipo)
        db.add(u)
        return u

    for i in range(90):
        u = nuevo("estudiante", "estudiantes.unileon.es", i)
        usuarios.append((u, "estudiante", rng.choice(GRADOS)))
    for i in range(90, 105):
        u = nuevo("profesor", "unileon.es", i)
        usuarios.append((u, "profesor", rng.choice(DEPARTAMENTOS)))
    cocina = []
    for i, esp in zip(range(105, 109), ["Jefa de cocina", "Cocina caliente", "Cocina fría", "Atención en línea"]):
        u = nuevo("personal_comedor", "comedor.unileon.es", i)
        cocina.append((u, esp))
    db.flush()

    for u, rol, detalle in usuarios:
        modelo = Estudiante if rol == "estudiante" else Profesor
        db.add(modelo(id_usuario=u.id_usuario, grado_academico=detalle,
                      tui_numero=f"TUI-{u.dni}", saldo=Decimal("0.00")))
    for u, esp in cocina:
        db.add(PersonalComedor(id_usuario=u.id_usuario, especialidad=esp,
                               fecha_contratacion=u.fecha_alta))
    db.flush()
    return usuarios, [u for u, _ in cocina]


def crear_catalogo(db):
    platos = {p.nombre: p for p in db.query(Plato).all()}
    for nombre, (tipo, alergenos) in CATALOGO.items():
        if nombre not in platos:
            platos[nombre] = Plato(nombre=nombre, tipo=tipo, alergenos=alergenos, activo=True)
            db.add(platos[nombre])
    existentes = {i.nombre for i in db.query(Ingrediente.nombre).all()}
    for nombre, (_, alergenos) in CATALOGO.items():
        if nombre not in existentes:
            minimo = Decimal(rng.choice([15, 20, 25]))
            # unos pocos por debajo del mínimo para que el panel de stock tenga avisos
            actual = Decimal(rng.randint(3, 12)) if rng.random() < 0.15 else Decimal(rng.randint(40, 160))
            db.add(Ingrediente(nombre=nombre, unidad_medida="Raciones", stock_actual=actual,
                               stock_minimo=minimo, alergeno=alergenos != "Ninguno",
                               tipo_alergeno=alergenos))
    db.flush()
    return platos


def crear_menus(db, platos):
    por_tipo = {t: [p for p in platos.values() if p.tipo == t] for t in ("primero", "segundo", "postre")}
    menus = []
    hoy = date.today()
    for dia in _dias_laborables(hoy - timedelta(days=DIAS_HISTORIAL), hoy + timedelta(days=DIAS_FUTUROS)):
        for turno in ("almuerzo", "cena"):
            menu = db.query(Menu).filter(Menu.fecha == dia, Menu.tipo == turno).first()
            if menu is None:
                seleccion = (rng.sample(por_tipo["primero"], 3) + rng.sample(por_tipo["segundo"], 3)
                             + rng.sample(por_tipo["postre"], rng.choice([2, 3])))
                menu = Menu(fecha=dia, tipo=turno, max_reservas=150 if turno == "almuerzo" else 80,
                            disponible=True, platos=seleccion)
                db.add(menu)
            menus.append(menu)
    db.flush()
    return menus


def _hora_reserva(dia: date, turno: str) -> datetime:
    if turno == "almuerzo":
        return datetime.combine(dia, time(rng.randint(8, 13), rng.randint(0, 59)))
    return datetime.combine(dia, time(rng.randint(12, 19), rng.randint(0, 59)))


def crear_reservas(db, menus, usuarios):
    hoy = date.today()
    ahora = datetime.now()
    saldo = {u.id_usuario: Decimal("0.00") for u, _, _ in usuarios}
    rol_de = {u.id_usuario: rol for u, rol, _ in usuarios}
    # cada usuario tiene una "frecuencia" distinta: unos comen casi a diario, otros poco
    frecuencia = {u.id_usuario: rng.uniform(0.15, 0.8) for u, _, _ in usuarios}
    eventos = []  # (fecha, tipo, datos) para simular el monedero en orden

    for menu in sorted(menus, key=lambda m: (m.fecha, m.tipo)):
        if menu.fecha > hoy:
            continue
        factor = 1.0 if menu.tipo == "almuerzo" else 0.35
        for u, rol, _ in usuarios:
            if rng.random() < frecuencia[u.id_usuario] * factor:
                eventos.append((_hora_reserva(menu.fecha, menu.tipo), "reserva", (u.id_usuario, menu)))
        for _ in range(rng.randint(2, 9) if menu.tipo == "almuerzo" else rng.randint(0, 3)):
            eventos.append((_hora_reserva(menu.fecha, menu.tipo), "visitante", menu))

    eventos.sort(key=lambda e: e[0])
    n_reservas = 0
    for cuando, tipo, datos in eventos:
        if cuando > ahora:
            cuando = ahora - timedelta(minutes=rng.randint(1, 90))
        menu = datos[1] if tipo == "reserva" else datos
        primeros = [p for p in menu.platos if p.tipo == "primero"]
        segundos = [p for p in menu.platos if p.tipo == "segundo"]
        postres = [p for p in menu.platos if p.tipo == "postre"]
        eleccion = [rng.choice(primeros), rng.choice(segundos), rng.choice(postres)]

        es_hoy = menu.fecha == hoy
        turno_pasado = menu.tipo == "almuerzo" and ahora.time() >= time(15, 0)
        if es_hoy and not turno_pasado:
            estado = "recogida" if (menu.tipo == "almuerzo" and ahora.time() > time(13, 30) and rng.random() < 0.6) else "confirmada"
        else:
            estado = "cancelada" if rng.random() < 0.06 else "recogida"

        if tipo == "reserva":
            id_usuario, _ = datos
            precio = PRECIO_MENU_POR_ROL[rol_de[id_usuario]]
            # recarga previa si no llega el saldo (como haría un usuario real)
            if saldo[id_usuario] < precio:
                importe = Decimal(rng.choice([10, 20, 20, 30, 50]))
                db.add(Pago(id_usuario=id_usuario, monto=importe, metodo=rng.choice(["tarjeta", "tarjeta", "efectivo"]),
                            fecha_pago=cuando - timedelta(minutes=rng.randint(5, 600)), estado="completado"))
                saldo[id_usuario] += importe
            saldo[id_usuario] -= precio
            reserva = Reserva(id_usuario=id_usuario, id_menu=menu.id_menu, fecha_reserva=cuando,
                              estado=estado, estado_bit=estado == "recogida", platos=eleccion)
            db.add(reserva)
            db.flush()
            pago_estado = "completado"
            if estado == "cancelada":
                saldo[id_usuario] += precio
                pago_estado = "reembolsado"
            db.add(Pago(id_usuario=id_usuario, id_reserva=reserva.id_reserva, monto=precio, metodo="tui",
                        fecha_pago=cuando, estado=pago_estado))
        else:
            reserva = Reserva(id_usuario=0, id_menu=menu.id_menu, fecha_reserva=cuando,
                              estado=estado, estado_bit=estado == "recogida", platos=eleccion)
            db.add(reserva)
            db.flush()
            db.add(Pago(id_usuario=0, id_reserva=reserva.id_reserva, monto=PRECIO_MENU_VISITANTE,
                        metodo="tarjeta", fecha_pago=cuando, correo=f"visitante{rng.randint(100, 999)}@gmail.com",
                        estado="reembolsado" if estado == "cancelada" else "completado"))
        n_reservas += 1

    # unos pocos usuarios con recargas recientes de colchón
    for u, _, _ in rng.sample(usuarios, 25):
        importe = Decimal(rng.choice([20, 30, 50]))
        db.add(Pago(id_usuario=u.id_usuario, monto=importe, metodo="tarjeta",
                    fecha_pago=ahora - timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 10)), estado="completado"))
        saldo[u.id_usuario] += importe

    for u, rol, _ in usuarios:
        perfil = db.get(Estudiante if rol == "estudiante" else Profesor, u.id_usuario)
        perfil.saldo = saldo[u.id_usuario]
    return n_reservas


INCIDENCIAS = [
    ("Cobro duplicado en el monedero", "Al reservar el menú me han descontado el importe dos veces.", "administracion", "alta"),
    ("No me llega el comprobante", "Hice una recarga con tarjeta y no veo el movimiento en el historial.", "administracion", "media"),
    ("Plato frío", "El segundo plato estaba frío al recogerlo a las 14:30.", "cocina", "media"),
    ("Falta información de alérgenos", "Las croquetas no indicaban que llevan huevo.", "cocina", "alta"),
    ("Cola muy larga en el comedor", "Hoy la espera ha sido de más de 25 minutos.", "cocina", "baja"),
    ("Error al iniciar sesión", "La aplicación me dice que el correo o la contraseña son incorrectos.", "administracion", "media"),
    ("Opción vegetariana", "¿Podría haber al menos un segundo plato vegetariano cada día?", "cocina", "baja"),
    ("TUI no reconocida", "En caja no leen mi tarjeta TUI aunque está activa en la app.", "administracion", "critica"),
    ("Ración pequeña", "La ración de lentejas ha sido bastante más pequeña de lo habitual.", "cocina", "baja"),
    ("Cambio de grado académico", "He cambiado de grado y quiero actualizar mis datos.", "administracion", "baja"),
    ("Producto en mal estado", "El yogur del postre estaba caducado.", "cocina", "critica"),
    ("Reserva no aparece", "Reservé el almuerzo pero no aparece en Mis reservas.", "administracion", "alta"),
    ("Sugerencia de menú", "Estaría bien que hubiera fruta como postre todos los días.", "cocina", "baja"),
    ("Saldo incorrecto", "Mi saldo no coincide con mis recargas.", "administracion", "media"),
]
SOLUCIONES = {
    "administracion": "Revisado: se ha corregido el movimiento y el saldo ya es el correcto. Gracias por avisar.",
    "cocina": "Gracias por el aviso. Lo hemos revisado con el equipo de cocina y tomado medidas.",
}


def crear_incidencias(db, usuarios, cocina, admin_id):
    ahora = datetime.now()
    for i, (titulo, desc, destino, prioridad) in enumerate(INCIDENCIAS):
        autor = rng.choice(usuarios)[0]
        fecha = ahora - timedelta(days=rng.randint(0, 25), hours=rng.randint(0, 8))
        estado = rng.choice(["resuelta", "resuelta", "cerrada", "en_proceso", "abierta"]) if i > 2 else "abierta"
        inc = Incidencia(id_usuario=autor.id_usuario, titulo=titulo, descripcion=desc, destino=destino,
                         prioridad=prioridad, estado=estado, fecha_reporte=fecha,
                         numero_seguimiento=f"INC-{rng.randint(0, 0xFFFFFFFF):08X}")
        if estado in ("resuelta", "cerrada"):
            inc.solucion = SOLUCIONES[destino]
            inc.fecha_resolucion = fecha + timedelta(hours=rng.randint(2, 48))
            inc.id_responsable = admin_id if destino == "administracion" else rng.choice(cocina).id_usuario
        elif estado == "en_proceso":
            inc.id_responsable = admin_id if destino == "administracion" else rng.choice(cocina).id_usuario
        db.add(inc)


def main() -> None:
    with SessionLocal() as db:
        if db.query(Usuario).filter(Usuario.email.like("%@comedor.unileon.es"), Usuario.dni.like("714%")).first():
            print("Los datos de demo ya están cargados; no se ha cambiado nada.")
            return
        admin = db.query(Usuario).filter(Usuario.tipo == "administrador").first()
        try:
            usuarios, cocina = crear_usuarios(db, RegisterService.hash_password(PASSWORD_DEMO))
            platos = crear_catalogo(db)
            menus = crear_menus(db, platos)
            n = crear_reservas(db, menus, usuarios)
            crear_incidencias(db, usuarios, cocina, admin.id_usuario if admin else None)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print(f"Usuarios: {len(usuarios)} comensales + {len(cocina)} de cocina (contraseña: {PASSWORD_DEMO})")
        print(f"Menús: {len(menus)} | Reservas: {n} | Incidencias: {len(INCIDENCIAS)}")
        ejemplo = {rol: next(u.email for u, r, _ in usuarios if r == rol) for rol in ("estudiante", "profesor")}
        print(f"Cuentas de ejemplo: {ejemplo['estudiante']}, {ejemplo['profesor']}, {cocina[0].email}")


if __name__ == "__main__":
    main()
