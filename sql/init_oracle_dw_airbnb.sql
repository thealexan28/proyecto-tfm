/* ============================================================
   Script de inicialización del Data Warehouse de alquiler turístico
   Motor: Oracle Database 12.2+ recomendado
   Nota: la tabla FACT_DISPONIBILIDAD_ALOJAMIENTO supera 30 caracteres.
   ============================================================ */

/* ============================================================
   1. Borrado seguro de tablas existentes
   ============================================================ */
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE fact_disponibilidad_alojamiento CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE fact_contexto_residencial CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE dim_valoracion CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE dim_geografia CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE dim_tiempo CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE dim_tipo_alojamiento CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE dim_anfitrion CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE dim_vivienda CASCADE CONSTRAINTS PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

/* ============================================================
   2. Creación de dimensiones
   ============================================================ */

CREATE TABLE dim_vivienda (
   id_vivienda        NUMBER(10)      NOT NULL,
   id_anuncio_airbnb  NUMBER(20),
   nombre_anuncio     VARCHAR2(255),
   url_vivienda       VARCHAR2(500),
   licencia_turistica VARCHAR2(100),
   fuente_dato        VARCHAR2(100),
   fecha_extraccion   DATE,
   latitud            NUMBER(10,6),
   longitud           NUMBER(10,6),
   CONSTRAINT pk_dim_vivienda PRIMARY KEY (id_vivienda),
   CONSTRAINT uq_dim_viv_airbnb UNIQUE (id_anuncio_airbnb),
   CONSTRAINT ck_dim_viv_lat CHECK (latitud IS NULL OR latitud BETWEEN -90 AND 90),
   CONSTRAINT ck_dim_viv_lon CHECK (longitud IS NULL OR longitud BETWEEN -180 AND 180)
);

CREATE TABLE dim_anfitrion (
   id_anfitrion              NUMBER(10)    NOT NULL,
   id_anfitrion_airbnb       NUMBER(20),
   nombre_anfitrion          VARCHAR2(150),
   fecha_alta                DATE,
   ubicacion_anfitrion       VARCHAR2(255),
   tasa_respuesta            NUMBER(5,2),
   tasa_aceptacion           NUMBER(5,2),
   es_superhost              CHAR(1),
   tiene_foto_perfil         CHAR(1),
   identidad_verificada      CHAR(1),
   num_anuncios_declarados   NUMBER(10),
   num_anuncios_totales      NUMBER(10),
   num_anuncios_calculados   NUMBER(10),
   num_viviendas_completas   NUMBER(10),
   num_habitaciones_privadas NUMBER(10),
   num_habitaciones_compartidas NUMBER(10),
   perfil_inversor           VARCHAR2(50),
   CONSTRAINT pk_dim_anfitrion PRIMARY KEY (id_anfitrion),
   CONSTRAINT uq_dim_anf_airbnb UNIQUE (id_anfitrion_airbnb),
   CONSTRAINT ck_dim_anf_tasa_resp CHECK (tasa_respuesta IS NULL OR tasa_respuesta BETWEEN 0 AND 100),
   CONSTRAINT ck_dim_anf_tasa_acep CHECK (tasa_aceptacion IS NULL OR tasa_aceptacion BETWEEN 0 AND 100),
   CONSTRAINT ck_dim_anf_superhost CHECK (es_superhost IS NULL OR es_superhost IN ('S','N')),
   CONSTRAINT ck_dim_anf_foto CHECK (tiene_foto_perfil IS NULL OR tiene_foto_perfil IN ('S','N')),
   CONSTRAINT ck_dim_anf_ident CHECK (identidad_verificada IS NULL OR identidad_verificada IN ('S','N')),
   CONSTRAINT ck_dim_anf_num_decl CHECK (num_anuncios_declarados IS NULL OR num_anuncios_declarados >= 0),
   CONSTRAINT ck_dim_anf_num_tot CHECK (num_anuncios_totales IS NULL OR num_anuncios_totales >= 0),
   CONSTRAINT ck_dim_anf_num_calc CHECK (num_anuncios_calculados IS NULL OR num_anuncios_calculados >= 0),
   CONSTRAINT ck_dim_anf_viv_comp CHECK (num_viviendas_completas IS NULL OR num_viviendas_completas >= 0),
   CONSTRAINT ck_dim_anf_hab_priv CHECK (num_habitaciones_privadas IS NULL OR num_habitaciones_privadas >= 0),
   CONSTRAINT ck_dim_anf_hab_comp CHECK (num_habitaciones_compartidas IS NULL OR num_habitaciones_compartidas >= 0)
);

