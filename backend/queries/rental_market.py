"""Queries comparing Airbnb prices with long-term rent."""

from backend.db import run_query


# Fixed reference window used to compare every city over the same 30 days and
# against residential data from the same reporting date.
RENTAL_COMPARISON_START_DATE = "2025-11-01"
RENTAL_COMPARISON_END_DATE = "2025-11-30"
RENTAL_CONTEXT_DATE = "2025-11-30"


def get_comparativa_alquiler_ciudad(
    ciudad: str | None = None,
    fecha_inicio: str = RENTAL_COMPARISON_START_DATE,
    fecha_fin: str = RENTAL_COMPARISON_END_DATE,
    fecha_contexto: str = RENTAL_CONTEXT_DATE,
):
    """Compare monthly equivalent Airbnb prices with municipal rent."""

    sql = """
        WITH airbnb_ciudad AS (
            SELECT
                g.ciudad,

                COUNT(DISTINCT f.id_vivienda) AS num_viviendas,
                COUNT(*) AS registros_calendario,
                COUNT(NVL(f.precio_ajustado_diario, f.precio_diario)) AS registros_con_precio,

                ROUND(
                    AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                    2
                ) AS precio_medio_airbnb_diario,

                ROUND(
                    AVG(NVL(f.precio_ajustado_diario, f.precio_diario)) * 30,
                    2
                ) AS precio_airbnb_mensualizado,

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

            JOIN dim_tiempo t
                ON f.id_tiempo = t.id_tiempo

            WHERE t.fecha BETWEEN TO_DATE(:fecha_inicio, 'YYYY-MM-DD')
                              AND TO_DATE(:fecha_fin, 'YYYY-MM-DD')
              AND (:ciudad IS NULL OR g.ciudad = :ciudad)
              AND g.barrio IS NOT NULL
              AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

            GROUP BY
                g.ciudad
        ),

        contexto_ciudad AS (
            SELECT
                g.ciudad,

                MAX(ctx.alquiler_medio_habitual) AS alquiler_habitual_municipal,
                MAX(ctx.renta_media_hogar) AS renta_media_hogar,
                MAX(ctx.ingresos_ciudadanos) AS ingresos_ciudadanos,
                MAX(ctx.num_viviendas_residenciales) AS num_viviendas_residenciales,
                MAX(ctx.num_viviendas_turisticas) AS num_viviendas_turisticas,
                MAX(ctx.capacidad_viviendas_turisticas) AS capacidad_viviendas_turisticas,
                MAX(ctx.indice_presion_turistica) AS indice_presion_turistica

            FROM fact_contexto_residencial ctx

            JOIN dim_geografia g
                ON ctx.id_geografia = g.id_geografia

            JOIN dim_tiempo t
                ON ctx.id_tiempo = t.id_tiempo

            WHERE t.fecha = TO_DATE(:fecha_contexto, 'YYYY-MM-DD')
              AND UPPER(REPLACE(g.barrio, ' ', '_')) = 'TOTAL_MUNICIPIO'
              AND (:ciudad IS NULL OR g.ciudad = :ciudad)

            GROUP BY
                g.ciudad
        )

        SELECT
            a.ciudad,
            a.num_viviendas,
            a.registros_calendario,
            a.registros_con_precio,
            a.precio_medio_airbnb_diario,
            a.precio_airbnb_mensualizado,

            c.alquiler_habitual_municipal,

            ROUND(
                a.precio_airbnb_mensualizado - c.alquiler_habitual_municipal,
                2
            ) AS diferencia_mensual,

            ROUND(
                a.precio_airbnb_mensualizado / NULLIF(c.alquiler_habitual_municipal, 0),
                2
            ) AS ratio_airbnb_vs_alquiler,

            a.disponibilidad_pct,
            a.ocupacion_estimada_pct,
            a.ingreso_potencial_total,

            c.renta_media_hogar,
            c.ingresos_ciudadanos,
            c.num_viviendas_residenciales,
            c.num_viviendas_turisticas,
            c.capacidad_viviendas_turisticas,
            c.indice_presion_turistica

        FROM airbnb_ciudad a

        LEFT JOIN contexto_ciudad c
            ON a.ciudad = c.ciudad

        ORDER BY
            diferencia_mensual DESC NULLS LAST
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_contexto": fecha_contexto,
        },
    )


def get_comparativa_alquiler_barrios(
    ciudad: str | None = None,
    limite: int = 15,
    fecha_inicio: str = RENTAL_COMPARISON_START_DATE,
    fecha_fin: str = RENTAL_COMPARISON_END_DATE,
    fecha_contexto: str = RENTAL_CONTEXT_DATE,
):
    """Compare neighborhood Airbnb prices with the municipal rent benchmark."""

    sql = """
        SELECT *
        FROM (
            WITH contexto_municipal AS (
                SELECT
                    g.ciudad,

                    MAX(ctx.alquiler_medio_habitual) AS alquiler_habitual_municipal,
                    MAX(ctx.renta_media_hogar) AS renta_media_hogar,
                    MAX(ctx.ingresos_ciudadanos) AS ingresos_ciudadanos,
                    MAX(ctx.num_viviendas_residenciales) AS num_viviendas_residenciales,
                    MAX(ctx.num_viviendas_turisticas) AS num_viviendas_turisticas,
                    MAX(ctx.capacidad_viviendas_turisticas) AS capacidad_viviendas_turisticas,
                    MAX(ctx.indice_presion_turistica) AS indice_presion_turistica

                FROM fact_contexto_residencial ctx

                JOIN dim_geografia g
                    ON ctx.id_geografia = g.id_geografia

                JOIN dim_tiempo t
                    ON ctx.id_tiempo = t.id_tiempo

                WHERE t.fecha = TO_DATE(:fecha_contexto, 'YYYY-MM-DD')
                  AND UPPER(REPLACE(g.barrio, ' ', '_')) = 'TOTAL_MUNICIPIO'
                  AND (:ciudad IS NULL OR g.ciudad = :ciudad)

                GROUP BY
                    g.ciudad
            ),

            airbnb_barrio AS (
                SELECT
                    g.ciudad,
                    g.barrio,

                    COUNT(DISTINCT f.id_vivienda) AS num_viviendas,
                    COUNT(*) AS registros_calendario,
                    COUNT(NVL(f.precio_ajustado_diario, f.precio_diario)) AS registros_con_precio,

                    ROUND(
                        AVG(NVL(f.precio_ajustado_diario, f.precio_diario)),
                        2
                    ) AS precio_medio_airbnb_diario,

                    ROUND(
                        AVG(NVL(f.precio_ajustado_diario, f.precio_diario)) * 30,
                        2
                    ) AS precio_airbnb_mensualizado_barrio,

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

                JOIN dim_tiempo t
                    ON f.id_tiempo = t.id_tiempo

                WHERE t.fecha BETWEEN TO_DATE(:fecha_inicio, 'YYYY-MM-DD')
                                  AND TO_DATE(:fecha_fin, 'YYYY-MM-DD')
                  AND (:ciudad IS NULL OR g.ciudad = :ciudad)
                  AND g.barrio IS NOT NULL
                  AND UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'

                GROUP BY
                    g.ciudad,
                    g.barrio
            )

            SELECT
                b.ciudad,
                b.barrio,
                b.num_viviendas,
                b.registros_calendario,
                b.registros_con_precio,
                b.precio_medio_airbnb_diario,
                b.precio_airbnb_mensualizado_barrio,

                c.alquiler_habitual_municipal,

                ROUND(
                    b.precio_airbnb_mensualizado_barrio - c.alquiler_habitual_municipal,
                    2
                ) AS diferencia_frente_alquiler_municipal,

                ROUND(
                    b.precio_airbnb_mensualizado_barrio / NULLIF(c.alquiler_habitual_municipal, 0),
                    2
                ) AS ratio_frente_alquiler_municipal,

                b.disponibilidad_pct,
                b.ocupacion_estimada_pct,
                b.ingreso_potencial_total,

                c.renta_media_hogar,
                c.ingresos_ciudadanos,
                c.num_viviendas_residenciales,
                c.num_viviendas_turisticas,
                c.capacidad_viviendas_turisticas,
                c.indice_presion_turistica

            FROM airbnb_barrio b

            LEFT JOIN contexto_municipal c
                ON b.ciudad = c.ciudad

            ORDER BY
                diferencia_frente_alquiler_municipal DESC NULLS LAST
        )
        WHERE ROWNUM <= :limite
    """

    return run_query(
        sql,
        {
            "ciudad": ciudad,
            "limite": limite,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_contexto": fecha_contexto,
        },
    )
