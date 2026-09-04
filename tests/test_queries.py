import re

import pandas as pd
import pytest

from backend.queries import (
    accommodation,
    geography,
    hosts,
    listings,
    neighborhoods,
    occupancy,
    overview,
    ratings,
    rental_market,
)


@pytest.fixture
def query_spy(monkeypatch):
    def install(module):
        calls = []

        def fake_run_query(sql, params=None):
            bind_names = set(re.findall(r":([A-Za-z_][A-Za-z0-9_]*)", sql))
            assert bind_names == set(params or {})
            calls.append((sql, params))
            return pd.DataFrame()

        monkeypatch.setattr(module, "run_query", fake_run_query)
        return calls

    return install


def _compact_sql(sql):
    return " ".join(sql.split())


def test_available_cities_are_restricted_to_loaded_fact_data(query_spy):
    calls = query_spy(geography)
    geography.get_available_cities()

    sql, params = calls[0]
    compact_sql = _compact_sql(sql)
    assert params is None
    assert "EXISTS" in compact_sql
    assert "fact_disponibilidad_alojamiento" in compact_sql
    assert "f.id_geografia = g.id_geografia" in compact_sql


def test_map_filters_are_bound_parameters(query_spy):
    calls = query_spy(listings)
    city = "Madrid' OR 1=1 --"
    neighborhood = "Centro"

    listings.get_map_listings(city=city, neighborhood=neighborhood)

    sql, params = calls[0]
    assert city not in sql
    assert neighborhood not in sql
    assert "g.ciudad = :ciudad" in sql
    assert "g.barrio = :barrio" in sql
    assert params == {"ciudad": city, "barrio": neighborhood}


def test_accommodation_grouping_uses_whitelisted_column(query_spy):
    calls = query_spy(accommodation)
    accommodation.get_accommodation_type_analysis(group_by="property_type")
    property_sql, _ = calls[-1]

    accommodation.get_accommodation_type_analysis(
        group_by="property_type); DROP TABLE dim_vivienda; --"
    )
    fallback_sql, _ = calls[-1]

    assert "ta.tipo_propiedad" in property_sql
    assert "ta.tipo_habitacion" in fallback_sql
    assert "DROP TABLE" not in fallback_sql


def test_rental_comparison_uses_documented_reference_period(query_spy):
    calls = query_spy(rental_market)
    rental_market.get_city_rental_comparison()
    rental_market.get_neighborhood_rental_comparison()

    city_params = calls[0][1]
    neighborhood_params = calls[1][1]
    expected_dates = {
        "fecha_inicio": rental_market.RENTAL_COMPARISON_START_DATE,
        "fecha_fin": rental_market.RENTAL_COMPARISON_END_DATE,
        "fecha_contexto": rental_market.RENTAL_CONTEXT_DATE,
    }

    assert {key: city_params[key] for key in expected_dates} == expected_dates
    assert {key: neighborhood_params[key] for key in expected_dates} == expected_dates


def test_ratings_city_filter_is_bound(query_spy):
    calls = query_spy(ratings)
    city = "Málaga"

    ratings.get_listing_ratings(city=city)

    sql, params = calls[0]
    assert city not in sql
    assert "g.ciudad = :ciudad" in sql
    assert params == {"ciudad": city}


@pytest.mark.parametrize(
    ("module", "function_name", "kwargs"),
    [
        (accommodation, "get_accommodation_type_analysis", {}),
        (accommodation, "get_price_by_capacity", {}),
        (geography, "get_available_cities", {}),
        (geography, "get_available_neighborhoods_by_city", {"city": "Madrid"}),
        (hosts, "get_host_summary", {}),
        (hosts, "get_large_owner_prices", {}),
        (hosts, "get_superhost_availability", {}),
        (hosts, "get_top_hosts", {}),
        (listings, "get_map_listings", {"city": "Madrid", "neighborhood": "Centro"}),
        (neighborhoods, "get_neighborhood_concentration", {}),
        (neighborhoods, "get_neighborhood_potential_revenue", {}),
        (occupancy, "get_monthly_occupancy", {}),
        (occupancy, "get_occupancy_by_season", {}),
        (overview, "get_availability_by_season", {}),
        (overview, "get_city_summary", {}),
        (overview, "get_overview_kpis", {}),
        (overview, "get_top_neighborhoods", {}),
        (ratings, "get_best_rated_neighborhoods", {}),
        (ratings, "get_instant_booking_availability", {}),
        (ratings, "get_listing_ratings", {"city": "Madrid"}),
        (rental_market, "get_city_rental_comparison", {}),
        (rental_market, "get_neighborhood_rental_comparison", {}),
    ],
)
def test_all_query_bind_parameters_match_sql(query_spy, module, function_name, kwargs):
    calls = query_spy(module)

    getattr(module, function_name)(**kwargs)

    assert len(calls) == 1
