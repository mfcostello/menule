import reflex as rx
from typing import List
from datetime import datetime

from app.config.navigation import NAV_ITEMS, NavigationItem
from app.database import SessionLocal
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.models import Estudiante, Profesor


class AppState(rx.State):
    # =====================================
    # LOGIN
    # =====================================
    email: str = ""
    password: str = ""

    is_logged_in: bool = False
    is_loading: bool = False
    error_message: str = ""

    # =====================================
    # USUARIO ACTUAL Y MONEDERO
    # =====================================
    user_id: int = 0
    user_name: str = ""
    user_email: str = ""
    user_role: str = ""
    user_dni: str = ""
    user_saldo: float = 0.00
    user_tui_num: str = ""
    notificaciones: List[str] = []

    users: list = []

    # =====================================
    # VARS COMPUTADOS PARA LA UI
    # =====================================
    @rx.var
    def user_saldo_str(self) -> str:
        return f"{self.user_saldo:.2f} €"

    @rx.var
    def user_role_upper(self) -> str:
        return self.user_role.upper() if self.user_role else ""

    @rx.var
    def saludo_actual(self) -> str:
        hora = datetime.now().hour
        if 5 <= hora < 12:
            return "Buenos días, "
        elif 12 <= hora < 20:
            return "Buenas tardes, "
        else:
            return "Buenas noches, "

    @rx.var
    def fecha_hoy_str(self) -> str:
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        hoy = datetime.now()
        return f"{hoy.day} {meses[hoy.month - 1]} {hoy.year}"

    # =====================================
    # LOGIN EVENT
    # =====================================
    @rx.event
    def login(self):
        self.is_loading = True
        self.error_message = ""

        try:
            with SessionLocal() as db:
                user = AuthService.login(
                    db,
                    self.email,
                    self.password,
                )

                if user is None:
                    self.error_message = "Correo o contraseña incorrectos."
                    self.is_loading = False
                    return

                self.is_logged_in = True
                self.user_id = user.id_usuario
                self.user_name = f"{user.nombre} {user.apellido}"
                self.user_email = user.email
                role = str(user.tipo).lower() if user.tipo else ""
                self.user_role = role
                self.user_dni = user.dni or f"ID-{user.id_usuario}"

                # Obtención de perfil vinculado (Estudiante / Profesor)
                est_info = getattr(user, "estudiante_info", None)
                prof_info = getattr(user, "profesor_info", None)

                if isinstance(est_info, list) and len(est_info) > 0:
                    est_info = est_info[0]
                if isinstance(prof_info, list) and len(prof_info) > 0:
                    prof_info = prof_info[0]

                if role == "estudiante":
                    if est_info:
                        self.user_saldo = float(getattr(est_info, "saldo", 0.0) or 0.0)
                        self.user_tui_num = getattr(est_info, "tui_numero", "") or f"TUI-{user.dni or user.id_usuario}"
                    else:
                        # Auto-recuperación si el usuario fue creado sin fila en Estudiantes
                        tui = f"TUI-{user.dni or user.id_usuario}"
                        nuevo_est = Estudiante(id_usuario=user.id_usuario, grado_academico="Grado", tui_numero=tui, saldo=0.0)
                        db.add(nuevo_est)
                        db.commit()
                        self.user_saldo = 0.0
                        self.user_tui_num = tui
                elif role == "profesor":
                    if prof_info:
                        self.user_saldo = float(getattr(prof_info, "saldo", 0.0) or 0.0)
                        self.user_tui_num = getattr(prof_info, "tui_numero", "") or f"TUI-{user.dni or user.id_usuario}"
                    else:
                        # Auto-recuperación si el profesor fue creado sin fila en Profesores
                        tui = f"TUI-{user.dni or user.id_usuario}"
                        nuevo_prof = Profesor(id_usuario=user.id_usuario, grado_academico="Docente", tui_numero=tui, saldo=0.0)
                        db.add(nuevo_prof)
                        db.commit()
                        self.user_saldo = 0.0
                        self.user_tui_num = tui
                else:
                    self.user_saldo = 0.0
                    self.user_tui_num = self.user_dni

            self.is_loading = False
            return rx.redirect("/home")

        except Exception as e:
            print("Error en login:", e)
            self.error_message = "Ha ocurrido un error al iniciar sesión."
            self.is_loading = False

    # =====================================
    # LOGIN VISITANTE
    # =====================================
    @rx.event
    def login_visitante(self):
        self.email = ""
        self.password = ""
        self.error_message = ""
        self.is_loading = False

        self.is_logged_in = True
        self.user_id = 0
        self.user_name = "Visitante"
        self.user_email = ""
        self.user_role = "visitante"
        self.user_dni = ""
        self.user_saldo = 0.0
        self.user_tui_num = ""

        return rx.redirect("/home")

    # =====================================
    # LOGOUT
    # =====================================
    @rx.event
    def logout(self):
        self.email = ""
        self.password = ""

        self.is_logged_in = False
        self.is_loading = False
        self.error_message = ""

        self.user_id = 0
        self.user_name = ""
        self.user_email = ""
        self.user_role = ""
        self.user_dni = ""
        self.user_saldo = 0.0
        self.user_tui_num = ""

        self.notificaciones = []

        return rx.redirect("/")

    # =====================================
    # SETTERS
    # =====================================
    def set_email(self, value: str):
        self.email = value

    def set_password(self, value: str):
        self.password = value

    # =====================================
    # ROLES
    # =====================================
    @rx.var
    def is_admin(self) -> bool:
        return self.user_role == "administrador"

    @rx.var
    def is_estudiante(self) -> bool:
        return self.user_role == "estudiante"

    @rx.var
    def is_profesor(self) -> bool:
        return self.user_role == "profesor"

    @rx.var
    def is_cocina(self) -> bool:
        return self.user_role == "personal_comedor"

    @rx.var
    def is_visitante(self) -> bool:
        return self.user_role == "visitante"

    def _tiene_rol(self, *roles: str) -> bool:
        """Comprobación de permisos para usar dentro de los event handlers.

        Cualquier event handler puede invocarse desde el navegador, así que
        toda acción que modifique datos debe comprobar el rol en el servidor.
        """
        return self.is_logged_in and self.user_role in roles

    # =====================================
    # NAVEGACIÓN DINÁMICA
    # =====================================
    @rx.var
    def navigation_items(self) -> List[NavigationItem]:
        return NAV_ITEMS.get(self.user_role, [])

    # =====================================
    # CARGAR USUARIOS
    # =====================================
    @rx.event
    def load_users(self):
        with SessionLocal() as db:
            self.users = UserService.get_all_users(db)

    # =====================================
    # INICIALES Y NOMBRE COMPLETO DINÁMICOS
    # =====================================
    @rx.var
    def user_full_name(self) -> str:
        if not self.user_name:
            return "Usuario MenULE"
        return self.user_name

    @rx.var
    def user_initials(self) -> str:
        name = self.user_name.strip() if self.user_name else ""
        if not name:
            return "U"

        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return parts[0][0].upper()

    # =====================================
    # NOTIFICACIONES
    # =====================================
    def agregar_notificacion(self, mensaje: str):
        self.notificaciones.append(mensaje)

    def limpiar_notificaciones(self):
        self.notificaciones = []
