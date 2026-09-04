import pandas as pd
import plotly.express as px
import streamlit as st

from backend.queries import (
    get_available_cities,
    get_host_summary,
    get_top_hosts,
    get_superhost_availability,
    get_large_owner_prices,
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


def build_host_labels(df):
    df = df.copy()
    names = df["nombre_anfitrion"].fillna("Unnamed")
    duplicate_names = names.duplicated(keep=False)
    ids = df["id_anfitrion"].apply(
        lambda value: str(int(value)) if pd.notna(value) else "unknown"
    )
    df["label"] = names.where(
        ~duplicate_names,
        names + " (ID " + ids + ")",
    )
    return df


def render_hosts():
    st.title("👤 Host analysis")

    st.markdown(
        """
        Analyzes property concentration by host and compares prices,
        availability, and potential revenue across management profiles.
        """
    )

    st.divider()

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
        large_owner_threshold = st.slider(
            "Large-scale owner threshold",
            min_value=2,
            max_value=20,
            value=5,
            step=1,
        )

    with col3:
        limit = st.slider(
            "Hosts to display",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    city_filter = None if selected_city == "All cities" else selected_city

    summary_df = get_host_summary(
        city=city_filter,
        large_owner_threshold=large_owner_threshold,
    )

    top_df = get_top_hosts(
        city=city_filter,
        limit=limit,
    )

    superhost_df = get_superhost_availability(
        city=city_filter,
    )

    owner_types_df = get_large_owner_prices(
        city=city_filter,
        large_owner_threshold=large_owner_threshold,
    )

    if summary_df.empty:
        st.warning("No data is available for the selected filters.")
        return

    summary = summary_df.iloc[0]

    # =========================
    # Main results
    # =========================
    st.subheader("Key indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Hosts",
        format_number(summary["total_anfitriones"]),
    )

    col2.metric(
        "Properties",
        format_number(summary["total_viviendas"]),
    )

    col3.metric(
        "Large-scale owners",
        format_number(summary["total_grandes_tenedores"]),
    )

    col4.metric(
        "Properties managed by large-scale owners",
        format_pct(summary["pct_viviendas_grandes_tenedores"]),
        format_number(summary["viviendas_grandes_tenedores"]),
    )

    st.caption(
        f"Active threshold: large-scale owner = {large_owner_threshold} or more properties."
    )

    st.divider()

    # =========================
    # Top hosts
    # =========================
    st.subheader("Which hosts manage the most properties?")

    if not top_df.empty:
        top_df = build_host_labels(top_df)

        df_chart = top_df.sort_values("num_viviendas", ascending=True)

        top_figure = px.bar(
            df_chart,
            x="num_viviendas",
            y="label",
            orientation="h",
            text="num_viviendas",
            title=f"Top {limit} hosts by number of properties",
            labels={
                "num_viviendas": "Number of properties",
                "label": "Host",
            },
            hover_data={
                "es_superhost": True,
                "precio_medio_diario": ":.2f",
                "disponibilidad_pct": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "ingreso_potencial_total": ":.2f",
                "label": False,
            },
        )

        top_figure.update_traces(textposition="outside")

        top_figure.update_layout(
            height=max(450, limit * 34),
            xaxis_title="Number of properties",
            yaxis_title="Host",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(top_figure, width="stretch")

    st.divider()

    # =========================
    # Superhost availability
    # =========================
    st.subheader("Do Superhosts have higher availability or unavailability?")

    if not superhost_df.empty:
        superhost_melt_df = superhost_df.melt(
            id_vars=["tipo_anfitrion", "num_anfitriones", "num_viviendas"],
            value_vars=["disponibilidad_pct", "no_disponibilidad_pct"],
            var_name="Metric",
            value_name="Percentage",
        )

        superhost_melt_df["Metric"] = superhost_melt_df["Metric"].replace(
            {
                "disponibilidad_pct": "Availability",
                "no_disponibilidad_pct": "Unavailability",
            }
        )

        superhost_figure = px.bar(
            superhost_melt_df,
            x="tipo_anfitrion",
            y="Percentage",
            color="Metric",
            barmode="group",
            text="Percentage",
            title="Availability and unavailability by host type",
            labels={
                "tipo_anfitrion": "Host type",
                "Percentage": "Percentage (%)",
            },
        )

        superhost_figure.update_traces(
            texttemplate="%{text:.2f} %",
            textposition="outside",
        )

        superhost_figure.update_layout(
            height=450,
            yaxis_range=[0, 100],
            xaxis_title="",
            yaxis_title="Percentage (%)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(superhost_figure, width="stretch")

    st.divider()

    # =========================
    # Large-scale owners vs individual hosts
    # =========================
    st.subheader("Do large-scale owners charge higher prices than individual hosts?")

    if not owner_types_df.empty:
        price_figure = px.bar(
            owner_types_df,
            x="tipo_tenedor",
            y="precio_medio_diario",
            text="precio_medio_diario",
            title="Average daily price by owner type",
            labels={
                "tipo_tenedor": "Host type",
                "precio_medio_diario": "Average daily price (€)",
            },
            hover_data={
                "num_anfitriones": True,
                "num_viviendas": True,
                "disponibilidad_pct": ":.2f",
                "no_disponibilidad_pct": ":.2f",
                "ingreso_potencial_total": ":.2f",
            },
        )

        price_figure.update_traces(
            texttemplate="%{text:.2f} €",
            textposition="outside",
        )

        price_figure.update_layout(
            height=430,
            xaxis_title="",
            yaxis_title="Average daily price (€)",
            margin=dict(l=20, r=20, t=70, b=20),
        )

        st.plotly_chart(price_figure, width="stretch")

        if len(owner_types_df) >= 2:
            highest_price = owner_types_df.sort_values(
                "precio_medio_diario",
                ascending=False,
            ).iloc[0]

            st.info(
                f"""
                The group with the highest average daily price is **{highest_price["tipo_tenedor"]}**
                at **{format_currency_dec(highest_price["precio_medio_diario"])}**.
                """
            )

    st.divider()

    # =========================
    # Detailed table
    # =========================
    st.subheader("Detailed host table")

    if not top_df.empty:
        table = build_host_labels(top_df)

        table = table.rename(
            columns={
                "label": "Host",
                "es_superhost": "Superhost",
                "num_viviendas": "No. of properties",
                "precio_medio_diario": "Average daily price",
                "disponibilidad_pct": "Availability (%)",
                "no_disponibilidad_pct": "Unavailability (%)",
                "ingreso_potencial_total": "Total potential revenue",
            }
        )

        columns = [
            "Host",
            "Superhost",
            "No. of properties",
            "Average daily price",
            "Availability (%)",
            "Unavailability (%)",
            "Total potential revenue",
        ]

        st.dataframe(
            table[columns],
            width="stretch",
            hide_index=True,
        )
