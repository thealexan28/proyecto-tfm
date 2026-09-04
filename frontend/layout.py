import streamlit as st
import plotly.express as px

from frontend.i18n import install_data_translation_hooks


MAIN_NAV_ITEMS = [
    ("app.py", "Main dashboard"),
    ("pages/4_Property_map.py", "Property map"),
]


REQUIRED_NAV_ITEMS = [
    ("pages/1_Neighborhood_concentration.py", "1. Neighborhood concentration"),
    ("pages/2_Potential_revenue.py", "2. Potential revenue"),
    ("pages/5_Airbnb_vs_rent.py", "3. Airbnb vs long-term rentals"),
    ("pages/3_Seasonal_occupancy.py", "4. Seasonal occupancy"),
]


COMPLEMENTARY_NAV_ITEMS = [
    ("pages/6_Accommodation_type.py", "Property type"),
    ("pages/7_Hosts.py", "Hosts"),
    ("pages/8_Ratings.py", "Ratings"),
]


SOURCE_ITEMS = [
    ("Inside Airbnb", "https://insideairbnb.com/get-the-data/"),
    ("INE", "https://www.ine.es/"),
]


def apply_global_styles():
    px.defaults.template = "plotly_white"
    px.defaults.color_discrete_sequence = [
        "#2563eb",
        "#16a34a",
        "#f97316",
        "#9333ea",
        "#0f766e",
        "#dc2626",
    ]

    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"],
            #MainMenu,
            footer {
                display: none;
            }

            .block-container {
                max-width: 1280px;
                padding-top: 2.25rem;
                padding-bottom: 3rem;
            }

            h1 {
                font-size: clamp(2rem, 3vw, 3rem);
                line-height: 1.08;
                margin-bottom: 0.35rem;
            }

            h2, h3 {
                margin-top: 0.35rem;
            }

            div[data-testid="stMetric"] {
                background: var(--secondary-background-color);
                color: var(--text-color);
                border: 1px solid rgba(120, 120, 120, 0.22);
                border-radius: 8px;
                padding: 1rem 1.1rem;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
                min-height: 112px;
            }

            div[data-testid="stMetric"] label {
                color: var(--text-color);
                opacity: 0.78;
                font-weight: 600;
            }

            div[data-testid="stMetricValue"] {
                color: var(--text-color);
            }

            div[data-testid="stAlert"] {
                border-radius: 8px;
            }

            div[data-testid="stDataFrame"],
            div[data-testid="stPlotlyChart"],
            .stDeckGlJsonChart {
                border: 1px solid rgba(120, 120, 120, 0.22);
                border-radius: 8px;
                overflow: hidden;
                background: var(--background-color);
            }

            section[data-testid="stSidebar"] {
                border-right: 1px solid rgba(120, 120, 120, 0.22);
            }

            section[data-testid="stSidebar"] h1 {
                font-size: 1.35rem;
                margin-bottom: 0;
            }

            section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
                margin-bottom: 0.35rem;
            }

            section[data-testid="stSidebar"] a {
                text-decoration: none;
            }

            section[data-testid="stSidebar"] a:hover {
                text-decoration: underline;
            }

            div[data-testid="stHorizontalBlock"] {
                gap: 1rem;
            }

            hr {
                margin: 1.75rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        st.title("Tourism analysis")
        st.caption("Airbnb rental platform")

        st.markdown("### Home")
        for page_path, label in MAIN_NAV_ITEMS:
            st.page_link(page_path, label=label)

        st.markdown("### Core analysis")
        for page_path, label in REQUIRED_NAV_ITEMS:
            st.page_link(page_path, label=label)

        st.markdown("### Additional analysis")
        for page_path, label in COMPLEMENTARY_NAV_ITEMS:
            st.page_link(page_path, label=label)

        st.divider()
        st.markdown("### Main sources")
        for label, url in SOURCE_ITEMS:
            st.markdown(f"- [{label}]({url})")


def configure_page(page_title, page_icon=":house_with_garden:"):
    install_data_translation_hooks()
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_global_styles()
    render_sidebar()
