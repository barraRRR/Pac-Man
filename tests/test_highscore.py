# uv run python -m pytest tests/ -v
"""Pruebas de la subtarea #46: limpieza del nombre y validación de la puntuación."""

import pytest

from src.score.highscore import HighScore


# --- clean_name -----------------------------------------------------------


def test_valid_name_passes_unchanged() -> None:
    assert HighScore.clean_name("Ana") == "Ana"


def test_internal_spaces_are_kept() -> None:
    assert HighScore.clean_name("Pac Man") == "Pac Man"


def test_leading_spaces_kept_and_trailing_removed() -> None:
    # Acordado: solo se limpia el final del nombre.
    assert HighScore.clean_name("  Ana  ") == "  Ana"


def test_forbidden_characters_are_removed() -> None:
    assert HighScore.clean_name("A-B") == "AB"
    assert HighScore.clean_name('"Ana"') == "Ana"


def test_real_tab_and_newline_are_removed() -> None:
    assert HighScore.clean_name("A\tB\nC") == "ABC"


def test_literal_backslash_removed_but_letter_kept() -> None:
    # La barra escrita a mano desaparece y la letra se queda: "\t" -> "t".
    assert HighScore.clean_name("A\\tB") == "AtB"


def test_all_spaces_gives_empty_name() -> None:
    assert HighScore.clean_name("   \t ") == ""


def test_name_of_exactly_ten_characters_is_kept() -> None:
    assert HighScore.clean_name("ABCDEFGHIJ") == "ABCDEFGHIJ"


def test_long_name_is_truncated_with_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert HighScore.clean_name("ABCDEFGHIJK") == "ABCDEFGHIJ"
    assert "Error" in capsys.readouterr().err


def test_leading_spaces_count_toward_the_limit() -> None:
    # 12 posiciones al recortar: 2 espacios + 8 letras.
    assert HighScore.clean_name("  ABCDEFGHIJK") == "  ABCDEFGH"


# --- is_valid_score -------------------------------------------------------


def test_zero_and_positive_scores_are_valid() -> None:
    assert HighScore.is_valid_score(0)
    assert HighScore.is_valid_score(1)
    assert HighScore.is_valid_score(846)


def test_negative_score_is_invalid() -> None:
    assert not HighScore.is_valid_score(-1)


def test_boolean_is_not_a_score() -> None:
    # Trampa de Python: True y False son enteros; los descartamos a mano.
    assert not HighScore.is_valid_score(True)
    assert not HighScore.is_valid_score(False)


def test_other_types_are_invalid() -> None:
    assert not HighScore.is_valid_score("846")
    assert not HighScore.is_valid_score(3.5)
    assert not HighScore.is_valid_score(None)