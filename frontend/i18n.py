"""English localization for UI text and categorical values returned by the database."""

import functools

import pandas as pd
import plotly.express as px
from plotly.basedatatypes import BaseFigure
from streamlit.delta_generator import DeltaGenerator


TRANSLATIONS = {
    "Todas las ciudades": "All cities", "Todos los barrios": "All neighborhoods",
    "Selecciona una ciudad": "Select a city", "Selecciona un barrio": "Select a neighborhood",
    "Selecciona primero una ciudad": "Select a city first", "Ciudad": "City", "Barrio": "Neighborhood",
    "Temporada": "Season", "Mes": "Month", "Métrica": "Metric", "Porcentaje": "Percentage",
    "Anfitrión": "Host", "Tipo de anfitrión": "Host type", "Tipo de tenedor": "Owner type",
    "Tipo de habitación": "Room type", "Tipo de propiedad": "Property type",
    "Número de viviendas": "Number of properties", "Nº viviendas": "No. of properties",
    "Viviendas turísticas": "Short-term rental properties", "Número de viviendas turísticas": "Number of short-term rental properties",
    "Precio medio diario": "Average daily price", "Precio medio": "Average price",
    "Ingreso potencial total": "Total potential revenue", "Ingreso potencial": "Potential revenue",
    "Disponibilidad media": "Average availability", "Disponibilidad": "Availability",
    "No disponibilidad media": "Average unavailability", "No disponibilidad": "Unavailability",
    "Ocupación estimada": "Estimated occupancy", "Noches analizadas": "Nights analyzed",
    "Noches disponibles": "Available nights", "Noches no disponibles": "Unavailable nights",
    "Puntuación general": "Overall rating", "Puntuación media": "Average rating",
    "Volumen de reseñas": "Review volume", "Reserva instantánea": "Instant booking",
    "Sin reserva instantánea": "No instant booking", "Número de huéspedes": "Number of guests",
    "Capacidad huéspedes": "Guest capacity", "Nombre del anuncio": "Listing name",
    "Nombre anfitrión": "Host name", "Gran tenedor": "Large-scale owner",
    "Anfitrión particular": "Individual host", "Superhost": "Superhost", "No superhost": "Not a Superhost",
    "Vivienda completa": "Entire home", "Habitación privada": "Private room",
    "Habitación compartida": "Shared room", "Habitación de hotel": "Hotel room",
    "Primavera": "Spring", "Verano": "Summer", "Otoño": "Autumn", "Invierno": "Winter",
    "Sí": "Yes", "No": "No", "Bajo": "Low", "Medio": "Medium", "Alto": "High", "Muy alto": "Very high",
    "Baja": "Low", "Media": "Medium", "Alta": "High", "Muy baja": "Very low", "Muy alta": "Very high",
    "Sin reseñas": "No reviews", "Pocas reseñas": "Few reviews", "Muchas reseñas": "Many reviews",
    "Anfitriones particulares": "Individual hosts", "Grandes tenedores": "Large-scale owners",
    "Viviendas": "Properties", "Barrios": "Neighborhoods", "Anfitriones": "Hosts",
    "Grandes tenedores": "Large-scale owners", "Sin nombre": "Unnamed", "desconocido": "unknown",
    "Sin clasificar": "Unclassified", "Airbnb mensualizado": "Monthly Airbnb revenue",
    "Alquiler habitual municipal": "Municipal long-term rent", "Importe mensual": "Monthly amount",
    "Barrios a mostrar": "Neighborhoods to display", "Anfitriones a mostrar": "Hosts to display",
    "Umbral gran tenedor": "Large-scale owner threshold", "Tipos de habitación": "Room types",
    "Tipos de propiedad mostrados": "Property types displayed", "tipo de habitación": "room type",
    "tipo de propiedad": "property type", "Detalle por": "Details by", "Top": "Top",
}

