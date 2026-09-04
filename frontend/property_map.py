import streamlit as st
import pydeck as pdk

from backend.queries import get_map_listings


CARTO_VOYAGER_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"

CITY_CENTERS = {
    "Madrid": (40.4168, -3.7038),
    "Málaga": (36.7213, -4.4214),
    "Sevilla": (37.3891, -5.9845),
    "Valencia": (39.4699, -0.3763),
}


def render_property_map():
    st.title("🗺️ Short-term rental property map")

    st.markdown(
        """
        Geographic distribution of short-term rental properties. The map helps locate
        spatial clusters and provides details for each property.
        """
    )

    city = st.selectbox(
        "Select a city",
        ["Madrid", "Málaga", "Sevilla", "Valencia"],
        index=1,
    )

    df = get_map_listings(city=city)

    if df.empty:
        st.warning("No properties are available for the selected filters.")
        return

    st.subheader("City summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Properties displayed",
        f"{len(df):,}".replace(",", "."),
    )

    col2.metric(
        "Neighborhoods",
        df["barrio"].nunique(),
    )

    col3.metric(
        "Average daily price",
        f"{df['precio_medio_diario'].mean():,.2f} €".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )

    col4.metric(
        "Average rating",
        f"{df['puntuacion_general'].mean():.2f}",
    )

    st.divider()

    center_latitude, center_longitude = CITY_CENTERS.get(
        city,
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
        latitude=center_latitude,
        longitude=center_longitude,
        zoom=11,
        pitch=0,
    )

    tooltip = {
        "html": """
        <div style="margin:0; padding:0; line-height:1.15; font-size:13px;">
          <div style="font-weight:700; margin-bottom:4px;">{nombre_anuncio}</div>
          <div><b>City:</b> {ciudad} | <b>Neighborhood:</b> {barrio}</div>
          <div><b>Room:</b> {tipo_habitacion} | <b>Property:</b> {tipo_propiedad}</div>
          <div><b>Capacity:</b> {capacidad_huespedes} guests</div>
          <div><b>Host:</b> {nombre_anfitrion}</div>
          <div><b>Rating:</b> {puntuacion_general}</div>
          <div><b>Price:</b> {precio_medio_diario} € | <b>Avail.:</b> {disponibilidad_pct} %</div>
          <div><b>Occupancy:</b> {ocupacion_estimada_pct} % | <b>Revenue:</b> {ingreso_potencial_total} €</div>
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

    st.subheader("Property map")
    st.pydeck_chart(deck, width="stretch", key=f"map-{city}")

    st.subheader("Property details")
    detail_columns = [col for col in df.columns if col != "id_vivienda"]
    st.dataframe(df[detail_columns], width="stretch", hide_index=True)
