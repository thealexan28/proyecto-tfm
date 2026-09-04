import streamlit as st
import plotly.express as px

from backend.queries import (
    get_available_cities,
    get_available_neighborhoods_by_city,
    get_occupancy_by_season,
    get_monthly_occupancy,
)


def format_number(value):
    if value is None:
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_pct(value):
    if value is None:
        return "-"

    return f"{value:.2f} %"


def render_seasonal_occupancy():
    st.title("📈 Estimated occupancy by season")

    st.markdown(
        """
        Time-based comparison of unavailability recorded in the calendar.
        It helps identify seasonal peaks and monthly changes in usage pressure.
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

    col_filter_1, col_filter_2 = st.columns([2, 2])

    with col_filter_1:
        selected_city = st.selectbox(
            "Select a city",
            options=["All cities"] + cities,
            index=0,
        )

    city_filter = None if selected_city == "All cities" else selected_city

    neighborhood_filter = None

    with col_filter_2:
        if city_filter is not None:
            neighborhoods_df = get_available_neighborhoods_by_city(city_filter)
            neighborhoods = neighborhoods_df["barrio"].dropna().sort_values().tolist()

            selected_neighborhood = st.selectbox(
                "Select a neighborhood",
                options=["All neighborhoods"] + neighborhoods,
                index=0,
            )

            neighborhood_filter = (
                None
                if selected_neighborhood == "All neighborhoods"
                else selected_neighborhood
            )
        else:
            st.selectbox(
                "Select a neighborhood",
                options=["Select a city first"],
                index=0,
                disabled=True,
            )

    # =========================
    # Data loading
    # =========================
    season_df = get_occupancy_by_season(
        city=city_filter,
        neighborhood=neighborhood_filter,
    )

    monthly_df = get_monthly_occupancy(
        city=city_filter,
        neighborhood=neighborhood_filter,
    )

    if season_df.empty:
        st.warning("No data is available for the selected filters.")
        return

    # =========================
    # Overview KPIs
    # =========================
    total_records = season_df["registros_calendario"].sum()
    total_unavailable_nights = season_df["noches_ocupadas_estimadas"].sum()
    total_available_nights = season_df["noches_disponibles"].sum()

    weighted_average_occupancy = (
        total_unavailable_nights * 100 / total_records if total_records > 0 else None
    )

    weighted_average_availability = (
        total_available_nights * 100 / total_records if total_records > 0 else None
    )

    highest_row = season_df.sort_values("ocupacion_estimada_pct", ascending=False).iloc[
        0
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average estimated occupancy",
        format_pct(weighted_average_occupancy),
    )

    col2.metric(
        "Season with the highest occupancy",
        highest_row["temporada"],
    )

    col3.metric(
        "Occupancy in that season",
        format_pct(highest_row["ocupacion_estimada_pct"]),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Nights analyzed",
        format_number(total_records),
    )

    col5.metric(
        "Unavailable nights",
        format_number(total_unavailable_nights),
    )

    col6.metric(
        "Average availability",
        format_pct(weighted_average_availability),
    )

    st.divider()

    # =========================
    # Seasonal bar chart
    # =========================
    st.subheader("Estimated occupancy by season")

    if city_filter is None:
        fig_bar = px.bar(
            season_df,
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
            season_df,
            x="temporada",
            y="ocupacion_estimada_pct",
            text="ocupacion_estimada_pct",
            title=f"Estimated occupancy by season in {selected_city}",
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
    # Monthly trend
    # =========================
    st.subheader("Monthly estimated occupancy trend")

    if not monthly_df.empty:
        if city_filter is None:
            fig_line = px.line(
                monthly_df,
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
                monthly_df,
                x="periodo",
                y="ocupacion_estimada_pct",
                markers=True,
                title=f"Monthly estimated occupancy trend in {selected_city}",
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
    # Detailed table by season
    # =========================
    st.subheader("Detailed table by season")

    table = season_df.copy()

    table = table.rename(
        columns={
            "ciudad": "City",
            "temporada": "Season",
            "registros_calendario": "Nights analyzed",
            "num_viviendas": "No. of properties",
            "noches_ocupadas_estimadas": "Unavailable nights",
            "noches_disponibles": "Available nights",
            "ocupacion_estimada_pct": "Estimated occupancy (%)",
            "disponibilidad_pct": "Availability (%)",
            "precio_medio_diario": "Average daily price",
            "ingreso_potencial_total": "Total potential revenue",
        }
    )

    columns = [
        "City",
        "Season",
        "No. of properties",
        "Nights analyzed",
        "Unavailable nights",
        "Available nights",
        "Estimated occupancy (%)",
        "Availability (%)",
        "Average daily price",
        "Total potential revenue",
    ]

    st.dataframe(
        table[columns],
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Estimated occupancy represents nights marked as unavailable in the calendar."
    )
