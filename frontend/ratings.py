import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_available_cities,
    get_best_rated_neighborhoods,
    get_listing_ratings,
    get_instant_booking_availability,
)


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


def add_review_volume_order(df):
    """
    Converts the categorical volumen_resenas field into a numeric order
    so a trend can be plotted.
    """

    df = df.copy()

    def calculate_order(value):
        if pd.isna(value):
            return float("nan")

        text = str(value).lower().strip()

        if "sin" in text or text == "0":
            return 0

        if "bajo" in text or "poca" in text or "1" in text:
            return 1

        if "medio" in text or "moderado" in text:
            return 2

        if "alto" in text and "muy" not in text:
            return 3

        if "muy" in text:
            return 4

        return float("nan")

    df["volumen_resenas"] = df["volumen_resenas"].fillna("Unclassified")
    df["review_volume_order"] = df["volumen_resenas"].apply(calculate_order)

    return df


def exclude_price_outliers(df):
    prices = df["precio_medio_diario"].dropna()
    if prices.empty:
        return df.copy()

    q1 = prices.quantile(0.25)
    q3 = prices.quantile(0.75)
    upper_limit = q3 + 1.5 * (q3 - q1)

    return df[
        df["precio_medio_diario"].notna() & (df["precio_medio_diario"] <= upper_limit)
    ].copy()


def create_scatter_sample(df, max_per_city=250):
    samples = []

    for _, group in df.groupby("ciudad", dropna=False):
        samples.append(
            group.sample(
                n=min(len(group), max_per_city),
                random_state=42,
            )
        )

    if not samples:
        return df.copy()

    return pd.concat(samples, ignore_index=True)


def prepare_neighborhood_rating_chart(df, include_city):
    """Build and sort the neighborhood labels used by the ratings chart."""

    result = df.copy()
    if include_city:
        result["area_label"] = result["barrio"] + " (" + result["ciudad"] + ")"
    else:
        result["area_label"] = result["barrio"]

    return result.sort_values("puntuacion_media", ascending=True)


