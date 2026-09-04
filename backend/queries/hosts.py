"""Queries for host analysis."""

from backend.db import run_query


def get_resumen_anfitriones(
    ciudad: str | None = None,
    umbral_gran_tenedor: int = 5,
):
    sql = """
        WITH anfitrion_stats AS (
            SELECT
                f.id_anfitrion,
                NVL(a.nombre_anfitrion, 'Unnamed') AS nombre_anfitrion,

                COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

                ROUND(
                    AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                    2
                ) AS precio_medio_diario,

                ROUND(
                    AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                    2
                ) AS disponibilidad_pct,

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

            LEFT JOIN dim_anfitrion a
                ON f.id_anfitrion = a.id_anfitrion

            WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
              AND g.barrio IS NOT NULL
              AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

            GROUP BY
                f.id_anfitrion,
                NVL(a.nombre_anfitrion, 'Unnamed')
        )

        SELECT
            COUNT(*) AS total_anfitriones,
            SUM(num_viviendas) AS total_viviendas,

            SUM(
                CASE 
                    WHEN num_viviendas >= :umbral_gran_tenedor 
                    THEN 1 
                    ELSE 0 
                END
            ) AS total_grandes_tenedores,

            SUM(
                CASE 
                    WHEN num_viviendas >= :umbral_gran_tenedor 
                    THEN num_viviendas 
                    ELSE 0 
                END
            ) AS viviendas_grandes_tenedores,

            ROUND(
                SUM(
                    CASE 
                        WHEN num_viviendas >= :umbral_gran_tenedor 
                        THEN num_viviendas 
                        ELSE 0 
                    END
                ) * 100 / NULLIF(SUM(num_viviendas), 0),
                2
            ) AS pct_viviendas_grandes_tenedores,

            ROUND(AVG(precio_medio_diario), 2) AS precio_medio_anfitrion,
            ROUND(AVG(disponibilidad_pct), 2) AS disponibilidad_media,
            ROUND(AVG(no_disponibilidad_pct), 2) AS no_disponibilidad_media

        FROM anfitrion_stats
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "umbral_gran_tenedor": umbral_gran_tenedor,
        },
    )


def get_top_anfitriones(
    ciudad: str | None = None,
    limite: int = 15,
):
    sql = """
        SELECT *
        FROM (
            SELECT
                f.id_anfitrion,
                NVL(a.nombre_anfitrion, 'Unnamed') AS nombre_anfitrion,

                CASE
                    WHEN UPPER(NVL(a.es_superhost, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                    THEN 'Yes'
                    ELSE 'No'
                END AS es_superhost,

                COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

                ROUND(
                    AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                    2
                ) AS precio_medio_diario,

                ROUND(
                    AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                    2
                ) AS disponibilidad_pct,

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

            LEFT JOIN dim_anfitrion a
                ON f.id_anfitrion = a.id_anfitrion

            WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
              AND g.barrio IS NOT NULL
              AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

            GROUP BY
                f.id_anfitrion,
                NVL(a.nombre_anfitrion, 'Unnamed'),
                CASE
                    WHEN UPPER(NVL(a.es_superhost, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                    THEN 'Yes'
                    ELSE 'No'
                END

            ORDER BY
                num_viviendas DESC,
                ingreso_potencial_total DESC
        )
        WHERE ROWNUM <= :limite
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "limite": limite,
        },
    )


def get_superhost_disponibilidad(ciudad: str | None = None):
    sql = """
        SELECT
            CASE
                WHEN UPPER(NVL(a.es_superhost, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                THEN 'Superhost'
                ELSE 'No superhost'
            END AS tipo_anfitrion,

            COUNT(DISTINCT f.id_anfitrion) AS num_anfitriones,
            COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS disponibilidad_pct,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) * 100,
                2
            ) AS no_disponibilidad_pct,

            ROUND(
                AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                2
            ) AS precio_medio_diario

        FROM fact_disponibilidad_alojamiento f

        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia

        LEFT JOIN dim_anfitrion a
            ON f.id_anfitrion = a.id_anfitrion

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND g.barrio IS NOT NULL
          AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

        GROUP BY
            CASE
                WHEN UPPER(NVL(a.es_superhost, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                THEN 'Superhost'
                ELSE 'No superhost'
            END

        ORDER BY
            tipo_anfitrion
    """

    return run_query(sql, {"ciudad": ciudad})


def get_grandes_tenedores_precio(
    ciudad: str | None = None,
    umbral_gran_tenedor: int = 5,
):
    sql = """
        WITH anfitrion_clase AS (
            SELECT
                f.id_anfitrion,
                COUNT(DISTINCT f.id_vivienda) AS num_viviendas_anfitrion
            FROM fact_disponibilidad_alojamiento f
            JOIN dim_geografia g
                ON f.id_geografia = g.id_geografia
            WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
              AND g.barrio IS NOT NULL
              AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'
            GROUP BY
                f.id_anfitrion
        )

        SELECT
            CASE
                WHEN ac.num_viviendas_anfitrion >= :umbral_gran_tenedor
                THEN 'Large-scale owners'
                ELSE 'Individual hosts'
            END AS tipo_tenedor,

            COUNT(DISTINCT f.id_anfitrion) AS num_anfitriones,
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
                AVG(CASE WHEN f.esta_disponible = 'S' THEN 1 ELSE 0 END) * 100,
                2
            ) AS disponibilidad_pct,

            ROUND(
                AVG(CASE WHEN f.esta_disponible = 'N' THEN 1 ELSE 0 END) * 100,
                2
            ) AS no_disponibilidad_pct,

            ROUND(
                SUM(NVL(f.ingreso_potencial_diario, 0)),
                2
            ) AS ingreso_potencial_total

        FROM fact_disponibilidad_alojamiento f

        JOIN anfitrion_clase ac
            ON f.id_anfitrion = ac.id_anfitrion

        JOIN dim_geografia g
            ON f.id_geografia = g.id_geografia

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND g.barrio IS NOT NULL
          AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

        GROUP BY
            CASE
                WHEN ac.num_viviendas_anfitrion >= :umbral_gran_tenedor
                THEN 'Large-scale owners'
                ELSE 'Individual hosts'
            END

        ORDER BY
            precio_medio_diario DESC
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "umbral_gran_tenedor": umbral_gran_tenedor,
        },
    )
