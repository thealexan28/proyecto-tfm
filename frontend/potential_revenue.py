import streamlit as st
import plotly.express as px

from backend.queries import (
    get_available_cities,
    get_neighborhood_potential_revenue,
)


def format_number(value):
    if value is None:
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_currency(value):
    if value is None:
        return "-"

    return f"{value:,.0f} €".replace(",", ".")


def render_potential_revenue():
    st.title("💰 Potential revenue by neighborhood")

    st.markdown(
        """
        Identifies the neighborhoods with the greatest estimated revenue potential,
        combining property volume, daily price, and availability.
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
    df = get_neighborhood_potential_revenue(
        city=city_filter,
        limit=limit,
    )

    if df.empty:
        st.warning("No data is available for the selected filters.")
        return

    if city_filter is None:
        df["area_label"] = df["barrio"] + " (" + df["ciudad"] + ")"
        chart_title = f"Top {limit} neighborhoods by potential revenue"
    else:
        df["area_label"] = df["barrio"]
        chart_title = (
            f"Top {limit} neighborhoods by potential revenue in {selected_city}"
        )

    # =========================
    # KPIs
    # =========================
    top_revenue = df["ingreso_potencial_total"].sum()
    top_neighborhood = df.iloc[0]["barrio"]
    top_city = df.iloc[0]["ciudad"]
    top_neighborhood_revenue = df.iloc[0]["ingreso_potencial_total"]
    top_neighborhood_listings = df.iloc[0]["num_viviendas"]
    top_revenue_share = df.iloc[0]["porcentaje_ingreso_sobre_ciudad"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Potential revenue in the ranking",
        format_currency(top_revenue),
    )

    col2.metric(
        "Neighborhood with the highest revenue",
        top_neighborhood,
    )

    col3.metric(
        "Leading neighborhood revenue",
        format_currency(top_neighborhood_revenue),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Properties in the leading neighborhood",
        format_number(top_neighborhood_listings),
    )

    col5.metric(
        "Leading neighborhood average daily price",
        f"{df.iloc[0]['precio_medio_diario']:,.2f} €".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
        if df.iloc[0]["precio_medio_diario"] is not None
        else "-",
    )

    col6.metric(
        "Share of city total",
        f"{top_revenue_share:.2f} %",
    )

    if city_filter is None:
        st.caption(
            f"The neighborhood with the highest potential revenue is **{top_neighborhood}**, in **{top_city}**."
        )
    else:
        st.caption(
            f"In **{selected_city}**, the neighborhood with the highest potential revenue is **{top_neighborhood}**."
        )

    st.divider()

    # =========================
    # Main chart
    # =========================
    st.subheader("Neighborhood ranking by potential revenue")

    df_chart = df.sort_values("ingreso_potencial_total", ascending=True)

    fig = px.bar(
        df_chart,
        x="ingreso_potencial_total",
        y="area_label",
        orientation="h",
        text="ingreso_potencial_total",
        title=chart_title,
        labels={
            "ingreso_potencial_total": "Total potential revenue (€)",
            "area_label": "Neighborhood",
        },
        hover_data={
            "ciudad": True,
            "barrio": True,
            "num_viviendas": True,
            "ingreso_potencial_total": ":.2f",
            "porcentaje_ingreso_sobre_ciudad": ":.2f",
            "ingreso_potencial_por_vivienda": ":.2f",
            "precio_medio_diario": ":.2f",
            "tasa_disponibilidad_pct": ":.2f",
            "area_label": False,
        },
    )

    fig.update_traces(
        texttemplate="%{x:,.0f} €",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Total potential revenue (€)",
        yaxis_title="Neighborhood",
        height=max(450, limit * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # =========================
    # Secondary chart: revenue per listing
    # =========================
    st.subheader("Average potential revenue per property")

    fig_media = px.bar(
        df_chart,
        x="ingreso_potencial_por_vivienda",
        y="area_label",
        orientation="h",
        title="Average potential revenue per property in the ranked neighborhoods",
        labels={
            "ingreso_potencial_por_vivienda": "Potential revenue per property (€)",
            "area_label": "Neighborhood",
        },
        hover_data={
            "ciudad": True,
            "barrio": True,
            "num_viviendas": True,
            "ingreso_potencial_por_vivienda": ":.2f",
            "area_label": False,
        },
    )

    fig_media.update_layout(
        xaxis_title="Potential revenue per property (€)",
        yaxis_title="Neighborhood",
        height=max(450, limit * 32),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(fig_media, width="stretch")

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
            "ingreso_potencial_total": "Total potential revenue",
            "porcentaje_ingreso_sobre_ciudad": "% of city revenue",
            "ingreso_potencial_por_vivienda": "Potential revenue per property",
            "precio_medio_diario": "Average daily price",
            "tasa_disponibilidad_pct": "Average availability (%)",
            "registros_calendario": "Nights analyzed",
        }
    )

    columns = [
        "City",
        "Neighborhood",
        "No. of short-term rental properties",
        "Total potential revenue",
        "% of city revenue",
        "Potential revenue per property",
        "Average daily price",
        "Average availability (%)",
        "Nights analyzed",
    ]

    st.dataframe(
        table[columns],
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Potential revenue is estimated from the daily price and recorded availability."
    )
