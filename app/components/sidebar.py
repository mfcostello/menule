import reflex as rx
from app.states.auth_state import AppState
from app.config.navigation import NavigationItem


def _section_title(title: str) -> rx.Component:
    return rx.text(
        title,
        size="1",
        weight="bold",
        color="var(--gray-10)",
        style={"letterSpacing": "0.08em"},
        text_transform="uppercase",
        margin_top="0.5em",
    )


def sidebar_item(item: NavigationItem) -> rx.Component:
    is_active = rx.State.router.page.path == item.href

    return rx.link(
        rx.hstack(
            rx.icon(
                item.icon,
                size=18,
                color=rx.cond(is_active, "var(--violet-10)", "var(--gray-11)"),
            ),
            rx.text(
                item.title,
                weight=rx.cond(is_active, "bold", "medium"),
                color=rx.cond(is_active, "var(--gray-12)", "var(--gray-11)"),
            ),
            spacing="3",
            width="100%",
            padding="0.72em 0.8em",
            border_radius="12px",
            background=rx.cond(is_active, "var(--violet-a3)", "transparent"),
            border=rx.cond(is_active, "1px solid var(--violet-a6)", "1px solid transparent"),
            style={"transition": "all 180ms ease"},
            _hover={
                "background": "var(--gray-3)",
                "transform": "translateX(2px)",
            },
        ),
        href=item.href,
        underline="none",
        width="100%",
    )


def _grouped_items() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AppState.is_admin,
            rx.vstack(
                _section_title("General"),
                rx.foreach(AppState.navigation_items[:2], sidebar_item),
                _section_title("Gestión"),
                rx.foreach(AppState.navigation_items[2:6], sidebar_item),
                _section_title("Sistema"),
                rx.foreach(AppState.navigation_items[6:], sidebar_item),
                spacing="2",
                width="100%",
                align_items="start",
            ),
            rx.cond(
                (AppState.is_estudiante | AppState.is_profesor),
                rx.vstack(
                    _section_title("General"),
                    rx.foreach(AppState.navigation_items[:2], sidebar_item),
                    _section_title("Servicios"),
                    rx.foreach(AppState.navigation_items[2:5], sidebar_item),
                    _section_title("Cuenta"),
                    rx.foreach(AppState.navigation_items[5:], sidebar_item),
                    spacing="2",
                    width="100%",
                    align_items="start",
                ),
                rx.cond(
                    AppState.is_cocina,
                    rx.vstack(
                        _section_title("Operación"),
                        rx.foreach(AppState.navigation_items[:4], sidebar_item),
                        _section_title("Cuenta"),
                        rx.foreach(AppState.navigation_items[4:], sidebar_item),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                    rx.vstack(
                        _section_title("Visitante"),
                        rx.foreach(AppState.navigation_items, sidebar_item),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                ),
            ),
        ),
        width="100%",
        spacing="1",
        align_items="start",
    )


def _tarjeta_usuario() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(AppState.user_name, weight="bold", size="2", color="var(--gray-12)"),
                rx.text(AppState.user_role, size="1", color="var(--gray-11)"),
                spacing="0",
                align_items="start",
                min_width="0",
            ),
            rx.spacer(),
            rx.cond(
                (AppState.is_estudiante | AppState.is_profesor),
                rx.badge(
                    AppState.user_saldo_str,
                    color_scheme="violet",
                    variant="soft",
                    radius="full",
                ),
            ),
            align="center",
            width="100%",
        ),
        width="100%",
        padding="0.8em 0.9em",
        style={
            "borderRadius": "14px",
            "border": "1px solid var(--gray-5)",
            "background": "var(--color-panel-solid)",
        },
    )


def _logo() -> rx.Component:
    return rx.hstack(
        rx.image(src="/logo_menule.png", width="34px", height="34px"),
        rx.heading("MenULE", size="6", weight="bold", color="var(--gray-12)"),
        spacing="3",
        align="center",
    )


def contenido_navegacion() -> rx.Component:
    """Logo, enlaces por rol y tarjeta de usuario (compartido por escritorio y móvil)."""
    return rx.vstack(
        _logo(),
        rx.divider(),
        _grouped_items(),
        rx.spacer(),
        _tarjeta_usuario(),
        spacing="4",
        width="100%",
        height="100%",
        align_items="stretch",
    )


def sidebar() -> rx.Component:
    """Barra lateral fija, solo en pantallas grandes (>= 62em)."""
    return rx.desktop_only(
        rx.box(
            contenido_navegacion(),
            width="272px",
            min_width="272px",
            padding="1.2em",
            border_right="1px solid var(--gray-5)",
            background="var(--color-panel-solid)",
            position="sticky",
            top="0",
            height="100vh",
            overflow_y="auto",
        ),
    )


def menu_movil() -> rx.Component:
    """Botón hamburguesa + panel deslizante con la navegación (móvil y tablet)."""
    return rx.mobile_and_tablet(
        rx.drawer.root(
            rx.drawer.trigger(
                rx.icon_button(
                    rx.icon("menu", size=20),
                    variant="soft",
                    color_scheme="gray",
                    size="2",
                    radius="large",
                    aria_label="Abrir menú",
                ),
            ),
            rx.drawer.overlay(z_index="40"),
            rx.drawer.portal(
                rx.drawer.content(
                    rx.box(
                        rx.drawer.close(
                            rx.icon_button(
                                rx.icon("x", size=18),
                                variant="ghost",
                                color_scheme="gray",
                                aria_label="Cerrar menú",
                            ),
                            position="absolute",
                            top="1.3em",
                            right="1em",
                            z_index="1",
                        ),
                        contenido_navegacion(),
                        position="relative",
                        width="100%",
                        height="100%",
                        padding="1.2em",
                        overflow_y="auto",
                    ),
                    width="min(300px, 85vw)",
                    height="100%",
                    top="0",
                    left="0",
                    background="var(--color-panel-solid)",
                    z_index="50",
                ),
            ),
            direction="left",
        ),
    )
