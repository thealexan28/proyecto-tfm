import streamlit as st
import plotly.express as px

from backend.queries import (
    get_ciudades_disponibles,
    get_ingresos_potenciales_barrios,
)


def format_number(value):
    if value is None:
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_currency(value):
    if value is None:
        return "-"

    return f"{value:,.0f} €".replace(",", ".")


def render_ingresos_potenciales():
    st.title("💰 Potential revenue by neighborhood")

    st.markdown(
        """
        Identifies the neighborhoods with the greatest estimated revenue potential,
        combining property volume, daily price, and availability.
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
    df = get_ingresos_potenciales_barrios(
        ciudad=ciudad_param,
        limite=limite,
    )

    if df.empty:
        st.warning("No data is available for the selected filters.")
        return

    if ciudad_param is None:
        df["zona"] = df["barrio"] + " (" + df["ciudad"] + ")"
        titulo_grafico = f"Top {limite} neighborhoods by potential revenue"
    else:
        df["zona"] = df["barrio"]
        titulo_grafico = f"Top {limite} neighborhoods by potential revenue in {ciudad_seleccionada}"

    # =========================
    # KPIs
    # =========================
    ingreso_top = df["ingreso_potencial_total"].sum()
    barrio_top = df.iloc[0]["barrio"]
    ciudad_top = df.iloc[0]["ciudad"]
    ingreso_barrio_top = df.iloc[0]["ingreso_potencial_total"]
    viviendas_barrio_top = df.iloc[0]["num_viviendas"]
    peso_ingreso_top = df.iloc[0]["porcentaje_ingreso_sobre_ciudad"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Potential revenue in the ranking",
        format_currency(ingreso_top),
    )

    col2.metric(
        "Neighborhood with the highest revenue",
        barrio_top,
    )

    col3.metric(
        "Leading neighborhood revenue",
        format_currency(ingreso_barrio_top),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Properties in the leading neighborhood",
        format_number(viviendas_barrio_top),
    )

    col5.metric(
        "Leading neighborhood average daily price",
        f"{df.iloc[0]['precio_medio_diario']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        if df.iloc[0]["precio_medio_diario"] is not None
        else "-",
    )

    col6.metric(
        "Share of city total",
        f"{peso_ingreso_top:.2f} %",
    )

    if ciudad_param is None:
        st.caption(
            f"The neighborhood with the highest potential revenue is **{barrio_top}**, in **{ciudad_top}**."
        )
    else:
        st.caption(
            f"In **{ciudad_seleccionada}**, the neighborhood with the highest potential revenue is **{barrio_top}**."
        )

    st.divider()

    # =========================
    # Gráfico principal
    # =========================
    st.subheader("Neighborhood ranking by potential revenue")

    df_chart = df.sort_values("ingreso_potencial_total", ascending=True)

    fig = px.bar(
        df_chart,
        x="ingreso_potencial_total",
        y="zona",
        orientation="h",
        text="ingreso_potencial_total",
        title=titulo_grafico,
        labels={
            "ingreso_potencial_total": "Total potential revenue (€)",
            "zona": "Neighborhood",
        },
        hover_data={
            "ciudad": True,
            "barrio": True,
            "num_viviendas": True,
            "ingreso_potencial_total": ":.2f",
            "porcentaje_ingreso_sobre_ciudad": ":.2f",
            "ingreso_potencial_por_vivienda": ":.2f",
            "precio_medio_diario": ":.2f",
            "tasa_disponibilidad_pct": ":.2f",
            "zona": False,
        },
    )

    fig.update_traces(
        texttemplate="%{x:,.0f} €",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Total potential revenue (€)",
        yaxis_title="Neighborhood",
        height=max(450, limite * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # =========================
    # Gráfico secundario: ingreso por vivienda
    # =========================
    st.subheader("Average potential revenue per property")

    fig_media = px.bar(
        df_chart,
        x="ingreso_potencial_por_vivienda",
        y="zona",
        orientation="h",
        title="Average potential revenue per property in the ranked neighborhoods",
        labels={
            "ingreso_potencial_por_vivienda": "Potential revenue per property (€)",
            "zona": "Neighborhood",
        },
        hover_data={
            "ciudad": True,
            "barrio": True,
            "num_viviendas": True,
            "ingreso_potencial_por_vivienda": ":.2f",
            "zona": False,
        },
    )

    fig_media.update_layout(
        xaxis_title="Potential revenue per property (€)",
        yaxis_title="Neighborhood",
        height=max(450, limite * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_media, width="stretch")

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
            "ingreso_potencial_total": "Total potential revenue",
            "porcentaje_ingreso_sobre_ciudad": "% of city revenue",
            "ingreso_potencial_por_vivienda": "Potential revenue per property",
            "precio_medio_diario": "Average daily price",
            "tasa_disponibilidad_pct": "Average availability (%)",
            "registros_calendario": "Nights analyzed",
        }
    )

    columnas = [
        "City",
        "Neighborhood",
        "No. of short-term rental properties",
        "Total potential revenue",
        "% of city revenue",
        "Potential revenue per property",
        "Average daily price",
        "Average availability (%)",
        "Nights analyzed",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("Potential revenue is estimated from the daily price and recorded availability.")
