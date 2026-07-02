import streamlit as st
import pydeck as pdk

from backend.queries import get_viviendas_mapa


CARTO_VOYAGER_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"

CENTROS_CIUDAD = {
    "Madrid": (40.4168, -3.7038),
    "Málaga": (36.7213, -4.4214),
    "Sevilla": (37.3891, -5.9845),
    "Valencia": (39.4699, -0.3763),
}


def render_mapa_viviendas():
    st.title("🗺️ Mapa de viviendas turísticas")

    st.markdown(
        """
        Distribución geográfica de los alojamientos turísticos. El mapa ayuda a
        localizar concentraciones espaciales y consultar el detalle de cada vivienda.
        """
    )

    ciudad = st.selectbox(
        "Selecciona una ciudad",
        ["Madrid", "Málaga", "Sevilla", "Valencia"],
        index=1,
    )

    df = get_viviendas_mapa(ciudad=ciudad)

    if df.empty:
        st.warning("No hay viviendas disponibles para la selección realizada.")
        return

    st.subheader("Resumen de la ciudad")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Viviendas mostradas",
        f"{len(df):,}".replace(",", "."),
    )

    col2.metric(
        "Barrios",
        df["barrio"].nunique(),
    )

    col3.metric(
        "Precio medio diario",
        f"{df['precio_medio_diario'].mean():,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    col4.metric(
        "Puntuación media",
        f"{df['puntuacion_general'].mean():.2f}",
    )

    st.divider()

    lat_centro, lon_centro = CENTROS_CIUDAD.get(
        ciudad,
        (df["latitud"].median(), df["longitud"].median()),
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[longitud, latitud]",
        get_radius=8,
        radius_min_pixels=1,
        radius_max_pixels=4,
        get_fill_color="[255, 70, 70, 220]",
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=lat_centro,
        longitude=lon_centro,
        zoom=11,
        pitch=0,
    )

    tooltip = {
        "html": """
        <div style="margin:0; padding:0; line-height:1.15; font-size:13px;">
          <div style="font-weight:700; margin-bottom:4px;">{nombre_anuncio}</div>
          <div><b>Ciudad:</b> {ciudad} | <b>Barrio:</b> {barrio}</div>
          <div><b>Habitación:</b> {tipo_habitacion} | <b>Propiedad:</b> {tipo_propiedad}</div>
          <div><b>Capacidad:</b> {capacidad_huespedes} huéspedes</div>
          <div><b>Anfitrión:</b> {nombre_anfitrion}</div>
          <div><b>Puntuación:</b> {puntuacion_general}</div>
          <div><b>Precio:</b> {precio_medio_diario} € | <b>Disp.:</b> {disponibilidad_pct} %</div>
          <div><b>Ocupación:</b> {ocupacion_estimada_pct} % | <b>Ingreso:</b> {ingreso_potencial_total} €</div>
        </div>
        """,
        "style": {
            "backgroundColor": "white",
            "color": "black",
            "padding": "6px 8px",
            "borderRadius": "4px",
            "maxWidth": "240px",
        },
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=CARTO_VOYAGER_STYLE,
    )

    st.subheader("Mapa de alojamientos")
    st.pydeck_chart(deck, width="stretch", key=f"mapa-{ciudad}")

    st.subheader("Detalle de viviendas")
    columnas_detalle = [col for col in df.columns if col != "id_vivienda"]
    st.dataframe(df[columnas_detalle], width="stretch", hide_index=True)
