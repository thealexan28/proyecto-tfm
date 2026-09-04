import streamlit as st
import plotly.express as px

from backend.queries import (
    get_overview_kpis,
    get_city_summary,
    get_top_neighborhoods,
    get_availability_by_season,
)


def render_home():
    st.title("Short-term rental analysis in Spain")
    st.markdown(
        """
        Overview of the short-term rental market in the cities analyzed:
        supply volume, prices, availability, and estimated potential revenue.
        """
    )

    st.divider()

    # Overview KPIs
    kpis_df = get_overview_kpis()

    if kpis_df.empty:
        st.warning("No data is available to build the summary.")
        return

    kpis = kpis_df.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total properties analyzed",
        f"{int(kpis['total_viviendas']):,}".replace(",", "."),
    )

    col2.metric(
        "Cities analyzed",
        f"{int(kpis['total_ciudades'])}",
    )

    col3.metric(
        "Average daily price",
        f"{kpis['precio_medio_diario']:,.2f} €".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Nights analyzed",
        f"{int(kpis['total_registros_calendario']):,}".replace(",", "."),
    )

    col5.metric(
        "Average availability",
        f"{kpis['tasa_disponibilidad_pct']:.2f} %",
    )

    col6.metric(
        "Total potential revenue",
        f"{kpis['ingreso_potencial_total']:,.0f} €".replace(",", "."),
    )

    st.divider()

    # Summary by city
    st.subheader("Supply by city")

    city_df = get_city_summary()

    if not city_df.empty:
        city_figure = px.bar(
            city_df,
            x="ciudad",
            y="num_viviendas",
            text="num_viviendas",
            title="Short-term rental properties by city",
            labels={
                "ciudad": "City",
                "num_viviendas": "Number of properties",
            },
        )

        city_figure.update_traces(textposition="outside")
        city_figure.update_layout(
            xaxis_title="City",
            yaxis_title="Number of properties",
            height=450,
        )

        st.plotly_chart(city_figure, width="stretch")

        city_table = city_df.rename(
            columns={
                "ciudad": "City",
                "num_viviendas": "Short-term rental properties",
                "registros_calendario": "Nights analyzed",
                "precio_medio_diario": "Average daily price",
                "ingreso_potencial_total": "Total potential revenue",
                "tasa_disponibilidad_pct": "Average availability (%)",
            }
        )

        st.dataframe(
            city_table,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No city-level data is available yet.")

    st.divider()

    # Top neighborhoods
    st.subheader("Concentration by neighborhood")

    top_neighborhoods_df = get_top_neighborhoods(limit=10)

    if not top_neighborhoods_df.empty:
        top_neighborhoods_df["neighborhood_city"] = (
            top_neighborhoods_df["barrio"] + " (" + top_neighborhoods_df["ciudad"] + ")"
        )

        neighborhoods_figure = px.bar(
            top_neighborhoods_df.sort_values("num_viviendas", ascending=True),
            x="num_viviendas",
            y="neighborhood_city",
            orientation="h",
            title="Neighborhoods with the highest property concentration",
            labels={
                "num_viviendas": "Number of properties",
                "neighborhood_city": "Neighborhood",
            },
        )

        neighborhoods_figure.update_layout(
            xaxis_title="Number of properties",
            yaxis_title="Neighborhood",
            height=500,
        )

        st.plotly_chart(neighborhoods_figure, width="stretch")
    else:
        st.info("No neighborhood data is available yet.")

    st.divider()

    # Availability by season
    st.subheader("Availability by season")

    season_df = get_availability_by_season()

    if not season_df.empty:
        fig_temp = px.bar(
            season_df,
            x="temporada",
            y="tasa_disponibilidad_pct",
            color="ciudad",
            barmode="group",
            title="Average availability by season and city",
            labels={
                "temporada": "Season",
                "tasa_disponibilidad_pct": "Availability (%)",
                "ciudad": "City",
            },
        )

        fig_temp.update_layout(
            xaxis_title="Season",
            yaxis_title="Availability (%)",
            height=450,
        )

        st.plotly_chart(fig_temp, width="stretch")
    else:
        st.info("No seasonal availability data is available yet.")
