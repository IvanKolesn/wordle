"""Interactive terminal UI for playing a game against ``WordleEnv``.

Run directly (``python terminal_ui.py``) to play a round in the console with
colored tiles, using the default language from ``config.yaml``. Pass
``--lang en`` (or any other language key defined there) to switch. Type a
guess each turn, or ``?`` for a solver hint.
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.text import Text

from wordle import corpus
from wordle.env import (
    ALPHABET_EN,
    ALPHABET_RU,
    WordleEnv,
    FEEDBACK_BLACK,
    FEEDBACK_YELLOW,
    FEEDBACK_GREEN,
)
from wordle.models import simple_solver as slv

_STYLE = {
    FEEDBACK_GREEN: "bold black on green",
    FEEDBACK_YELLOW: "bold black on yellow",
    FEEDBACK_BLACK: "white on grey30",
}
_CODE = {"g": FEEDBACK_GREEN, "y": FEEDBACK_YELLOW, "b": FEEDBACK_BLACK}

# Built-in alphabets keyed by the language codes used in config.yaml. Add an
# entry here (or pass alphabet=... directly to WordleEnv) for other languages.
_ALPHABETS = {"ru": ALPHABET_RU, "en": ALPHABET_EN}

_LABELS = {
    "ru": {
        "intro": "[bold]Угадайте слово из {n} букв.[/bold] "
        "[dim]g=зелёный, y=жёлтый, b=чёрный. Введите '?' для подсказки.[/dim]",
        "attempt": "Попытка {step}/{max_steps}. Возможных слов: {n}",
        "prompt": "Ваше слово: ",
        "hint": "[cyan]Подсказка: {word}[/cyan]",
        "unknown": "[red]Такого слова нет в словаре, попробуйте снова.[/red]",
        "win": "[bold green]Поздравляю! Слово «{word}» угадано за {step} попыток![/bold green]",
        "lose": "[bold red]Не повезло. Загаданное слово было: «{word}»[/bold red]",
    },
    "en": {
        "intro": "[bold]Guess the {n}-letter word.[/bold] "
        "[dim]g=green, y=yellow, b=gray. Type '?' for a hint.[/dim]",
        "attempt": "Attempt {step}/{max_steps}. Possible words left: {n}",
        "prompt": "Your guess: ",
        "hint": "[cyan]Hint: {word}[/cyan]",
        "unknown": "[red]That word isn't in the dictionary, try again.[/red]",
        "win": "[bold green]Nice! The word «{word}» was guessed in {step} tries![/bold green]",
        "lose": "[bold red]Out of guesses. The word was: «{word}»[/bold red]",
    },
}


def render_board(env: WordleEnv, console: Console) -> None:
    """Print the current guess grid with colored tiles.

    Args:
        env: The environment whose guess/feedback history to render.
        console: Rich console to print to.
    """
    console.print()
    for row in range(env.max_steps):
        line = Text()
        if row < len(env.guesses):
            guess, feedback = env.guesses[row], env.feedbacks[row]
            for ch, code in zip(guess, feedback):
                line.append(f" {ch.upper()} ", style=_STYLE[_CODE[code]])
                line.append(" ")
        else:
            for _ in range(env.word_length):
                line.append(" _ ", style="dim")
                line.append(" ")
        console.print(line)
    console.print()


def _build_env(language: str):
    """Build a terminal-game environment from a bundled corpus."""
    if language == "en":
        alphabet = ALPHABET_EN
        corpus_path = Path(__file__).parent / "corpus" / "english.txt"
    else:
        language = "ru"
        alphabet = ALPHABET_RU
        corpus_path = Path(__file__).parent / "corpus" / "russian.txt"

    raw_lines = corpus.load_corpus(str(corpus_path))
    words = corpus.clean_corpus(raw_lines, alphabet=set(alphabet), word_length=5)
    return (
        WordleEnv(words, max_steps=6, word_length=5, alphabet=alphabet),
        _LABELS[language],
    )


def play(language: str = "ru") -> None:
    """Run one interactive terminal game."""
    console = Console()
    env, labels = _build_env(language)
    _, info = env.reset()
    console.print(labels["intro"].format(n=env.word_length))

    terminated = truncated = False
    while not (terminated or truncated):
        render_board(env, console)
        console.print(
            labels["attempt"].format(
                step=env.step_count + 1,
                max_steps=env.max_steps,
                n=info["num_candidates"],
            )
        )
        guess = console.input(labels["prompt"]).strip().lower()

        if guess == "?":
            console.print(labels["hint"].format(word=slv.best_guess(env.candidates)))
            continue
        if guess not in env.word_to_idx:
            console.print(labels["unknown"])
            continue

        _, _, terminated, truncated, info = env.step(env.word_to_idx[guess])

    render_board(env, console)
    if terminated:
        console.print(labels["win"].format(word=env.target, step=env.step_count))
    else:
        console.print(labels["lose"].format(word=env.target))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play Wordle in the terminal.")
    parser.add_argument("--lang", choices=("ru", "en"), default="ru")
    args = parser.parse_args()
    play(language=args.lang)
