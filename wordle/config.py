"""
Load gameplay configuration (language, alphabet, corpus source, word
length, max guesses) from ``config.yaml`` (or an equivalent ``.json`` file).

Usage:
    >>> from config import load_config
    >>> cfg = load_config("en")           # or load_config() for the default
    >>> cfg.alphabet, cfg.corpus_file, cfg.first_guess
    ({'a', 'b', ...}, 'english.txt', 'crane')
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_CONFIG_PATH = str(Path(__file__).with_name("config.yaml"))


@dataclass
class GameConfig:
    """Resolved settings for one language/game combination."""

    language: str
    alphabet: set[str]
    corpus_url: str
    corpus_file: str
    first_guess: str
    word_length: int = 5
    max_steps: int = 6


def _read_raw(path: str) -> dict:
    text = Path(path).read_text(encoding="utf8")
    if path.endswith((".yaml", ".yml")):
        if yaml is None:
            raise ImportError(
                "PyYAML is required to read .yaml configs "
                "(pip install pyyaml), or use a .json config instead."
            )
        return yaml.safe_load(text)
    return json.loads(text)


def load_config(
    language: str | None = None, path: str = DEFAULT_CONFIG_PATH
) -> GameConfig:
    """Load gameplay config for a given language.

    Args:
        language: Language key to load (e.g. ``"ru"``, ``"en"``). Defaults
            to the config file's ``default_language`` entry.
        path: Path to the config file (``.yaml``/``.yml`` or ``.json``).

    Returns:
        A populated ``GameConfig``.

    Raises:
        KeyError: If ``language`` isn't defined under ``languages`` in the config.
    """
    raw = _read_raw(path)
    language = language or raw["default_language"]

    if language not in raw["languages"]:
        raise KeyError(
            f"Unknown language '{language}'. Available: {list(raw['languages'])}"
        )

    lang_cfg = raw["languages"][language]
    game_cfg = raw.get("game", {})

    config_dir = Path(path).resolve().parent
    corpus_file = Path(lang_cfg["corpus_file"])
    if not corpus_file.is_absolute():
        corpus_file = config_dir / corpus_file

    return GameConfig(
        language=language,
        alphabet=set(lang_cfg["alphabet"]),
        corpus_url=lang_cfg["corpus_url"],
        corpus_file=str(corpus_file),
        first_guess=lang_cfg["first_guess"],
        word_length=game_cfg.get("word_length", 5),
        max_steps=game_cfg.get("max_steps", 6),
    )
