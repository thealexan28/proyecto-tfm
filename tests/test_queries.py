import pandas as pd
import pytest

from backend.queries import accommodation, geography, listings, ratings, rental_market


@pytest.fixture
def query_spy(monkeypatch):
    def install(module):
        calls = []

        def fake_run_query(sql, params=None):
            calls.append((sql, params))
            return pd.DataFrame()

        monkeypatch.setattr(module, "run_query", fake_run_query)
        return calls

    return install


def _compact_sql(sql):
    return " ".join(sql.split())


def test_available_cities_are_restricted_to_loaded_fact_data(query_spy):
    calls = query_spy(geography)
    geography.get_ciudades_disponibles()

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

    listings.get_viviendas_mapa(ciudad=city, barrio=neighborhood)

    sql, params = calls[0]
    assert city not in sql
    assert neighborhood not in sql
    assert "g.ciudad = :ciudad" in sql
    assert "g.barrio = :barrio" in sql
    assert params == {"ciudad": city, "barrio": neighborhood}


def test_accommodation_grouping_uses_whitelisted_column(query_spy):
    calls = query_spy(accommodation)
    accommodation.get_analisis_tipo_alojamiento(agrupar_por="tipo_propiedad")
    property_sql, _ = calls[-1]

    accommodation.get_analisis_tipo_alojamiento(
        agrupar_por="tipo_propiedad); DROP TABLE dim_vivienda; --"
    )
    fallback_sql, _ = calls[-1]

    assert "ta.tipo_propiedad" in property_sql
    assert "ta.tipo_habitacion" in fallback_sql
    assert "DROP TABLE" not in fallback_sql


def test_rental_comparison_uses_documented_reference_period(query_spy):
    calls = query_spy(rental_market)
    rental_market.get_comparativa_alquiler_ciudad()
    rental_market.get_comparativa_alquiler_barrios()

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

    ratings.get_valoraciones_viviendas(ciudad=city)

    sql, params = calls[0]
    assert city not in sql
    assert "g.ciudad = :ciudad" in sql
    assert params == {"ciudad": city}
