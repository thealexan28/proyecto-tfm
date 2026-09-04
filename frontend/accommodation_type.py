import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_available_cities,
    get_accommodation_type_analysis,
    get_price_by_capacity,
)


def format_currency(value):
    if pd.isna(value):
        return "-"

    return f"{value:,.0f} €".replace(",", ".")


def format_currency_dec(value):
    if pd.isna(value):
        return "-"

    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value):
    if pd.isna(value):
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_pct(value):
    if pd.isna(value):
        return "-"

    return f"{value:.2f} %"


def normalize_text(value):
    if pd.isna(value):
        return ""

    return str(value).lower().strip()


def find_entire_home(df):
    for _, row in df.iterrows():
        accommodation_type_name = normalize_text(row["tipo_alojamiento"])

        if (
            "entire" in accommodation_type_name
            or "complet" in accommodation_type_name
            or "vivienda" in accommodation_type_name
        ):
            return row

    return None


def find_private_room(df):
    for _, row in df.iterrows():
        accommodation_type_name = normalize_text(row["tipo_alojamiento"])

        if "private" in accommodation_type_name or "privad" in accommodation_type_name:
            return row

    return None


def render_accommodation_type():
    st.title("🏘️ Analysis by property type")

    st.markdown(
        """
        Compares price, availability, capacity, and potential revenue by room
        or property type.
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

    col_filter_1, col_filter_2, col_filter_3 = st.columns([2, 1, 1])

    with col_filter_1:
        selected_city = st.selectbox(
            "Select a city",
            options=["All cities"] + cities,
            index=0,
        )

    with col_filter_2:
        grouping_option = st.selectbox(
            "Group analysis by",
            options=[
                "Room type",
                "Property type",
            ],
            index=0,
        )

    with col_filter_3:
        min_listings = st.slider(
            "Minimum properties per capacity",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
        )

    city_filter = None if selected_city == "All cities" else selected_city

    group_by = "room_type" if grouping_option == "Room type" else "property_type"
    grouping_label = "room type" if group_by == "room_type" else "property type"
    plural_label = (
        "Room types" if group_by == "room_type" else "Property types displayed"
    )

    # =========================
    # Data loading
    # =========================
    accommodation_df = get_accommodation_type_analysis(
        city=city_filter,
        group_by=group_by,
    )

    capacity_df = get_price_by_capacity(
        city=city_filter,
        min_listings=min_listings,
    )

    if accommodation_df.empty:
        st.warning("No data is available for the selected filters.")
        return

    if group_by == "property_type":
        accommodation_df = accommodation_df.nlargest(20, "num_viviendas").copy()

    # =========================
    # Main results
    # =========================
    st.subheader("Key indicators")

    highest_price_type = accommodation_df.sort_values(
        "precio_medio_diario",
        ascending=False,
    ).iloc[0]

    highest_revenue_type = accommodation_df.sort_values(
        "ingreso_potencial_total",
        ascending=False,
    ).iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Highest average price",
        highest_price_type["tipo_alojamiento"],
        format_currency_dec(highest_price_type["precio_medio_diario"]),
    )

    col2.metric(
        "Highest potential revenue",
        highest_revenue_type["tipo_alojamiento"],
        format_currency(highest_revenue_type["ingreso_potencial_total"]),
    )

    col3.metric(
        plural_label,
        format_number(len(accommodation_df)),
    )

    st.divider()

    # =========================
    # Entire homes vs private rooms
    # =========================
    if group_by == "room_type":
        st.subheader("Entire homes vs private rooms")

        entire_home_row = find_entire_home(accommodation_df)
        private_room_row = find_private_room(accommodation_df)

        if entire_home_row is not None and private_room_row is not None:
            unavailability_difference = (
                entire_home_row["no_disponibilidad_pct"]
                - private_room_row["no_disponibilidad_pct"]
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Entire-home unavailability",
                format_pct(entire_home_row["no_disponibilidad_pct"]),
            )

            col2.metric(
                "Private-room unavailability",
                format_pct(private_room_row["no_disponibilidad_pct"]),
            )

            col3.metric(
                "Difference",
                format_pct(unavailability_difference),
            )

            if unavailability_difference > 0:
                st.success(
                    "Entire homes have higher unavailability than private rooms."
                )
            elif unavailability_difference < 0:
                st.warning(
                    "Private rooms have higher unavailability than entire homes."
                )
            else:
                st.info("Both types have very similar unavailability.")

            comparison_df = pd.DataFrame(
                {
                    "Type": [
                        entire_home_row["tipo_alojamiento"],
                        private_room_row["tipo_alojamiento"],
                    ],
                    "Unavailability (%)": [
                        entire_home_row["no_disponibilidad_pct"],
                        private_room_row["no_disponibilidad_pct"],
                    ],
                }
            )

            comparison_figure = px.bar(
                comparison_df,
                x="Type",
                y="Unavailability (%)",
                text="Unavailability (%)",
                title="Unavailability comparison",
                labels={
                    "Type": "Property type",
                    "Unavailability (%)": "Unavailability (%)",
                },
            )

            comparison_figure.update_traces(
                texttemplate="%{text:.2f} %",
                textposition="outside",
            )

            comparison_figure.update_layout(
                height=420,
                yaxis_range=[0, 100],
                xaxis_title="",
                yaxis_title="Unavailability (%)",
                margin=dict(l=20, r=20, t=70, b=20),
            )

            st.plotly_chart(comparison_figure, width="stretch")

        else:
            st.info(
                """
                Entire homes and private rooms were not both found under the expected
                names in the available data.
                """
            )
        st.divider()

    # =========================
    # Average price by type
    # =========================
    st.subheader(f"Which {grouping_label} has the highest average price?")

    price_df = accommodation_df.sort_values("precio_medio_diario", ascending=True)

    price_figure = px.bar(
        price_df,
        x="precio_medio_diario",
        y="tipo_alojamiento",
        orientation="h",
        text="precio_medio_diario",
        title=f"Average daily price by {grouping_label}",
        labels={
            "precio_medio_diario": "Average daily price (€)",
            "tipo_alojamiento": grouping_label.capitalize(),
        },
        hover_data={
            "num_viviendas": True,
            "capacidad_media": ":.2f",
            "precio_mensualizado": ":.2f",
            "tipo_alojamiento": False,
        },
    )

    price_figure.update_traces(
        texttemplate="%{text:,.2f} €",
        textposition="outside",
    )

    price_figure.update_layout(
        height=max(420, len(price_df) * 45),
        xaxis_title="Average daily price (€)",
        yaxis_title=grouping_label.capitalize(),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(price_figure, width="stretch")

    st.divider()

    # =========================
    # Potential revenue by type
    # =========================
    st.subheader(f"Which {grouping_label} generates the most potential revenue?")

    revenue_df = accommodation_df.sort_values("ingreso_potencial_total", ascending=True)

    revenue_figure = px.bar(
        revenue_df,
        x="ingreso_potencial_total",
        y="tipo_alojamiento",
        orientation="h",
        text="ingreso_potencial_total",
        title=f"Total potential revenue by {grouping_label}",
        labels={
            "ingreso_potencial_total": "Total potential revenue (€)",
            "tipo_alojamiento": grouping_label.capitalize(),
        },
        hover_data={
            "num_viviendas": True,
            "precio_medio_diario": ":.2f",
            "no_disponibilidad_pct": ":.2f",
            "tipo_alojamiento": False,
        },
    )

    revenue_figure.update_traces(
        texttemplate="%{text:,.0f} €",
        textposition="outside",
    )

    revenue_figure.update_layout(
        height=max(420, len(revenue_df) * 45),
        xaxis_title="Total potential revenue (€)",
        yaxis_title=grouping_label.capitalize(),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(revenue_figure, width="stretch")

    st.divider()

    # =========================
    # Capacity vs price
    # =========================
    st.subheader("Do higher-capacity properties have a higher average price?")

    if capacity_df.empty:
        st.info(
            "There is not enough capacity data for the selected minimum number of properties."
        )
    else:
        capacity_line_df = capacity_df.sort_values("capacidad_huespedes").copy()

        capacity_figure = px.line(
            capacity_line_df,
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

        capacity_figure.update_traces(
            mode="lines+markers",
        )

        capacity_figure.update_layout(
            height=500,
            xaxis_title="Number of guests",
            yaxis_title="Average daily price (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(capacity_figure, width="stretch")

        correlation = capacity_df["capacidad_huespedes"].corr(
            capacity_df["precio_medio_diario"]
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Capacity-price correlation",
            f"{correlation:.2f}" if not pd.isna(correlation) else "-",
        )

        highest_price_capacity = capacity_df.sort_values(
            "precio_medio_diario",
            ascending=False,
        ).iloc[0]

        col2.metric(
            "Capacity with the highest average price",
            f"{int(highest_price_capacity['capacidad_huespedes'])} guests",
            format_currency_dec(highest_price_capacity["precio_medio_diario"]),
        )

        if not pd.isna(correlation):
            if correlation >= 0.6:
                st.success(
                    "There is a clear positive relationship: higher capacity is associated with a higher average price."
                )
            elif correlation >= 0.3:
                st.info(
                    "There is a moderate positive relationship between capacity and average price."
                )
            elif correlation > 0:
                st.info(
                    "There is a weak positive relationship between capacity and average price."
                )
            else:
                st.warning(
                    "No clear positive relationship between capacity and average price is observed."
                )

    st.divider()

    # =========================
    # Detailed table
    # =========================
    st.subheader(f"Details by {grouping_label}")

    table = accommodation_df.copy()

    table = table.rename(
        columns={
            "tipo_alojamiento": grouping_label.capitalize(),
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

    columns = [
        grouping_label.capitalize(),
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
        table[columns],
        width="stretch",
        hide_index=True,
    )

    st.caption("Unavailability is used as a proxy for estimated occupancy.")
