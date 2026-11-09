"""Pruebas del saneamiento de nombres y el ranking de puntuaciones."""

import pathlib

import pytest

from src.score.highscore import HighScore


# --- clean_name -----------------------------------------------------------


def test_valid_name_passes_unchanged() -> None:
    """Conserva un nombre válido sin modificarlo."""
    assert HighScore.clean_name("Ana") == "Ana"


def test_internal_spaces_are_kept() -> None:
    """Conserva los espacios situados entre caracteres."""
    assert HighScore.clean_name("Pac Man") == "Pac Man"


def test_leading_spaces_kept_and_trailing_removed() -> None:
    """Conserva espacios iniciales y elimina los finales."""
    # Acordado: solo se limpia el final del nombre.
    assert HighScore.clean_name("  Ana  ") == "  Ana"


def test_forbidden_characters_are_removed() -> None:
    """Elimina los caracteres no permitidos del nombre."""
    assert HighScore.clean_name("A-B") == "AB"
    assert HighScore.clean_name('"Ana"') == "Ana"


def test_real_tab_and_newline_are_removed() -> None:
    """Elimina tabuladores y saltos de línea reales."""
    assert HighScore.clean_name("A\tB\nC") == "ABC"


def test_literal_backslash_removed_but_letter_kept() -> None:
    """Elimina la barra literal y conserva la letra siguiente."""
    # La barra escrita a mano desaparece y la letra se queda: "\t" -> "t".
    assert HighScore.clean_name("A\\tB") == "AtB"


def test_all_spaces_gives_empty_name() -> None:
    """Devuelve un nombre vacío si solo quedan espacios."""
    assert HighScore.clean_name("   \t ") == ""


def test_name_of_exactly_ten_characters_is_kept() -> None:
    """Conserva nombres cuya longitud coincide con el máximo."""
    assert HighScore.clean_name("ABCDEFGHIJ") == "ABCDEFGHIJ"