CREATE TABLE dim_tipo_alojamiento (
   id_tipo_alojamiento  NUMBER(10)    NOT NULL,
   id_anuncio_airbnb  NUMBER(20),
   tipo_propiedad       VARCHAR2(150),
   tipo_habitacion      VARCHAR2(100),
   capacidad_huespedes  NUMBER(5),
   num_banos            NUMBER(5,1),
   descripcion_banos    VARCHAR2(150),
   num_dormitorios      NUMBER(5),
   num_camas            NUMBER(5),
   noches_minimas_base  NUMBER(10),
   noches_maximas_base  NUMBER(10),
   num_comodidades      NUMBER(10),
   CONSTRAINT pk_dim_tipo_aloj PRIMARY KEY (id_tipo_alojamiento),
   CONSTRAINT uq_dim_tipo_aloj_airbnb UNIQUE (id_anuncio_airbnb),
   CONSTRAINT ck_dim_tipo_cap CHECK (capacidad_huespedes IS NULL OR capacidad_huespedes >= 0),
   CONSTRAINT ck_dim_tipo_banos CHECK (num_banos IS NULL OR num_banos >= 0),
   CONSTRAINT ck_dim_tipo_dorm CHECK (num_dormitorios IS NULL OR num_dormitorios >= 0),
   CONSTRAINT ck_dim_tipo_camas CHECK (num_camas IS NULL OR num_camas >= 0),
   CONSTRAINT ck_dim_tipo_min CHECK (noches_minimas_base IS NULL OR noches_minimas_base >= 0),
   CONSTRAINT ck_dim_tipo_max CHECK (noches_maximas_base IS NULL OR noches_maximas_base >= 0),
   CONSTRAINT ck_dim_tipo_comod CHECK (num_comodidades IS NULL OR num_comodidades >= 0)
);

CREATE TABLE dim_tiempo (
   id_tiempo      NUMBER(8)    NOT NULL,
   fecha          DATE         NOT NULL,
   dia            NUMBER(2),
   mes            NUMBER(2),
   nombre_mes     VARCHAR2(20),
   trimestre      NUMBER(1),
   anio           NUMBER(4),
   dia_semana     VARCHAR2(20),
   es_fin_semana  CHAR(1),
   temporada      VARCHAR2(20),
   CONSTRAINT pk_dim_tiempo PRIMARY KEY (id_tiempo),
   CONSTRAINT uq_dim_tiempo_fecha UNIQUE (fecha),
   CONSTRAINT ck_dim_tiempo_dia CHECK (dia IS NULL OR dia BETWEEN 1 AND 31),
   CONSTRAINT ck_dim_tiempo_mes CHECK (mes IS NULL OR mes BETWEEN 1 AND 12),
   CONSTRAINT ck_dim_tiempo_trim CHECK (trimestre IS NULL OR trimestre BETWEEN 1 AND 4),
   CONSTRAINT ck_dim_tiempo_finde CHECK (es_fin_semana IS NULL OR es_fin_semana IN ('S','N'))
);

CREATE TABLE dim_geografia (
   id_geografia        NUMBER(10)    NOT NULL,
   pais                VARCHAR2(100),
   comunidad_autonoma  VARCHAR2(150),
   provincia           VARCHAR2(150),
   ciudad              VARCHAR2(150),
   distrito            VARCHAR2(150),
   barrio              VARCHAR2(150),
   codigo_barrio       VARCHAR2(50),
   CONSTRAINT pk_dim_geo PRIMARY KEY (id_geografia)
);