PHRASES = {
    "No hay ciudades disponibles en la base de datos.": "No cities are available in the database.",
    "No hay datos disponibles para la selección realizada.": "No data is available for the selected filters.",
    "Tabla de detalle": "Detailed table", "Indicadores clave": "Key indicators",
    "Número de barrios a mostrar": "Number of neighborhoods to display",
    "Mínimo viviendas por barrio": "Minimum properties per neighborhood",
    "Mínimo viviendas por capacidad": "Minimum properties per capacity",
    "Agrupar análisis por": "Group analysis by",
    "🗺️ Mapa de viviendas turísticas": "🗺️ Short-term rental property map",
    "Resumen de la ciudad": "City summary", "Mapa de alojamientos": "Property map",
    "Detalle de viviendas": "Property details", "No hay viviendas disponibles para la selección realizada.": "No properties are available for the selected filters.",
    "🏠 Airbnb frente al alquiler habitual": "🏠 Airbnb vs long-term rentals",
    "Brecha mensual por ciudad": "Monthly gap by city", "Airbnb mensualizado frente al alquiler habitual municipal": "Monthly Airbnb revenue vs municipal long-term rent",
    "Importe mensual (€)": "Monthly amount (€)", "Comparación mensual en": "Monthly comparison in",
    "Contexto residencial municipal": "Municipal housing context", "Barrios frente a la referencia municipal": "Neighborhoods vs the municipal benchmark",
    "No hay datos por barrio para la selección realizada.": "No neighborhood data is available for the selected filters.",
    "Diferencia frente al alquiler municipal (€)": "Difference from municipal rent (€)",
    "Relación entre concentración y precio Airbnb": "Relationship between concentration and Airbnb price",
    "Número de viviendas frente a Airbnb mensualizado por barrio": "Number of properties vs monthly Airbnb revenue by neighborhood",
    "Airbnb mensualizado por barrio (€)": "Monthly Airbnb revenue by neighborhood (€)",
    "Tabla de detalle por barrio": "Detailed table by neighborhood",
    "⭐ Análisis de valoraciones": "⭐ Ratings analysis", "No hay datos de valoraciones disponibles para la selección realizada.": "No rating data is available for the selected filters.",
    "¿Qué barrios tienen alojamientos mejor valorados?": "Which neighborhoods have the highest-rated properties?",
    "¿Existe relación entre puntuación media y precio?": "Is there a relationship between average rating and price?",
    "Relación entre puntuación general y precio medio diario": "Relationship between overall rating and average daily price",
    "Se observa una relación positiva entre puntuación y precio.": "A positive relationship between rating and price is observed.",
    "La relación entre puntuación y precio es positiva, pero débil.": "The relationship between rating and price is positive but weak.",
    "No se observa una relación positiva; la correlación es negativa.": "No positive relationship is observed; the correlation is negative.",
    "No se observa una relación clara entre puntuación y precio.": "No clear relationship between rating and price is observed.",
    "¿Los alojamientos con mayor volumen de reseñas tienen más no disponibilidad?": "Do properties with more reviews have higher unavailability?",
    "No disponibilidad media según volumen de reseñas": "Average unavailability by review volume",
    "No se observa una relación clara entre volumen de reseñas y no disponibilidad.": "No clear relationship between review volume and unavailability is observed.",
    "¿Los alojamientos con reserva instantánea tienen mayor disponibilidad?": "Do properties with instant booking have higher availability?",
    "Disponibilidad según reserva instantánea": "Availability by instant-booking status",
    "No hay datos suficientes sobre reserva instantánea.": "There is not enough instant-booking data.",
    "Tabla de detalle de alojamientos valorados": "Detailed table of rated properties",
    "La no disponibilidad se usa como aproximación de ocupación estimada.": "Unavailability is used as a proxy for estimated occupancy.",
    "👤 Análisis de anfitriones": "👤 Host analysis", "¿Qué anfitriones concentran más viviendas?": "Which hosts manage the most properties?",
    "¿Los superhost tienen mayor disponibilidad o no disponibilidad?": "Do Superhosts have higher availability or unavailability?",
    "Disponibilidad y no disponibilidad según tipo de anfitrión": "Availability and unavailability by host type",
    "¿Los grandes tenedores tienen precios más altos que los anfitriones particulares?": "Do large-scale owners charge higher prices than individual hosts?",
    "Precio medio diario según tipo de tenedor": "Average daily price by owner type", "Tabla de detalle de anfitriones": "Detailed host table",
    "🏘️ Análisis por tipo de alojamiento": "🏘️ Analysis by property type",
    "Viviendas completas frente a habitaciones privadas": "Entire homes vs private rooms", "Comparación de no disponibilidad": "Unavailability comparison",
    "¿Los alojamientos con mayor capacidad tienen mayor precio medio?": "Do higher-capacity properties have a higher average price?",
    "Evolución del precio medio según la capacidad del alojamiento": "Average price trend by property capacity",
    "Correlación capacidad-precio": "Capacity-price correlation",
    "No hay datos suficientes por capacidad con el mínimo de viviendas seleccionado.": "There is not enough capacity data for the selected minimum number of properties.",
    "Viviendas en grandes tenedores": "Properties managed by large-scale owners",
    "El ranking solo incluye barrios que cumplen el mínimo de viviendas seleccionado.": "The ranking only includes neighborhoods that meet the selected minimum property count.",
    "No hay barrios suficientes con el mínimo de viviendas seleccionado.": "Not enough neighborhoods meet the selected minimum property count.",
    "Existe una relación positiva clara: a mayor capacidad, mayor precio medio.": "There is a clear positive relationship: higher capacity is associated with a higher average price.",
    "Existe una relación positiva moderada entre capacidad y precio medio.": "There is a moderate positive relationship between capacity and average price.",
    "Existe una relación positiva débil entre capacidad y precio medio.": "There is a weak positive relationship between capacity and average price.",
    "No se observa una relación positiva clara entre capacidad y precio medio.": "No clear positive relationship between capacity and average price is observed.",
    "¿Qué tipo de habitación tiene mayor precio medio?": "Which room type has the highest average price?",
    "¿Qué tipo de propiedad tiene mayor precio medio?": "Which property type has the highest average price?",
    "¿Qué tipo de habitación genera más ingreso potencial?": "Which room type generates the most potential revenue?",
    "¿Qué tipo de propiedad genera más ingreso potencial?": "Which property type generates the most potential revenue?",
    "Precio medio diario por tipo de habitación": "Average daily price by room type",
    "Precio medio diario por tipo de propiedad": "Average daily price by property type",
    "Ingreso potencial total por tipo de habitación": "Total potential revenue by room type",
    "Ingreso potencial total por tipo de propiedad": "Total potential revenue by property type",
}


