"""Queries for the property map."""

from backend.db import run_query


def get_viviendas_mapa(ciudad: str | None = None, barrio: str | None = None):
    filtros = [
        "g.barrio IS NOT NULL",
        "UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'",
    ]
    params = {}

    if ciudad is not None:
        filtros.append("g.ciudad = :ciudad")
        params["ciudad"] = ciudad

    if barrio is not None:
        filtros.append("g.barrio = :barrio")
        params["barrio"] = barrio

    sql = f"""
        WITH vivienda_stats AS (
            SELECT
                f.id_vivienda,
                f.id_geografia,
                f.id_tipo_alojamiento,
                f.id_anfitrion,
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
                ) AS ocupacion_estimada_pct,

                ROUND(
                    SUM(NVL(f.ingreso_potencial_diario, 0)),
                    2
                ) AS ingreso_potencial_total

            FROM fact_disponibilidad_alojamiento f

            JOIN dim_geografia g
                ON f.id_geografia = g.id_geografia

            WHERE {" AND ".join(filtros)}

            GROUP BY
                f.id_vivienda,
                f.id_geografia,
                f.id_tipo_alojamiento,
                f.id_anfitrion,
                f.id_valoracion
        )

        SELECT
            v.id_vivienda,
            v.nombre_anuncio,
            v.latitud,
            v.longitud,
            g.ciudad,
            g.barrio,
            ta.tipo_habitacion,
            ta.tipo_propiedad,
            ta.capacidad_huespedes,
            a.nombre_anfitrion,
            val.puntuacion_general,
            s.precio_medio_diario,
            s.disponibilidad_pct,
            s.ocupacion_estimada_pct,
            s.ingreso_potencial_total

        FROM vivienda_stats s

        JOIN dim_vivienda v
            ON s.id_vivienda = v.id_vivienda

        JOIN dim_geografia g
            ON s.id_geografia = g.id_geografia

        LEFT JOIN dim_tipo_alojamiento ta
            ON s.id_tipo_alojamiento = ta.id_tipo_alojamiento

        LEFT JOIN dim_anfitrion a
            ON s.id_anfitrion = a.id_anfitrion

        LEFT JOIN dim_valoracion val
            ON s.id_valoracion = val.id_valoracion

        WHERE v.latitud IS NOT NULL
          AND v.longitud IS NOT NULL
    """

    return run_query(sql, params)
