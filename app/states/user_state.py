import reflex as rx
from pydantic import BaseModel
from typing import Optional
from app.database import SessionLocal
from app.services.register_service import RegisterService
from app.services.user_service import UserService
from app.states.auth_state import AppState


class UsuarioSchema(BaseModel):
    id_usuario: int
    dni: Optional[str] = ""
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = ""
    tipo: str


class UserState(rx.State):
    users: list[UsuarioSchema] = []
    search_text: str = ""

    # Control de Modales
    show_modal_nuevo: bool = False
    show_modal_editar: bool = False

    # Campos de Formulario (Crear / Editar)
    current_id: int = 0
    form_dni: str = ""
    form_nombre: str = ""
    form_apellido: str = ""
    form_email: str = ""
    form_telefono: str = ""
    form_tipo: str = "estudiante"
    form_password: str = ""

    # --- SETTERS ---
    def set_search_text(self, val: str):
        self.search_text = val
        self.search_users()

    def set_show_modal_nuevo(self, val: bool):
        self.show_modal_nuevo = val

    def set_show_modal_editar(self, val: bool):
        self.show_modal_editar = val

    def set_form_dni(self, val: str):
        self.form_dni = val

    def set_form_nombre(self, val: str):
        self.form_nombre = val

    def set_form_apellido(self, val: str):
        self.form_apellido = val

    def set_form_email(self, val: str):
        self.form_email = val

    def set_form_telefono(self, val: str):
        self.form_telefono = val

    def set_form_tipo(self, val: str):
        self.form_tipo = val

    def set_form_password(self, val: str):
        self.form_password = val

    # --- CONTROL DE ACCESO ADMIN ---
    @rx.event
    async def check_admin_access(self):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in:
            return rx.redirect("/")
        if not app_state.is_admin:
            app_state.agregar_notificacion("Acceso denegado: Se requieren permisos de administrador.")
            return rx.redirect("/home")

    # --- LECTURA ---
    @rx.event
    async def load_users(self):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in:
            self.users = []
            return rx.redirect("/")
        if not app_state.is_admin:
            self.users = []
            app_state.agregar_notificacion("Acceso denegado: Se requieren permisos de administrador.")
            return rx.redirect("/home")

        with SessionLocal() as db:
            query_results = UserService.get_all_users(db)
            self.users = [
                UsuarioSchema(
                    id_usuario=u.id_usuario,
                    dni=u.dni or "",
                    nombre=u.nombre,
                    apellido=u.apellido,
                    email=u.email,
                    telefono=u.telefono or "",
                    tipo=u.tipo,
                )
                for u in query_results
            ]

    @rx.event
    async def search_users(self):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in or not app_state.is_admin:
            self.users = []
            return

        with SessionLocal() as db:
            if self.search_text.strip():
                results = UserService.search_users(db, self.search_text.strip())
            else:
                results = UserService.get_all_users(db)

            self.users = [
                UsuarioSchema(
                    id_usuario=u.id_usuario,
                    dni=u.dni or "",
                    nombre=u.nombre,
                    apellido=u.apellido,
                    email=u.email,
                    telefono=u.telefono or "",
                    tipo=u.tipo,
                )
                for u in results
            ]

    # --- CREAR USUARIO EN MYSQL (DESDE PANEL ADMIN) ---
    def abrir_modal_nuevo(self):
        self.form_dni = ""
        self.form_nombre = ""
        self.form_apellido = ""
        self.form_email = ""
        self.form_telefono = ""
        self.form_tipo = "estudiante"
        self.form_password = ""
        self.show_modal_nuevo = True

    @rx.event
    async def crear_usuario(self):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in or not app_state.is_admin:
            return rx.window_alert("No tienes permisos para realizar esta acción.")

        if not self.form_nombre.strip() or not self.form_email.strip() or not self.form_password.strip():
            return rx.window_alert("Nombre, Email y Contraseña son obligatorios.")

        with SessionLocal() as db:
            if UserService.email_exists(db, self.form_email):
                return rx.window_alert("Ya existe un usuario con ese correo electrónico.")

            if self.form_dni.strip() and UserService.dni_exists(db, self.form_dni):
                return rx.window_alert("Ya existe un usuario con ese DNI.")

            try:
                pwd_hashed = RegisterService.hash_password(self.form_password)
                UserService.create_user(
                    db=db,
                    nombre=self.form_nombre,
                    apellido=self.form_apellido,
                    email=self.form_email,
                    contrasena_hash=pwd_hashed,
                    tipo=self.form_tipo,
                    dni=self.form_dni,
                    telefono=self.form_telefono,
                )
                self.show_modal_nuevo = False
                return [
                    UserState.load_users,
                    rx.window_alert("Usuario creado exitosamente."),
                ]
            except Exception as e:
                db.rollback()
                return rx.window_alert(f"Error al crear usuario: {str(e)}")

    # --- EDITAR USUARIO EN MYSQL ---
    def abrir_modal_editar(self, u: UsuarioSchema):
        self.current_id = u.id_usuario
        self.form_dni = u.dni or ""
        self.form_nombre = u.nombre
        self.form_apellido = u.apellido
        self.form_email = u.email
        self.form_telefono = u.telefono or ""
        self.form_tipo = u.tipo
        self.form_password = ""
        self.show_modal_editar = True

    @rx.event
    async def guardar_edicion_usuario(self):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in or not app_state.is_admin:
            return rx.window_alert("No tienes permisos para realizar esta acción.")

        with SessionLocal() as db:
            try:
                update_data = {
                    "dni": self.form_dni.strip().upper() if self.form_dni.strip() else None,
                    "nombre": self.form_nombre.strip(),
                    "apellido": self.form_apellido.strip(),
                    "email": self.form_email.strip().lower(),
                    "telefono": self.form_telefono.strip() if self.form_telefono.strip() else None,
                    "tipo": self.form_tipo,
                }
                if self.form_password.strip():
                    update_data["contrasena_hash"] = RegisterService.hash_password(self.form_password)

                UserService.update_user(db, self.current_id, **update_data)
                self.show_modal_editar = False
                return [
                    UserState.load_users,
                    rx.window_alert("Usuario actualizado correctamente."),
                ]
            except Exception as e:
                db.rollback()
                return rx.window_alert(f"Error al actualizar: {str(e)}")

    # --- ELIMINAR USUARIO EN MYSQL ---
    @rx.event
    async def eliminar_usuario(self, id_usuario: int):
        app_state = await self.get_state(AppState)
        if not app_state.is_logged_in or not app_state.is_admin:
            return rx.window_alert("No tienes permisos para realizar esta acción.")

        with SessionLocal() as db:
            try:
                UserService.delete_user(db, id_usuario)
                return [
                    UserState.load_users,
                    rx.window_alert(f"Usuario #{id_usuario} eliminado con éxito."),
                ]
            except Exception as e:
                db.rollback()
                return rx.window_alert(f"No se pudo eliminar el usuario: {str(e)}")