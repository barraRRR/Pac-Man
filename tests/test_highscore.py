"""Tests for name cleaning and the score leaderboard."""

import pathlib

import pytest

from src.score.highscore import HighScore


# --- clean_name -----------------------------------------------------------


def test_valid_name_passes_unchanged() -> None:
    """Keep a valid name unchanged."""
    assert HighScore.clean_name("Ana") == "Ana"


def test_internal_spaces_are_kept() -> None:
    """Keep spaces between characters."""
    assert HighScore.clean_name("Pac Man") == "Pac Man"


def test_leading_spaces_kept_and_trailing_removed() -> None:
    """Keep leading spaces and remove trailing spaces."""
    # As agreed, only trailing spaces are removed.
    assert HighScore.clean_name("  Ana  ") == "  Ana"


def test_forbidden_characters_are_removed() -> None:
    """Remove disallowed characters from the name."""
    assert HighScore.clean_name("A-B") == "AB"
    assert HighScore.clean_name('"Ana"') == "Ana"


def test_real_tab_and_newline_are_removed() -> None:
    """Remove actual tabs and newline characters."""
    assert HighScore.clean_name("A\tB\nC") == "ABC"


def test_literal_backslash_removed_but_letter_kept() -> None:
    """Remove the literal backslash and keep the following letter."""
    # A manually typed backslash is removed; the letter remains: "\t" -> "t".
    assert HighScore.clean_name("A\\tB") == "AtB"


def test_all_spaces_gives_empty_name() -> None:
    """Return an empty name if only spaces remain."""
    assert HighScore.clean_name("   \t ") == ""


def test_name_of_exactly_ten_characters_is_kept() -> None:
    """Keep names whose length exactly matches the limit."""
    assert HighScore.clean_name("ABCDEFGHIJ") == "ABCDEFGHIJ"


def test_long_name_is_truncated_with_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Truncate long names and log a warning."""
    assert HighScore.clean_name("ABCDEFGHIJK") == "ABCDEFGHIJ"
    assert "Error" in capsys.readouterr().err


def test_leading_spaces_count_toward_the_limit() -> None:
    """Count leading spaces toward the name length limit."""
    # The 12-character limit includes 2 spaces and 8 letters.
    assert HighScore.clean_name("  ABCDEFGHIJK") == "  ABCDEFGH"


# --- is_valid_score -------------------------------------------------------


def test_zero_and_positive_scores_are_valid() -> None:
    """Accept non-negative integer scores."""
    assert HighScore.is_valid_score(0)
    assert HighScore.is_valid_score(1)
    assert HighScore.is_valid_score(846)


def test_negative_score_is_invalid() -> None:
    """Reject negative scores."""
    assert not HighScore.is_valid_score(-1)


def test_boolean_is_not_a_score() -> None:
    """Reject booleans even though Python treats them as integers."""
    # Python treats True and False as integers, so reject them explicitly.
    assert not HighScore.is_valid_score(True)
    assert not HighScore.is_valid_score(False)


def test_other_types_are_invalid() -> None:
    """Reject scores that are not integers."""
    assert not HighScore.is_valid_score("846")
    assert not HighScore.is_valid_score(3.5)
    assert not HighScore.is_valid_score(None)


# --- Obfuscation (#45) -------------------------------------------------------


def test_encode_decode_round_trip() -> None:
    """Recover the original text after encoding and decoding."""
    text = "Ana,846\nPac Man ñ,42\n"
    assert HighScore._decode(HighScore._encode(text)) == text


def test_decode_garbage_returns_none() -> None:
    """Reject content that does not have a valid encoding."""
    assert HighScore._decode("not-valid-base64!!") is None


def test_decode_valid_base64_but_broken_text_returns_none() -> None:
    """Reject decoded data that is not UTF-8 text."""
    # Valid base64 whose decoded content is not UTF-8 is corrupted.
    assert HighScore._decode("////") is None


# --- save (#45) -------------------------------------------------------------


def test_save_creates_folder_and_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create the directory and file when saving scores."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER",
                        str(tmp_path / "highscore"))
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 846}])
    HighScore.save()
    assert (tmp_path / "highscore" / "highscore.csv").is_file()


def test_save_then_load_round_trip(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Load saved scores successfully."""
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
    """Save the leaderboard without leaving it as plain-text CSV."""
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
    """Keep the leaderboard in memory when saving fails."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "RETRY_SECONDS", 0)
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 1}])

    def broken_write(self: pathlib.Path, data: str, encoding: str = "") -> int:
        """Simulate a write error caused by insufficient disk space."""
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
    """Retry saving and succeed after a transient failure."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "RETRY_SECONDS", 0)
    monkeypatch.setattr(HighScore, "scores", [{"name": "Ana", "score": 1}])
    real_write_text = pathlib.Path.write_text
    calls: list[int] = []

    def flaky_write(self: pathlib.Path, data: str, encoding: str = "") -> int:
        """Fail once, then delegate to the real write operation."""
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
    """A full leaderboard with ten entries scoring from 100 to 91."""
    return [{"name": f"player{i}", "score": 100 - i} for i in range(10)]


