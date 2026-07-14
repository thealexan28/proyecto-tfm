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
        Compares monthly Airbnb revenue with municipal long-term rent.
        This view highlights the cities and neighborhoods with the largest price gap.
        """
    )

    st.divider()

    # =========================
    # Filtros
    # =========================
    ciudades_df = get_ciudades_disponibles()

    if ciudades_df.empty:
        st.warning("No hay ciudades disponibles en la base de datos.")
        return

    ciudades = ciudades_df["ciudad"].dropna().sort_values().tolist()

    col_filter_1, col_filter_2 = st.columns([2, 1])

    with col_filter_1:
        ciudad_seleccionada = st.selectbox(
            "Selecciona una ciudad",
            options=["Todas las ciudades"] + ciudades,
            index=0,
        )

    with col_filter_2:
        limite = st.slider(
            "Barrios a mostrar",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    ciudad_param = (
        None
        if ciudad_seleccionada == "Todas las ciudades"
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
        st.warning("No hay datos disponibles para la selección realizada.")
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
                "precio_airbnb_mensualizado": "Airbnb mensualizado",
                "alquiler_habitual_municipal": "Alquiler habitual municipal",
            }
        )

        df_melt = df_plot.melt(
            id_vars="ciudad",
            value_vars=[
                "Airbnb mensualizado",
                "Alquiler habitual municipal",
            ],
            var_name="Métrica",
            value_name="Importe mensual",
        )

        fig_comparacion = px.bar(
            df_melt,
            x="ciudad",
            y="Importe mensual",
            color="Métrica",
            barmode="group",
            text="Importe mensual",
            title="Airbnb mensualizado frente al alquiler habitual municipal",
            labels={
                "ciudad": "Ciudad",
                "Importe mensual": "Importe mensual (€)",
            },
        )

        fig_comparacion.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        fig_comparacion.update_layout(
            height=500,
            yaxis_title="Importe mensual (€)",
            xaxis_title="Ciudad",
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
            "Diferencia media",
            format_currency(diferencia_media),
        )

        col2.metric(
            "Ratio medio Airbnb/alquiler",
            format_ratio(ratio_medio),
        )

        col3.metric(
            "Mayor diferencia",
            ciudad_mayor_dif["ciudad"],
            format_currency(ciudad_mayor_dif["diferencia_mensual"]),
        )

    else:
        fila = df_ciudad.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Airbnb mensualizado",
            format_currency(fila["precio_airbnb_mensualizado"]),
        )

        col2.metric(
            "Alquiler habitual municipal",
            format_currency(fila["alquiler_habitual_municipal"]),
        )

        col3.metric(
            "Diferencia mensual",
            format_currency(fila["diferencia_mensual"]),
        )

        col4.metric(
            "Ratio Airbnb/alquiler",
            format_ratio(fila["ratio_airbnb_vs_alquiler"]),
        )

        df_plot = pd.DataFrame(
            {
                "Métrica": [
                    "Airbnb mensualizado",
                    "Alquiler habitual municipal",
                ],
                "Importe mensual": [
                    fila["precio_airbnb_mensualizado"],
                    fila["alquiler_habitual_municipal"],
                ],
            }
        )

        fig_comparacion = px.bar(
            df_plot,
            x="Métrica",
            y="Importe mensual",
            text="Importe mensual",
            title=f"Comparación mensual en {ciudad_seleccionada}",
            labels={
                "Importe mensual": "Importe mensual (€)",
            },
        )

        fig_comparacion.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        fig_comparacion.update_layout(
            height=450,
            yaxis_title="Importe mensual (€)",
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
            "ciudad": "Ciudad",
            "alquiler_habitual_municipal": "Alquiler habitual municipal",
            "renta_media_hogar": "Renta media hogar",
            "ingresos_ciudadanos": "Renta media persona",
            "num_viviendas_residenciales": "Viviendas residenciales",
            "num_viviendas_turisticas": "Viviendas turísticas oficiales",
            "capacidad_viviendas_turisticas": "Plazas turísticas oficiales",
            "indice_presion_turistica": "Índice presión turística",
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
        st.warning("No hay datos por barrio para la selección realizada.")
    else:
        if ciudad_param is None:
            df_barrios["zona"] = (
                df_barrios["barrio"] + " (" + df_barrios["ciudad"] + ")"
            )
            titulo_barrios = (
                f"Top {limite} barrios por diferencia frente al alquiler municipal"
            )
        else:
            df_barrios["zona"] = df_barrios["barrio"]
            titulo_barrios = (
                f"Top {limite} barrios por diferencia frente al alquiler municipal en {ciudad_seleccionada}"
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
                "diferencia_frente_alquiler_municipal": "Diferencia frente al alquiler municipal (€)",
                "zona": "Barrio",
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
            xaxis_title="Diferencia frente al alquiler municipal (€)",
            yaxis_title="Barrio",
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
            title="Número de viviendas frente a Airbnb mensualizado por barrio",
            labels={
                "num_viviendas": "Número de viviendas turísticas",
                "precio_airbnb_mensualizado_barrio": "Airbnb mensualizado por barrio (€)",
                "ingreso_potencial_total": "Ingreso potencial total",
                "ciudad": "Ciudad",
            },
        )

        fig_scatter.update_layout(
            height=500,
            xaxis_title="Número de viviendas turísticas",
            yaxis_title="Airbnb mensualizado por barrio (€)",
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
                "ciudad": "Ciudad",
                "barrio": "Barrio",
                "num_viviendas": "Nº viviendas",
                "precio_medio_airbnb_diario": "Precio Airbnb diario",
                "precio_airbnb_mensualizado_barrio": "Airbnb mensualizado barrio",
                "alquiler_habitual_municipal": "Alquiler habitual municipal",
                "diferencia_frente_alquiler_municipal": "Diferencia frente referencia municipal",
                "ratio_frente_alquiler_municipal": "Ratio frente referencia municipal",
                "disponibilidad_pct": "Disponibilidad (%)",
                "ocupacion_estimada_pct": "Ocupación estimada (%)",
                "ingreso_potencial_total": "Ingreso potencial total",
                "registros_con_precio": "Registros con precio",
                "registros_calendario": "Noches analizadas",
            }
        )

        columnas = [
            "Ciudad",
            "Barrio",
            "Nº viviendas",
            "Precio Airbnb diario",
            "Airbnb mensualizado barrio",
            "Alquiler habitual municipal",
            "Diferencia frente referencia municipal",
            "Ratio frente referencia municipal",
            "Disponibilidad (%)",
            "Ocupación estimada (%)",
            "Ingreso potencial total",
            "Registros con precio",
            "Noches analizadas",
        ]

        st.dataframe(
            tabla[columnas],
            width="stretch",
            hide_index=True,
        )

    st.caption(
        """
        El precio Airbnb se mensualiza multiplicando el precio diario medio por 30.
        La referencia de alquiler habitual es municipal.
        """
    )
