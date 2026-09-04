"""Queries for accommodation-type analysis."""

from backend.db import run_query


def get_analisis_tipo_alojamiento(
    ciudad: str | None = None,
    agrupar_por: str = "tipo_habitacion",
):
    """
    Aggregated analysis by room type or property type.
    Uses all available information in FACT_DISPONIBILIDAD_ALOJAMIENTO.
    """

    columnas_validas = {
        "tipo_habitacion": "ta.tipo_habitacion",
        "tipo_propiedad": "ta.tipo_propiedad",
    }

    if agrupar_por not in columnas_validas:
        agrupar_por = "tipo_habitacion"

    columna = columnas_validas[agrupar_por]

    sql = f"""
        SELECT
            NVL({columna}, 'Unclassified') AS tipo_alojamiento,

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
            NVL({columna}, 'Unclassified')

        ORDER BY
            precio_medio_diario DESC NULLS LAST
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
        },
    )


def get_precio_por_capacidad(
    ciudad: str | None = None,
    min_viviendas: int = 5,
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
            "ciudad": ciudad,
            "min_viviendas": min_viviendas,
        },
    )
