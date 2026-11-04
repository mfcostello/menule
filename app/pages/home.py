import reflex as rx
from app.config.precios import PRECIO_ESTUDIANTE_STR, PRECIO_PROFESOR_STR, PRECIO_VISITANTE_STR

from app.components.layout import layout
from app.states.auth_state import AppState
from app.states.home_state import HomeState


# ==============================================================================
# COMPONENTES REUTILIZABLES DE DISEÑO UI (STRIPE/LINEAR STYLE)
# ==============================================================================

def dashboard_hero_banner(
    title: str,
    subtitle: str,
    badge_1: str,
    badge_2: str,
    icon: str,
    gradient_from: str = "var(--violet-3)",
    gradient_to: str = "var(--violet-5)",
    icon_color: str = "var(--violet-10)",
) -> rx.Component:
    """Hero Banner superior unificado para dar la bienvenida en cada Dashboard."""
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.badge(
                        badge_1,
                        color_scheme="purple",
                        variant="surface",
                        radius="full",
                    ),
                    rx.badge(
                        badge_2,
                        color_scheme="blue",
                        variant="surface",
                        radius="full",
                    ),
                    spacing="2",
                ),
                rx.heading(
                    title,
                    size="6",
                    weight="bold",
                    color="var(--gray-12)",
                ),
                rx.text(
                    subtitle,
                    color="var(--gray-11)",
                    size="3",
                ),
                spacing="2",
                align_items="start",
            ),
            rx.spacer(),
            rx.center(
                rx.icon(icon, size=40, color=icon_color),
                background=f"linear-gradient(135deg, {gradient_from} 0%, {gradient_to} 100%)",
                border_radius="20px",
                width="80px",
                height="80px",
                display=["none", "none", "flex"],
            ),
            align="center",
            width="100%",
        ),
        width="100%",
        padding="1.8em",
        style={
            "borderRadius": "22px",
            "background": "linear-gradient(135deg, var(--color-panel-solid) 0%, var(--gray-2) 100%)",
            "border": "1px solid var(--gray-5)",
            "boxShadow": "0 4px 15px rgba(0, 0, 0, 0.03)",
        },
    )


def stat_card(
    title: str, value: rx.Var, icon: str, color: str, subtitle: str = ""
) -> rx.Component:
    """Métrica destacada con elevado y bordes limpios."""
    return rx.card(
        rx.hstack(
            rx.center(
                rx.icon(icon, size=24, color="white"),
                background=color,
                border_radius="14px",
                width="52px",
                height="52px",
            ),
            rx.vstack(
                rx.text(value, size="6", weight="bold", color="var(--gray-12)"),
                rx.text(title, color="var(--gray-11)", size="2", weight="medium"),
                rx.cond(
                    subtitle != "",
                    rx.text(subtitle, color="var(--gray-10)", size="1"),
                ),
                align_items="start",
                spacing="0",
            ),
            spacing="4",
            align="center",
            width="100%",
        ),
        width="100%",
        padding="1.2em",
        style={
            "borderRadius": "18px",
            "border": "1px solid var(--gray-4)",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.03)",
        },
    )


