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
    st.title("📈 Ocupación estimada por temporada")

    st.markdown(
        """
        Comparativa temporal de la no disponibilidad registrada en el calendario.
        Sirve para detectar picos estacionales y cambios mensuales en la presión de uso.
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

    col_filter_1, col_filter_2 = st.columns([2, 2])

    with col_filter_1:
        ciudad_seleccionada = st.selectbox(
            "Selecciona una ciudad",
            options=["Todas las ciudades"] + ciudades,
            index=0,
        )

    ciudad_param = None if ciudad_seleccionada == "Todas las ciudades" else ciudad_seleccionada

    barrio_param = None

    with col_filter_2:
        if ciudad_param is not None:
            barrios_df = get_barrios_disponibles_por_ciudad(ciudad_param)
            barrios = barrios_df["barrio"].dropna().sort_values().tolist()

            barrio_seleccionado = st.selectbox(
                "Selecciona un barrio",
                options=["Todos los barrios"] + barrios,
                index=0,
            )

            barrio_param = None if barrio_seleccionado == "Todos los barrios" else barrio_seleccionado
        else:
            st.selectbox(
                "Selecciona un barrio",
                options=["Selecciona primero una ciudad"],
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
        st.warning("No hay datos disponibles para la selección realizada.")
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
        "Ocupación estimada media",
        format_pct(ocupacion_media_ponderada),
    )

    col2.metric(
        "Temporada con mayor ocupación",
        fila_max["temporada"],
    )

    col3.metric(
        "Ocupación de esa temporada",
        format_pct(fila_max["ocupacion_estimada_pct"]),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Noches analizadas",
        format_number(total_registros),
    )

    col5.metric(
        "Noches no disponibles",
        format_number(total_noches_ocupadas),
    )

    col6.metric(
        "Disponibilidad media",
        format_pct(disponibilidad_media_ponderada),
    )

    st.divider()

    # =========================
    # Gráfico de barras por temporada
    # =========================
    st.subheader("Ocupación estimada por temporada")

    if ciudad_param is None:
        fig_bar = px.bar(
            df_temporada,
            x="temporada",
            y="ocupacion_estimada_pct",
            color="ciudad",
            barmode="group",
            text="ocupacion_estimada_pct",
            title="Ocupación estimada por temporada y ciudad",
            labels={
                "temporada": "Temporada",
                "ocupacion_estimada_pct": "Ocupación estimada (%)",
                "ciudad": "Ciudad",
            },
        )
    else:
        fig_bar = px.bar(
            df_temporada,
            x="temporada",
            y="ocupacion_estimada_pct",
            text="ocupacion_estimada_pct",
            title=f"Ocupación estimada por temporada en {ciudad_seleccionada}",
            labels={
                "temporada": "Temporada",
                "ocupacion_estimada_pct": "Ocupación estimada (%)",
            },
        )

    fig_bar.update_traces(
        texttemplate="%{text:.2f} %",
        textposition="outside",
    )

    fig_bar.update_layout(
        xaxis_title="Temporada",
        yaxis_title="Ocupación estimada (%)",
        yaxis_range=[0, 100],
        height=450,
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_bar, width="stretch")

    st.divider()

    # =========================
    # Línea mensual
    # =========================
    st.subheader("Evolución mensual de la ocupación estimada")

    if not df_mensual.empty:
        if ciudad_param is None:
            fig_line = px.line(
                df_mensual,
                x="periodo",
                y="ocupacion_estimada_pct",
                color="ciudad",
                markers=True,
                title="Evolución mensual de la ocupación estimada por ciudad",
                labels={
                    "periodo": "Mes",
                    "ocupacion_estimada_pct": "Ocupación estimada (%)",
                    "ciudad": "Ciudad",
                },
            )
        else:
            fig_line = px.line(
                df_mensual,
                x="periodo",
                y="ocupacion_estimada_pct",
                markers=True,
                title=f"Evolución mensual de la ocupación estimada en {ciudad_seleccionada}",
                labels={
                    "periodo": "Mes",
                    "ocupacion_estimada_pct": "Ocupación estimada (%)",
                },
            )

        fig_line.update_layout(
            xaxis_title="Mes",
            yaxis_title="Ocupación estimada (%)",
            yaxis_range=[0, 100],
            height=450,
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_line, width="stretch")
    else:
        st.info("No hay datos mensuales disponibles para la selección realizada.")

    st.divider()

    # =========================
    # Tabla de detalle por temporada
    # =========================
    st.subheader("Tabla de detalle por temporada")

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

    st.caption("La ocupación estimada representa noches no disponibles en el calendario.")
