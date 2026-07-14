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
    st.title("📍 Short-term rental concentration by neighborhood")

    st.markdown(
        """
        Neighborhood ranking by number of short-term rental properties. It highlights
        the areas where supply is most heavily concentrated.
        """
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
            "Number of neighborhoods to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    ciudad_param = None if ciudad_seleccionada == "All cities" else ciudad_seleccionada

    # =========================
    # Carga de datos
    # =========================
    df = get_concentracion_barrios(
        ciudad=ciudad_param,
        limite=limite,
    )

    if df.empty:
        st.warning("No data is available for the selected filters.")
        return

    # Campo auxiliar para que el gráfico sea claro cuando no se selecciona ciudad
    if ciudad_param is None:
        df["zona"] = df["barrio"] + " (" + df["ciudad"] + ")"
        titulo_grafico = f"Top {limite} neighborhoods by number of short-term rentals"
    else:
        df["zona"] = df["barrio"]
        titulo_grafico = f"Top {limite} neighborhoods by number of short-term rentals in {ciudad_seleccionada}"

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
        "Properties in the ranking",
        format_number(total_viviendas_top),
    )

    col2.metric(
        "Neighborhood with the most properties",
        barrio_top,
    )

    col3.metric(
        "Leading neighborhood share",
        f"{peso_top:.2f} %",
        format_number(viviendas_top),
    )

    if ciudad_param is None:
        st.caption(
            f"The neighborhood with the highest concentration is **{barrio_top}**, in **{ciudad_top}**."
        )
    else:
        st.caption(
            f"In **{ciudad_seleccionada}**, the neighborhood with the highest concentration is **{barrio_top}**."
        )

    st.divider()

    # =========================
    # Gráfico de barras
    # =========================
    st.subheader("Neighborhood ranking")

    df_chart = df.sort_values("num_viviendas", ascending=True)

    fig = px.bar(
        df_chart,
        x="num_viviendas",
        y="zona",
        orientation="h",
        text="num_viviendas",
        title=titulo_grafico,
        labels={
            "num_viviendas": "Number of short-term rental properties",
            "zona": "Neighborhood",
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
        xaxis_title="Number of short-term rental properties",
        yaxis_title="Neighborhood",
        height=max(450, limite * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # =========================
    # Tabla de detalle
    # =========================
    st.subheader("Detailed table")

    tabla = df.copy()

    tabla = tabla.rename(
        columns={
            "ciudad": "City",
            "barrio": "Neighborhood",
            "num_viviendas": "No. of short-term rental properties",
            "porcentaje_sobre_ciudad": "% of city total",
            "registros_calendario": "Nights analyzed",
            "precio_medio_diario": "Average daily price",
            "tasa_disponibilidad_pct": "Average availability (%)",
        }
    )

    columnas = [
        "City",
        "Neighborhood",
        "No. of short-term rental properties",
        "% of city total",
        "Nights analyzed",
        "Average daily price",
        "Average availability (%)",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("The ranking uses unique properties to prevent duplicates from the daily calendar.")
