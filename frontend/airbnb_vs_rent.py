import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_available_cities,
    get_city_rental_comparison,
    get_neighborhood_rental_comparison,
)


def format_currency(value):
    if pd.isna(value):
        return "-"

    return f"{value:,.0f} €".replace(",", ".")


def format_ratio(value):
    if pd.isna(value):
        return "-"

    return f"{value:.2f}x"


def render_airbnb_vs_rent():
    st.title("🏠 Airbnb vs long-term rentals")

    st.markdown(
        """
        Compares the monthly equivalent Airbnb price with municipal long-term rent.
        This view highlights the cities and neighborhoods with the largest price gap.
        """
    )

    st.caption(
        "Reference period: 1–30 November 2025. All cities use the same 30-day "
        "window and the same municipal reporting date."
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
            "Neighborhoods to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    city_filter = None if selected_city == "All cities" else selected_city

    # =========================
    # Data loading
    # =========================
    city_df = get_city_rental_comparison(
        city=city_filter,
    )

    neighborhoods_df = get_neighborhood_rental_comparison(
        city=city_filter,
        limit=limit,
    )

    if city_df.empty:
        st.warning("No data is available for the selected filters.")
        return

    # =========================
    # SECTION 1: city comparison
    # =========================
    st.subheader("Monthly gap by city")

    if city_filter is None:
        df_plot = city_df[
            [
                "ciudad",
                "precio_airbnb_mensualizado",
                "alquiler_habitual_municipal",
            ]
        ].copy()

        df_plot = df_plot.rename(
            columns={
                "precio_airbnb_mensualizado": "Monthly equivalent Airbnb price",
                "alquiler_habitual_municipal": "Municipal long-term rent",
            }
        )

        df_melt = df_plot.melt(
            id_vars="ciudad",
            value_vars=[
                "Monthly equivalent Airbnb price",
                "Municipal long-term rent",
            ],
            var_name="Metric",
            value_name="Monthly amount",
        )

        comparison_figure = px.bar(
            df_melt,
            x="ciudad",
            y="Monthly amount",
            color="Metric",
            barmode="group",
            text="Monthly amount",
            title="Monthly equivalent Airbnb price vs municipal long-term rent",
            labels={
                "ciudad": "City",
                "Monthly amount": "Monthly amount (€)",
            },
        )

        comparison_figure.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        comparison_figure.update_layout(
            height=500,
            yaxis_title="Monthly amount (€)",
            xaxis_title="City",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(comparison_figure, width="stretch")

        average_difference = city_df["diferencia_mensual"].mean()
        average_ratio = city_df["ratio_airbnb_vs_alquiler"].mean()

        city_with_largest_gap = city_df.sort_values(
            "diferencia_mensual",
            ascending=False,
        ).iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average difference",
            format_currency(average_difference),
        )

        col2.metric(
            "Average Airbnb/rent ratio",
            format_ratio(average_ratio),
        )

        col3.metric(
            "Largest difference",
            city_with_largest_gap["ciudad"],
            format_currency(city_with_largest_gap["diferencia_mensual"]),
        )

    else:
        row = city_df.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Monthly equivalent Airbnb price",
            format_currency(row["precio_airbnb_mensualizado"]),
        )

        col2.metric(
            "Municipal long-term rent",
            format_currency(row["alquiler_habitual_municipal"]),
        )

        col3.metric(
            "Monthly difference",
            format_currency(row["diferencia_mensual"]),
        )

        col4.metric(
            "Airbnb/rent ratio",
            format_ratio(row["ratio_airbnb_vs_alquiler"]),
        )

        df_plot = pd.DataFrame(
            {
                "Metric": [
                    "Monthly equivalent Airbnb price",
                    "Municipal long-term rent",
                ],
                "Monthly amount": [
                    row["precio_airbnb_mensualizado"],
                    row["alquiler_habitual_municipal"],
                ],
            }
        )

        comparison_figure = px.bar(
            df_plot,
            x="Metric",
            y="Monthly amount",
            text="Monthly amount",
            title=f"Monthly comparison in {selected_city}",
            labels={
                "Monthly amount": "Monthly amount (€)",
            },
        )

        comparison_figure.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        comparison_figure.update_layout(
            height=450,
            yaxis_title="Monthly amount (€)",
            xaxis_title="",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(comparison_figure, width="stretch")

    st.divider()

    # =========================
    # SECTION 2: municipal housing context
    # =========================
    st.subheader("Municipal housing context")

    context_columns = [
        "ciudad",
        "alquiler_habitual_municipal",
        "renta_media_hogar",
        "ingresos_ciudadanos",
        "num_viviendas_residenciales",
        "num_viviendas_turisticas",
        "capacidad_viviendas_turisticas",
        "indice_presion_turistica",
    ]

    context_df = city_df[context_columns].copy()

    context_table = context_df.rename(
        columns={
            "ciudad": "City",
            "alquiler_habitual_municipal": "Municipal long-term rent",
            "renta_media_hogar": "Average household income",
            "ingresos_ciudadanos": "Average personal income",
            "num_viviendas_residenciales": "Residential properties",
            "num_viviendas_turisticas": "Official short-term rental properties",
            "capacidad_viviendas_turisticas": "Official tourist capacity",
            "indice_presion_turistica": "Tourism pressure index",
        }
    )

    st.dataframe(
        context_table,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # =========================
    # SECTION 3: neighborhoods vs municipal benchmark
    # =========================
    st.subheader("Neighborhoods vs the municipal benchmark")

    if neighborhoods_df.empty:
        st.warning("No neighborhood data is available for the selected filters.")
    else:
        if city_filter is None:
            neighborhoods_df["area_label"] = (
                neighborhoods_df["barrio"] + " (" + neighborhoods_df["ciudad"] + ")"
            )
            neighborhood_chart_title = (
                f"Top {limit} neighborhoods by difference from municipal rent"
            )
        else:
            neighborhoods_df["area_label"] = neighborhoods_df["barrio"]
            neighborhood_chart_title = f"Top {limit} neighborhoods by difference from municipal rent in {selected_city}"

        df_chart = neighborhoods_df.sort_values(
            "diferencia_frente_alquiler_municipal",
            ascending=True,
        )

        neighborhoods_figure = px.bar(
            df_chart,
            x="diferencia_frente_alquiler_municipal",
            y="area_label",
            orientation="h",
            text="diferencia_frente_alquiler_municipal",
            title=neighborhood_chart_title,
            labels={
                "diferencia_frente_alquiler_municipal": "Difference from municipal rent (€)",
                "area_label": "Neighborhood",
            },
            hover_data={
                "ciudad": True,
                "barrio": True,
                "num_viviendas": True,
                "precio_airbnb_mensualizado_barrio": ":.2f",
                "alquiler_habitual_municipal": ":.2f",
                "ratio_frente_alquiler_municipal": ":.2f",
                "area_label": False,
            },
        )

        neighborhoods_figure.update_traces(
            texttemplate="%{text:,.0f} €",
            textposition="outside",
        )

        neighborhoods_figure.update_layout(
            height=max(450, limit * 34),
            xaxis_title="Difference from municipal rent (€)",
            yaxis_title="Neighborhood",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(neighborhoods_figure, width="stretch")

    st.divider()

    # =========================
    # SECTION 4: concentration-price relationship
    # =========================
    st.subheader("Relationship between concentration and Airbnb price")

    if not neighborhoods_df.empty:
        fig_scatter = px.scatter(
            neighborhoods_df,
            x="num_viviendas",
            y="precio_airbnb_mensualizado_barrio",
            size="ingreso_potencial_total",
            color="ciudad" if city_filter is None else None,
            hover_name="barrio",
            title="Number of properties vs monthly equivalent Airbnb price by neighborhood",
            labels={
                "num_viviendas": "Number of short-term rental properties",
                "precio_airbnb_mensualizado_barrio": "Monthly equivalent Airbnb price by neighborhood (€)",
                "ingreso_potencial_total": "Total potential revenue",
                "ciudad": "City",
            },
        )

        fig_scatter.update_layout(
            height=500,
            xaxis_title="Number of short-term rental properties",
            yaxis_title="Monthly equivalent Airbnb price by neighborhood (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(fig_scatter, width="stretch")

    st.divider()

    # =========================
    # SECTION 5: neighborhood details
    # =========================
    st.subheader("Detailed table by neighborhood")

    if not neighborhoods_df.empty:
        table = neighborhoods_df.copy()

        table = table.rename(
            columns={
                "ciudad": "City",
                "barrio": "Neighborhood",
                "num_viviendas": "No. of properties",
                "precio_medio_airbnb_diario": "Daily Airbnb price",
                "precio_airbnb_mensualizado_barrio": "Monthly equivalent neighborhood Airbnb price",
                "alquiler_habitual_municipal": "Municipal long-term rent",
                "diferencia_frente_alquiler_municipal": "Difference from municipal benchmark",
                "ratio_frente_alquiler_municipal": "Ratio to municipal benchmark",
                "disponibilidad_pct": "Availability (%)",
                "ocupacion_estimada_pct": "Estimated occupancy (%)",
                "ingreso_potencial_total": "Total potential revenue",
                "registros_con_precio": "Records with price",
                "registros_calendario": "Nights analyzed",
            }
        )

        columns = [
            "City",
            "Neighborhood",
            "No. of properties",
            "Daily Airbnb price",
            "Monthly equivalent neighborhood Airbnb price",
            "Municipal long-term rent",
            "Difference from municipal benchmark",
            "Ratio to municipal benchmark",
            "Availability (%)",
            "Estimated occupancy (%)",
            "Total potential revenue",
            "Records with price",
            "Nights analyzed",
        ]

        st.dataframe(
            table[columns],
            width="stretch",
            hide_index=True,
        )

    st.caption(
        """
        The Airbnb price is converted to a monthly amount by multiplying the average daily price by 30.
        The long-term rental benchmark is municipal.
        """
    )
