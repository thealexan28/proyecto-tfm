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
    st.title("🏘️ Analysis by property type")

    st.markdown(
        """
        Compares price, availability, capacity, and potential revenue by room
        or property type.
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

    col_filter_1, col_filter_2, col_filter_3 = st.columns([2, 1, 1])

    with col_filter_1:
        ciudad_seleccionada = st.selectbox(
            "Select a city",
            options=["All cities"] + ciudades,
            index=0,
        )

    with col_filter_2:
        agrupar_opcion = st.selectbox(
            "Group analysis by",
            options=[
                "Room type",
                "Property type",
            ],
            index=0,
        )

    with col_filter_3:
        min_viviendas = st.slider(
            "Minimum properties per capacity",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
        )

    ciudad_param = (
        None
        if ciudad_seleccionada == "All cities"
        else ciudad_seleccionada
    )

    agrupar_por = (
        "tipo_habitacion"
        if agrupar_opcion == "Room type"
        else "tipo_propiedad"
    )
    etiqueta_agrupacion = (
        "room type"
        if agrupar_por == "tipo_habitacion"
        else "property type"
    )
    etiqueta_plural = (
        "Room types"
        if agrupar_por == "tipo_habitacion"
        else "Property types displayed"
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
        st.warning("No data is available for the selected filters.")
        return

    if agrupar_por == "tipo_propiedad":
        df_tipo = df_tipo.nlargest(20, "num_viviendas").copy()

    # =========================
    # Respuestas principales
    # =========================
    st.subheader("Key indicators")

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
        "Highest average price",
        tipo_mayor_precio["tipo_alojamiento"],
        format_currency_dec(tipo_mayor_precio["precio_medio_diario"]),
    )

    col2.metric(
        "Highest potential revenue",
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
        st.subheader("Entire homes vs private rooms")

        fila_completa = buscar_vivienda_completa(df_tipo)
        fila_privada = buscar_habitacion_privada(df_tipo)

        if fila_completa is not None and fila_privada is not None:
            diferencia_no_disp = (
                fila_completa["no_disponibilidad_pct"]
                - fila_privada["no_disponibilidad_pct"]
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Entire-home unavailability",
                format_pct(fila_completa["no_disponibilidad_pct"]),
            )

            col2.metric(
                "Private-room unavailability",
                format_pct(fila_privada["no_disponibilidad_pct"]),
            )

            col3.metric(
                "Difference",
                format_pct(diferencia_no_disp),
            )

            if diferencia_no_disp > 0:
                st.success(
                    "Entire homes have higher unavailability than private rooms."
                )
            elif diferencia_no_disp < 0:
                st.warning(
                    "Private rooms have higher unavailability than entire homes."
                )
            else:
                st.info(
                    "Both types have very similar unavailability."
                )

            df_comparacion = pd.DataFrame(
                {
                    "Type": [
                        fila_completa["tipo_alojamiento"],
                        fila_privada["tipo_alojamiento"],
                    ],
                    "Unavailability (%)": [
                        fila_completa["no_disponibilidad_pct"],
                        fila_privada["no_disponibilidad_pct"],
                    ],
                }
            )

            fig_comparacion = px.bar(
                df_comparacion,
                x="Type",
                y="Unavailability (%)",
                text="Unavailability (%)",
                title="Unavailability comparison",
                labels={
                    "Type": "Property type",
                    "Unavailability (%)": "Unavailability (%)",
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
                yaxis_title="Unavailability (%)",
                margin=dict(l=20, r=20, t=70, b=20),
            )

            st.plotly_chart(fig_comparacion, width="stretch")

        else:
            st.info(
                """
                Entire homes and private rooms were not both found under the expected
                names in the available data.
                """
            )
        st.divider()

    # =========================
    # Precio medio por tipo
    # =========================
    st.subheader(f"Which {etiqueta_agrupacion} has the highest average price?")

    df_precio = df_tipo.sort_values("precio_medio_diario", ascending=True)

    fig_precio = px.bar(
        df_precio,
        x="precio_medio_diario",
        y="tipo_alojamiento",
        orientation="h",
        text="precio_medio_diario",
        title=f"Average daily price by {etiqueta_agrupacion}",
        labels={
            "precio_medio_diario": "Average daily price (€)",
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
        xaxis_title="Average daily price (€)",
        yaxis_title=etiqueta_agrupacion.capitalize(),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_precio, width="stretch")

    st.divider()

    # =========================
    # Ingreso potencial por tipo
    # =========================
    st.subheader(f"Which {etiqueta_agrupacion} generates the most potential revenue?")

    df_ingreso = df_tipo.sort_values("ingreso_potencial_total", ascending=True)

    fig_ingreso = px.bar(
        df_ingreso,
        x="ingreso_potencial_total",
        y="tipo_alojamiento",
        orientation="h",
        text="ingreso_potencial_total",
        title=f"Total potential revenue by {etiqueta_agrupacion}",
        labels={
            "ingreso_potencial_total": "Total potential revenue (€)",
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
        xaxis_title="Total potential revenue (€)",
        yaxis_title=etiqueta_agrupacion.capitalize(),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_ingreso, width="stretch")

    st.divider()

    # =========================
    # Capacidad vs precio
    # =========================
    st.subheader("Do higher-capacity properties have a higher average price?")

    if df_capacidad.empty:
        st.info(
            "There is not enough capacity data for the selected minimum number of properties."
        )
    else:
        df_capacidad_linea = df_capacidad.sort_values("capacidad_huespedes").copy()

        fig_capacidad = px.line(
            df_capacidad_linea,
            x="capacidad_huespedes",
            y="precio_medio_diario",
            markers=True,
            title="Average price trend by property capacity",
            labels={
                "capacidad_huespedes": "Number of guests",
                "precio_medio_diario": "Average daily price (€)",
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
            xaxis_title="Number of guests",
            yaxis_title="Average daily price (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_capacidad, width="stretch")

        correlacion = df_capacidad["capacidad_huespedes"].corr(
            df_capacidad["precio_medio_diario"]
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Capacity-price correlation",
            f"{correlacion:.2f}" if not pd.isna(correlacion) else "-",
        )

        capacidad_mayor_precio = df_capacidad.sort_values(
            "precio_medio_diario",
            ascending=False,
        ).iloc[0]

        col2.metric(
            "Capacity with the highest average price",
            f"{int(capacidad_mayor_precio['capacidad_huespedes'])} guests",
            format_currency_dec(capacidad_mayor_precio["precio_medio_diario"]),
        )

        if not pd.isna(correlacion):
            if correlacion >= 0.6:
                st.success(
                    "There is a clear positive relationship: higher capacity is associated with a higher average price."
                )
            elif correlacion >= 0.3:
                st.info(
                    "There is a moderate positive relationship between capacity and average price."
                )
            elif correlacion > 0:
                st.info(
                    "There is a weak positive relationship between capacity and average price."
                )
            else:
                st.warning(
                    "No clear positive relationship between capacity and average price is observed."
                )

    st.divider()

    # =========================
    # Tabla detalle
    # =========================
    st.subheader(f"Details by {etiqueta_agrupacion}")

    tabla = df_tipo.copy()

    tabla = tabla.rename(
        columns={
            "tipo_alojamiento": etiqueta_agrupacion.capitalize(),
            "num_viviendas": "No. of properties",
            "registros_calendario": "Nights analyzed",
            "registros_con_precio": "Records with price",
            "precio_medio_diario": "Average daily price",
            "precio_mensualizado": "Monthly price",
            "no_disponibilidad_pct": "Unavailability (%)",
            "disponibilidad_pct": "Availability (%)",
            "ingreso_potencial_total": "Total potential revenue",
            "capacidad_media": "Average capacity",
        }
    )

    columnas = [
        etiqueta_agrupacion.capitalize(),
        "No. of properties",
        "Average daily price",
        "Monthly price",
        "Unavailability (%)",
        "Availability (%)",
        "Total potential revenue",
        "Average capacity",
        "Records with price",
        "Nights analyzed",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("Unavailability is used as a proxy for estimated occupancy.")
