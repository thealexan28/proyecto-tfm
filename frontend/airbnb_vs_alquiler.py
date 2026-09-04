import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_ciudades_disponibles,
    get_comparativa_alquiler_ciudad,
    get_comparativa_alquiler_barrios,
)


def format_currency(value):
    if pd.isna(value):
        return "-"

    return f"{value:,.0f} €".replace(",", ".")


def format_ratio(value):
    if pd.isna(value):
        return "-"

    return f"{value:.2f}x"


def render_airbnb_vs_alquiler():
    st.title("🏠 Airbnb vs long-term rentals")

    st.markdown(
        """
        Compares the monthly equivalent Airbnb price with municipal long-term rent.
        This view highlights the cities and neighborhoods with the largest price gap.
        """
    )

    st.caption(
        "Reference period: 1–30 November 2025. All cities use the same 30-day "
        "window and the same municipal reporting date."
    )

    st.divider()

    # =========================
    # Filtros
    # =========================
    ciudades_df = get_ciudades_disponibles()

    if ciudades_df.empty:
        st.warning("No cities are available in the database.")
        return

    ciudades = ciudades_df["ciudad"].dropna().sort_values().tolist()

    col_filter_1, col_filter_2 = st.columns([2, 1])

    with col_filter_1:
        ciudad_seleccionada = st.selectbox(
            "Select a city",
            options=["All cities"] + ciudades,
            index=0,
        )

    with col_filter_2:
        limite = st.slider(
            "Neighborhoods to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    ciudad_param = (
        None
        if ciudad_seleccionada == "All cities"
        else ciudad_seleccionada
    )

    # =========================
    # Carga de datos
    # =========================
    df_ciudad = get_comparativa_alquiler_ciudad(
        ciudad=ciudad_param,
    )

    df_barrios = get_comparativa_alquiler_barrios(
        ciudad=ciudad_param,
        limite=limite,
    )

    if df_ciudad.empty:
        st.warning("No data is available for the selected filters.")
        return

    # =========================
    # BLOQUE 1: comparación principal ciudad
    # =========================
    st.subheader("Monthly gap by city")

    if ciudad_param is None:
        df_plot = df_ciudad[
            [
                "ciudad",
                "precio_airbnb_mensualizado",
                "alquiler_habitual_municipal",
            ]
        ].copy()

        df_plot = df_plot.rename(
            columns={
                "precio_airbnb_mensualizado": "Monthly equivalent Airbnb price",
                "alquiler_habitual_municipal": "Municipal long-term rent",
            }
        )

        df_melt = df_plot.melt(
            id_vars="ciudad",
            value_vars=[
                "Monthly equivalent Airbnb price",
                "Municipal long-term rent",
            ],
            var_name="Metric",
            value_name="Monthly amount",
        )

        fig_comparacion = px.bar(
            df_melt,
            x="ciudad",
            y="Monthly amount",
            color="Metric",
            barmode="group",
            text="Monthly amount",
            title="Monthly equivalent Airbnb price vs municipal long-term rent",
            labels={
                "ciudad": "City",
                "Monthly amount": "Monthly amount (€)",
            },
        )

        fig_comparacion.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        fig_comparacion.update_layout(
            height=500,
            yaxis_title="Monthly amount (€)",
            xaxis_title="City",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_comparacion, width="stretch")

        diferencia_media = df_ciudad["diferencia_mensual"].mean()
        ratio_medio = df_ciudad["ratio_airbnb_vs_alquiler"].mean()

        ciudad_mayor_dif = df_ciudad.sort_values(
            "diferencia_mensual",
            ascending=False,
        ).iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average difference",
            format_currency(diferencia_media),
        )

        col2.metric(
            "Average Airbnb/rent ratio",
            format_ratio(ratio_medio),
        )

        col3.metric(
            "Largest difference",
            ciudad_mayor_dif["ciudad"],
            format_currency(ciudad_mayor_dif["diferencia_mensual"]),
        )

    else:
        fila = df_ciudad.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Monthly equivalent Airbnb price",
            format_currency(fila["precio_airbnb_mensualizado"]),
        )

        col2.metric(
            "Municipal long-term rent",
            format_currency(fila["alquiler_habitual_municipal"]),
        )

        col3.metric(
            "Monthly difference",
            format_currency(fila["diferencia_mensual"]),
        )

        col4.metric(
            "Airbnb/rent ratio",
            format_ratio(fila["ratio_airbnb_vs_alquiler"]),
        )

        df_plot = pd.DataFrame(
            {
                "Metric": [
                    "Monthly equivalent Airbnb price",
                    "Municipal long-term rent",
                ],
                "Monthly amount": [
                    fila["precio_airbnb_mensualizado"],
                    fila["alquiler_habitual_municipal"],
                ],
            }
        )

        fig_comparacion = px.bar(
            df_plot,
            x="Metric",
            y="Monthly amount",
            text="Monthly amount",
            title=f"Monthly comparison in {ciudad_seleccionada}",
            labels={
                "Monthly amount": "Monthly amount (€)",
            },
        )

        fig_comparacion.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        fig_comparacion.update_layout(
            height=450,
            yaxis_title="Monthly amount (€)",
            xaxis_title="",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_comparacion, width="stretch")

    st.divider()

    # =========================
    # BLOQUE 2: contexto residencial municipal
    # =========================
    st.subheader("Municipal housing context")

    contexto_cols = [
        "ciudad",
        "alquiler_habitual_municipal",
        "renta_media_hogar",
        "ingresos_ciudadanos",
        "num_viviendas_residenciales",
        "num_viviendas_turisticas",
        "capacidad_viviendas_turisticas",
        "indice_presion_turistica",
    ]

    contexto_df = df_ciudad[contexto_cols].copy()

    contexto_tabla = contexto_df.rename(
        columns={
            "ciudad": "City",
            "alquiler_habitual_municipal": "Municipal long-term rent",
            "renta_media_hogar": "Average household income",
            "ingresos_ciudadanos": "Average personal income",
            "num_viviendas_residenciales": "Residential properties",
            "num_viviendas_turisticas": "Official short-term rental properties",
            "capacidad_viviendas_turisticas": "Official tourist capacity",
            "indice_presion_turistica": "Tourism pressure index",
        }
    )

    st.dataframe(
        contexto_tabla,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # =========================
    # BLOQUE 3: barrios frente a referencia municipal
    # =========================
    st.subheader("Neighborhoods vs the municipal benchmark")

    if df_barrios.empty:
        st.warning("No neighborhood data is available for the selected filters.")
    else:
        if ciudad_param is None:
            df_barrios["zona"] = (
                df_barrios["barrio"] + " (" + df_barrios["ciudad"] + ")"
            )
            titulo_barrios = (
                f"Top {limite} neighborhoods by difference from municipal rent"
            )
        else:
            df_barrios["zona"] = df_barrios["barrio"]
            titulo_barrios = (
                f"Top {limite} neighborhoods by difference from municipal rent in {ciudad_seleccionada}"
            )

        df_chart = df_barrios.sort_values(
            "diferencia_frente_alquiler_municipal",
            ascending=True,
        )

        fig_barrios = px.bar(
            df_chart,
            x="diferencia_frente_alquiler_municipal",
            y="zona",
            orientation="h",
            text="diferencia_frente_alquiler_municipal",
            title=titulo_barrios,
            labels={
                "diferencia_frente_alquiler_municipal": "Difference from municipal rent (€)",
                "zona": "Neighborhood",
            },
            hover_data={
                "ciudad": True,
                "barrio": True,
                "num_viviendas": True,
                "precio_airbnb_mensualizado_barrio": ":.2f",
                "alquiler_habitual_municipal": ":.2f",
                "ratio_frente_alquiler_municipal": ":.2f",
                "zona": False,
            },
        )

        fig_barrios.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        fig_barrios.update_layout(
            height=max(450, limite * 34),
            xaxis_title="Difference from municipal rent (€)",
            yaxis_title="Neighborhood",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_barrios, width="stretch")

    st.divider()

    # =========================
    # BLOQUE 4: relación concentración-precio
    # =========================
    st.subheader("Relationship between concentration and Airbnb price")

    if not df_barrios.empty:
        fig_scatter = px.scatter(
            df_barrios,
            x="num_viviendas",
            y="precio_airbnb_mensualizado_barrio",
            size="ingreso_potencial_total",
            color="ciudad" if ciudad_param is None else None,
            hover_name="barrio",
            title="Number of properties vs monthly equivalent Airbnb price by neighborhood",
            labels={
                "num_viviendas": "Number of short-term rental properties",
                "precio_airbnb_mensualizado_barrio": "Monthly equivalent Airbnb price by neighborhood (€)",
                "ingreso_potencial_total": "Total potential revenue",
                "ciudad": "City",
            },
        )

        fig_scatter.update_layout(
            height=500,
            xaxis_title="Number of short-term rental properties",
            yaxis_title="Monthly equivalent Airbnb price by neighborhood (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_scatter, width="stretch")

    st.divider()

    # =========================
    # BLOQUE 5: tabla detalle barrios
    # =========================
    st.subheader("Detailed table by neighborhood")

    if not df_barrios.empty:
        tabla = df_barrios.copy()

        tabla = tabla.rename(
            columns={
                "ciudad": "City",
                "barrio": "Neighborhood",
                "num_viviendas": "No. of properties",
                "precio_medio_airbnb_diario": "Daily Airbnb price",
                "precio_airbnb_mensualizado_barrio": "Monthly equivalent neighborhood Airbnb price",
                "alquiler_habitual_municipal": "Municipal long-term rent",
                "diferencia_frente_alquiler_municipal": "Difference from municipal benchmark",
                "ratio_frente_alquiler_municipal": "Ratio to municipal benchmark",
                "disponibilidad_pct": "Availability (%)",
                "ocupacion_estimada_pct": "Estimated occupancy (%)",
                "ingreso_potencial_total": "Total potential revenue",
                "registros_con_precio": "Records with price",
                "registros_calendario": "Nights analyzed",
            }
        )

        columnas = [
            "City",
            "Neighborhood",
            "No. of properties",
            "Daily Airbnb price",
            "Monthly equivalent neighborhood Airbnb price",
            "Municipal long-term rent",
            "Difference from municipal benchmark",
            "Ratio to municipal benchmark",
            "Availability (%)",
            "Estimated occupancy (%)",
            "Total potential revenue",
            "Records with price",
            "Nights analyzed",
        ]

        st.dataframe(
            tabla[columnas],
            width="stretch",
            hide_index=True,
        )

    st.caption(
        """
        The Airbnb price is converted to a monthly amount by multiplying the average daily price by 30.
        The long-term rental benchmark is municipal.
        """
    )
