import reflex as rx
from app.components.sidebar import sidebar, menu_movil
from app.states.auth_state import AppState


def campana_notificaciones() -> rx.Component:
    """Componente con Popover funcional para desplegar alertas individuales por usuario."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.box(
                rx.button(
                    rx.icon("bell", size=16),
                    variant="soft",
                    color_scheme=rx.cond(
                        AppState.notificaciones.length() > 0,
                        "amber",
                        "gray",
                    ),
                    size="2",
                    radius="large",
                ),
                rx.cond(
                    AppState.notificaciones.length() > 0,
                    rx.badge(
                        AppState.notificaciones.length(),
                        color_scheme="red",
                        radius="full",
                        size="1",
                        position="absolute",
                        top="-4px",
                        right="-4px",
                    ),
                ),
                position="relative",
            )
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Notificaciones y Avisos", weight="bold", size="2"),
                    rx.spacer(),
                    rx.cond(
                        AppState.notificaciones.length() > 0,
                        rx.button(
                            "Limpiar",
                            size="1",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=AppState.limpiar_notificaciones,
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.divider(),
                rx.cond(
                    AppState.notificaciones.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            AppState.notificaciones,
                            lambda notif: rx.callout(
                                notif,
                                size="1",
                                color_scheme="amber",
                                icon="triangle-alert",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                        max_height="250px",
                        overflow_y="auto",
                    ),
                    rx.text("Sin avisos pendientes.", size="2", color="var(--gray-11)"),
                ),
                spacing="2",
                width="min(320px, 80vw)",
                padding="0.5em",
            ),
            align="end",
            side="bottom",
        ),
    )


def menu_usuario_dropdown() -> rx.Component:
    """Menú desplegable contextual adaptado para Usuarios Registrados y Visitantes."""
    return rx.dropdown_menu.root(
        rx.dropdown_menu.trigger(
            rx.box(
                rx.avatar(
                    fallback=AppState.user_initials,
                    size="2",
                    radius="full",
                    color_scheme=rx.cond(AppState.is_visitante, "gray", "blue"),
                    high_contrast=False,
                    style={
                        "cursor": "pointer",
                        "transition": "transform 0.2s ease, box-shadow 0.2s ease",
                        "&:hover": {
                            "transform": "scale(1.08)",
                            "box-shadow": "0 0 0 2px var(--blue-8)",
                        },
                    },
                ),
            )
        ),
        rx.dropdown_menu.content(
            # Si es visitante: Texto + Cerrar sesión
            rx.cond(
                AppState.is_visitante,
                rx.fragment(
                    rx.dropdown_menu.item(
                        "Modo Visitante (Sesión no registrada)",
                        disabled=True,
                    ),
                    rx.dropdown_menu.separator(),
                    rx.dropdown_menu.item(
                        rx.hstack(
                            rx.icon("log-out", size=16),
                            "Cerrar Sesión",
                            align="center",
                            spacing="2",
                        ),
                        color_scheme="red",
                        on_click=AppState.logout,
                    ),
                ),
                # Si es usuario registrado: Nombre/Email + Mi Perfil + Cerrar sesión
                rx.fragment(
                    rx.dropdown_menu.item(
                        AppState.user_full_name,
                        disabled=True,
                    ),
                    rx.dropdown_menu.separator(),
                    rx.dropdown_menu.item(
                        rx.hstack(
                            rx.icon("user", size=16),
                            "Mi Perfil",
                            align="center",
                            spacing="2",
                        ),
                        on_click=rx.redirect("/perfil"),
                    ),
                    rx.dropdown_menu.separator(),
                    rx.dropdown_menu.item(
                        rx.hstack(
                            rx.icon("log-out", size=16),
                            "Cerrar Sesión",
                            align="center",
                            spacing="2",
                        ),
                        color_scheme="red",
                        on_click=AppState.logout,
                    ),
                ),
            ),
            align="end",
            side="bottom",
        ),
    )

def navbar() -> rx.Component:
    return rx.hstack(
        menu_movil(),
        rx.vstack(
            rx.text(
                AppState.fecha_hoy_str,
                size="2",
                color="var(--gray-11)",
                display=rx.breakpoints(initial="none", sm="block"),
            ),
            rx.heading(
                AppState.saludo_actual + AppState.user_name,
                size=rx.breakpoints(initial="3", sm="5"),
                weight="bold",
                color="var(--gray-12)",
                style={"overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"},
                max_width="100%",
            ),
            spacing="0",
            align_items="start",
            min_width="0",
            flex="1",
        ),
        rx.hstack(
            campana_notificaciones(),
            menu_usuario_dropdown(),
            rx.button(
                rx.icon("log-out", size=16),
                "Cerrar sesión",
                variant="soft",
                color_scheme="red",
                size="2",
                radius="large",
                on_click=AppState.logout,
                display=rx.breakpoints(initial="none", md="flex"),
            ),
            spacing="3",
            align="center",
            flex_shrink="0",
        ),
        width="100%",
        spacing="3",
        padding=rx.breakpoints(initial="0.7em 1em", sm="0.9em 1.2em"),
        background="color-mix(in srgb, var(--color-panel-solid) 88%, transparent)",
        style={
            "backdropFilter": "blur(8px)",
            "WebkitBackdropFilter": "blur(8px)",
        },
        border_bottom="1px solid var(--gray-5)",
        position="sticky",
        top="0",
        z_index="20",
        align="center",
    )


def layout(page_content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.vstack(
            navbar(),
            rx.box(
                page_content,
                padding=rx.breakpoints(initial="0.9em", sm="1.25em"),
                width="100%",
                max_width="1600px",
                margin="0 auto",
                min_width="0",
            ),
            flex="1",
            min_width="0",  # permite que el contenido se encoja en pantallas estrechas
            min_height="100vh",
            background="var(--gray-2)",
            spacing="0",
            align_items="stretch",
        ),
        width="100%",
        min_height="100vh",
        spacing="0",
        align="stretch",
    )
