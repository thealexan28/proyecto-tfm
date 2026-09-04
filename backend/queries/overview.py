"""Queries for the main dashboard overview."""

from backend.db import run_query


def get_overview_kpis():
    sql = """
        SELECT
            COUNT(DISTINCT f.id_vivienda) AS total_viviendas,
            COUNT(*) AS total_registros_calendario,
            COUNT(DISTINCT g.ciudad) AS total_ciudades,
            ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario,
            ROUND(SUM(f.ingreso_potencial_diario), 2) AS ingreso_potencial_total,
            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS tasa_disponibilidad_pct
        FROM fact_disponibilidad_alojamiento f
        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia
        WHERE f.precio_ajustado_diario IS NOT NULL
    """
    return run_query(sql)


def get_city_summary():
    sql = """
        SELECT
            g.ciudad,
            COUNT(DISTINCT f.id_vivienda) AS num_viviendas,
            COUNT(*) AS registros_calendario,
            ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario,
            ROUND(SUM(f.ingreso_potencial_diario), 2) AS ingreso_potencial_total,
            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS tasa_disponibilidad_pct
        FROM fact_disponibilidad_alojamiento f
        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia
        WHERE f.precio_ajustado_diario IS NOT NULL
        GROUP BY
            g.ciudad
        ORDER BY
            num_viviendas DESC
    """
    return run_query(sql)


def get_top_neighborhoods(limit: int = 10):
    sql = """
        SELECT *
        FROM (
            SELECT
                g.ciudad,
                g.barrio,
                COUNT(DISTINCT f.id_vivienda) AS num_viviendas,
                ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario,
                ROUND(SUM(f.ingreso_potencial_diario), 2) AS ingreso_potencial_total
            FROM fact_disponibilidad_alojamiento f
            JOIN dim_geografia g
                ON f.id_geografia = g.id_geografia
            WHERE f.precio_ajustado_diario IS NOT NULL
            GROUP BY
                g.ciudad,
                g.barrio
            ORDER BY
                num_viviendas DESC
        )
        WHERE ROWNUM <= :limit
    """
    return run_query(sql, {"limit": limit})


def get_availability_by_season():
    sql = """
        SELECT
            g.ciudad,
            t.temporada,
            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS tasa_disponibilidad_pct,
            ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario
        FROM fact_disponibilidad_alojamiento f
        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia
        JOIN dim_tiempo t
            ON f.id_tiempo = t.id_tiempo
        WHERE f.precio_ajustado_diario IS NOT NULL
        GROUP BY
            g.ciudad,
            t.temporada
        ORDER BY
            g.ciudad,
            t.temporada
    """
    return run_query(sql)
