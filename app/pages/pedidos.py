import reflex as rx

from app.components.layout import layout
from app.states.pedido_state import PedidoState


def modal_detalle_pedido() -> rx.Component:
    """Modal para visualizar los detalles exactos del menú de la comanda."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Detalle de Comanda / Reserva"),
            rx.cond(
                PedidoState.pedido_seleccionado,
                rx.vstack(
                    rx.hstack(
                        rx.text("ID Reserva:", weight="bold"),
                        rx.badge(f"#{PedidoState.pedido_seleccionado.id_reserva}", color_scheme="violet"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.text("Usuario:", weight="bold"),
                        rx.text(PedidoState.pedido_seleccionado.correo),
                        spacing="2",
                    ),
                    rx.divider(),
                    rx.text("Platos Seleccionados:", weight="bold", size="2"),
                    rx.vstack(
                        rx.foreach(
                            PedidoState.pedido_seleccionado.platos_lista,
                            lambda plato: rx.hstack(
                                rx.icon("chef-hat", size=18, color="var(--violet-10)"),
                                rx.text(plato, size="2", weight="medium"),
                                spacing="2",
                                align="center",
                            )
                        ),
                        spacing="2",
                        width="100%",
                        padding="0.5em",
                        background="var(--gray-2)",
                        border_radius="10px",
                    ),
                    spacing="3",
                    padding_y="1em",
                ),
                rx.fragment()
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=lambda: PedidoState.set_show_modal_detalle(False)
                    )
                ),
                justify="end",
                width="100%",
            ),
            max_width="450px",
        ),
        open=PedidoState.show_modal_detalle,
        on_open_change=PedidoState.set_show_modal_detalle,
    )


def tarjeta_metrica(titulo: str, valor: rx.Var, icono: str, color_bg: str, color_icon: str) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=24, color=color_icon),
                background=color_bg,
                border_radius="12px",
                padding="10px",
            ),
            rx.vstack(
                rx.text(titulo, size="1", color="gray", weight="medium"),
                rx.heading(valor, size="6", weight="bold"),
                spacing="0",
                align_items="start",
            ),
            align="center",
            spacing="3",
        ),
        padding="1.2em",
        border_radius="16px",
        width="100%",
    )


def pedidos_page() -> rx.Component:
    return layout(
        rx.vstack(
            # ENCABEZADO
            rx.vstack(
                rx.heading("Procesar Pedidos y Comandas", size=rx.breakpoints(initial="6", sm="8")),
                rx.text(
                    "Control en tiempo real de entregas de comida y pase de comedor.",
                    color="gray",
                ),
                align_items="start",
                spacing="1",
                width="100%",
            ),

            # METRICAS RÁPIDAS
            rx.grid(
                tarjeta_metrica("Total Reservas", PedidoState.total_hoy, "receipt", "var(--violet-3)", "var(--violet-10)"),
                tarjeta_metrica("Pendientes de Entrega", PedidoState.pendientes_hoy, "clock", "var(--amber-3)", "var(--amber-11)"),
                tarjeta_metrica("Entregados / Recogidos", PedidoState.recogidos_hoy, "circle-check", "var(--green-3)", "var(--green-11)"),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="4",
                width="100%",
            ),

            # TABLA DE RESERVAS Y COMANDAS
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.input(
                            placeholder="Buscar por correo o ID...",
                    min_width="180px",
                    flex="1",
                            value=PedidoState.search_text,
                            on_change=PedidoState.set_search_text,
                            width="100%", max_width="280px",
                        ),
                        rx.select.root(
                            rx.select.trigger(placeholder="Filtrar estado..."),
                            rx.select.content(
                                rx.select.item("Todos los estados", value="todos"),
                                rx.select.item("Pendientes", value="pendientes"),
                                rx.select.item("Recogidos", value="recogidos"),
                                rx.select.item("Cancelados", value="cancelados"),
                            ),
                            value=PedidoState.filtro_estado,
                            on_change=PedidoState.set_filtro_estado,
                        ),
                        rx.button(
                            rx.icon("search", size=16),
                            "Filtrar",
                            on_click=PedidoState.cargar_pedidos,
                            variant="soft",
                            color_scheme="violet",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("refresh-cw", size=16),
                            "Actualizar",
                            on_click=PedidoState.cargar_pedidos,
                            variant="outline",
                            color_scheme="gray",
                        ),
                        width="100%",
                        align="center",
                        spacing="3",
                        flex_wrap="wrap",
                    ),

                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Fecha / Hora"),
                                rx.table.column_header_cell("ID Reserva"),
                                rx.table.column_header_cell("Usuario"),
                                rx.table.column_header_cell("Menú"),
                                rx.table.column_header_cell("Estado"),
                                rx.table.column_header_cell("Acciones (Pase)"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                PedidoState.pedidos,
                                lambda p: rx.table.row(
                                    rx.table.cell(
                                        rx.vstack(
                                            rx.text(p.fecha, weight="bold", size="2"),
                                            rx.text(p.hora, size="1", color="gray"),
                                            spacing="0",
                                        )
                                    ),
                                    rx.table.cell(rx.badge(f"#{p.id_reserva}", variant="soft", color_scheme="gray")),
                                    rx.table.cell(rx.text(p.correo, weight="medium")),
                                    rx.table.cell(
                                        rx.button(
                                            rx.icon("utensils", size=14),
                                            rx.text("Ver Menú", size="1"),
                                            variant="ghost",
                                            color_scheme="violet",
                                            on_click=lambda: PedidoState.ver_detalle_menu(p),
                                        )
                                    ),
                                    rx.table.cell(
                                        rx.cond(
                                            p.estado_bit == 1,
                                            rx.badge("Recogido", color_scheme="green", variant="soft"),
                                            rx.cond(
                                                p.estado == "cancelada",
                                                rx.badge("Cancelado", color_scheme="red", variant="soft"),
                                                rx.badge("Pendiente", color_scheme="amber", variant="soft")
                                            )
                                        )
                                    ),
                                    rx.table.cell(
                                        rx.cond(
                                            # Solo los pedidos pendientes admiten acciones
                                            (p.estado == "confirmada") | (p.estado == "pendiente"),
                                            rx.hstack(
                                                rx.button(
                                                    "Recogida",
                                                    color_scheme="green",
                                                    variant="soft",
                                                    size="1",
                                                    cursor="pointer",
                                                    on_click=lambda: PedidoState.marcar_recogido(p.id_reserva),
                                                ),
                                                rx.button(
                                                    "Cancelar",
                                                    color_scheme="red",
                                                    variant="soft",
                                                    size="1",
                                                    cursor="pointer",
                                                    on_click=lambda: PedidoState.marcar_cancelado(p.id_reserva),
                                                ),
                                                spacing="2",
                                            ),
                                            rx.text("—", color="gray", size="2"),
                                        )
                                    ),
                                )
                            )
                        ),
                        variant="surface",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                padding="1.5em",
                border_radius="20px",
                width="100%",
            ),

            modal_detalle_pedido(),

            spacing="5",
            width="100%",
            on_mount=PedidoState.cargar_pedidos,
        )
    )