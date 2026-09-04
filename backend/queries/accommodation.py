"""Queries for accommodation-type analysis."""

from backend.db import run_query


def get_accommodation_type_analysis(
    city: str | None = None,
    group_by: str = "room_type",
):
    """
    Aggregated analysis by room type or property type.
    Uses all available information in FACT_DISPONIBILIDAD_ALOJAMIENTO.
    """

    valid_columns = {
        "room_type": "ta.tipo_habitacion",
        "property_type": "ta.tipo_propiedad",
    }

    if group_by not in valid_columns:
        group_by = "room_type"

    column = valid_columns[group_by]

    sql = f"""
        SELECT
            NVL({column}, 'Unclassified') AS tipo_alojamiento,

            COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

            COUNT(*) AS registros_calendario,

            COUNT(NVL(f.precio_ajustado_diario, f.precio_diario)) AS registros_con_precio,

            ROUND(
                AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                2
            ) AS precio_medio_diario,

            ROUND(
                AVG(NVL(f.precio_ajustado_diario, f.precio_diario)) * 30,
                2
            ) AS precio_mensualizado,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) * 100,
                2
            ) AS no_disponibilidad_pct,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS disponibilidad_pct,

            ROUND(
                SUM(NVL(f.ingreso_potencial_diario, 0)),
                2
            ) AS ingreso_potencial_total,

            ROUND(
                AVG(ta.capacidad_huespedes),
                2
            ) AS capacidad_media

        FROM fact_disponibilidad_alojamiento f

        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia

        LEFT JOIN dim_tipo_alojamiento ta
            ON f.id_tipo_alojamiento = ta.id_tipo_alojamiento

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND g.barrio IS NOT NULL
          AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

        GROUP BY
            NVL({column}, 'Unclassified')

        ORDER BY
            precio_medio_diario DESC NULLS LAST
    """

    return run_query(
        sql,
        {
            "ciudad": city,
        },
    )


def get_price_by_capacity(
    city: str | None = None,
    min_listings: int = 5,
):
    """
    Relationship between property capacity and average daily price.
    Uses all available information in FACT_DISPONIBILIDAD_ALOJAMIENTO.
    """

    sql = """
        SELECT
            ta.capacidad_huespedes,

            COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

            ROUND(
                AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                2
            ) AS precio_medio_diario,

            ROUND(
                AVG(NVL(f.precio_ajustado_diario, f.precio_diario)) * 30,
                2
            ) AS precio_mensualizado,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) * 100,
                2
            ) AS no_disponibilidad_pct,

            ROUND(
                SUM(NVL(f.ingreso_potencial_diario, 0)),
                2
            ) AS ingreso_potencial_total

        FROM fact_disponibilidad_alojamiento f

        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia

        LEFT JOIN dim_tipo_alojamiento ta
            ON f.id_tipo_alojamiento = ta.id_tipo_alojamiento

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND ta.capacidad_huespedes IS NOT NULL
          AND g.barrio IS NOT NULL
          AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

        GROUP BY
            ta.capacidad_huespedes

        HAVING COUNT(DISTINCT f.id_vivienda) >= :min_viviendas

        ORDER BY
            ta.capacidad_huespedes
    """

    return run_query(
        sql,
        {
            "ciudad": city,
            "min_viviendas": min_listings,
        },
    )