def test_long_name_is_truncated_with_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Recorta los nombres largos y registra un aviso."""
    assert HighScore.clean_name("ABCDEFGHIJK") == "ABCDEFGHIJ"
    assert "Error" in capsys.readouterr().err


def test_leading_spaces_count_toward_the_limit() -> None:
    """Cuenta los espacios iniciales dentro del límite del nombre."""
    # 12 posiciones al recortar: 2 espacios + 8 letras.
    assert HighScore.clean_name("  ABCDEFGHIJK") == "  ABCDEFGH"


# --- is_valid_score -------------------------------------------------------


def test_zero_and_positive_scores_are_valid() -> None:
    """Acepta puntuaciones enteras no negativas."""
    assert HighScore.is_valid_score(0)
    assert HighScore.is_valid_score(1)
    assert HighScore.is_valid_score(846)


def test_negative_score_is_invalid() -> None:
    """Rechaza puntuaciones negativas."""
    assert not HighScore.is_valid_score(-1)


def test_boolean_is_not_a_score() -> None:
    """Rechaza booleanos aunque Python los trate como enteros."""
    # Trampa de Python: True y False son enteros; los descartamos a mano.
    assert not HighScore.is_valid_score(True)
    assert not HighScore.is_valid_score(False)


def test_other_types_are_invalid() -> None:
    """Rechaza puntuaciones que no sean enteros."""
    assert not HighScore.is_valid_score("846")
    assert not HighScore.is_valid_score(3.5)
    assert not HighScore.is_valid_score(None)


# --- ofuscación (#45) -------------------------------------------------------


def test_encode_decode_round_trip() -> None:
    """Recupera el texto original tras codificarlo y descodificarlo."""
    text = "Ana,846\nPac Man ñ,42\n"
    assert HighScore._decode(HighScore._encode(text)) == text


def test_decode_garbage_returns_none() -> None:
    """Rechaza contenido que no tenga una codificación válida."""
    assert HighScore._decode("not-valid-base64!!") is None


def test_decode_valid_base64_but_broken_text_returns_none() -> None:
    """Rechaza datos descodificados que no sean texto UTF-8."""
    # Base64 válido cuyo contenido descodificado no es UTF-8: dañado.
    assert HighScore._decode("////") is None



# --- save (#45) -------------------------------------------------------------


def test_save_creates_folder_and_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Crea el directorio y el archivo al guardar puntuaciones."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path / "highscore"))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 846}])
    HighScore.save()
    assert (tmp_path / "highscore" / "highscore.csv").is_file()


def test_save_then_load_round_trip(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Carga correctamente las puntuaciones guardadas."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [
        {"name": "Ana", "score": 846},
        {"name": "Pac Man", "score": 42},
    ])
    HighScore.save()
    assert HighScore.load() == [
        {"name": "Ana", "score": 846},
        {"name": "Pac Man", "score": 42},
    ]


def test_saved_file_is_not_plain_csv(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guarda el ranking sin dejarlo como CSV en texto plano."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 846}])
    HighScore.save()
    content = (tmp_path / "highscore.csv").read_text(encoding="ascii")
    assert "Ana" not in content

def test_save_total_failure_keeps_memory_and_returns_false(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Mantiene el ranking en memoria cuando falla el guardado."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "RETRY_SECONDS", 0)
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 1}])

    def broken_write(self: pathlib.Path, data: str, encoding: str = "") -> int:
        """Simula un error de escritura por falta de espacio."""
        raise OSError("disk full")

    monkeypatch.setattr(pathlib.Path, "write_text", broken_write)
    saved: bool = HighScore.save()
    assert saved is False
    assert HighScore.scores == [{"name": "Ana", "score": 1}]
    assert "total failure" in capsys.readouterr().err


def test_save_succeeds_after_one_failed_attempt(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reintenta el guardado y tiene éxito tras un fallo transitorio."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "RETRY_SECONDS", 0)
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 1}])
    real_write_text = pathlib.Path.write_text
    calls: list[int] = []

    def flaky_write(self: pathlib.Path, data: str, encoding: str = "") -> int:
        """Falla una vez y luego delega en la escritura real."""
        calls.append(1)
        if len(calls) == 1:
            raise OSError("temporary glitch")
        return real_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(pathlib.Path, "write_text", flaky_write)
    assert HighScore.save() is True
    assert len(calls) == 2
    assert HighScore.load() == [{"name": "Ana", "score": 1}]


@pytest.fixture
def full_ranking() -> list[dict[str, str | int]]:
    """Ranking ya lleno: diez registros de 100 a 91 puntos."""
    return [{"name": f"player{i}", "score": 100 - i} for i in range(10)]


def test_register_adds_record_and_returns_true(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Añade una puntuación válida al ranking."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("Ana", 50) is True
    assert HighScore.scores == [{"name": "Ana", "score": 50}]


def test_register_sorts_by_score_descending(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ordena las puntuaciones de mayor a menor."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 10}])
    HighScore.register("Carl", 30)
    HighScore.register("Bea", 20)
    assert HighScore.scores == [
        {"name": "Carl", "score": 30},
        {"name": "Bea", "score": 20},
        {"name": "Ana", "score": 10},
    ]


def test_register_tie_keeps_earlier_entry_first(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mantiene primero el registro anterior cuando hay un empate."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 50}])
    assert HighScore.register("Bea", 50) is True
    assert HighScore.scores == [
        {"name": "Ana", "score": 50},
        {"name": "Bea", "score": 50},
    ]


def test_register_rejects_equal_score_when_full(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    full_ranking: list[dict[str, str | int]],
) -> None:
    """Rechaza un empate cuando el ranking ya está completo."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", full_ranking)
    assert HighScore.register("Zoe", 91) is False
    assert len(HighScore.scores) == 10
    assert all(record["name"] != "Zoe" for record in HighScore.scores)


def test_register_rejects_lower_score_when_full(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    full_ranking: list[dict[str, str | int]],
) -> None:
    """Rechaza puntuaciones menores cuando el ranking está completo."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", full_ranking)
    assert HighScore.register("Zoe", 1) is False
    assert len(HighScore.scores) == 10


def test_register_higher_score_drops_last_when_full(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    full_ranking: list[dict[str, str | int]],
) -> None:
    """Incluye la puntuación superior y elimina la más baja."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", full_ranking)
    assert HighScore.register("Zoe", 95) is True
    assert len(HighScore.scores) == 10
    assert HighScore.scores[6] == {"name": "Zoe", "score": 95}
    names = [record["name"] for record in HighScore.scores]
    assert "player9" not in names


