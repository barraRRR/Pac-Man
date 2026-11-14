"""Store and validate scores and the player's name."""

import base64
import csv
import string
from pathlib import Path
import time
from src.utils.title import Title
from src.utils.utils import make_interval_ticker
from src.utils.logger import logger


PLAYER_MAX_LEN_NAME = 10
PROMPT_INTERVAL = 300


class HighScore:
    """Validate, load, and save the score leaderboard."""

    SCORES_FOLDER = "highscore"

    MAX_NAME_LENGTH = 10

    # Allowed name characters: ASCII letters, digits, and spaces.
    VALID_CHARACTERS = string.ascii_letters + string.digits + " "

    # Obfuscation password.
    PASSWORD = "jajajaja"

    scores: list[dict[str, str | int]] = []
    filename: str = "highscore.csv"

    SAVE_ATTEMPTS = 3
    RETRY_SECONDS = 1

    security: bool = True

    @classmethod
    def clean_name(cls, name: str) -> str:
        """Prepare the name for storage according to the agreed rules.

        Keep only ASCII letters, digits, and spaces; remove trailing spaces
        but preserve leading and internal spaces. Truncate names longer than
        ``MAX_NAME_LENGTH`` and log an error. Return an empty string if no
        characters remain.
        """
        characters: list[str] = []
        for char in name:
            if char in cls.VALID_CHARACTERS:
                characters.append(char)
            else:
                characters.append('')

        clean_name = "".join(characters).rstrip()

        if len(clean_name) > cls.MAX_NAME_LENGTH:
            clean_name = clean_name[:cls.MAX_NAME_LENGTH]
            logger.error("Error: name is longer than %s characters, "
                         'keeping "%s".', cls.MAX_NAME_LENGTH, clean_name)
        return clean_name

    @classmethod
    def is_valid_score(cls, score: object) -> bool:
        """Check for a non-negative integer score, excluding booleans."""
        if isinstance(score, bool):
            return False
        if isinstance(score, int) and score >= 0:
            return True
        return False

    @classmethod
    def _xor(cls, data: bytes) -> bytes:
        """Apply or undo XOR using the password as a repeating key.

        XOR is its own inverse: applying it twice restores the original, so
        this method can both encode and decode.
        """
        key = cls.PASSWORD.encode("utf-8")
        return bytes(
            byte ^ key[index % len(key)]
            for index, byte in enumerate(data)
        )

    @classmethod
    def _encode(cls, text: str) -> str:
        """Convert the CSV to the output format required by ``security``.

        When True, obfuscate it (UTF-8, XOR with the password, then base64).
        When False, return it unchanged so the file remains plain text.
        """
        if not cls.security:
            return text

        encrypter: bytes = cls._xor(text.encode("utf-8"))
        return base64.b64encode(encrypter).decode("ascii")

    @classmethod
    def _decode(cls, encoded: str) -> str | None:
        """Undo obfuscation, returning None if the text is corrupted.

        None means the content is not valid base64 or that removing the
        obfuscation does not produce UTF-8 text; the file was modified or
        corrupted.
        """
        try:
            encrypted = base64.b64decode(
                encoded.encode("ascii"), validate=True
            )
            return cls._xor(encrypted).decode("utf-8")
        except ValueError:
            return None

    @classmethod
    def _is_encoded(cls, raw: str) -> bool:
        """Check whether the file content is obfuscated.

        The format is inferred from strict base64 validity rather than the
        ``security`` flag, allowing files written under either setting to be
        read. Non-empty plain CSV contains commas and is not valid base64.
        """
        try:
            base64.b64decode(raw.encode("ascii"), validate=True)
            return True
        except ValueError:
            return False

    @classmethod
    def load(cls) -> list[dict[str, str | int]]:
        """Load the leaderboard from the score file.

        Read both formats: valid base64 is deobfuscated; otherwise, treat the
        content as regular CSV. This means ``security`` controls only how
        data is written, so existing files remain readable if the flag
        changes. Parse each row as a name and integer score. If the file does
        not exist, start with an empty leaderboard; if any row is malformed
        or the file is corrupted, log an error and start empty.
        """

        patch: Path = Path(cls.SCORES_FOLDER) / cls.filename
        if not patch.is_file():
            cls.scores = []
            return cls.scores
        try:
            raw: str = patch.read_text(encoding="ascii")

            # Valid base64 means obfuscated; otherwise, treat it as plain CSV.
            if cls._is_encoded(raw):
                text = cls._decode(raw)
                if text is None:
                    raise ValueError("File is corrupted or not base64.")
            else:
                text = raw

            rows: list[dict[str, str | int]] = []
            for row in csv.reader(text.splitlines()):
                if not row:
                    continue
                rows.append({"name": row[0], "score": int(row[1])})
        except (ValueError, IndexError, OSError, UnicodeError) as error:
            logger.error("Highscore file is damaged; starting with an empty "
                         "ranking: %s", error)
            cls.scores = []
            return cls.scores
        cls.scores = rows
        return cls.scores

    @classmethod
    def save(cls) -> bool:
        """Save the leaderboard to the score file.

        Build and encode CSV text from the in-memory records. If writing fails
        (for example, due to permissions or a full disk), retry a few times
        with a countdown between attempts and write English warnings to
        stderr. If all attempts fail, return False without a traceback; the
        in-memory leaderboard remains available for the next save attempt.
        Return True if the file was written.
        """
        text = "".join(
            f"{record['name']},{record['score']}\n" for record in cls.scores)
        path = Path(cls.SCORES_FOLDER) / cls.filename
        for attempt in range(1, cls.SAVE_ATTEMPTS + 1):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(cls._encode(text), encoding="ascii")
                return True
            except OSError as error:
                if attempt == cls.SAVE_ATTEMPTS:
                    break
                logger.error("Error: could not save the highscore file "
                             "(attempt %s of %s): %s",
                             attempt, cls.SAVE_ATTEMPTS, error)
                for count in range(cls.SAVE_ATTEMPTS, 0, -1):
                    logger.info("Retrying in %s...", count)
                    time.sleep(cls.RETRY_SECONDS)
        logger.error("Error: total failure saving the highscore. "
                     "The ranking survives in memory: play again and "
                     "we will try again.")
        return False

    @classmethod
    def register(cls, name: str, score: int) -> bool:
        """Register a score if it qualifies for the Top 10.

        Clean the name and validate the score; if either fails, log an error
        and leave the leaderboard unchanged. When the leaderboard is full,
        only a score strictly greater than the lowest one qualifies; a tie
        does not displace an earlier entry. Add qualifying scores, sort them
        in descending order (stable sorting preserves arrival order for ties),
        truncate to ten entries, and save the file.

        Return True if the entry is in the in-memory Top 10. ``save()`` writes
        its own warning if the disk write fails.
        """
        clean_name = cls.clean_name(name)
        if not clean_name:
            logger.error("Error: player name cannot be empty.")
            return False

        if not cls.is_valid_score(score):
            logger.error("Error: score must be a non-negative integer.")
            return False

        if len(cls.scores) >= 10:
            lowest_score = int(cls.scores[-1]["score"])
            if score <= lowest_score:
                return False

        cls.scores.append({"name": clean_name, "score": score})
        cls.scores.sort(key=lambda record: int(record["score"]), reverse=True)
        cls.scores = cls.scores[:10]

        cls.save()
        return True

    @classmethod
    def top(cls) -> int:
        """Return the leaderboard's highest score, or 0 if it is empty.

        The leaderboard is always sorted in descending order, so its first
        entry is the record displayed in the game HUD.
        """
        if not cls.scores:
            return 0
        return int(cls.scores[0]["score"])


