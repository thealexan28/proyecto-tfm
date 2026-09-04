"""Translate categorical values returned by the Spanish Oracle schema."""

import functools

import pandas as pd
import plotly.express as px
from streamlit.delta_generator import DeltaGenerator


TRANSLATIONS = {
    # Display column names
    "Ciudad": "City",
    "Barrio": "Neighborhood",
    "Temporada": "Season",
    "Mes": "Month",
    "Métrica": "Metric",
    "Porcentaje": "Percentage",
    "Anfitrión": "Host",
    "Tipo de anfitrión": "Host type",
    "Tipo de tenedor": "Owner type",
    "Tipo de habitación": "Room type",
    "Tipo de propiedad": "Property type",
    "Número de viviendas": "Number of properties",
    "Nº viviendas": "No. of properties",
    "Precio medio diario": "Average daily price",
    "Ingreso potencial total": "Total potential revenue",
    "Disponibilidad": "Availability",
    "No disponibilidad": "Unavailability",
    "Ocupación estimada": "Estimated occupancy",
    "Puntuación general": "Overall rating",
    "Volumen de reseñas": "Review volume",
    "Reserva instantánea": "Instant booking",
    "Capacidad huéspedes": "Guest capacity",
    "Nombre del anuncio": "Listing name",
    "Nombre anfitrión": "Host name",
    # Categorical source values
    "Todas las ciudades": "All cities",
    "Todos los barrios": "All neighborhoods",
    "Gran tenedor": "Large-scale owner",
    "Grandes tenedores": "Large-scale owners",
    "Anfitrión particular": "Individual host",
    "Anfitriones particulares": "Individual hosts",
    "No superhost": "Not a Superhost",
    "Vivienda completa": "Entire home",
    "Habitación privada": "Private room",
    "Habitación compartida": "Shared room",
    "Habitación de hotel": "Hotel room",
    "Primavera": "Spring",
    "Verano": "Summer",
    "Otoño": "Autumn",
    "Invierno": "Winter",
    "Sí": "Yes",
    "Bajo": "Low",
    "Medio": "Medium",
    "Alto": "High",
    "Muy alto": "Very high",
    "Baja": "Low",
    "Media": "Medium",
    "Alta": "High",
    "Muy baja": "Very low",
    "Muy alta": "Very high",
    "Sin reseñas": "No reviews",
    "Pocas reseñas": "Few reviews",
    "Muchas reseñas": "Many reviews",
    "Sin nombre": "Unnamed",
    "desconocido": "unknown",
    "Sin clasificar": "Unclassified",
}


def translate(value):
    """Translate a known source value while leaving all other values unchanged."""

    if not isinstance(value, str):
        return value
    return TRANSLATIONS.get(value, value)


def translate_frame(frame):
    """Return a translated DataFrame copy, including columns and string values."""

    if not isinstance(frame, pd.DataFrame):
        return frame

    result = frame.copy()
    result.columns = [translate(column) for column in result.columns]
    return translate_frame_values(result)


def translate_frame_values(frame):
    """Return a copy with translated string values and unchanged column names."""

    if not isinstance(frame, pd.DataFrame):
        return frame

    result = frame.copy()
    for column in result.select_dtypes(include=["object", "string"]).columns:
        result[column] = result[column].map(translate)
    return result


def install_data_translation_hooks():
    """Translate database values passed to Streamlit tables and Plotly Express."""

    if getattr(DeltaGenerator, "_data_translation_hooks_installed", False):
        return

    original_dataframe = DeltaGenerator.dataframe

    @functools.wraps(original_dataframe)
    def dataframe(self, data=None, *args, **kwargs):
        return original_dataframe(self, translate_frame(data), *args, **kwargs)

    DeltaGenerator.dataframe = dataframe

    for name in ("bar", "line", "scatter", "pie", "histogram", "box"):
        original = getattr(px, name)

        @functools.wraps(original)
        def chart(*args, __original=original, **kwargs):
            args = list(args)
            if args and isinstance(args[0], pd.DataFrame):
                args[0] = translate_frame_values(args[0])
            if "data_frame" in kwargs:
                kwargs["data_frame"] = translate_frame_values(kwargs["data_frame"])
            return __original(*args, **kwargs)

        setattr(px, name, chart)

    DeltaGenerator._data_translation_hooks_installed = True
