import pandas as pd

from frontend.anfitriones import crear_etiquetas_anfitrion
from frontend.tipo_alojamiento import (
    buscar_habitacion_privada,
    buscar_vivienda_completa,
    normalizar_texto,
)
from frontend.valoraciones import (
    crear_muestra_scatter,
    crear_orden_volumen_resenas,
    excluir_precios_atipicos,
)


def test_duplicate_host_names_are_disambiguated_with_ids():
    hosts = pd.DataFrame(
        {
            "id_anfitrion": [12708, 15212, 3],
            "nombre_anfitrion": ["Alex", "Alex", "Home Club"],
        }
    )

    result = crear_etiquetas_anfitrion(hosts)

    assert result["etiqueta"].tolist() == [
        "Alex (ID 12708)",
        "Alex (ID 15212)",
        "Home Club",
    ]
    assert "etiqueta" not in hosts.columns


def test_review_volume_order_excludes_unknown_categories_from_statistics():
    listings = pd.DataFrame(
        {
            "volumen_resenas": [
                "Sin reseñas",
                "Pocas reseñas",
                "Medio",
                "Alto",
                "Muy alto",
                None,
                "Unexpected",
            ]
        }
    )

    result = crear_orden_volumen_resenas(listings)

    assert result["orden_volumen"].iloc[:5].tolist() == [0, 1, 2, 3, 4]
    assert result["orden_volumen"].iloc[5:].isna().all()
    assert result.loc[5, "volumen_resenas"] == "Unclassified"


def test_price_outlier_filter_uses_upper_iqr_boundary():
    listings = pd.DataFrame({"precio_medio_diario": [70, 80, 90, 100, 92_150]})

    result = excluir_precios_atipicos(listings)

    assert result["precio_medio_diario"].tolist() == [70, 80, 90, 100]


def test_scatter_sample_is_bounded_per_city_and_reproducible():
    listings = pd.DataFrame(
        {
            "ciudad": ["Madrid"] * 20 + ["Sevilla"] * 15,
            "id_vivienda": range(35),
        }
    )

    first = crear_muestra_scatter(listings, max_por_ciudad=5)
    second = crear_muestra_scatter(listings, max_por_ciudad=5)

    assert first.groupby("ciudad").size().to_dict() == {"Madrid": 5, "Sevilla": 5}
    pd.testing.assert_frame_equal(first, second)


def test_accommodation_type_helpers_support_source_and_english_values():
    accommodation_types = pd.DataFrame(
        {
            "tipo_alojamiento": [
                "Entire home/apt",
                "Habitación privada",
            ]
        }
    )

    entire_home = buscar_vivienda_completa(accommodation_types)
    private_room = buscar_habitacion_privada(accommodation_types)

    assert entire_home["tipo_alojamiento"] == "Entire home/apt"
    assert private_room["tipo_alojamiento"] == "Habitación privada"
    assert normalizar_texto(None) == ""
    assert normalizar_texto("  PRIVATE ROOM  ") == "private room"
