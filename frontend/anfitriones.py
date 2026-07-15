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
    nombres = df["nombre_anfitrion"].fillna("Unnamed")
    nombres_duplicados = nombres.duplicated(keep=False)
    ids = df["id_anfitrion"].apply(
        lambda value: str(int(value)) if pd.notna(value) else "unknown"
    )
    df["etiqueta"] = nombres.where(
        ~nombres_duplicados,
        nombres + " (ID " + ids + ")",
    )
    return df


def render_anfitriones():
    st.title("👤 Host analysis")

    st.markdown(
        """
        Analyzes property concentration by host and compares prices,
        availability, and potential revenue across management profiles.
        """
    )

    st.divider()

    ciudades_df = get_ciudades_disponibles()

    if ciudades_df.empty:
        st.warning("No cities are available in the database.")
        return

    ciudades = ciudades_df["ciudad"].dropna().sort_values().tolist()

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        ciudad_seleccionada = st.selectbox(
            "Select a city",
            options=["All cities"] + ciudades,
            index=0,
        )

    with col2:
        umbral_gran_tenedor = st.slider(
            "Large-scale owner threshold",
            min_value=2,
            max_value=20,
            value=5,
            step=1,
        )

    with col3:
        limite = st.slider(
            "Hosts to display",
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
        st.warning("No data is available for the selected filters.")
        return

    resumen = resumen_df.iloc[0]

    # =========================
    # Respuestas principales
    # =========================
    st.subheader("Key indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Hosts",
        format_number(resumen["total_anfitriones"]),
    )

    col2.metric(
        "Properties",
        format_number(resumen["total_viviendas"]),
    )

    col3.metric(
        "Large-scale owners",
        format_number(resumen["total_grandes_tenedores"]),
    )

    col4.metric(
        "Properties managed by large-scale owners",
        format_pct(resumen["pct_viviendas_grandes_tenedores"]),
        format_number(resumen["viviendas_grandes_tenedores"]),
    )

    st.caption(
        f"Active threshold: large-scale owner = {umbral_gran_tenedor} or more properties."
    )

    st.divider()

    # =========================
    # Top anfitriones
    # =========================
    st.subheader("Which hosts manage the most properties?")

    if not top_df.empty:
        df_top = crear_etiquetas_anfitrion(top_df)

        df_chart = df_top.sort_values("num_viviendas", ascending=True)

        fig_top = px.bar(
            df_chart,
            x="num_viviendas",
            y="etiqueta",
            orientation="h",
            text="num_viviendas",
            title=f"Top {limite} hosts by number of properties",
            labels={
                "num_viviendas": "Number of properties",
                "etiqueta": "Host",
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
            xaxis_title="Number of properties",
            yaxis_title="Host",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_top, width="stretch")

    st.divider()

    # =========================
    # Superhost disponibilidad
    # =========================
    st.subheader("Do Superhosts have higher availability or unavailability?")

    if not superhost_df.empty:
        df_superhost_melt = superhost_df.melt(
            id_vars=["tipo_anfitrion", "num_anfitriones", "num_viviendas"],
            value_vars=["disponibilidad_pct", "no_disponibilidad_pct"],
            var_name="Metric",
            value_name="Percentage",
        )

        df_superhost_melt["Metric"] = df_superhost_melt["Metric"].replace(
            {
                "disponibilidad_pct": "Availability",
                "no_disponibilidad_pct": "Unavailability",
            }
        )

        fig_superhost = px.bar(
            df_superhost_melt,
            x="tipo_anfitrion",
            y="Percentage",
            color="Metric",
            barmode="group",
            text="Percentage",
            title="Availability and unavailability by host type",
            labels={
                "tipo_anfitrion": "Host type",
                "Percentage": "Percentage (%)",
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
            yaxis_title="Percentage (%)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_superhost, width="stretch")

    st.divider()

    # =========================
    # Grandes tenedores vs particulares
    # =========================
    st.subheader("Do large-scale owners charge higher prices than individual hosts?")

    if not tenedores_df.empty:
        fig_precio = px.bar(
            tenedores_df,
            x="tipo_tenedor",
            y="precio_medio_diario",
            text="precio_medio_diario",
            title="Average daily price by owner type",
            labels={
                "tipo_tenedor": "Host type",
                "precio_medio_diario": "Average daily price (€)",
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
            yaxis_title="Average daily price (€)",
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
                The group with the highest average daily price is **{mayor_precio['tipo_tenedor']}**
                at **{format_currency_dec(mayor_precio['precio_medio_diario'])}**.
                """
            )

    st.divider()

    # =========================
    # Tabla detalle
    # =========================
    st.subheader("Detailed host table")

    if not top_df.empty:
        tabla = crear_etiquetas_anfitrion(top_df)

        tabla = tabla.rename(
            columns={
                "etiqueta": "Host",
                "es_superhost": "Superhost",
                "num_viviendas": "No. of properties",
                "precio_medio_diario": "Average daily price",
                "disponibilidad_pct": "Availability (%)",
                "no_disponibilidad_pct": "Unavailability (%)",
                "ingreso_potencial_total": "Total potential revenue",
            }
        )

        columnas = [
            "Host",
            "Superhost",
            "No. of properties",
            "Average daily price",
            "Availability (%)",
            "Unavailability (%)",
            "Total potential revenue",
        ]

        st.dataframe(
            tabla[columnas],
            width="stretch",
            hide_index=True,
        )

