"""Queries for neighborhood concentration and revenue."""

from backend.db import run_query


def get_neighborhood_concentration(city: str | None = None, limit: int = 15):
    """
    Return the neighborhoods with the most short-term rental properties.

    Return the overall ranking when ``city`` is ``None``; otherwise, return
    the ranking for the selected city.
    """

    sql = """
        SELECT *
        FROM (
            WITH barrios AS (
                SELECT
                    g.ciudad,
                    g.barrio,
                    COUNT(DISTINCT f.id_vivienda) AS num_viviendas,
                    COUNT(*) AS registros_calendario,
                    ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario,
                    ROUND(
                        AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                        2
                    ) AS tasa_disponibilidad_pct
                FROM fact_disponibilidad_alojamiento f
                JOIN dim_geografia g
                    ON f.id_geografia = g.id_geografia
                WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
                  AND g.barrio IS NOT NULL
                  AND UPPER(g.barrio) <> 'TOTAL MUNICIPIO'
                GROUP BY
                    g.ciudad,
                    g.barrio
            ),
            totales_ciudad AS (
                SELECT
                    ciudad,
                    SUM(num_viviendas) AS total_viviendas_ciudad
                FROM barrios
                GROUP BY ciudad
            )
            SELECT
                b.ciudad,
                b.barrio,
                b.num_viviendas,
                ROUND(
                    b.num_viviendas * 100 / NULLIF(t.total_viviendas_ciudad, 0),
                    2
                ) AS porcentaje_sobre_ciudad,
                b.registros_calendario,
                b.precio_medio_diario,
                b.tasa_disponibilidad_pct
            FROM barrios b
            JOIN totales_ciudad t
                ON b.ciudad = t.ciudad
            ORDER BY
                b.num_viviendas DESC
        )
        WHERE ROWNUM <= :limite
    """

    return run_query(
        sql,
        {
            "ciudad": city,
            "limite": limit,
        },
    )


def get_neighborhood_potential_revenue(city: str | None = None, limit: int = 15):
    """
    Return the neighborhoods that generate the most potential revenue.

    Return the overall ranking when ``city`` is ``None``; otherwise, return
    the ranking for the selected city.
    """

    sql = """
        SELECT *
        FROM (
            WITH barrios AS (
                SELECT
                    g.ciudad,
                    g.barrio,

                    COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

                    ROUND(SUM(NVL(f.ingreso_potencial_diario, 0)), 2) AS ingreso_potencial_total,

                    ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario,

                    ROUND(
                        SUM(NVL(f.ingreso_potencial_diario, 0))
                        / NULLIF(COUNT(DISTINCT f.id_vivienda), 0),
                        2
                    ) AS ingreso_potencial_por_vivienda,

                    ROUND(
                        AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                        2
                    ) AS tasa_disponibilidad_pct,

                    COUNT(*) AS registros_calendario

                FROM fact_disponibilidad_alojamiento f
                JOIN dim_geografia g
                    ON f.id_geografia = g.id_geografia

                WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
                  AND g.barrio IS NOT NULL
                  AND UPPER(g.barrio) <> 'TOTAL MUNICIPIO'

                GROUP BY
                    g.ciudad,
                    g.barrio
            ),
            totales_ciudad AS (
                SELECT
                    ciudad,
                    SUM(ingreso_potencial_total) AS ingreso_total_ciudad
                FROM barrios
                GROUP BY ciudad
            )
            SELECT
                b.ciudad,
                b.barrio,
                b.num_viviendas,
                b.ingreso_potencial_total,
                ROUND(
                    b.ingreso_potencial_total * 100 / NULLIF(t.ingreso_total_ciudad, 0),
                    2
                ) AS porcentaje_ingreso_sobre_ciudad,
                b.ingreso_potencial_por_vivienda,
                b.precio_medio_diario,
                b.tasa_disponibilidad_pct,
                b.registros_calendario
            FROM barrios b
            JOIN totales_ciudad t
                ON b.ciudad = t.ciudad
            ORDER BY
                b.ingreso_potencial_total DESC
        )
        WHERE ROWNUM <= :limite
    """

    return run_query(
        sql,
        {
            "ciudad": city,
            "limite": limit,
        },
    )