class Score(Title):
    """Track and draw the current game's score."""

    def __init__(self) -> None:
        """Initialize the score to zero."""
        self._points: int = 0
        super().__init__(text=str(self._points))

    def add(self, points: int) -> None:
        """Add points to the score and update its surface."""
        self._points += points
        self.sur = self._render(text=str(self._points))

    @property
    def points(self) -> int:
        """Return the current score."""
        return self._points

    def reset(self) -> None:
        """Reset the score to zero and refresh the HUD surface."""
        self._points = 0
        self.sur = self._render(text=str(self._points))


class PlayerName(Title):
    """Manage the entered name and blinking input cursor."""

    def __init__(self) -> None:
        """Initialize an empty name and the cursor timer."""
        super().__init__(text="")
        self._name = ""
        self.prompt = "|"
        self.timer = make_interval_ticker(PROMPT_INTERVAL)
        self.prompt_visible: bool = True

    def set_name(self, new: str) -> bool:
        """Set the name if it does not exceed the allowed length."""
        if len(new) > PLAYER_MAX_LEN_NAME:
            return False

        self._name = new
        self.text = new
        self.sur = self._render(text=new)
        return True

    def build_name(self, char: str) -> bool:
        """Add a character to the name if there is room."""
        return self.set_name(self._name + char)

    def delete_last(self) -> bool:
        """Remove the last character from the name."""
        return self.set_name(self._name[:-2])

    def get_name(self) -> str:
        """Return the entered name."""
        return self._name

    def define_visible_prompt(self) -> None:
        """Update the visible cursor character."""
        self.prompt = "|" if self.prompt_visible else " "

    def get_prompt(self, dt: int) -> str:
        """Return the name followed by the blinking cursor."""
        ticks = self.timer(dt)
        for _ in range(ticks):
            self.prompt_visible = not self.prompt_visible
            self.define_visible_prompt()
        return self._name + self.prompt
