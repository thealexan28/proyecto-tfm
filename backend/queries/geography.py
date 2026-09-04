"""Queries for available geographic filters."""

from backend.db import run_query


def get_ciudades_disponibles():
    """Return only cities with records in the accommodation fact table."""

    sql = """
        SELECT DISTINCT
            g.ciudad
        FROM dim_geografia g
        WHERE g.ciudad IS NOT NULL
          AND EXISTS (
              SELECT 1
              FROM fact_disponibilidad_alojamiento f
              WHERE f.id_geografia = g.id_geografia
          )
        ORDER BY g.ciudad
    """

    return run_query(sql)


def get_barrios_disponibles_por_ciudad(ciudad: str):
    """
    Devuelve los barrios disponibles para una ciudad concreta.
    """

    sql = """
        SELECT DISTINCT
            g.barrio
        FROM dim_geografia g
        WHERE g.ciudad = :ciudad
          AND g.barrio IS NOT NULL
          AND UPPER(g.barrio) <> 'TOTAL MUNICIPIO'
          AND EXISTS (
              SELECT 1
              FROM fact_disponibilidad_alojamiento f
              WHERE f.id_geografia = g.id_geografia
          )
        ORDER BY g.barrio
    """

    return run_query(sql, {"ciudad": ciudad})
