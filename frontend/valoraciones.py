import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_ciudades_disponibles,
    get_barrios_mejor_valorados,
    get_valoraciones_viviendas,
    get_reserva_instantanea_disponibilidad,
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


def crear_orden_volumen_resenas(df):
    """
    Converts the categorical volumen_resenas field into a numeric order
    so a trend can be plotted.
    """

    df = df.copy()

    def calcular_orden(valor):
        if pd.isna(valor):
            return 99

        texto = str(valor).lower().strip()

        if "sin" in texto or texto == "0":
            return 0

        if "bajo" in texto or "poca" in texto or "1" in texto:
            return 1

        if "medio" in texto or "moderado" in texto:
            return 2

        if "alto" in texto and "muy" not in texto:
            return 3

        if "muy" in texto:
            return 4

        return 50

    df["volumen_resenas"] = df["volumen_resenas"].fillna("Unclassified")
    df["orden_volumen"] = df["volumen_resenas"].apply(calcular_orden)

    return df


def excluir_precios_atipicos(df):
    precios = df["precio_medio_diario"].dropna()
    if precios.empty:
        return df.copy()

    q1 = precios.quantile(0.25)
    q3 = precios.quantile(0.75)
    limite_superior = q3 + 1.5 * (q3 - q1)

    return df[
        df["precio_medio_diario"].notna()
        & (df["precio_medio_diario"] <= limite_superior)
    ].copy()


def crear_muestra_scatter(df, max_por_ciudad=250):
    muestras = []

    for _, grupo in df.groupby("ciudad", dropna=False):
        muestras.append(
            grupo.sample(
                n=min(len(grupo), max_por_ciudad),
                random_state=42,
            )
        )

    if not muestras:
        return df.copy()

    return pd.concat(muestras, ignore_index=True)


