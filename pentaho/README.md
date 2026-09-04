# ETL - Pentaho Data Integration

Este directorio contiene las transformaciones desarrolladas con **Pentaho Data Integration (PDI)** para la carga del Data Warehouse del TFM.

## Estructura

```text
pentaho/
├── jobs/
│   └── carga_datawarehouse.kjb
├── transformations/
│   ├── 01_carga_dim_geografia.ktr
│   ├── 02_carga_dim_tiempo.ktr
│   ├── 03_carga_dim_vivienda.ktr
│   ├── 04_carga_dim_anfitrion.ktr
│   ├── 05_carga_dim_tipo_alojamiento.ktr
│   ├── 06_carga_dim_valoracion.ktr
│   ├── 07_carga_fact_contexto_residencial.ktr
│   └── 08_carga_fact_disponibilidad_alojamiento.ktr
└── README.md
```

## Proceso ETL

El proceso sigue el orden habitual de carga de un modelo dimensional:

1. Se cargan primero las **dimensiones** del Data Warehouse.
2. A continuación se cargan las **tablas de hechos**, que se relacionan con las dimensiones previamente creadas.
3. El resultado final se almacena en **Oracle**, desde donde posteriormente se consulta la información para el dashboard.

## Transformaciones incluidas

- `01_carga_dim_geografia.ktr`: carga la información geográfica de las ciudades, distritos y barrios analizados.
- `02_carga_dim_tiempo.ktr`: genera y carga la dimensión temporal utilizada en los análisis por fecha y temporada.
- `03_carga_dim_vivienda.ktr`: carga la información básica de cada alojamiento.
- `04_carga_dim_anfitrion.ktr`: carga la información de los anfitriones y sus principales características.
- `05_carga_dim_tipo_alojamiento.ktr`: carga las características y tipología de los alojamientos.
- `06_carga_dim_valoracion.ktr`: carga la información relacionada con valoraciones, reseñas y reserva instantánea.
- `07_carga_fact_contexto_residencial.ktr`: carga los indicadores residenciales y socioeconómicos utilizados como contexto.
- `08_carga_fact_disponibilidad_alojamiento.ktr`: carga la información diaria de disponibilidad, precios y otras métricas asociadas a los alojamientos.

## Job principal

El archivo `jobs/carga_datawarehouse.kjb` agrupa las transformaciones anteriores y define su orden de ejecución.

El flujo general es:

```text
START
  ↓
Dimensiones
  ↓
Fact Contexto Residencial
  ↓
Fact Disponibilidad Alojamiento
```

Los archivos `.ktr` y `.kjb` pueden abrirse con **Pentaho Data Integration (Spoon)** para visualizar las transformaciones y el flujo completo del proceso.

La explicación detallada del diseño del Data Warehouse y del proceso ETL se encuentra en la memoria del TFM.
