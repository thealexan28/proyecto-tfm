import streamlit as st
import plotly.express as px

from backend.queries import (
    get_ciudades_disponibles,
    get_concentracion_barrios,
)


def format_number(value):
    if value is None:
        return "-"

    return f"{int(value):,}".replace(",", ".")


def render_concentracion_barrios():
    st.title("📍 Concentración de pisos turísticos por barrio")

    st.markdown(
        """
        Ranking de barrios por volumen de viviendas turísticas. Permite detectar
        las zonas donde la oferta se concentra con mayor intensidad.
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
            "Número de barrios a mostrar",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    ciudad_param = None if ciudad_seleccionada == "Todas las ciudades" else ciudad_seleccionada

    # =========================
    # Carga de datos
    # =========================
    df = get_concentracion_barrios(
        ciudad=ciudad_param,
        limite=limite,
    )

    if df.empty:
        st.warning("No hay datos disponibles para la selección realizada.")
        return

    # Campo auxiliar para que el gráfico sea claro cuando no se selecciona ciudad
    if ciudad_param is None:
        df["zona"] = df["barrio"] + " (" + df["ciudad"] + ")"
        titulo_grafico = f"Top {limite} barrios con más viviendas turísticas"
    else:
        df["zona"] = df["barrio"]
        titulo_grafico = f"Top {limite} barrios con más viviendas turísticas en {ciudad_seleccionada}"

    # =========================
    # KPIs
    # =========================
    total_viviendas_top = df["num_viviendas"].sum()
    barrio_top = df.iloc[0]["barrio"]
    ciudad_top = df.iloc[0]["ciudad"]
    viviendas_top = df.iloc[0]["num_viviendas"]
    peso_top = df.iloc[0]["porcentaje_sobre_ciudad"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Viviendas en el ranking",
        format_number(total_viviendas_top),
    )

    col2.metric(
        "Barrio con más viviendas",
        barrio_top,
    )

    col3.metric(
        "Peso del barrio líder",
        f"{peso_top:.2f} %",
        format_number(viviendas_top),
    )

    if ciudad_param is None:
        st.caption(
            f"El barrio con mayor concentración es **{barrio_top}**, en **{ciudad_top}**."
        )
    else:
        st.caption(
            f"En **{ciudad_seleccionada}**, el barrio con mayor concentración es **{barrio_top}**."
        )

    st.divider()

    # =========================
    # Gráfico de barras
    # =========================
    st.subheader("Ranking de barrios")

    df_chart = df.sort_values("num_viviendas", ascending=True)

    fig = px.bar(
        df_chart,
        x="num_viviendas",
        y="zona",
        orientation="h",
        text="num_viviendas",
        title=titulo_grafico,
        labels={
            "num_viviendas": "Número de viviendas turísticas",
            "zona": "Barrio",
        },
        hover_data={
            "ciudad": True,
            "barrio": True,
            "num_viviendas": True,
            "porcentaje_sobre_ciudad": ":.2f",
            "precio_medio_diario": ":.2f",
            "tasa_disponibilidad_pct": ":.2f",
            "zona": False,
        },
    )

    fig.update_traces(
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Número de viviendas turísticas",
        yaxis_title="Barrio",
        height=max(450, limite * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # =========================
    # Tabla de detalle
    # =========================
    st.subheader("Tabla de detalle")

    tabla = df.copy()

    tabla = tabla.rename(
        columns={
            "ciudad": "Ciudad",
            "barrio": "Barrio",
            "num_viviendas": "Nº viviendas turísticas",
            "porcentaje_sobre_ciudad": "% sobre ciudad",
            "registros_calendario": "Noches analizadas",
            "precio_medio_diario": "Precio medio diario",
            "tasa_disponibilidad_pct": "Disponibilidad media (%)",
        }
    )

    columnas = [
        "Ciudad",
        "Barrio",
        "Nº viviendas turísticas",
        "% sobre ciudad",
        "Noches analizadas",
        "Precio medio diario",
        "Disponibilidad media (%)",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("El ranking usa viviendas únicas para evitar duplicados del calendario diario.")