def action_feature_card(
    title: str,
    subtitle: str,
    icon: str,
    href: str,
    badge_text: str,
    color: str,
    button_text: str,
) -> rx.Component:
    """Tarjeta interactiva con hover suave para acciones principales."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(icon, size=24, color="white"),
                    background=color,
                    border_radius="14px",
                    width="48px",
                    height="48px",
                ),
                rx.badge(
                    badge_text,
                    color_scheme="purple",
                    variant="soft",
                    radius="full",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.vstack(
                rx.heading(title, size="4", weight="bold", color="var(--gray-12)"),
                rx.text(subtitle, color="var(--gray-11)", size="2"),
                spacing="1",
                align_items="start",
            ),
            rx.spacer(),
            rx.link(
                rx.button(
                    rx.text(button_text, weight="medium"),
                    rx.icon("arrow-right", size=18),
                    width="100%",
                    size="3",
                    color_scheme="purple",
                    radius="large",
                    cursor="pointer",
                ),
                href=href,
                underline="none",
                width="100%",
            ),
            spacing="4",
            align_items="start",
            height="100%",
        ),
        width="100%",
        padding="1.5em",
        style={
            "borderRadius": "20px",
            "border": "1px solid var(--gray-4)",
            "boxShadow": "0 10px 25px -5px rgba(0, 0, 0, 0.04)",
            "transition": "all 0.2s ease-in-out",
            "_hover": {
                "transform": "translateY(-4px)",
                "boxShadow": "0 15px 30px -5px var(--violet-a3)",
            },
        },
    )


def quick_button(text: str, icon: str, href: str, color: str) -> rx.Component:
    return rx.link(
        rx.button(
            rx.icon(icon, size=18),
            rx.text(text, weight="medium"),
            width="100%",
            justify="start",
            variant="soft",
            color_scheme=color,
            size="3",
            height="44px",
            radius="large",
            cursor="pointer",
        ),
        href=href,
        underline="none",
        width="100%",
    )


# ==============================================================================
# DASHBOARDS ESPECÍFICOS POR ROL
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. ADMIN DASHBOARD
# ------------------------------------------------------------------------------
def admin_dashboard() -> rx.Component:
    return rx.vstack(
        dashboard_hero_banner(
            "Panel de Administración General",
            "Supervisión global de usuarios, menús publicados, reservas activas y estado de la infraestructura.",
            "Panel Control",
            "Modo Administrador",
            "shield-check",
            "var(--blue-3)",
            "var(--blue-6)",
            "var(--blue-10)",
        ),
        rx.grid(
            stat_card("Usuarios Totales", HomeState.total_users, "users", "var(--blue-10)", "Cuentas registradas"),
            stat_card("Menús Publicados", HomeState.total_menus, "utensils", "var(--green-9)", "Platos e historia"),
            stat_card("Reservas Totales", HomeState.total_reservations, "calendar-days", "var(--violet-10)", "Gestión activa"),
            stat_card("Incidencias", HomeState.total_incidents, "triangle-alert", "var(--red-9)", "Soporte activo"),
            columns=rx.breakpoints(initial="1", xs="2", lg="4"),
            spacing="4",
            width="100%",
        ),
        rx.grid(
            rx.card(
                rx.vstack(
                    rx.heading("Acciones Rápidas", size="4", weight="bold", color="var(--gray-12)"),
                    quick_button("Gestión de Usuarios", "user-plus", "/usuarios", "blue"),
                    quick_button("Crear / Editar Menú", "utensils-crossed", "/menus", "green"),
                    quick_button("Catálogo de Platos", "soup", "/platos", "violet"),
                    quick_button("Control de Reservas", "calendar-days", "/reservas", "orange"),
                    spacing="3",
                    width="100%",
                ),
                width="100%",
                padding="1.4em",
                style={"borderRadius": "20px", "border": "1px solid var(--gray-4)", "backgroundColor": "var(--color-panel-solid)"},
            ),
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Estado del Sistema", size="4", weight="bold", color="var(--gray-12)"),
                        rx.spacer(),
                        rx.badge("Servicios Activos", color_scheme="green", variant="surface", radius="full"),
                        width="100%",
                        align="center",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon("database", size=18, color="var(--blue-10)"),
                                rx.text("Base de Datos MySQL", weight="medium", color="var(--gray-11)"),
                                spacing="2",
                                align="center",
                            ),
                            rx.badge("Operativo", color_scheme="green", variant="soft", radius="full"),
                            justify="between",
                            width="100%",
                            align="center",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.hstack(
                                rx.icon("server", size=18, color="var(--violet-10)"),
                                rx.text("Servidor Backend Reflex", weight="medium", color="var(--gray-11)"),
                                spacing="2",
                                align="center",
                            ),
                            rx.badge("Operativo", color_scheme="green", variant="soft", radius="full"),
                            justify="between",
                            width="100%",
                            align="center",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.hstack(
                                rx.icon("shield-check", size=18, color="var(--green-9)"),
                                rx.text("Módulo Autenticación Bcrypt", weight="medium", color="var(--gray-11)"),
                                spacing="2",
                                align="center",
                            ),
                            rx.badge("Seguro", color_scheme="green", variant="soft", radius="full"),
                            justify="between",
                            width="100%",
                            align="center",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.hstack(
                                rx.icon("bell-ring", size=18, color="var(--amber-9)"),
                                rx.text("Notificaciones y Alertas", weight="medium", color="var(--gray-11)"),
                                spacing="2",
                                align="center",
                            ),
                            rx.badge("Sin alertas", color_scheme="blue", variant="soft", radius="full"),
                            justify="between",
                            width="100%",
                            align="center",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                width="100%",
                padding="1.4em",
                style={"borderRadius": "20px", "border": "1px solid var(--gray-4)", "backgroundColor": "var(--color-panel-solid)"},
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="4",
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


# ------------------------------------------------------------------------------
# 2. ESTUDIANTE Y PROFESOR DASHBOARD
# ------------------------------------------------------------------------------
def student_prof_dashboard() -> rx.Component:
    precio_texto = rx.cond(AppState.is_estudiante, PRECIO_ESTUDIANTE_STR, PRECIO_PROFESOR_STR)
    tarifa_tipo = rx.cond(AppState.is_estudiante, "Tarifa Estudiante", "Tarifa Profesorado")

    return rx.vstack(
        dashboard_hero_banner(
            f"¡Hola de nuevo, {AppState.user_full_name}!",
            "Gestiona tus reservas, consulta el menú de la universidad y controla tu saldo TUI fácilmente.",
            "Comedor ULE",
            tarifa_tipo,
            "graduation-cap",
            "var(--violet-3)",
            "var(--violet-5)",
            "var(--violet-10)",
        ),
        rx.grid(
            stat_card(
                "Saldo TUI Actual",
                AppState.user_saldo_str,
                "wallet",
                "var(--violet-10)",
                subtitle=f"Nº TUI: {AppState.user_tui_num}",
            ),
            stat_card(
                "Precio por Menú",
                precio_texto,
                "tag",
                "var(--green-9)",
                subtitle=tarifa_tipo,
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="4",
            width="100%",
        ),
        rx.grid(
            action_feature_card(
                "Menú del día",
                "Consulta los 1º, 2º platos y postres del menú diario con sus alérgenos.",
                "utensils",
                "/menu",
                "Platos Disponibles",
                "var(--green-9)",
                "Ver menú del día",
            ),
            action_feature_card(
                "Mis reservas",
                "Revisa tus reservas confirmadas, descarga tickets o cancela a tiempo.",
                "calendar-check",
                "/mis-reservas",
                "Histórico",
                "var(--blue-10)",
                "Gestionar reservas",
            ),
            action_feature_card(
                "Monedero TUI",
                "Consulta tus últimos movimientos y recarga tu saldo para reservas.",
                "wallet",
                "/monedero",
                "Pagos y Recargas",
                "var(--violet-10)",
                "Acceder al monedero",
            ),
            action_feature_card(
                "Incidencias",
                "Reporta sugerencias o inconvenientes en el servicio del comedor.",
                "triangle-alert",
                "/mis-incidencias",
                "Atención Usuario",
                "var(--red-9)",
                "Crear incidencia",
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="4",
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Información relevante del servicio", size="3", weight="bold", color="var(--gray-11)"),
                rx.grid(
                    rx.hstack(
                        rx.center(
                            rx.icon("clock", size=18, color="var(--blue-10)"),
                            background="var(--blue-3)",
                            border_radius="10px",
                            padding="8px",
                        ),
                        rx.vstack(
                            rx.text("Horarios de Reserva", weight="bold", size="2", color="var(--gray-12)"),
                            rx.text("Se reserva el menú del turno actual: almuerzo hasta las 16:30 h y cena a partir de entonces.", size="2", color="var(--gray-11)"),
                            spacing="0",
                            align_items="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.hstack(
                        rx.center(
                            rx.icon("credit-card", size=18, color="var(--green-9)"),
                            background="var(--green-3)",
                            border_radius="10px",
                            padding="8px",
                        ),
                        rx.vstack(
                            rx.text("Pago con TUI", weight="bold", size="2", color="var(--gray-12)"),
                            rx.text("Cobro automático descontado de tu monedero.", size="2", color="var(--gray-11)"),
                            spacing="0",
                            align_items="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="4",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            padding="1.3em",
            style={"borderRadius": "18px", "border": "1px solid var(--gray-4)", "backgroundColor": "var(--color-panel-solid)"},
        ),
        spacing="5",
        width="100%",
    )


# ------------------------------------------------------------------------------
# 3. PERSONAL COMEDOR / COCINA DASHBOARD
# ------------------------------------------------------------------------------
def cocina_dashboard() -> rx.Component:
    return rx.vstack(
        dashboard_hero_banner(
            "Panel de Operaciones de Cocina",
            "Gestión del menú diario, validación de comandas y control de incidencias en sala.",
            "Personal Comedor",
            "Turno Activo",
            "chef-hat",
            "var(--amber-3)",
            "var(--amber-6)",
            "var(--amber-11)",
        ),
        rx.grid(
            action_feature_card(
                "Menú Publicado",
                "Revisa la preparación de los platos configurados para el servicio de hoy.",
                "utensils",
                "/menu",
                "Servicio Hoy",
                "var(--green-9)",
                "Ver menú",
            ),
            action_feature_card(
                "Procesar Pedidos",
                "Valida la llegada de estudiantes/profesores mediante lector o TUI.",
                "circle-check",
                "/pedidos",
                "Control Accesos",
                "var(--amber-9)",
                "Validar pedidos",
            ),
            action_feature_card(
                "Inventario y Stock",
                "Controla las existencias e ingredientes para las raciones de la semana.",
                "boxes",
                "/stock",
                "Almacén",
                "var(--blue-10)",
                "Consultar stock",
            ),
            action_feature_card(
                "Incidencias Operativas",
                "Avisa sobre platos agotados o inconvenientes en la cocina.",
                "triangle-alert",
                "/incidencias",
                "Mantenimiento",
                "var(--red-9)",
                "Reportar evento",
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="4",
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


# ------------------------------------------------------------------------------
# 4. VISITANTE DASHBOARD
# ------------------------------------------------------------------------------
def visitante_card(
    title: str,
    subtitle: str,
    icon: str,
    href: str,
    badge_text: str,
    color: str,
    button_text: str,
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(icon, size=24, color="white"),
                    background=color,
                    border_radius="14px",
                    width="48px",
                    height="48px",
                ),
                rx.badge(
                    badge_text,
                    color_scheme="purple",
                    variant="soft",
                    radius="full",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.vstack(
                rx.heading(title, size="4", weight="bold", color="var(--gray-12)"),
                rx.text(subtitle, color="var(--gray-11)", size="2"),
                spacing="1",
                align_items="start",
            ),
            rx.spacer(),
            rx.link(
                rx.button(
                    rx.text(button_text, weight="medium"),
                    rx.icon("arrow-right", size=18),
                    width="100%",
                    size="3",
                    color_scheme="purple",
                    radius="large",
                    cursor="pointer",
                ),
                href=href,
                underline="none",
                width="100%",
            ),
            spacing="4",
            align_items="start",
            height="100%",
        ),
        width="100%",
        padding="1.5em",
        style={
            "borderRadius": "20px",
            "border": "1px solid var(--gray-4)",
            "boxShadow": "0 10px 25px -5px rgba(0, 0, 0, 0.05)",
            "transition": "all 0.2s ease-in-out",
            "_hover": {
                "transform": "translateY(-4px)",
                "boxShadow": "0 15px 30px -5px var(--violet-a3)",
            },
        },
    )


def visitante_dashboard() -> rx.Component:
    return rx.vstack(
        dashboard_hero_banner(
            "Bienvenido al Comedor Universitario MenULE",
            "Consulta la oferta gastronómica del día o realiza tu reserva directa al instante de forma sencilla.",
            "Acceso Público",
            "Sin Registro Necesario",
            "utensils-crossed",
            "var(--violet-3)",
            "var(--violet-5)",
            "var(--violet-10)",
        ),
        rx.grid(
            visitante_card(
                "Menú del Día",
                "Explora los platos disponibles para el desayuno, almuerzo y cena con sus alérgenos detallados.",
                "utensils",
                "/visitante",
                "Consulta Libre",
                "var(--green-9)",
                "Ver menú del día",
            ),
            visitante_card(
                "Reserva de Menú",
                "Asegura tu plato en el comedor pagando directamente con tu tarjeta bancaria.",
                "ticket",
                "/visitante/reserva",
                "Pago Directo",
                "var(--violet-10)",
                "Reservar menú",
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="4",
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading(
                    "Información del Servicio para Visitantes",
                    size="3",
                    weight="bold",
                    color="var(--gray-11)",
                ),
                rx.grid(
                    rx.hstack(
                        rx.center(
                            rx.icon("credit-card", size=18, color="var(--violet-10)"),
                            background="var(--violet-3)",
                            border_radius="10px",
                            padding="8px",
                        ),
                        rx.vstack(
                            rx.text(
                                "Tarifa Visitante",
                                weight="bold",
                                size="2",
                                color="var(--gray-12)",
                            ),
                            rx.text(
                                f"{PRECIO_VISITANTE_STR} por menú completo",
                                size="2",
                                color="var(--gray-11)",
                            ),
                            spacing="0",
                            align_items="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.hstack(
                        rx.center(
                            rx.icon("clock", size=18, color="var(--blue-10)"),
                            background="var(--blue-3)",
                            border_radius="10px",
                            padding="8px",
                        ),
                        rx.vstack(
                            rx.text(
                                "Horario de Atención",
                                weight="bold",
                                size="2",
                                color="var(--gray-12)",
                            ),
                            rx.text(
                                "Almuerzos de 13:00 a 16:00 h",
                                size="2",
                                color="var(--gray-11)",
                            ),
                            spacing="0",
                            align_items="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.hstack(
                        rx.center(
                            rx.icon("shield-check", size=18, color="var(--green-9)"),
                            background="var(--green-3)",
                            border_radius="10px",
                            padding="8px",
                        ),
                        rx.vstack(
                            rx.text(
                                "Acceso Inmediato",
                                weight="bold",
                                size="2",
                                color="var(--gray-12)",
                            ),
                            rx.text(
                                "Muestra tu entrada en taquilla",
                                size="2",
                                color="var(--gray-11)",
                            ),
                            spacing="0",
                            align_items="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    spacing="4",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            padding="1.3em",
            style={
                "borderRadius": "18px",
                "border": "1px solid var(--gray-4)",
                "backgroundColor": "var(--color-panel-solid)",
            },
        ),
        spacing="5",
        width="100%",
    )


# ==============================================================================
# VISTA PRINCIPAL
# ==============================================================================

def home_page():
    return layout(
        rx.vstack(
            rx.cond(
                AppState.is_admin,
                admin_dashboard(),
                rx.cond(
                    (AppState.is_estudiante | AppState.is_profesor),
                    student_prof_dashboard(),
                    rx.cond(
                        AppState.is_cocina,
                        cocina_dashboard(),
                        visitante_dashboard(),
                    ),
                ),
            ),
            spacing="4",
            width="100%",
            padding_bottom="2em",
        )
    )