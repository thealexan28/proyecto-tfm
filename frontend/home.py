import streamlit as st
import plotly.express as px

from backend.queries import (
    get_kpis_generales,
    get_resumen_por_ciudad,
    get_top_barrios,
    get_disponibilidad_por_temporada,
)


def render_home():
    st.title("Análisis del alquiler turístico en España")
    st.markdown(
        """
        Visión general del mercado de alojamientos turísticos en las ciudades analizadas:
        volumen de oferta, precios, disponibilidad e ingreso potencial estimado.
        """
    )

    st.divider()

    # KPIs generales
    kpis_df = get_kpis_generales()

    if kpis_df.empty:
        st.warning("No hay datos disponibles para construir el resumen.")
        return

    kpis = kpis_df.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total de viviendas analizadas",
        f"{int(kpis['total_viviendas']):,}".replace(",", "."),
    )

    col2.metric(
        "Ciudades analizadas",
        f"{int(kpis['total_ciudades'])}",
    )

    col3.metric(
        "Precio medio diario",
        f"{kpis['precio_medio_diario']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Noches analizadas",
        f"{int(kpis['total_registros_calendario']):,}".replace(",", "."),
    )

    col5.metric(
        "Disponibilidad media",
        f"{kpis['tasa_disponibilidad_pct']:.2f} %",
    )

    col6.metric(
        "Ingreso potencial total",
        f"{kpis['ingreso_potencial_total']:,.0f} €".replace(",", "."),
    )

    st.divider()

    # Resumen por ciudad
    st.subheader("Oferta por ciudad")

    ciudad_df = get_resumen_por_ciudad()

    if not ciudad_df.empty:
        fig_ciudad = px.bar(
            ciudad_df,
            x="ciudad",
            y="num_viviendas",
            text="num_viviendas",
            title="Viviendas turísticas por ciudad",
            labels={
                "ciudad": "Ciudad",
                "num_viviendas": "Número de viviendas",
            },
        )

        fig_ciudad.update_traces(textposition="outside")
        fig_ciudad.update_layout(
            xaxis_title="Ciudad",
            yaxis_title="Número de viviendas",
            height=450,
        )

        st.plotly_chart(fig_ciudad, width="stretch")

        ciudad_tabla = ciudad_df.rename(
            columns={
                "ciudad": "Ciudad",
                "num_viviendas": "Viviendas turísticas",
                "registros_calendario": "Noches analizadas",
                "precio_medio_diario": "Precio medio diario",
                "ingreso_potencial_total": "Ingreso potencial total",
                "tasa_disponibilidad_pct": "Disponibilidad media (%)",
            }
        )

        st.dataframe(
            ciudad_tabla,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Todavía no hay datos por ciudad.")

    st.divider()

    # Top barrios
    st.subheader("Concentración por barrio")

    top_barrios_df = get_top_barrios(limit=10)

    if not top_barrios_df.empty:
        top_barrios_df["barrio_ciudad"] = (
            top_barrios_df["barrio"] + " (" + top_barrios_df["ciudad"] + ")"
        )

        fig_barrios = px.bar(
            top_barrios_df.sort_values("num_viviendas", ascending=True),
            x="num_viviendas",
            y="barrio_ciudad",
            orientation="h",
            title="Barrios con mayor concentración de alojamientos",
            labels={
                "num_viviendas": "Número de viviendas",
                "barrio_ciudad": "Barrio",
            },
        )

        fig_barrios.update_layout(
            xaxis_title="Número de viviendas",
            yaxis_title="Barrio",
            height=500,
        )

        st.plotly_chart(fig_barrios, width="stretch")
    else:
        st.info("Todavía no hay datos de barrios.")

    st.divider()

    # Disponibilidad por temporada
    st.subheader("Disponibilidad por temporada")

    temporada_df = get_disponibilidad_por_temporada()

    if not temporada_df.empty:
        fig_temp = px.bar(
            temporada_df,
            x="temporada",
            y="tasa_disponibilidad_pct",
            color="ciudad",
            barmode="group",
            title="Disponibilidad media por temporada y ciudad",
            labels={
                "temporada": "Temporada",
                "tasa_disponibilidad_pct": "Disponibilidad (%)",
                "ciudad": "Ciudad",
            },
        )

        fig_temp.update_layout(
            xaxis_title="Temporada",
            yaxis_title="Disponibilidad (%)",
            height=450,
        )

        st.plotly_chart(fig_temp, width="stretch")
    else:
        st.info("Todavía no hay datos de disponibilidad por temporada.")
