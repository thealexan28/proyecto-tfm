import streamlit as st
import plotly.express as px

from backend.queries import (
    get_ciudades_disponibles,
    get_barrios_disponibles_por_ciudad,
    get_ocupacion_por_temporada,
    get_ocupacion_mensual,
)


def format_number(value):
    if value is None:
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_pct(value):
    if value is None:
        return "-"

    return f"{value:.2f} %"


def render_ocupacion_temporada():
    st.title("📈 Estimated occupancy by season")

    st.markdown(
        """
        Time-based comparison of unavailability recorded in the calendar.
        It helps identify seasonal peaks and monthly changes in usage pressure.
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

    col_filter_1, col_filter_2 = st.columns([2, 2])

    with col_filter_1:
        ciudad_seleccionada = st.selectbox(
            "Select a city",
            options=["All cities"] + ciudades,
            index=0,
        )

    ciudad_param = None if ciudad_seleccionada == "All cities" else ciudad_seleccionada

    barrio_param = None

    with col_filter_2:
        if ciudad_param is not None:
            barrios_df = get_barrios_disponibles_por_ciudad(ciudad_param)
            barrios = barrios_df["barrio"].dropna().sort_values().tolist()

            barrio_seleccionado = st.selectbox(
                "Select a neighborhood",
                options=["All neighborhoods"] + barrios,
                index=0,
            )

            barrio_param = None if barrio_seleccionado == "All neighborhoods" else barrio_seleccionado
        else:
            st.selectbox(
                "Select a neighborhood",
                options=["Select a city first"],
                index=0,
                disabled=True,
            )

    # =========================
    # Carga de datos
    # =========================
    df_temporada = get_ocupacion_por_temporada(
        ciudad=ciudad_param,
        barrio=barrio_param,
    )

    df_mensual = get_ocupacion_mensual(
        ciudad=ciudad_param,
        barrio=barrio_param,
    )

    if df_temporada.empty:
        st.warning("No data is available for the selected filters.")
        return

    # =========================
    # KPIs generales
    # =========================
    total_registros = df_temporada["registros_calendario"].sum()
    total_noches_ocupadas = df_temporada["noches_ocupadas_estimadas"].sum()
    total_noches_disponibles = df_temporada["noches_disponibles"].sum()

    ocupacion_media_ponderada = (
        total_noches_ocupadas * 100 / total_registros
        if total_registros > 0
        else None
    )

    disponibilidad_media_ponderada = (
        total_noches_disponibles * 100 / total_registros
        if total_registros > 0
        else None
    )

    fila_max = df_temporada.sort_values("ocupacion_estimada_pct", ascending=False).iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average estimated occupancy",
        format_pct(ocupacion_media_ponderada),
    )

    col2.metric(
        "Season with the highest occupancy",
        fila_max["temporada"],
    )

    col3.metric(
        "Occupancy in that season",
        format_pct(fila_max["ocupacion_estimada_pct"]),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Nights analyzed",
        format_number(total_registros),
    )

    col5.metric(
        "Unavailable nights",
        format_number(total_noches_ocupadas),
    )

    col6.metric(
        "Average availability",
        format_pct(disponibilidad_media_ponderada),
    )

    st.divider()

    # =========================
    # Gráfico de barras por temporada
    # =========================
    st.subheader("Estimated occupancy by season")

    if ciudad_param is None:
        fig_bar = px.bar(
            df_temporada,
            x="temporada",
            y="ocupacion_estimada_pct",
            color="ciudad",
            barmode="group",
            text="ocupacion_estimada_pct",
            title="Estimated occupancy by season and city",
            labels={
                "temporada": "Season",
                "ocupacion_estimada_pct": "Estimated occupancy (%)",
                "ciudad": "City",
            },
        )
    else:
        fig_bar = px.bar(
            df_temporada,
            x="temporada",
            y="ocupacion_estimada_pct",
            text="ocupacion_estimada_pct",
            title=f"Estimated occupancy by season in {ciudad_seleccionada}",
            labels={
                "temporada": "Season",
                "ocupacion_estimada_pct": "Estimated occupancy (%)",
            },
        )

    fig_bar.update_traces(
        texttemplate="%{text:.2f} %",
        textposition="outside",
    )

    fig_bar.update_layout(
        xaxis_title="Season",
        yaxis_title="Estimated occupancy (%)",
        yaxis_range=[0, 100],
        height=450,
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_bar, width="stretch")

    st.divider()

    # =========================
    # Línea mensual
    # =========================
    st.subheader("Monthly estimated occupancy trend")

    if not df_mensual.empty:
        if ciudad_param is None:
            fig_line = px.line(
                df_mensual,
                x="periodo",
                y="ocupacion_estimada_pct",
                color="ciudad",
                markers=True,
                title="Monthly estimated occupancy trend by city",
                labels={
                    "periodo": "Month",
                    "ocupacion_estimada_pct": "Estimated occupancy (%)",
                    "ciudad": "City",
                },
            )
        else:
            fig_line = px.line(
                df_mensual,
                x="periodo",
                y="ocupacion_estimada_pct",
                markers=True,
                title=f"Monthly estimated occupancy trend in {ciudad_seleccionada}",
                labels={
                    "periodo": "Month",
                    "ocupacion_estimada_pct": "Estimated occupancy (%)",
                },
            )

        fig_line.update_layout(
            xaxis_title="Month",
            yaxis_title="Estimated occupancy (%)",
            yaxis_range=[0, 100],
            height=450,
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_line, width="stretch")
    else:
        st.info("No monthly data is available for the selected filters.")

    st.divider()

    # =========================
    # Tabla de detalle por temporada
    # =========================
    st.subheader("Detailed table by season")

    tabla = df_temporada.copy()

    tabla = tabla.rename(
        columns={
            "ciudad": "Ciudad",
            "temporada": "Temporada",
            "registros_calendario": "Noches analizadas",
            "num_viviendas": "Nº viviendas",
            "noches_ocupadas_estimadas": "Noches no disponibles",
            "noches_disponibles": "Noches disponibles",
            "ocupacion_estimada_pct": "Ocupación estimada (%)",
            "disponibilidad_pct": "Disponibilidad (%)",
            "precio_medio_diario": "Precio medio diario",
            "ingreso_potencial_total": "Ingreso potencial total",
        }
    )

    columnas = [
        "Ciudad",
        "Temporada",
        "Nº viviendas",
        "Noches analizadas",
        "Noches no disponibles",
        "Noches disponibles",
        "Ocupación estimada (%)",
        "Disponibilidad (%)",
        "Precio medio diario",
        "Ingreso potencial total",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("Estimated occupancy represents nights marked as unavailable in the calendar.")