def test_register_adds_record_and_returns_true(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Add a valid score to the leaderboard."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("Ana", 50) is True
    assert HighScore.scores == [{"name": "Ana", "score": 50}]


def test_register_sorts_by_score_descending(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sort scores in descending order."""
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
    """Keep the earlier entry first when scores are tied."""
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
    """Reject a tie when the leaderboard is already full."""
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
    """Reject lower scores when the leaderboard is already full."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", full_ranking)
    assert HighScore.register("Zoe", 1) is False
    assert len(HighScore.scores) == 10


def test_register_higher_score_drops_last_when_full(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    full_ranking: list[dict[str, str | int]],
) -> None:
    """Include the higher score and remove the lowest one."""
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
    """Reject negative scores without changing the leaderboard."""
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
    """Reject empty names without changing the leaderboard."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("   ", 100) is False
    assert HighScore.scores == []
    assert "name" in capsys.readouterr().err


def test_register_cleans_the_name(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean the name before adding it to the leaderboard."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    assert HighScore.register("  Ana<3  ", 10) is True
    assert HighScore.scores == [{"name": "  Ana3", "score": 10}]


def test_register_writes_the_obfuscated_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Save the entry and confirm it can be loaded again."""
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(HighScore, "scores", [])
    HighScore.register("Ana", 10)
    assert (tmp_path / "highscore.csv").is_file()
    HighScore.scores = []
    assert HighScore.load() == [{"name": "Ana", "score": 10}]


def test_real_registration_flow_creates_loads_and_keeps_top_ten() -> None:
    """Test actual registration, loading, and the Top 10 limit."""
    path = pathlib.Path(HighScore.SCORES_FOLDER) / HighScore.filename

    previous_file = path.read_bytes() if path.is_file() else None
    previous_scores = [record.copy() for record in HighScore.scores]

    try:
        HighScore.scores = []

        # First stage: register four scores and read the file.
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

        # Second stage: add eight entries; the top ten should remain.
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
    """Read and display the actual score leaderboard."""
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
    """Start with an empty leaderboard if the score file is missing.

    No warning should be logged for this expected case.
    """
    monkeypatch.setattr(HighScore, "SCORES_FOLDER", str(tmp_path))
    monkeypatch.setattr(
        HighScore, "scores", [{"name": "Viejo", "score": 999}]
    )

    assert HighScore.load() == []
    assert HighScore.scores == []
    # A missing file is expected; do not write a warning to stderr.
    assert capsys.readouterr().err == ""


def test_register_keeps_duplicate_names(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Allow two players with the same name; do not deduplicate them."""
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

    # Duplicate names also survive saving and reloading.
    HighScore.scores = []
    assert HighScore.load() == expected
