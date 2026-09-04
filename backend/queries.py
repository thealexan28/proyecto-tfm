from backend.db import run_query


# Fixed reference window used to compare every city over the same 30 days and
# against residential data from the same reporting date.
RENTAL_COMPARISON_START_DATE = "2025-11-01"
RENTAL_COMPARISON_END_DATE = "2025-11-30"
RENTAL_CONTEXT_DATE = "2025-11-30"


def get_kpis_generales():
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


def get_resumen_por_ciudad():
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


def get_top_barrios(limit: int = 10):
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


def get_disponibilidad_por_temporada():
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


def get_concentracion_barrios(ciudad: str | None = None, limite: int = 15):
    """
    Responde a la pregunta:
    Which neighborhoods contain the most short-term rental properties?

    Si ciudad es None, devuelve el ranking general.
    Si ciudad tiene valor, devuelve el ranking de esa ciudad.
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
            "ciudad": ciudad,
            "limite": limite,
        },
    )

def get_ingresos_potenciales_barrios(ciudad: str | None = None, limite: int = 15):
    """
    Responde a la pregunta:
    Which neighborhoods generate the most potential revenue?

    Si ciudad es None, devuelve el ranking general.
    Si ciudad tiene valor, devuelve el ranking de esa ciudad.
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
            "ciudad": ciudad,
            "limite": limite,
        },
    )

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

def get_barrios_mejor_valorados(
    ciudad: str | None = None,
    limite: int = 15,
    min_viviendas: int = 10,
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
            "ciudad": ciudad,
            "limite": limite,
            "min_viviendas": min_viviendas,
        },
    )


def get_valoraciones_viviendas(
    ciudad: str | None = None,
):
    filtros = [
        "g.barrio IS NOT NULL",
        "UPPER(REPLACE(g.barrio, ' ', '_')) <> 'TOTAL_MUNICIPIO'",
    ]
    params = {}

    if ciudad is not None:
        filtros.append("g.ciudad = :ciudad")
        params["ciudad"] = ciudad

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

            WHERE {" AND ".join(filtros)}

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


def get_reserva_instantanea_disponibilidad(
    ciudad: str | None = None,
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

    return run_query(sql, {"ciudad": ciudad})
