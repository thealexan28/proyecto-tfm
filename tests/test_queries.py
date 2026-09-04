import pandas as pd
import pytest

from backend import queries


@pytest.fixture
def query_spy(monkeypatch):
    calls = []

    def fake_run_query(sql, params=None):
        calls.append((sql, params))
        return pd.DataFrame()

    monkeypatch.setattr(queries, "run_query", fake_run_query)
    return calls


def _compact_sql(sql):
    return " ".join(sql.split())


def test_available_cities_are_restricted_to_loaded_fact_data(query_spy):
    queries.get_ciudades_disponibles()

    sql, params = query_spy[0]
    compact_sql = _compact_sql(sql)
    assert params is None
    assert "EXISTS" in compact_sql
    assert "fact_disponibilidad_alojamiento" in compact_sql
    assert "f.id_geografia = g.id_geografia" in compact_sql


def test_map_filters_are_bound_parameters(query_spy):
    city = "Madrid' OR 1=1 --"
    neighborhood = "Centro"

    queries.get_viviendas_mapa(ciudad=city, barrio=neighborhood)

    sql, params = query_spy[0]
    assert city not in sql
    assert neighborhood not in sql
    assert "g.ciudad = :ciudad" in sql
    assert "g.barrio = :barrio" in sql
    assert params == {"ciudad": city, "barrio": neighborhood}


def test_accommodation_grouping_uses_whitelisted_column(query_spy):
    queries.get_analisis_tipo_alojamiento(agrupar_por="tipo_propiedad")
    property_sql, _ = query_spy[-1]

    queries.get_analisis_tipo_alojamiento(
        agrupar_por="tipo_propiedad); DROP TABLE dim_vivienda; --"
    )
    fallback_sql, _ = query_spy[-1]

    assert "ta.tipo_propiedad" in property_sql
    assert "ta.tipo_habitacion" in fallback_sql
    assert "DROP TABLE" not in fallback_sql


def test_rental_comparison_uses_documented_reference_period(query_spy):
    queries.get_comparativa_alquiler_ciudad()
    queries.get_comparativa_alquiler_barrios()

    city_params = query_spy[0][1]
    neighborhood_params = query_spy[1][1]
    expected_dates = {
        "fecha_inicio": queries.RENTAL_COMPARISON_START_DATE,
        "fecha_fin": queries.RENTAL_COMPARISON_END_DATE,
        "fecha_contexto": queries.RENTAL_CONTEXT_DATE,
    }

    assert {key: city_params[key] for key in expected_dates} == expected_dates
    assert {key: neighborhood_params[key] for key in expected_dates} == expected_dates


def test_ratings_city_filter_is_bound(query_spy):
    city = "Málaga"

    queries.get_valoraciones_viviendas(ciudad=city)

    sql, params = query_spy[0]
    assert city not in sql
    assert "g.ciudad = :ciudad" in sql
    assert params == {"ciudad": city}
