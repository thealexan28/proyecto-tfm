import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_ciudades_disponibles,
    get_analisis_tipo_alojamiento,
    get_precio_por_capacidad,
)


def format_currency(value):
    if pd.isna(value):
        return "-"

    return f"{value:,.0f} €".replace(",", ".")


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


def normalizar_texto(value):
    if pd.isna(value):
        return ""

    return str(value).lower().strip()


def buscar_vivienda_completa(df):
    for _, row in df.iterrows():
        tipo = normalizar_texto(row["tipo_alojamiento"])

        if "entire" in tipo or "complet" in tipo or "vivienda" in tipo:
            return row

    return None


def buscar_habitacion_privada(df):
    for _, row in df.iterrows():
        tipo = normalizar_texto(row["tipo_alojamiento"])

        if "private" in tipo or "privad" in tipo:
            return row

    return None


def render_tipo_alojamiento():
    st.title("🏘️ Análisis por tipo de alojamiento")

    st.markdown(
        """
        Compara precio, disponibilidad, capacidad e ingreso potencial por tipo de
        habitación o propiedad.
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

    col_filter_1, col_filter_2, col_filter_3 = st.columns([2, 1, 1])

    with col_filter_1:
        ciudad_seleccionada = st.selectbox(
            "Selecciona una ciudad",
            options=["Todas las ciudades"] + ciudades,
            index=0,
        )

    with col_filter_2:
        agrupar_opcion = st.selectbox(
            "Agrupar análisis por",
            options=[
                "Tipo de habitación",
                "Tipo de propiedad",
            ],
            index=0,
        )

    with col_filter_3:
        min_viviendas = st.slider(
            "Mínimo viviendas por capacidad",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
        )

    ciudad_param = (
        None
        if ciudad_seleccionada == "Todas las ciudades"
        else ciudad_seleccionada
    )

    agrupar_por = (
        "tipo_habitacion"
        if agrupar_opcion == "Tipo de habitación"
        else "tipo_propiedad"
    )
    etiqueta_agrupacion = (
        "tipo de habitación"
        if agrupar_por == "tipo_habitacion"
        else "tipo de propiedad"
    )
    etiqueta_plural = (
        "Tipos de habitación"
        if agrupar_por == "tipo_habitacion"
        else "Tipos de propiedad mostrados"
    )

    # =========================
    # Carga de datos
    # =========================
    df_tipo = get_analisis_tipo_alojamiento(
        ciudad=ciudad_param,
        agrupar_por=agrupar_por,
    )

    df_capacidad = get_precio_por_capacidad(
        ciudad=ciudad_param,
        min_viviendas=min_viviendas,
    )

    if df_tipo.empty:
        st.warning("No hay datos disponibles para la selección realizada.")
        return

    if agrupar_por == "tipo_propiedad":
        df_tipo = df_tipo.nlargest(20, "num_viviendas").copy()

    # =========================
    # Respuestas principales
    # =========================
    st.subheader("Indicadores clave")

    tipo_mayor_precio = df_tipo.sort_values(
        "precio_medio_diario",
        ascending=False,
    ).iloc[0]

    tipo_mayor_ingreso = df_tipo.sort_values(
        "ingreso_potencial_total",
        ascending=False,
    ).iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mayor precio medio",
        tipo_mayor_precio["tipo_alojamiento"],
        format_currency_dec(tipo_mayor_precio["precio_medio_diario"]),
    )

    col2.metric(
        "Mayor ingreso potencial",
        tipo_mayor_ingreso["tipo_alojamiento"],
        format_currency(tipo_mayor_ingreso["ingreso_potencial_total"]),
    )

    col3.metric(
        etiqueta_plural,
        format_number(len(df_tipo)),
    )

    st.divider()

    # =========================
    # Comparación viviendas completas vs habitaciones privadas
    # =========================
    if agrupar_por == "tipo_habitacion":
        st.subheader("Viviendas completas frente a habitaciones privadas")

        fila_completa = buscar_vivienda_completa(df_tipo)
        fila_privada = buscar_habitacion_privada(df_tipo)

        if fila_completa is not None and fila_privada is not None:
            diferencia_no_disp = (
                fila_completa["no_disponibilidad_pct"]
                - fila_privada["no_disponibilidad_pct"]
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "No disponibilidad viviendas completas",
                format_pct(fila_completa["no_disponibilidad_pct"]),
            )

            col2.metric(
                "No disponibilidad habitaciones privadas",
                format_pct(fila_privada["no_disponibilidad_pct"]),
            )

            col3.metric(
                "Diferencia",
                format_pct(diferencia_no_disp),
            )

            if diferencia_no_disp > 0:
                st.success(
                    "Las viviendas completas presentan mayor no disponibilidad que las habitaciones privadas."
                )
            elif diferencia_no_disp < 0:
                st.warning(
                    "Las habitaciones privadas presentan mayor no disponibilidad que las viviendas completas."
                )
            else:
                st.info(
                    "Ambos tipos presentan una no disponibilidad muy similar."
                )

            df_comparacion = pd.DataFrame(
                {
                    "Tipo": [
                        fila_completa["tipo_alojamiento"],
                        fila_privada["tipo_alojamiento"],
                    ],
                    "No disponibilidad (%)": [
                        fila_completa["no_disponibilidad_pct"],
                        fila_privada["no_disponibilidad_pct"],
                    ],
                }
            )

            fig_comparacion = px.bar(
                df_comparacion,
                x="Tipo",
                y="No disponibilidad (%)",
                text="No disponibilidad (%)",
                title="Comparación de no disponibilidad",
                labels={
                    "Tipo": "Tipo de alojamiento",
                    "No disponibilidad (%)": "No disponibilidad (%)",
                },
            )

            fig_comparacion.update_traces(
                texttemplate="%{text:.2f} %",
                textposition="outside",
            )

            fig_comparacion.update_layout(
                height=420,
                yaxis_range=[0, 100],
                xaxis_title="",
                yaxis_title="No disponibilidad (%)",
                margin=dict(l=20, r=20, t=70, b=20),
            )

            st.plotly_chart(fig_comparacion, width="stretch")

        else:
            st.info(
                """
                No se han encontrado simultáneamente viviendas completas y habitaciones privadas
                con los nombres esperados en los datos disponibles.
                """
            )
        st.divider()

    # =========================
    # Precio medio por tipo
    # =========================
    st.subheader(f"¿Qué {etiqueta_agrupacion} tiene mayor precio medio?")

    df_precio = df_tipo.sort_values("precio_medio_diario", ascending=True)

    fig_precio = px.bar(
        df_precio,
        x="precio_medio_diario",
        y="tipo_alojamiento",
        orientation="h",
        text="precio_medio_diario",
        title=f"Precio medio diario por {etiqueta_agrupacion}",
        labels={
            "precio_medio_diario": "Precio medio diario (€)",
            "tipo_alojamiento": etiqueta_agrupacion.capitalize(),
        },
        hover_data={
            "num_viviendas": True,
            "capacidad_media": ":.2f",
            "precio_mensualizado": ":.2f",
            "tipo_alojamiento": False,
        },
    )

    fig_precio.update_traces(
        texttemplate="%{text:,.2f} €",
        textposition="outside",
    )

    fig_precio.update_layout(
        height=max(420, len(df_precio) * 45),
        xaxis_title="Precio medio diario (€)",
        yaxis_title=etiqueta_agrupacion.capitalize(),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_precio, width="stretch")

    st.divider()

    # =========================
    # Ingreso potencial por tipo
    # =========================
    st.subheader(f"¿Qué {etiqueta_agrupacion} genera más ingreso potencial?")

    df_ingreso = df_tipo.sort_values("ingreso_potencial_total", ascending=True)

    fig_ingreso = px.bar(
        df_ingreso,
        x="ingreso_potencial_total",
        y="tipo_alojamiento",
        orientation="h",
        text="ingreso_potencial_total",
        title=f"Ingreso potencial total por {etiqueta_agrupacion}",
        labels={
            "ingreso_potencial_total": "Ingreso potencial total (€)",
            "tipo_alojamiento": etiqueta_agrupacion.capitalize(),
        },
        hover_data={
            "num_viviendas": True,
            "precio_medio_diario": ":.2f",
            "no_disponibilidad_pct": ":.2f",
            "tipo_alojamiento": False,
        },
    )

    fig_ingreso.update_traces(
        texttemplate="%{text:,.0f} €",
        textposition="outside",
    )

    fig_ingreso.update_layout(
        height=max(420, len(df_ingreso) * 45),
        xaxis_title="Ingreso potencial total (€)",
        yaxis_title=etiqueta_agrupacion.capitalize(),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_ingreso, width="stretch")

    st.divider()

    # =========================
    # Capacidad vs precio
    # =========================
    st.subheader("¿Los alojamientos con mayor capacidad tienen mayor precio medio?")

    if df_capacidad.empty:
        st.info(
            "No hay datos suficientes por capacidad con el mínimo de viviendas seleccionado."
        )
    else:
        df_capacidad_linea = df_capacidad.sort_values("capacidad_huespedes").copy()

        fig_capacidad = px.line(
            df_capacidad_linea,
            x="capacidad_huespedes",
            y="precio_medio_diario",
            markers=True,
            title="Evolución del precio medio según la capacidad del alojamiento",
            labels={
                "capacidad_huespedes": "Número de huéspedes",
                "precio_medio_diario": "Precio medio diario (€)",
            },
            hover_data={
                "num_viviendas": True,
                "precio_mensualizado": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "ingreso_potencial_total": ":.2f",
            },
        )

        fig_capacidad.update_traces(
            mode="lines+markers",
        )

        fig_capacidad.update_layout(
            height=500,
            xaxis_title="Número de huéspedes",
            yaxis_title="Precio medio diario (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_capacidad, width="stretch")

        correlacion = df_capacidad["capacidad_huespedes"].corr(
            df_capacidad["precio_medio_diario"]
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Correlación capacidad-precio",
            f"{correlacion:.2f}" if not pd.isna(correlacion) else "-",
        )

        capacidad_mayor_precio = df_capacidad.sort_values(
            "precio_medio_diario",
            ascending=False,
        ).iloc[0]

        col2.metric(
            "Capacidad con mayor precio medio",
            f"{int(capacidad_mayor_precio['capacidad_huespedes'])} huéspedes",
            format_currency_dec(capacidad_mayor_precio["precio_medio_diario"]),
        )

        if not pd.isna(correlacion):
            if correlacion >= 0.6:
                st.success(
                    "Existe una relación positiva clara: a mayor capacidad, mayor precio medio."
                )
            elif correlacion >= 0.3:
                st.info(
                    "Existe una relación positiva moderada entre capacidad y precio medio."
                )
            elif correlacion > 0:
                st.info(
                    "Existe una relación positiva débil entre capacidad y precio medio."
                )
            else:
                st.warning(
                    "No se observa una relación positiva clara entre capacidad y precio medio."
                )

    st.divider()

    # =========================
    # Tabla detalle
    # =========================
    st.subheader(f"Detalle por {etiqueta_agrupacion}")

    tabla = df_tipo.copy()

    tabla = tabla.rename(
        columns={
            "tipo_alojamiento": etiqueta_agrupacion.capitalize(),
            "num_viviendas": "Nº viviendas",
            "registros_calendario": "Noches analizadas",
            "registros_con_precio": "Registros con precio",
            "precio_medio_diario": "Precio medio diario",
            "precio_mensualizado": "Precio mensualizado",
            "no_disponibilidad_pct": "No disponibilidad (%)",
            "disponibilidad_pct": "Disponibilidad (%)",
            "ingreso_potencial_total": "Ingreso potencial total",
            "capacidad_media": "Capacidad media",
        }
    )

    columnas = [
        etiqueta_agrupacion.capitalize(),
        "Nº viviendas",
        "Precio medio diario",
        "Precio mensualizado",
        "No disponibilidad (%)",
        "Disponibilidad (%)",
        "Ingreso potencial total",
        "Capacidad media",
        "Registros con precio",
        "Noches analizadas",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("La no disponibilidad se usa como aproximación de ocupación estimada.")