CREATE TABLE dim_valoracion (
   id_valoracion            NUMBER(10)    NOT NULL,
   id_anuncio_airbnb  NUMBER(20),
   rango_puntuacion         VARCHAR2(50),
   volumen_resenas          VARCHAR2(50),
   reserva_instantanea      CHAR(1),
   puntuacion_general       NUMBER(3,2),
   puntuacion_precision     NUMBER(3,2),
   puntuacion_limpieza      NUMBER(3,2),
   puntuacion_checkin       NUMBER(3,2),
   puntuacion_comunicacion  NUMBER(3,2),
   puntuacion_localizacion  NUMBER(3,2),
   puntuacion_valor         NUMBER(3,2),
   CONSTRAINT pk_dim_val PRIMARY KEY (id_valoracion),
   CONSTRAINT uq_dim_valor_anuncio UNIQUE (id_anuncio_airbnb),
   CONSTRAINT ck_dim_val_res_inst CHECK (reserva_instantanea IS NULL OR reserva_instantanea IN ('S','N')),
   CONSTRAINT ck_dim_val_gral CHECK (puntuacion_general IS NULL OR puntuacion_general BETWEEN 0 AND 5),
   CONSTRAINT ck_dim_val_prec CHECK (puntuacion_precision IS NULL OR puntuacion_precision BETWEEN 0 AND 5),
   CONSTRAINT ck_dim_val_limp CHECK (puntuacion_limpieza IS NULL OR puntuacion_limpieza BETWEEN 0 AND 5),
   CONSTRAINT ck_dim_val_checkin CHECK (puntuacion_checkin IS NULL OR puntuacion_checkin BETWEEN 0 AND 5),
   CONSTRAINT ck_dim_val_com CHECK (puntuacion_comunicacion IS NULL OR puntuacion_comunicacion BETWEEN 0 AND 5),
   CONSTRAINT ck_dim_val_loc CHECK (puntuacion_localizacion IS NULL OR puntuacion_localizacion BETWEEN 0 AND 5),
   CONSTRAINT ck_dim_val_valor CHECK (puntuacion_valor IS NULL OR puntuacion_valor BETWEEN 0 AND 5)
);

/* ============================================================
   3. Creación de tablas de hechos
   ============================================================ */

CREATE TABLE fact_disponibilidad_alojamiento (
   id_disponibilidad       NUMBER(10)    NOT NULL,
   id_vivienda             NUMBER(10)    NOT NULL,
   id_anfitrion            NUMBER(10)    NOT NULL,
   id_tipo_alojamiento     NUMBER(10)    NOT NULL,
   id_tiempo               NUMBER(8)     NOT NULL,
   id_valoracion           NUMBER(10)    NOT NULL,
   id_geografia            NUMBER(10)    NOT NULL,
   esta_disponible         CHAR(1),
   precio_diario           NUMBER(10,2),
   precio_ajustado_diario  NUMBER(10,2),
   noches_minimas          NUMBER(10),
   noches_maximas          NUMBER(10),
   ingreso_potencial_diario NUMBER(10,2),
   CONSTRAINT pk_fact_disp PRIMARY KEY (id_disponibilidad),
   CONSTRAINT fk_fd_viv FOREIGN KEY (id_vivienda)
      REFERENCES dim_vivienda (id_vivienda),
   CONSTRAINT fk_fd_anf FOREIGN KEY (id_anfitrion)
      REFERENCES dim_anfitrion (id_anfitrion),
   CONSTRAINT fk_fd_tipo FOREIGN KEY (id_tipo_alojamiento)
      REFERENCES dim_tipo_alojamiento (id_tipo_alojamiento),
   CONSTRAINT fk_fd_tiempo FOREIGN KEY (id_tiempo)
      REFERENCES dim_tiempo (id_tiempo),
   CONSTRAINT fk_fd_val FOREIGN KEY (id_valoracion)
      REFERENCES dim_valoracion (id_valoracion),
   CONSTRAINT fk_fd_geo FOREIGN KEY (id_geografia)
      REFERENCES dim_geografia (id_geografia),
   CONSTRAINT ck_fd_disp CHECK (esta_disponible IS NULL OR esta_disponible IN ('S','N')),
   CONSTRAINT ck_fd_precio CHECK (precio_diario IS NULL OR precio_diario >= 0),
   CONSTRAINT ck_fd_precio_aj CHECK (precio_ajustado_diario IS NULL OR precio_ajustado_diario >= 0),
   CONSTRAINT ck_fd_min CHECK (noches_minimas IS NULL OR noches_minimas >= 0),
   CONSTRAINT ck_fd_max CHECK (noches_maximas IS NULL OR noches_maximas >= 0),
   CONSTRAINT ck_fd_ingreso CHECK (ingreso_potencial_diario IS NULL OR ingreso_potencial_diario >= 0)
);

