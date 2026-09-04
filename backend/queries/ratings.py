"""Queries for ratings analysis."""

from backend.db import run_query


def get_best_rated_neighborhoods(
    city: str | None = None,
    limit: int = 15,
    min_listings: int = 10,
):
    sql = """
        SELECT *
        FROM (
            SELECT
                g.ciudad,
                g.barrio,

                COUNT(DISTINCT f.id_vivienda) AS num_viviendas,

                ROUND(
                    AVG(val.puntuacion_general),
                    2
                ) AS puntuacion_media,

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
                ) AS no_disponibilidad_pct

            FROM fact_disponibilidad_alojamiento f

            JOIN dim_geografia g
                ON f.id_geografia = g.id_geografia

            LEFT JOIN dim_valoracion val
                ON f.id_valoracion = val.id_valoracion

            WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
              AND g.barrio IS NOT NULL
              AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'
              AND val.puntuacion_general IS NOT NULL

            GROUP BY
                g.ciudad,
                g.barrio

            HAVING COUNT(DISTINCT f.id_vivienda) >= :min_viviendas

            ORDER BY
                puntuacion_media DESC NULLS LAST,
                num_viviendas DESC
        )
        WHERE ROWNUM <= :limite
    """

    return run_query(
        sql,
        {
            "ciudad": city,
            "limite": limit,
            "min_viviendas": min_listings,
        },
    )


def get_listing_ratings(
    city: str | None = None,
):
    filters = [
        "g.barrio IS NOT NULL",
        "UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'",
    ]
    params = {}

    if city is not None:
        filters.append("g.ciudad = :ciudad")
        params["ciudad"] = city

    sql = f"""
        WITH vivienda_stats AS (
            SELECT
                f.id_vivienda,
                f.id_geografia,
                f.id_valoracion,

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
                ) AS no_disponibilidad_pct

            FROM fact_disponibilidad_alojamiento f

            JOIN dim_geografia g
                ON f.id_geografia = g.id_geografia

            WHERE {" AND ".join(filters)}

            GROUP BY
                f.id_vivienda,
                f.id_geografia,
                f.id_valoracion
        )

        SELECT
            v.id_vivienda,
            v.nombre_anuncio,
            g.ciudad,
            g.barrio,

            val.puntuacion_general,
            val.volumen_resenas,

            CASE
                WHEN UPPER(NVL(val.reserva_instantanea, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                THEN 'Yes'
                ELSE 'No'
            END AS reserva_instantanea,

            s.precio_medio_diario,
            s.disponibilidad_pct,
            s.no_disponibilidad_pct

        FROM vivienda_stats s

        JOIN dim_vivienda v
            ON s.id_vivienda = v.id_vivienda

        JOIN dim_geografia g
            ON s.id_geografia = g.id_geografia

        LEFT JOIN dim_valoracion val
            ON s.id_valoracion = val.id_valoracion

        WHERE val.puntuacion_general IS NOT NULL
    """

    return run_query(sql, params)


def get_instant_booking_availability(
    city: str | None = None,
):
    sql = """
        SELECT
            CASE
                WHEN UPPER(NVL(val.reserva_instantanea, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                THEN 'Instant booking'
                ELSE 'No instant booking'
            END AS tipo_reserva,

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

        LEFT JOIN dim_valoracion val
            ON f.id_valoracion = val.id_valoracion

        WHERE (:ciudad IS NULL OR g.ciudad = :ciudad)
          AND g.barrio IS NOT NULL
          AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

        GROUP BY
            CASE
                WHEN UPPER(NVL(val.reserva_instantanea, 'N')) IN ('S', 'SI', 'Y', 'YES', 'T', 'TRUE')
                THEN 'Instant booking'
                ELSE 'No instant booking'
            END

        ORDER BY
            tipo_reserva
    """

    return run_query(sql, {"ciudad": city})