def render_valoraciones():
    st.title("⭐ Ratings analysis")

    st.markdown(
        """
        Explores the relationship between ratings, price, availability, review
        volume, and instant booking.
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

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        ciudad_seleccionada = st.selectbox(
            "Select a city",
            options=["All cities"] + ciudades,
            index=0,
        )

    with col2:
        limite = st.slider(
            "Neighborhoods to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    with col3:
        min_viviendas = st.slider(
            "Minimum properties per neighborhood",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
        )

    ciudad_param = (
        None
        if ciudad_seleccionada == "All cities"
        else ciudad_seleccionada
    )

    # =========================
    # Carga de datos
    # =========================
    barrios_df = get_barrios_mejor_valorados(
        ciudad=ciudad_param,
        limite=limite,
        min_viviendas=min_viviendas,
    )

    viviendas_df = get_valoraciones_viviendas(
        ciudad=ciudad_param,
    )

    reserva_df = get_reserva_instantanea_disponibilidad(
        ciudad=ciudad_param,
    )

    if viviendas_df.empty:
        st.warning("No rating data is available for the selected filters.")
        return

    viviendas_volumen_df = crear_orden_volumen_resenas(viviendas_df)
    viviendas_precio_df = excluir_precios_atipicos(viviendas_df)
    viviendas_scatter_df = crear_muestra_scatter(viviendas_precio_df)

    # =========================
    # KPIs principales
    # =========================
    st.subheader("Key indicators")

    puntuacion_media = viviendas_df["puntuacion_general"].mean()
    precio_medio = viviendas_df["precio_medio_diario"].mean()
    no_disp_media = viviendas_df["no_disponibilidad_pct"].mean()

    corr_puntuacion_precio = viviendas_precio_df["puntuacion_general"].corr(
        viviendas_precio_df["precio_medio_diario"]
    )

    corr_resenas_no_disp = viviendas_volumen_df["orden_volumen"].corr(
        viviendas_volumen_df["no_disponibilidad_pct"]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Average rating",
        f"{puntuacion_media:.2f}" if not pd.isna(puntuacion_media) else "-",
    )

    col2.metric(
        "Average price",
        format_currency_dec(precio_medio),
    )

    col3.metric(
        "Average unavailability",
        format_pct(no_disp_media),
    )

    col4.metric(
        "Rated properties",
        format_number(len(viviendas_df)),
    )

    col5, col6 = st.columns(2)

    col5.metric(
        "Rating-price correlation",
        f"{corr_puntuacion_precio:.2f}" if not pd.isna(corr_puntuacion_precio) else "-",
    )

    col6.metric(
        "Reviews-unavailability correlation",
        f"{corr_resenas_no_disp:.2f}" if not pd.isna(corr_resenas_no_disp) else "-",
    )

    st.divider()

    # =========================
    # Barrios mejor valorados
    # =========================
    st.subheader("Which neighborhoods have the highest-rated properties?")

    if not barrios_df.empty:
        if ciudad_param is None:
            barrios_df["zona"] = barrios_df["barrio"] + " (" + barrios_df["ciudad"] + ")"
        else:
            barrios_df["zona"] = barrios_df["barrio"]

        df_chart = barrios_df.sort_values("puntuacion_media", ascending=True)

        fig_barrios = px.bar(
            df_chart,
            x="puntuacion_media",
            y="zona",
            orientation="h",
            text="puntuacion_media",
            title=f"Top {limite} neighborhoods by average rating",
            labels={
                "puntuacion_media": "Average rating",
                "zona": "Neighborhood",
            },
            hover_data={
                "num_viviendas": True,
                "precio_medio_diario": ":.2f",
                "disponibilidad_pct": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "zona": False,
            },
        )

        fig_barrios.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )

        fig_barrios.update_layout(
            height=max(450, limite * 34),
            xaxis_title="Average rating",
            yaxis_title="Neighborhood",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_barrios, width="stretch")

        st.caption(
            "The ranking only includes neighborhoods that meet the selected minimum property count."
        )

    else:
        st.info("Not enough neighborhoods meet the selected minimum property count.")

    st.divider()

    # =========================
    # Puntuación vs precio
    # =========================
    st.subheader("Is there a relationship between average rating and price?")

    fig_precio = px.scatter(
        viviendas_scatter_df,
        x="puntuacion_general",
        y="precio_medio_diario",
        hover_name="nombre_anuncio",
        color="ciudad" if ciudad_param is None else None,
        color_discrete_map={
            "Madrid": "#2F7DF6",
            "Málaga": "#13B96B",
            "Sevilla": "#FF7A1A",
            "Valencia": "#A855F7",
        },
        opacity=0.85,
        render_mode="webgl",
        title="Relationship between overall rating and average daily price",
        labels={
            "puntuacion_general": "Overall rating",
            "precio_medio_diario": "Average daily price (€)",
            "ciudad": "City",
        },
        hover_data={
            "barrio": True,
            "volumen_resenas": True,
            "disponibilidad_pct": ":.2f",
            "no_disponibilidad_pct": ":.2f",
        },
    )

    fig_precio.update_traces(
        marker={
            "size": 7,
            "line": {"width": 0},
        }
    )

    fig_precio.update_layout(
        height=500,
        xaxis_title="Overall rating",
        yaxis_title="Average daily price (€)",
        legend_title_text="City",
        hovermode="closest",
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_precio, width="stretch")
    st.caption(
        "Reproducible sample of up to 250 properties per city; "
        "the correlation is calculated using all valid records."
    )

    if not pd.isna(corr_puntuacion_precio):
        if corr_puntuacion_precio >= 0.4:
            st.success("A positive relationship between rating and price is observed.")
        elif corr_puntuacion_precio > 0:
            st.info("The relationship between rating and price is positive but weak.")
        elif corr_puntuacion_precio < 0:
            st.warning("No positive relationship is observed; the correlation is negative.")
        else:
            st.info("No clear relationship between rating and price is observed.")

    st.divider()

    # =========================
    # Volumen de reseñas vs no disponibilidad
    # =========================
    st.subheader("Do properties with more reviews have higher unavailability?")

    tramos_df = (
        viviendas_volumen_df.groupby(["volumen_resenas", "orden_volumen"], observed=True)
        .agg(
            num_viviendas=("id_vivienda", "nunique"),
            no_disponibilidad_pct=("no_disponibilidad_pct", "mean"),
            precio_medio_diario=("precio_medio_diario", "mean"),
        )
        .reset_index()
        .sort_values("orden_volumen")
    )

    fig_resenas = px.line(
        tramos_df,
        x="volumen_resenas",
        y="no_disponibilidad_pct",
        markers=True,
        title="Average unavailability by review volume",
        labels={
            "volumen_resenas": "Review volume",
            "no_disponibilidad_pct": "Average unavailability (%)",
        },
        hover_data={
            "num_viviendas": True,
            "precio_medio_diario": ":.2f",
        },
    )

    fig_resenas.update_traces(mode="lines+markers")

    fig_resenas.update_layout(
        height=470,
        xaxis_title="Review volume",
        yaxis_title="Average unavailability (%)",
        yaxis_range=[0, 100],
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_resenas, width="stretch")

    if not pd.isna(corr_resenas_no_disp):
        if corr_resenas_no_disp >= 0.4:
            st.success(
                "Properties with more reviews tend to have higher unavailability."
            )
        elif corr_resenas_no_disp > 0:
            st.info(
                "The relationship between review volume and unavailability is positive but weak."
            )
        elif corr_resenas_no_disp < 0:
            st.warning(
                "No positive relationship is observed; the correlation is negative."
            )
        else:
            st.info("No clear relationship between review volume and unavailability is observed.")

    st.divider()

    # =========================
    # Reserva instantánea
    # =========================
    st.subheader("Do properties with instant booking have higher availability?")

    if not reserva_df.empty:
        reserva_melt = reserva_df.melt(
            id_vars=["tipo_reserva", "num_viviendas"],
            value_vars=["disponibilidad_pct", "no_disponibilidad_pct"],
            var_name="Metric",
            value_name="Percentage",
        )

        reserva_melt["Metric"] = reserva_melt["Metric"].replace(
            {
                "disponibilidad_pct": "Availability",
                "no_disponibilidad_pct": "Unavailability",
            }
        )

        fig_reserva = px.bar(
            reserva_melt,
            x="tipo_reserva",
            y="Percentage",
            color="Metric",
            barmode="group",
            text="Percentage",
            title="Availability by instant-booking status",
            labels={
                "tipo_reserva": "Booking type",
                "Percentage": "Percentage (%)",
            },
        )

        fig_reserva.update_traces(
            texttemplate="%{text:.2f} %",
            textposition="outside",
        )

        fig_reserva.update_layout(
            height=450,
            yaxis_range=[0, 100],
            xaxis_title="",
            yaxis_title="Percentage (%)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_reserva, width="stretch")

        if len(reserva_df) >= 2:
            mayor_disp = reserva_df.sort_values(
                "disponibilidad_pct",
                ascending=False,
            ).iloc[0]

            st.info(
                f"""
                The group with the highest average availability is **{mayor_disp['tipo_reserva']}**
                at **{format_pct(mayor_disp['disponibilidad_pct'])}**.
                """
            )

    else:
        st.info("There is not enough instant-booking data.")

    st.divider()

    # =========================
    # Tabla detalle
    # =========================
    st.subheader("Detailed table of rated properties")

    tabla = viviendas_df.copy()

    tabla = tabla.rename(
        columns={
            "ciudad": "City",
            "barrio": "Neighborhood",
            "nombre_anuncio": "Property",
            "puntuacion_general": "Overall rating",
            "volumen_resenas": "Review volume",
            "reserva_instantanea": "Instant booking",
            "precio_medio_diario": "Average daily price",
            "disponibilidad_pct": "Availability (%)",
            "no_disponibilidad_pct": "Unavailability (%)",
        }
    )

    columnas = [
        "City",
        "Neighborhood",
        "Property",
        "Overall rating",
        "Review volume",
        "Instant booking",
        "Average daily price",
        "Availability (%)",
        "Unavailability (%)",
    ]

    st.dataframe(
        tabla[columnas],
        width="stretch",
        hide_index=True,
    )

    st.caption("Unavailability is used as a proxy for estimated occupancy.")
