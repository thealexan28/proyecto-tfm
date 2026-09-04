"""Queries for seasonal and monthly occupancy analysis."""

from backend.db import run_query


def get_ocupacion_por_temporada(ciudad: str | None = None, barrio: str | None = None):
    """
    Responde a la pregunta:
    How does estimated occupancy vary by season?

    Estimated occupancy is calculated as the percentage of records
    en los que el alojamiento aparece como no disponible.
    """

    sql = """
        SELECT
            g.ciudad,
            t.temporada,

            COUNT(*) AS registros_calendario,

            COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

            SUM(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) AS noches_ocupadas_estimadas,

            SUM(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) AS noches_disponibles,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) * 100,
                2
            ) AS ocupacion_estimada_pct,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS disponibilidad_pct,

            ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario,

            ROUND(SUM(NVL(f.ingreso_potencial_diario, 0)), 2) AS ingreso_potencial_total

        FROM fact_disponibilidad_alojamiento f

        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia

        JOIN dim_tiempo t
            ON f.id_tiempo = t.id_tiempo

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND (:barrio IS NULL OR g.barrio = :barrio)
          AND t.temporada IS NOT NULL
          AND g.barrio IS NOT NULL
          AND UPPER(g.barrio) <> 'TOTAL MUNICIPIO'

        GROUP BY
            g.ciudad,
            t.temporada

        ORDER BY
            g.ciudad,
            CASE t.temporada
                WHEN 'Baja' THEN 1
                WHEN 'Media' THEN 2
                WHEN 'Alta' THEN 3
                ELSE 4
            END
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "barrio": barrio,
        },
    )


def get_ocupacion_mensual(ciudad: str | None = None, barrio: str | None = None):
    """
    Returns the monthly estimated occupancy trend.
    """

    sql = """
        SELECT
            g.ciudad,
            t.anio,
            t.mes,
            t.anio || '-' || LPAD(t.mes, 2, '0') AS periodo,

            COUNT(*) AS registros_calendario,

            COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

            SUM(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) AS noches_ocupadas_estimadas,

            SUM(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) AS noches_disponibles,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) * 100,
                2
            ) AS ocupacion_estimada_pct,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS disponibilidad_pct,

            ROUND(AVG(f.precio_ajustado_diario), 2) AS precio_medio_diario

        FROM fact_disponibilidad_alojamiento f

        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia

        JOIN dim_tiempo t
            ON f.id_tiempo = t.id_tiempo

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND (:barrio IS NULL OR g.barrio = :barrio)
          AND g.barrio IS NOT NULL
          AND UPPER(g.barrio) <> 'TOTAL MUNICIPIO'

        GROUP BY
            g.ciudad,
            t.anio,
            t.mes

        ORDER BY
            g.ciudad,
            t.anio,
            t.mes
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "barrio": barrio,
        },
    )
