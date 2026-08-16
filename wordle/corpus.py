"""Utilities for downloading, loading, and cleaning a word corpus used as the
Wordle candidate word list. Language-agnostic: pass the alphabet and source
URL for whichever language you're working with (see ``config.py`` for a
convenient way to load these from ``config.yaml``).
"""

import requests

# Kept as defaults so existing calls (and old scripts) keep working unchanged.
RUSSIAN_LETTERS = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
CORPUS_URL = (
    "https://raw.githubusercontent.com/Harrix/Russian-Nouns/main/dist/russian_nouns.txt"
)


def download_corpus(save_path: str, url: str = CORPUS_URL) -> None:
    """Download a raw word corpus from a URL and save it to disk.

    Args:
        save_path: Path where the raw corpus file will be written.
        url: Source URL to download from. Defaults to the Russian noun
            corpus; pass a different URL for other languages.

    Raises:
        requests.HTTPError: If the download request fails.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(response.content)


def load_corpus(path: str) -> list[str]:
    """Read a raw corpus file from disk.

    Args:
        path: Path to the corpus text file.

    Returns:
        The raw lines from the file, one word (plus stray marks/newline) per line.
    """
    with open(path, "r", encoding="utf8") as f:
        return f.readlines()


def clean_corpus(
    raw_lines: list[str],
    alphabet: set[str] | None = None,
    word_length: int = 5,
) -> list[str]:
    """Filter raw corpus lines down to unique words of a fixed length.

    Strips every character not in ``alphabet`` from each line (removing
    stress marks, punctuation, whitespace, etc.), then keeps only words whose
    cleaned length equals ``word_length``.

    Args:
        raw_lines: Raw lines as returned by :func:`load_corpus`.
        alphabet: Set of valid letters for the target language (lowercase).
            Defaults to Cyrillic; pass e.g. ``set("abcdefghijklmnopqrstuvwxyz")``
            for English.
        word_length: Target word length to keep (5, for standard Wordle).

    Returns:
        A list of unique, cleaned words of the given length.
    """
    alphabet = alphabet if alphabet is not None else RUSSIAN_LETTERS
    cleaned = []
    for line in raw_lines:
        word = "".join(ch for ch in line.lower() if ch in alphabet)
        if len(word) == word_length:
            cleaned.append(word)
    return list(set(cleaned))