CREATE TABLE fact_contexto_residencial (
   id_contexto_residencial       NUMBER(10)    NOT NULL,
   id_geografia                  NUMBER(10)    NOT NULL,
   id_tiempo                     NUMBER(8)     NOT NULL,
   alquiler_medio_habitual       NUMBER(10,2),
   renta_media_hogar             NUMBER(12,2),
   ingresos_ciudadanos           NUMBER(12,2),
   num_viviendas_residenciales   NUMBER(10),
   num_viviendas_turisticas      NUMBER(10),
   capacidad_viviendas_turisticas NUMBER(10),
   indice_presion_turistica      NUMBER(10,4),
   CONSTRAINT pk_fact_ctx_res PRIMARY KEY (id_contexto_residencial),
   CONSTRAINT fk_fcr_geo FOREIGN KEY (id_geografia)
      REFERENCES dim_geografia (id_geografia),
   CONSTRAINT fk_fcr_tiempo FOREIGN KEY (id_tiempo)
      REFERENCES dim_tiempo (id_tiempo),
   CONSTRAINT ck_fcr_alq CHECK (alquiler_medio_habitual IS NULL OR alquiler_medio_habitual >= 0),
   CONSTRAINT ck_fcr_renta CHECK (renta_media_hogar IS NULL OR renta_media_hogar >= 0),
   CONSTRAINT ck_fcr_ing CHECK (ingresos_ciudadanos IS NULL OR ingresos_ciudadanos >= 0),
   CONSTRAINT ck_fcr_viv_res CHECK (num_viviendas_residenciales IS NULL OR num_viviendas_residenciales >= 0),
   CONSTRAINT ck_fcr_viv_tur CHECK (num_viviendas_turisticas IS NULL OR num_viviendas_turisticas >= 0),
   CONSTRAINT ck_fcr_cap_tur CHECK (capacidad_viviendas_turisticas IS NULL OR capacidad_viviendas_turisticas >= 0),
   CONSTRAINT ck_fcr_ind_pres CHECK (indice_presion_turistica IS NULL OR indice_presion_turistica >= 0)
);

/* ============================================================
   4. Índices recomendados para claves foráneas y consultas analíticas
   ============================================================ */

CREATE INDEX idx_fd_vivienda ON fact_disponibilidad_alojamiento (id_vivienda);
CREATE INDEX idx_fd_anfitrion ON fact_disponibilidad_alojamiento (id_anfitrion);
CREATE INDEX idx_fd_tipo ON fact_disponibilidad_alojamiento (id_tipo_alojamiento);
CREATE INDEX idx_fd_tiempo ON fact_disponibilidad_alojamiento (id_tiempo);
CREATE INDEX idx_fd_valoracion ON fact_disponibilidad_alojamiento (id_valoracion);
CREATE INDEX idx_fd_geografia ON fact_disponibilidad_alojamiento (id_geografia);

CREATE INDEX idx_fcr_geografia ON fact_contexto_residencial (id_geografia);
CREATE INDEX idx_fcr_tiempo ON fact_contexto_residencial (id_tiempo);

CREATE INDEX idx_dim_geo_ciudad ON dim_geografia (ciudad);
CREATE INDEX idx_dim_geo_barrio ON dim_geografia (barrio);
CREATE INDEX idx_dim_tiempo_anio_mes ON dim_tiempo (anio, mes);

/* ============================================================
   5. Comentarios de tablas
   ============================================================ */

COMMENT ON TABLE dim_vivienda IS 'Dimensión que almacena la información básica de los anuncios o viviendas turísticas.';
COMMENT ON TABLE dim_anfitrion IS 'Dimensión que almacena la información descriptiva de los anfitriones de Airbnb.';
COMMENT ON TABLE dim_tipo_alojamiento IS 'Dimensión que describe las características físicas y comerciales del alojamiento.';
COMMENT ON TABLE dim_tiempo IS 'Dimensión temporal utilizada para el análisis por día, mes, trimestre, año y temporada.';
COMMENT ON TABLE dim_geografia IS 'Dimensión geográfica con país, comunidad autónoma, provincia, ciudad, distrito y barrio.';
COMMENT ON TABLE dim_valoracion IS 'Dimensión que recoge las puntuaciones, reseñas y condiciones de reserva instantánea.';
COMMENT ON TABLE fact_disponibilidad_alojamiento IS 'Tabla de hechos con granularidad vivienda-día, basada en el calendario de disponibilidad del alojamiento.';
COMMENT ON TABLE fact_contexto_residencial IS 'Tabla de hechos con indicadores residenciales agregados por zona geográfica y periodo temporal.';

/* ============================================================
   Fin del script
   ============================================================ */
