import streamlit as st
import plotly.express as px

from backend.queries import (
    get_available_cities,
    get_neighborhood_concentration,
)


def format_number(value):
    if value is None:
        return "-"

    return f"{int(value):,}".replace(",", ".")


def render_neighborhood_concentration():
    st.title("📍 Short-term rental concentration by neighborhood")

    st.markdown(
        """
        Neighborhood ranking by number of short-term rental properties. It highlights
        the areas where supply is most heavily concentrated.
        """
    )

    st.divider()

    # =========================
    # Filters
    # =========================
    cities_df = get_available_cities()

    if cities_df.empty:
        st.warning("No cities are available in the database.")
        return

    cities = cities_df["ciudad"].dropna().sort_values().tolist()

    col_filter_1, col_filter_2 = st.columns([2, 1])

    with col_filter_1:
        selected_city = st.selectbox(
            "Select a city",
            options=["All cities"] + cities,
            index=0,
        )

    with col_filter_2:
        limit = st.slider(
            "Number of neighborhoods to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    city_filter = None if selected_city == "All cities" else selected_city

    # =========================
    # Data loading
    # =========================
    df = get_neighborhood_concentration(
        city=city_filter,
        limit=limit,
    )

    if df.empty:
        st.warning("No data is available for the selected filters.")
        return

    # Helper field used when no city is selected
    if city_filter is None:
        df["area_label"] = df["barrio"] + " (" + df["ciudad"] + ")"
        chart_title = f"Top {limit} neighborhoods by number of short-term rentals"
    else:
        df["area_label"] = df["barrio"]
        chart_title = f"Top {limit} neighborhoods by number of short-term rentals in {selected_city}"

    # =========================
    # KPIs
    # =========================
    top_listing_count = df["num_viviendas"].sum()
    top_neighborhood = df.iloc[0]["barrio"]
    top_city = df.iloc[0]["ciudad"]
    top_listings = df.iloc[0]["num_viviendas"]
    top_share = df.iloc[0]["porcentaje_sobre_ciudad"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Properties in the ranking",
        format_number(top_listing_count),
    )

    col2.metric(
        "Neighborhood with the most properties",
        top_neighborhood,
    )

    col3.metric(
        "Leading neighborhood share",
        f"{top_share:.2f} %",
        format_number(top_listings),
    )

    if city_filter is None:
        st.caption(
            f"The neighborhood with the highest concentration is **{top_neighborhood}**, in **{top_city}**."
        )
    else:
        st.caption(
            f"In **{selected_city}**, the neighborhood with the highest concentration is **{top_neighborhood}**."
        )

    st.divider()

    # =========================
    # Bar chart
    # =========================
    st.subheader("Neighborhood ranking")

    df_chart = df.sort_values("num_viviendas", ascending=True)

    fig = px.bar(
        df_chart,
        x="num_viviendas",
        y="area_label",
        orientation="h",
        text="num_viviendas",
        title=chart_title,
        labels={
            "num_viviendas": "Number of short-term rental properties",
            "area_label": "Neighborhood",
        },
        hover_data={
            "ciudad": True,
            "barrio": True,
            "num_viviendas": True,
            "porcentaje_sobre_ciudad": ":.2f",
            "precio_medio_diario": ":.2f",
            "tasa_disponibilidad_pct": ":.2f",
            "area_label": False,
        },
    )

    fig.update_traces(
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Number of short-term rental properties",
        yaxis_title="Neighborhood",
        height=max(450, limit * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # =========================
    # Detailed table
    # =========================
    st.subheader("Detailed table")

    table = df.copy()

    table = table.rename(
        columns={
            "ciudad": "City",
            "barrio": "Neighborhood",
            "num_viviendas": "No. of short-term rental properties",
            "porcentaje_sobre_ciudad": "% of city total",
            "registros_calendario": "Nights analyzed",
            "precio_medio_diario": "Average daily price",
            "tasa_disponibilidad_pct": "Average availability (%)",
        }
    )

    columns = [
        "City",
        "Neighborhood",
        "No. of short-term rental properties",
        "% of city total",
        "Nights analyzed",
        "Average daily price",
        "Average availability (%)",
    ]

    st.dataframe(
        table[columns],
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "The ranking uses unique properties to prevent duplicates from the daily calendar."
    )