def test_register_rejects_invalid_score(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Rechaza puntuaciones negativas sin alterar el ranking."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("Ana", -5) is False
    assert HighScore.scores == []
    assert "score" in capsys.readouterr().err


def test_register_rejects_empty_name(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Rechaza nombres vacíos sin alterar el ranking."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("   ", 100) is False
    assert HighScore.scores == []
    assert "name" in capsys.readouterr().err


def test_register_cleans_the_name(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sanea el nombre antes de guardarlo en el ranking."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("  Ana<3  ", 10) is True
    assert HighScore.scores == [{"name": "  Ana3", "score": 10}]


def test_register_writes_the_obfuscated_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guarda el registro y confirma que se puede volver a cargar."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    HighScore.register("Ana", 10)
    assert (tmp_path / "highscore.csv").is_file()
    HighScore.scores = []
    assert HighScore.load() == [{"name": "Ana", "score": 10}]



def test_real_registration_flow_creates_loads_and_keeps_top_ten() -> None:
    """Prueba el registro real, la lectura y el límite del Top 10."""
    path = pathlib.Path(HighScore.SCORES_FOLDER) / HighScore.filename

    previous_file = path.read_bytes() if path.is_file() else None
    previous_scores = [record.copy() for record in HighScore.scores]

    try:
        HighScore.scores = []

        # Primer tramo: registrar cuatro puntuaciones y leer el archivo.
        first_entries = [
            ("Aitor", 40),
            ("Luna", 100),
            ("Marta", 70),
            ("Nico", 25),
        ]

        for name, score in first_entries:
            assert HighScore.register(name, score) is True

        expected_first = [
            {"name": "Luna", "score": 100},
            {"name": "Marta", "score": 70},
            {"name": "Aitor", "score": 40},
            {"name": "Nico", "score": 25},
        ]

        assert path.is_file()
        assert HighScore.scores == expected_first
        assert HighScore.load() == expected_first

        # Segundo tramo: añadir ocho registros; deben quedar los diez mejores.
        more_entries = [
            ("Olga", 110),
            ("Paco", 30),
            ("Rita", 95),
            ("Sara", 180),
            ("Teo", 60),
            ("Uma", 130),
            ("Vera", 200),
            ("Walt", 50),
        ]

        for name, score in more_entries:
            assert HighScore.register(name, score) is True

        expected_top_ten = [
            {"name": "Vera", "score": 200},
            {"name": "Sara", "score": 180},
            {"name": "Uma", "score": 130},
            {"name": "Olga", "score": 110},
            {"name": "Luna", "score": 100},
            {"name": "Rita", "score": 95},
            {"name": "Marta", "score": 70},
            {"name": "Teo", "score": 60},
            {"name": "Walt", "score": 50},
            {"name": "Aitor", "score": 40},
        ]

        assert len(HighScore.scores) == 10
        assert HighScore.scores == expected_top_ten
        assert HighScore.load() == expected_top_ten

    finally:
        HighScore.scores = previous_scores
        if previous_file is not None:
            path.write_bytes(previous_file)

def test_print_real_highscore_file() -> None:
    """Lee el archivo real de puntuaciones y muestra el ranking descodificado."""
    path = pathlib.Path(HighScore.SCORES_FOLDER) / HighScore.filename

    assert path.is_file(), f"Highscore file not found: {path}"

    ranking = HighScore.load()

    print("\nDecoded highscore ranking:")
    if not ranking:
        print("No scores recorded.")
        return

    for position, record in enumerate(ranking, start=1):
        print(f"{position}. {record['name']} - {record['score']}")

def test_load_with_missing_file_starts_empty(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Si el archivo no existe, el ranking empieza vacío y sin quejas."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(
        HighScore, "scores", [{"name": "Viejo", "score": 999}]
    )

    assert HighScore.load() == []
    assert HighScore.scores == []
    # Que no exista archivo es lo normal: ni un aviso por stderr.
    assert capsys.readouterr().err == ""

def test_register_keeps_duplicate_names(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dos jugadores con el mismo nombre conviven: no se deduplica."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])

    assert HighScore.register("Aitor", 100) is True
    assert HighScore.register("Aitor", 250) is True
    assert HighScore.register("Aitor", 40) is True

    expected = [
        {"name": "Aitor", "score": 250},
        {"name": "Aitor", "score": 100},
        {"name": "Aitor", "score": 40},
    ]
    assert HighScore.scores == expected

    # Los duplicados también sobreviven al archivo: guardar y volver a leer.
    HighScore.scores = []
    assert HighScore.load() == expected