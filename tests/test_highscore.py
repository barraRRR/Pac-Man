# uv run python -m pytest tests/ -v
"""Pruebas de la subtarea #46: limpieza del nombre y validación de la puntuación."""

import pathlib

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


# --- ofuscación (#45) -------------------------------------------------------


def test_encode_decode_round_trip() -> None:
    text = "Ana,846\nPac Man ñ,42\n"
    assert HighScore._decode(HighScore._encode(text)) == text


def test_decode_garbage_returns_none() -> None:
    assert HighScore._decode("not-valid-base64!!") is None


def test_decode_valid_base64_but_broken_text_returns_none() -> None:
    # Base64 válido cuyo contenido descodificado no es UTF-8: dañado.
    assert HighScore._decode("////") is None



# --- save (#45) -------------------------------------------------------------


def test_save_creates_folder_and_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path / "highscore"))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 846}])
    HighScore.save("highscore.csv")
    assert (tmp_path / "highscore" / "highscore.csv").is_file()


def test_save_then_load_round_trip(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [
        {"name": "Ana", "score": 846},
        {"name": "Pac Man", "score": 42},
    ])
    HighScore.save("highscore.csv")
    assert HighScore.load("highscore.csv") == [
        {"name": "Ana", "score": 846},
        {"name": "Pac Man", "score": 42},
    ]


def test_saved_file_is_not_plain_csv(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 846}])
    HighScore.save("highscore.csv")
    content = (tmp_path / "highscore.csv").read_text(encoding="ascii")
    assert "Ana" not in content

def test_save_total_failure_keeps_memory_and_returns_false(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "RETRY_SECONDS", 0)
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 1}])

    def broken_write(self: pathlib.Path, data: str, encoding: str = "") -> int:
        raise OSError("disk full")

    monkeypatch.setattr(pathlib.Path, "write_text", broken_write)
    saved: bool = HighScore.save("highscore.csv")
    assert saved is False
    assert HighScore.scores == [{"name": "Ana", "score": 1}]
    assert "total failure" in capsys.readouterr().err


def test_save_succeeds_after_one_failed_attempt(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "RETRY_SECONDS", 0)
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 1}])
    real_write_text = pathlib.Path.write_text
    calls: list[int] = []

    def flaky_write(self: pathlib.Path, data: str, encoding: str = "") -> int:
        calls.append(1)
        if len(calls) == 1:
            raise OSError("temporary glitch")
        return real_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(pathlib.Path, "write_text", flaky_write)
    assert HighScore.save("highscore.csv") is True
    assert len(calls) == 2
    assert HighScore.load("highscore.csv") == [{"name": "Ana", "score": 1}]
