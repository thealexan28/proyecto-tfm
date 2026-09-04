import pandas as pd

from frontend.i18n import translate, translate_frame, translate_frame_values


def test_translate_handles_exact_labels_and_non_strings():
    assert translate("Todas las ciudades") == "All cities"
    assert translate("Vivienda completa") == "Entire home"
    assert translate(42) == 42


def test_translate_frame_translates_columns_and_values_without_mutation():
    source = pd.DataFrame(
        {
            "Ciudad": ["Madrid"],
            "Tipo de habitación": ["Habitación privada"],
        }
    )

    result = translate_frame(source)

    assert result.columns.tolist() == ["City", "Room type"]
    assert result.iloc[0].tolist() == ["Madrid", "Private room"]
    assert source.columns.tolist() == ["Ciudad", "Tipo de habitación"]
    assert source.loc[0, "Tipo de habitación"] == "Habitación privada"


def test_translate_frame_values_preserves_internal_column_names():
    source = pd.DataFrame(
        {
            "tipo_habitacion": ["Habitación compartida"],
            "cantidad": [3],
        }
    )

    result = translate_frame_values(source)

    assert result.columns.tolist() == ["tipo_habitacion", "cantidad"]
    assert result.loc[0, "tipo_habitacion"] == "Shared room"
    assert result.loc[0, "cantidad"] == 3
