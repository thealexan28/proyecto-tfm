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
    st.title("💰 Ingresos potenciales por barrio")

    st.markdown(
        """
        Identifica los barrios con mayor capacidad de generación económica estimada,
        combinando volumen de viviendas, precio diario y disponibilidad.
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
    df = get_ingresos_potenciales_barrios(
        ciudad=ciudad_param,
        limite=limite,
    )

    if df.empty:
        st.warning("No hay datos disponibles para la selección realizada.")
        return

    if ciudad_param is None:
        df["zona"] = df["barrio"] + " (" + df["ciudad"] + ")"
        titulo_grafico = f"Top {limite} barrios por ingreso potencial"
    else:
        df["zona"] = df["barrio"]
        titulo_grafico = f"Top {limite} barrios por ingreso potencial en {ciudad_seleccionada}"

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
        "Ingreso potencial del ranking",
        format_currency(ingreso_top),
    )

    col2.metric(
        "Barrio con mayor ingreso",
        barrio_top,
    )

    col3.metric(
        "Ingreso del barrio líder",
        format_currency(ingreso_barrio_top),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Viviendas del barrio líder",
        format_number(viviendas_barrio_top),
    )

    col5.metric(
        "Precio medio diario del barrio líder",
        f"{df.iloc[0]['precio_medio_diario']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        if df.iloc[0]["precio_medio_diario"] is not None
        else "-",
    )

    col6.metric(
        "Peso sobre ciudad",
        f"{peso_ingreso_top:.2f} %",
    )

    if ciudad_param is None:
        st.caption(
            f"El barrio con mayor ingreso potencial es **{barrio_top}**, en **{ciudad_top}**."
        )
    else:
        st.caption(
            f"En **{ciudad_seleccionada}**, el barrio con mayor ingreso potencial es **{barrio_top}**."
        )

    st.divider()

    # =========================
    # Gráfico principal
    # =========================
    st.subheader("Ranking de barrios por ingreso potencial")

    df_chart = df.sort_values("ingreso_potencial_total", ascending=True)

    fig = px.bar(
        df_chart,
        x="ingreso_potencial_total",
        y="zona",
        orientation="h",
        text="ingreso_potencial_total",
        title=titulo_grafico,
        labels={
            "ingreso_potencial_total": "Ingreso potencial total (€)",
            "zona": "Barrio",
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
        xaxis_title="Ingreso potencial total (€)",
        yaxis_title="Barrio",
        height=max(450, limite * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # =========================
    # Gráfico secundario: ingreso por vivienda
    # =========================
    st.subheader("Ingreso potencial medio por vivienda")

    fig_media = px.bar(
        df_chart,
        x="ingreso_potencial_por_vivienda",
        y="zona",
        orientation="h",
        title="Ingreso potencial medio por vivienda en los barrios del ranking",
        labels={
            "ingreso_potencial_por_vivienda": "Ingreso potencial por vivienda (€)",
            "zona": "Barrio",
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
        xaxis_title="Ingreso potencial por vivienda (€)",
        yaxis_title="Barrio",
        height=max(450, limite * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_media, width="stretch")

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
            "ingreso_potencial_total": "Ingreso potencial total",
            "porcentaje_ingreso_sobre_ciudad": "% ingreso sobre ciudad",
            "ingreso_potencial_por_vivienda": "Ingreso potencial por vivienda",
            "precio_medio_diario": "Precio medio diario",
            "tasa_disponibilidad_pct": "Disponibilidad media (%)",
            "registros_calendario": "Noches analizadas",
        }
    )

    columnas = [
        "Ciudad",
        "Barrio",
        "Nº viviendas turísticas",
        "Ingreso potencial total",
        "% ingreso sobre ciudad",
        "Ingreso potencial por vivienda",
        "Precio medio diario",
        "Disponibilidad media (%)",
        "Noches analizadas",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("Ingreso potencial estimado a partir de precio diario y disponibilidad registrada.")
