"""Command-line entry point for Wordle benchmarks and browser play."""

from __future__ import annotations

import argparse
from pathlib import Path

from wordle import corpus, game
from wordle.web_ui import play as play_web

BASE_DIR = Path(__file__).resolve().parent
CORPORA = {
    "ru": BASE_DIR / "corpus" / "russian.txt",
    "en": BASE_DIR / "corpus" / "english.txt",
}
FIRST_GUESSES = {"ru": "отвар", "en": "crane"}
DEFAULT_LANGUAGE = "ru"
DEFAULT_MODE = "human"
N_SIMULATED_GAMES = 100


def build_word_list(language: str = DEFAULT_LANGUAGE) -> list[str]:
    if language not in CORPORA:
        raise ValueError(f"Unsupported language: {language}")
    alphabet = (
        set("abcdefghijklmnopqrstuvwxyz")
        if language == "en"
        else set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    )
    words = corpus.clean_corpus(
        corpus.load_corpus(str(CORPORA[language])), alphabet=alphabet, word_length=5
    )
    if not words:
        raise RuntimeError(f"No 5-letter words found in {CORPORA[language]}")
    return words


def main(
    language: str = DEFAULT_LANGUAGE,
    n_games: int = N_SIMULATED_GAMES,
    mode: str = DEFAULT_MODE,
) -> None:
    if mode == "test":
        words = build_word_list(language)
        results = game.AutomatedGame(
            words, first_guess=FIRST_GUESSES[language]
        ).run_simulation(n_games)
        print(f"Average steps: {sum(results) / len(results):.2f}")
    elif mode == "human":
        play_web(language=language)
    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Wordle solver and game.")
    parser.add_argument("--lang", choices=CORPORA, default=DEFAULT_LANGUAGE)
    parser.add_argument("--games", type=int, default=N_SIMULATED_GAMES)
    parser.add_argument("--game_mode", choices=("human", "test"), default=DEFAULT_MODE)
    args = parser.parse_args()
    main(language=args.lang, n_games=args.games, mode=args.game_mode)