def render_ratings():
    st.title("⭐ Ratings analysis")

    st.markdown(
        """
        Explores the relationship between ratings, price, availability, review
        volume, and instant booking.
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

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_city = st.selectbox(
            "Select a city",
            options=["All cities"] + cities,
            index=0,
        )

    with col2:
        limit = st.slider(
            "Neighborhoods to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    with col3:
        min_listings = st.slider(
            "Minimum properties per neighborhood",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
        )

    city_filter = None if selected_city == "All cities" else selected_city

    # =========================
    # Data loading
    # =========================
    neighborhoods_df = get_best_rated_neighborhoods(
        city=city_filter,
        limit=limit,
        min_listings=min_listings,
    )

    listings_df = get_listing_ratings(
        city=city_filter,
    )

    booking_df = get_instant_booking_availability(
        city=city_filter,
    )

    if listings_df.empty:
        st.warning("No rating data is available for the selected filters.")
        return

    review_volume_listings_df = add_review_volume_order(listings_df)
    price_listings_df = exclude_price_outliers(listings_df)
    scatter_listings_df = create_scatter_sample(price_listings_df)

    # =========================
    # Main KPIs
    # =========================
    st.subheader("Key indicators")

    average_rating = listings_df["puntuacion_general"].mean()
    average_price = listings_df["precio_medio_diario"].mean()
    average_unavailability = listings_df["no_disponibilidad_pct"].mean()

    rating_price_correlation = price_listings_df["puntuacion_general"].corr(
        price_listings_df["precio_medio_diario"]
    )

    reviews_unavailability_correlation = review_volume_listings_df[
        "review_volume_order"
    ].corr(review_volume_listings_df["no_disponibilidad_pct"])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Average rating",
        f"{average_rating:.2f}" if not pd.isna(average_rating) else "-",
    )

    col2.metric(
        "Average price",
        format_currency_dec(average_price),
    )

    col3.metric(
        "Average unavailability",
        format_pct(average_unavailability),
    )

    col4.metric(
        "Rated properties",
        format_number(len(listings_df)),
    )

    col5, col6 = st.columns(2)

    col5.metric(
        "Rating-price correlation",
        f"{rating_price_correlation:.2f}"
        if not pd.isna(rating_price_correlation)
        else "-",
    )

    col6.metric(
        "Reviews-unavailability correlation",
        f"{reviews_unavailability_correlation:.2f}"
        if not pd.isna(reviews_unavailability_correlation)
        else "-",
    )

    st.divider()

    # =========================
    # Highest-rated neighborhoods
    # =========================
    st.subheader("Which neighborhoods have the highest-rated properties?")

    if not neighborhoods_df.empty:
        df_chart = prepare_neighborhood_rating_chart(
            neighborhoods_df,
            include_city=city_filter is None,
        )

        neighborhoods_figure = px.bar(
            df_chart,
            x="puntuacion_media",
            y="area_label",
            orientation="h",
            text="puntuacion_media",
            title=f"Top {limit} neighborhoods by average rating",
            labels={
                "puntuacion_media": "Average rating",
                "area_label": "Neighborhood",
            },
            hover_data={
                "num_viviendas": True,
                "precio_medio_diario": ":.2f",
                "disponibilidad_pct": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "area_label": False,
            },
        )

        neighborhoods_figure.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )

        neighborhoods_figure.update_layout(
            height=max(450, limit * 34),
            xaxis_title="Average rating",
            yaxis_title="Neighborhood",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(neighborhoods_figure, width="stretch")

        st.caption(
            "The ranking only includes neighborhoods that meet the selected minimum property count."
        )

    else:
        st.info("Not enough neighborhoods meet the selected minimum property count.")

    st.divider()

    # =========================
    # Rating vs price
    # =========================
    st.subheader("Is there a relationship between average rating and price?")

    price_figure = px.scatter(
        scatter_listings_df,
        x="puntuacion_general",
        y="precio_medio_diario",
        hover_name="nombre_anuncio",
        color="ciudad" if city_filter is None else None,
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

    price_figure.update_traces(
        marker={
            "size": 7,
            "line": {"width": 0},
        }
    )

    price_figure.update_layout(
        height=500,
        xaxis_title="Overall rating",
        yaxis_title="Average daily price (€)",
        legend_title_text="City",
        hovermode="closest",
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(price_figure, width="stretch")
    st.caption(
        "Reproducible sample of up to 250 properties per city; "
        "the correlation is calculated using all valid records."
    )

    if not pd.isna(rating_price_correlation):
        if rating_price_correlation >= 0.4:
            st.success("A positive relationship between rating and price is observed.")
        elif rating_price_correlation > 0:
            st.info("The relationship between rating and price is positive but weak.")
        elif rating_price_correlation < 0:
            st.warning(
                "No positive relationship is observed; the correlation is negative."
            )
        else:
            st.info("No clear relationship between rating and price is observed.")

    st.divider()

    # =========================
    # Review volume vs unavailability
    # =========================
    st.subheader("Do properties with more reviews have higher unavailability?")

    review_groups_df = (
        review_volume_listings_df.groupby(
            ["volumen_resenas", "review_volume_order"], observed=True
        )
        .agg(
            listing_count=("id_vivienda", "nunique"),
            average_unavailability=("no_disponibilidad_pct", "mean"),
            average_daily_price=("precio_medio_diario", "mean"),
        )
        .reset_index()
        .sort_values("review_volume_order")
    )

    reviews_figure = px.line(
        review_groups_df,
        x="volumen_resenas",
        y="average_unavailability",
        markers=True,
        title="Average unavailability by review volume",
        labels={
            "volumen_resenas": "Review volume",
            "average_unavailability": "Average unavailability (%)",
        },
        hover_data={
            "listing_count": True,
            "average_daily_price": ":.2f",
        },
    )

    reviews_figure.update_traces(mode="lines+markers")

    reviews_figure.update_layout(
        height=470,
        xaxis_title="Review volume",
        yaxis_title="Average unavailability (%)",
        yaxis_range=[0, 100],
        margin=dict(l=20, r=20, t=70, b=20),
    )

    st.plotly_chart(reviews_figure, width="stretch")

    if not pd.isna(reviews_unavailability_correlation):
        if reviews_unavailability_correlation >= 0.4:
            st.success(
                "Properties with more reviews tend to have higher unavailability."
            )
        elif reviews_unavailability_correlation > 0:
            st.info(
                "The relationship between review volume and unavailability is positive but weak."
            )
        elif reviews_unavailability_correlation < 0:
            st.warning(
                "No positive relationship is observed; the correlation is negative."
            )
        else:
            st.info(
                "No clear relationship between review volume and unavailability is observed."
            )

    st.divider()

    # =========================
    # Instant booking
    # =========================
    st.subheader("Do properties with instant booking have higher availability?")

    if not booking_df.empty:
        booking_melt = booking_df.melt(
            id_vars=["tipo_reserva", "num_viviendas"],
            value_vars=["disponibilidad_pct", "no_disponibilidad_pct"],
            var_name="Metric",
            value_name="Percentage",
        )

        booking_melt["Metric"] = booking_melt["Metric"].replace(
            {
                "disponibilidad_pct": "Availability",
                "no_disponibilidad_pct": "Unavailability",
            }
        )

        booking_figure = px.bar(
            booking_melt,
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

        booking_figure.update_traces(
            texttemplate="%{text:.2f} %",
            textposition="outside",
        )

        booking_figure.update_layout(
            height=450,
            yaxis_range=[0, 100],
            xaxis_title="",
            yaxis_title="Percentage (%)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(booking_figure, width="stretch")

        if len(booking_df) >= 2:
            highest_availability = booking_df.sort_values(
                "disponibilidad_pct",
                ascending=False,
            ).iloc[0]

            st.info(
                f"""
                The group with the highest average availability is **{highest_availability["tipo_reserva"]}**
                at **{format_pct(highest_availability["disponibilidad_pct"])}**.
                """
            )

    else:
        st.info("There is not enough instant-booking data.")

    st.divider()

    # =========================
    # Detailed table
    # =========================
    st.subheader("Detailed table of rated properties")

    table = listings_df.copy()

    table = table.rename(
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

    columns = [
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
        table[columns],
        width="stretch",
        hide_index=True,
    )

    st.caption("Unavailability is used as a proxy for estimated occupancy.")
