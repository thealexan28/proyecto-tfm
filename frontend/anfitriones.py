import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_ciudades_disponibles,
    get_resumen_anfitriones,
    get_top_anfitriones,
    get_superhost_disponibilidad,
    get_grandes_tenedores_precio,
)


def format_currency_dec(value):
    if pd.isna(value):
        return "-"

    return (
        f"{value:,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def format_number(value):
    if pd.isna(value):
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_pct(value):
    if pd.isna(value):
        return "-"

    return f"{value:.2f} %"


def crear_etiquetas_anfitrion(df):
    df = df.copy()
    nombres = df["nombre_anfitrion"].fillna("Sin nombre")
    nombres_duplicados = nombres.duplicated(keep=False)
    ids = df["id_anfitrion"].apply(
        lambda value: str(int(value)) if pd.notna(value) else "desconocido"
    )
    df["etiqueta"] = nombres.where(
        ~nombres_duplicados,
        nombres + " (ID " + ids + ")",
    )
    return df


def render_anfitriones():
    st.title("👤 Análisis de anfitriones")

    st.markdown(
        """
        Analiza la concentración de viviendas por anfitrión y compara precios,
        disponibilidad e ingreso potencial entre perfiles de gestión.
        """
    )

    st.divider()

    ciudades_df = get_ciudades_disponibles()

    if ciudades_df.empty:
        st.warning("No hay ciudades disponibles en la base de datos.")
        return

    ciudades = ciudades_df["ciudad"].dropna().sort_values().tolist()

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        ciudad_seleccionada = st.selectbox(
            "Selecciona una ciudad",
            options=["Todas las ciudades"] + ciudades,
            index=0,
        )

    with col2:
        umbral_gran_tenedor = st.slider(
            "Umbral gran tenedor",
            min_value=2,
            max_value=20,
            value=5,
            step=1,
        )

    with col3:
        limite = st.slider(
            "Anfitriones a mostrar",
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

    resumen_df = get_resumen_anfitriones(
        ciudad=ciudad_param,
        umbral_gran_tenedor=umbral_gran_tenedor,
    )

    top_df = get_top_anfitriones(
        ciudad=ciudad_param,
        limite=limite,
    )

    superhost_df = get_superhost_disponibilidad(
        ciudad=ciudad_param,
    )

    tenedores_df = get_grandes_tenedores_precio(
        ciudad=ciudad_param,
        umbral_gran_tenedor=umbral_gran_tenedor,
    )

    if resumen_df.empty:
        st.warning("No hay datos disponibles para la selección realizada.")
        return

    resumen = resumen_df.iloc[0]

    # =========================
    # Respuestas principales
    # =========================
    st.subheader("Indicadores clave")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Anfitriones",
        format_number(resumen["total_anfitriones"]),
    )

    col2.metric(
        "Viviendas",
        format_number(resumen["total_viviendas"]),
    )

    col3.metric(
        "Grandes tenedores",
        format_number(resumen["total_grandes_tenedores"]),
    )

    col4.metric(
        "Viviendas en grandes tenedores",
        format_pct(resumen["pct_viviendas_grandes_tenedores"]),
        format_number(resumen["viviendas_grandes_tenedores"]),
    )

    st.caption(
        f"Umbral activo: gran tenedor = {umbral_gran_tenedor} o más viviendas."
    )

    st.divider()

    # =========================
    # Top anfitriones
    # =========================
    st.subheader("¿Qué anfitriones concentran más viviendas?")

    if not top_df.empty:
        df_top = crear_etiquetas_anfitrion(top_df)

        df_chart = df_top.sort_values("num_viviendas", ascending=True)

        fig_top = px.bar(
            df_chart,
            x="num_viviendas",
            y="etiqueta",
            orientation="h",
            text="num_viviendas",
            title=f"Top {limite} anfitriones por número de viviendas",
            labels={
                "num_viviendas": "Número de viviendas",
                "etiqueta": "Anfitrión",
            },
            hover_data={
                "es_superhost": True,
                "precio_medio_diario": ":.2f",
                "disponibilidad_pct": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "ingreso_potencial_total": ":.2f",
                "etiqueta": False,
            },
        )

        fig_top.update_traces(textposition="outside")

        fig_top.update_layout(
            height=max(450, limite * 34),
            xaxis_title="Número de viviendas",
            yaxis_title="Anfitrión",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_top, width="stretch")

    st.divider()

    # =========================
    # Superhost disponibilidad
    # =========================
    st.subheader("¿Los superhost tienen mayor disponibilidad o no disponibilidad?")

    if not superhost_df.empty:
        df_superhost_melt = superhost_df.melt(
            id_vars=["tipo_anfitrion", "num_anfitriones", "num_viviendas"],
            value_vars=["disponibilidad_pct", "no_disponibilidad_pct"],
            var_name="Métrica",
            value_name="Porcentaje",
        )

        df_superhost_melt["Métrica"] = df_superhost_melt["Métrica"].replace(
            {
                "disponibilidad_pct": "Disponibilidad",
                "no_disponibilidad_pct": "No disponibilidad",
            }
        )

        fig_superhost = px.bar(
            df_superhost_melt,
            x="tipo_anfitrion",
            y="Porcentaje",
            color="Métrica",
            barmode="group",
            text="Porcentaje",
            title="Disponibilidad y no disponibilidad según tipo de anfitrión",
            labels={
                "tipo_anfitrion": "Tipo de anfitrión",
                "Porcentaje": "Porcentaje (%)",
            },
        )

        fig_superhost.update_traces(
            texttemplate="%{text:.2f} %",
            textposition="outside",
        )

        fig_superhost.update_layout(
            height=450,
            yaxis_range=[0, 100],
            xaxis_title="",
            yaxis_title="Porcentaje (%)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_superhost, width="stretch")

    st.divider()

    # =========================
    # Grandes tenedores vs particulares
    # =========================
    st.subheader("¿Los grandes tenedores tienen precios más altos que los anfitriones particulares?")

    if not tenedores_df.empty:
        fig_precio = px.bar(
            tenedores_df,
            x="tipo_tenedor",
            y="precio_medio_diario",
            text="precio_medio_diario",
            title="Precio medio diario según tipo de tenedor",
            labels={
                "tipo_tenedor": "Tipo de anfitrión",
                "precio_medio_diario": "Precio medio diario (€)",
            },
            hover_data={
                "num_anfitriones": True,
                "num_viviendas": True,
                "disponibilidad_pct": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "ingreso_potencial_total": ":.2f",
            },
        )

        fig_precio.update_traces(
            texttemplate="%{text:.2f} €",
            textposition="outside",
        )

        fig_precio.update_layout(
            height=430,
            xaxis_title="",
            yaxis_title="Precio medio diario (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_precio, width="stretch")

        if len(tenedores_df) >= 2:
            mayor_precio = tenedores_df.sort_values(
                "precio_medio_diario",
                ascending=False,
            ).iloc[0]

            st.info(
                f"""
                El grupo con mayor precio medio diario es **{mayor_precio['tipo_tenedor']}**
                con **{format_currency_dec(mayor_precio['precio_medio_diario'])}**.
                """
            )

    st.divider()

    # =========================
    # Tabla detalle
    # =========================
    st.subheader("Tabla de detalle de anfitriones")

    if not top_df.empty:
        tabla = crear_etiquetas_anfitrion(top_df)

        tabla = tabla.rename(
            columns={
                "etiqueta": "Anfitrión",
                "es_superhost": "Superhost",
                "num_viviendas": "Nº viviendas",
                "precio_medio_diario": "Precio medio diario",
                "disponibilidad_pct": "Disponibilidad (%)",
                "no_disponibilidad_pct": "No disponibilidad (%)",
                "ingreso_potencial_total": "Ingreso potencial total",
            }
        )

        columnas = [
            "Anfitrión",
            "Superhost",
            "Nº viviendas",
            "Precio medio diario",
            "Disponibilidad (%)",
            "No disponibilidad (%)",
            "Ingreso potencial total",
        ]

        st.dataframe(
            tabla[columnas],
            width="stretch",
            hide_index=True,
        )

