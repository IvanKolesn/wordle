"""Core Wordle solving logic."""

from __future__ import annotations

import random
from collections import Counter


def choose_random_word(word_list: list[str]) -> str:
    """Return a random word from *word_list*."""
    if not word_list:
        raise ValueError("word_list must not be empty")
    return random.choice(word_list)


def letters_intersection(word: str, letters: str | list[str] | tuple[str, ...]) -> int:
    """Return the multiset intersection size of two collections of letters."""
    return sum((Counter(word) & Counter(letters)).values())


def determine_feedback(target: str, guess: str) -> list[str]:
    """Compute Wordle feedback, correctly handling repeated letters.

    Codes are ``g`` (green), ``y`` (yellow), and ``b`` (black/absent).
    """
    if len(target) != len(guess):
        raise ValueError("target and guess must have the same length")

    feedback = ["b"] * len(guess)
    remaining = Counter(target)

    # Greens consume their copies first.
    for i, (target_letter, guess_letter) in enumerate(zip(target, guess)):
        if guess_letter == target_letter:
            feedback[i] = "g"
            remaining[guess_letter] -= 1

    # Then mark yellows only while copies remain.
    for i, guess_letter in enumerate(guess):
        if feedback[i] == "g":
            continue
        if remaining[guess_letter] > 0:
            feedback[i] = "y"
            remaining[guess_letter] -= 1

    return feedback


def filter_candidates(
    guess: str, feedback: list[str], word_list: list[str]
) -> list[str]:
    """Keep exactly the words that would produce *feedback* for *guess*."""
    if len(guess) != len(feedback):
        raise ValueError("guess and feedback must have the same length")
    return [
        word
        for word in word_list
        if word != guess and determine_feedback(word, guess) == feedback
    ]


def best_guess(word_list: list[str], stop: int = 10_000) -> str:
    """Choose a strong guess using aggregate letter-frequency scoring.

    ``stop`` is retained for API compatibility with the previous solver.
    The current implementation does not need an exhaustive combination search.
    """
    del stop
    if not word_list:
        raise ValueError("word_list must not be empty")
    if len(word_list) == 1:
        return word_list[0]

    frequencies = Counter("".join(word_list))

    def score(word: str) -> int:
        # Count each distinct letter once: repeated letters provide less
        # information in an opening/information-seeking guess.
        return sum(frequencies[ch] for ch in set(word))

    return max(word_list, key=score)


def next_guess(
    guess: str, feedback: list[str], word_list: list[str]
) -> tuple[list[str], str | None]:
    """Filter candidates and return the next suggested guess."""
    candidates = filter_candidates(guess, feedback, word_list)
    if not candidates:
        return [], None
    if len(candidates) == 1:
        return candidates, candidates[0]
    return candidates, best_guess(candidates)
