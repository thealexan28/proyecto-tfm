import pandas as pd

from frontend.hosts import build_host_labels
from frontend.accommodation_type import (
    find_private_room,
    find_entire_home,
    normalize_text,
)
from frontend.ratings import (
    add_review_volume_order,
    create_scatter_sample,
    exclude_price_outliers,
    prepare_neighborhood_rating_chart,
)


def test_duplicate_host_names_are_disambiguated_with_ids():
    hosts = pd.DataFrame(
        {
            "id_anfitrion": [12708, 15212, 3],
            "nombre_anfitrion": ["Alex", "Alex", "Home Club"],
        }
    )

    result = build_host_labels(hosts)

    assert result["label"].tolist() == [
        "Alex (ID 12708)",
        "Alex (ID 15212)",
        "Home Club",
    ]
    assert "label" not in hosts.columns


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

    result = add_review_volume_order(listings)

    assert result["review_volume_order"].iloc[:5].tolist() == [0, 1, 2, 3, 4]
    assert result["review_volume_order"].iloc[5:].isna().all()
    assert result.loc[5, "volumen_resenas"] == "Unclassified"


def test_price_outlier_filter_uses_upper_iqr_boundary():
    listings = pd.DataFrame({"precio_medio_diario": [70, 80, 90, 100, 92_150]})

    result = exclude_price_outliers(listings)

    assert result["precio_medio_diario"].tolist() == [70, 80, 90, 100]


def test_scatter_sample_is_bounded_per_city_and_reproducible():
    listings = pd.DataFrame(
        {
            "ciudad": ["Madrid"] * 20 + ["Sevilla"] * 15,
            "id_vivienda": range(35),
        }
    )

    first = create_scatter_sample(listings, max_per_city=5)
    second = create_scatter_sample(listings, max_per_city=5)

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

    entire_home = find_entire_home(accommodation_types)
    private_room = find_private_room(accommodation_types)

    assert entire_home["tipo_alojamiento"] == "Entire home/apt"
    assert private_room["tipo_alojamiento"] == "Habitación privada"
    assert normalize_text(None) == ""
    assert normalize_text("  PRIVATE ROOM  ") == "private room"


def test_neighborhood_rating_chart_uses_query_column_and_sorts_ascending():
    neighborhoods = pd.DataFrame(
        {
            "ciudad": ["Madrid", "Sevilla"],
            "barrio": ["Centro", "Triana"],
            "puntuacion_media": [4.8, 4.6],
        }
    )

    result = prepare_neighborhood_rating_chart(neighborhoods, include_city=True)

    assert result["puntuacion_media"].tolist() == [4.6, 4.8]
    assert result["area_label"].tolist() == [
        "Triana (Sevilla)",
        "Centro (Madrid)",
    ]
    assert "area_label" not in neighborhoods.columns