def translate(value):
    if not isinstance(value, str):
        return value
    if value in PHRASES:
        return PHRASES[value]
    if value in TRANSLATIONS:
        return TRANSLATIONS[value]
    result = value
    for source in sorted(TRANSLATIONS, key=len, reverse=True):
        result = result.replace(source, TRANSLATIONS[source])
    return result


def translate_frame(frame):
    if not isinstance(frame, pd.DataFrame):
        return frame
    result = frame.copy()
    result.columns = [translate(column) for column in result.columns]
    for column in result.select_dtypes(include=["object", "string"]).columns:
        result[column] = result[column].map(translate)
    return result


def translate_frame_values(frame):
    if not isinstance(frame, pd.DataFrame):
        return frame
    result = frame.copy()
    for column in result.select_dtypes(include=["object", "string"]).columns:
        result[column] = result[column].map(translate)
    return result


def _translate_object(value):
    if isinstance(value, str):
        return translate(value)
    if isinstance(value, dict):
        return {key: _translate_object(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_translate_object(item) for item in value)
    return value


def install_english_ui():
    if getattr(DeltaGenerator, "_english_ui_installed", False):
        return

    for name in ("title", "header", "subheader", "markdown", "caption", "warning", "info", "success", "error", "metric", "slider", "radio", "checkbox", "button", "multiselect"):
        original = getattr(DeltaGenerator, name, None)
        if original is None:
            continue

        @functools.wraps(original)
        def wrapped(self, *args, __original=original, **kwargs):
            return __original(self, *(_translate_object(arg) for arg in args), **_translate_object(kwargs))

        setattr(DeltaGenerator, name, wrapped)

    original_selectbox = DeltaGenerator.selectbox

    @functools.wraps(original_selectbox)
    def selectbox(self, label, options, *args, **kwargs):
        kwargs.setdefault("format_func", translate)
        return original_selectbox(self, translate(label), options, *args, **kwargs)

    DeltaGenerator.selectbox = selectbox

    original_dataframe = DeltaGenerator.dataframe

    @functools.wraps(original_dataframe)
    def dataframe(self, data=None, *args, **kwargs):
        return original_dataframe(self, translate_frame(data), *args, **kwargs)

    DeltaGenerator.dataframe = dataframe

    for name in ("bar", "line", "scatter", "pie", "histogram", "box"):
        original = getattr(px, name, None)
        if original is None:
            continue

        @functools.wraps(original)
        def chart(*args, __original=original, **kwargs):
            args = list(args)
            if args and isinstance(args[0], pd.DataFrame):
                args[0] = translate_frame_values(args[0])
            if "data_frame" in kwargs:
                kwargs["data_frame"] = translate_frame_values(kwargs["data_frame"])
            for key in ("title", "labels"):
                if key in kwargs:
                    kwargs[key] = _translate_object(kwargs[key])
            return __original(*args, **kwargs)

        setattr(px, name, chart)

    original_update_layout = BaseFigure.update_layout

    @functools.wraps(original_update_layout)
    def update_layout(self, *args, **kwargs):
        return original_update_layout(self, *(_translate_object(arg) for arg in args), **_translate_object(kwargs))

    BaseFigure.update_layout = update_layout

    DeltaGenerator._english_ui_installed = True
