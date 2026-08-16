"""Gymnasium-compatible Wordle environment for Russian 5-letter words.

Designed to serve two purposes with one implementation:
    1. Backend for interactive play (see ``terminal_ui.py``).
    2. A proper RL environment (``reset`` / ``step`` / ``render``) that can be
       dropped into stable-baselines3, sb3-contrib's MaskablePPO (via the
       ``action_mask`` in ``info``), or a custom REINFORCE loop.

Design notes:
    - The action space is ``Discrete(len(word_list))``: an action is an index
      into the fixed word list, so the agent can only ever guess real words
      (mirrors how a human plays, and keeps the action space tractable
      relative to a raw 5x33 letter grid).
    - The observation is the guess/feedback history as integer grids, which
      is enough for a model to reconstruct full game state. It deliberately
      does NOT include the target or the remaining-candidates list — that
      information lives in ``info`` for logging/debugging/hints only, since
      leaking it into the observation would trivialize the task.
    - ``info["action_mask"]`` exposes which word-list indices are still
      consistent with all feedback so far. Wordle rules don't require guesses
      to be valid candidates, so this is provided as an optional aid rather
      than being enforced in ``step``.
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from . import solver as slv

# Feedback encoding used in observations: 0 = cell not yet played.
FEEDBACK_EMPTY, FEEDBACK_BLACK, FEEDBACK_YELLOW, FEEDBACK_GREEN = 0, 1, 2, 3
_FEEDBACK_TO_CODE = {"b": FEEDBACK_BLACK, "y": FEEDBACK_YELLOW, "g": FEEDBACK_GREEN}

# Built-in alphabets for convenience; pass a custom one to WordleEnv for
# other languages (see config.py / config.yaml for a config-driven setup).
ALPHABET_RU = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
ALPHABET_EN = list("abcdefghijklmnopqrstuvwxyz")


class WordleEnv(gym.Env):  # pylint: disable=too-many-instance-attributes
    """A single-player Wordle episode over a fixed 5-letter word list.

    The attribute count is inherent to tracking full episode state (target,
    history, candidates, spaces) for a Gymnasium environment, not a sign the
    class is doing too much.
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        word_list: list[str],
        max_steps: int = 6,
        word_length: int = 5,
        target: str | None = None,
        alphabet: list[str] | None = None,
    ):
        """
        Args:
            word_list: Full vocabulary of valid words; also the action space.
            max_steps: Maximum guesses allowed per episode.
            word_length: Length of each word (5 for standard Wordle).
            target: If given, every episode targets this word (useful for
                debugging or curriculum learning). Otherwise a random word
                from ``word_list`` is chosen on each ``reset``.
            alphabet: Letters used to encode observations, in a fixed order.
                Defaults to Cyrillic (``ALPHABET_RU``); pass ``ALPHABET_EN``
                or a custom list for other languages. Should match whatever
                alphabet ``word_list`` was cleaned with (see ``config.py``).
        """
        super().__init__()
        if not word_list:
            raise ValueError("word_list must not be empty")
        if any(len(word) != word_length for word in word_list):
            raise ValueError("all words must have word_length characters")
        self.word_list = list(word_list)
        self.word_to_idx = {w: i for i, w in enumerate(self.word_list)}
        self.max_steps = max_steps
        self.word_length = word_length
        self._fixed_target = target

        self.alphabet = alphabet or ALPHABET_RU
        # 0 is reserved to mean "empty cell"; real letters start at 1.
        self.letter_to_idx = {letter: i + 1 for i, letter in enumerate(self.alphabet)}

        self.action_space = spaces.Discrete(len(self.word_list))
        self.observation_space = spaces.Dict(
            {
                "letters": spaces.Box(
                    low=0,
                    high=len(self.alphabet),
                    shape=(max_steps, word_length),
                    dtype=np.int64,
                ),
                "feedback": spaces.Box(
                    low=0, high=3, shape=(max_steps, word_length), dtype=np.int64
                ),
            }
        )

        self.target: str | None = None
        self.step_count = 0
        self.done = False
        self.guesses: list[str] = []
        self.feedbacks: list[list[str]] = []
        self.candidates: list[str] = []

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        """Start a new episode against a (random or fixed) target word.

        Returns:
            A tuple ``(observation, info)``, per the Gymnasium API.
        """
        super().reset(seed=seed)

        if (
            self._fixed_target is not None
            and self._fixed_target not in self.word_to_idx
        ):
            raise ValueError("target must be present in word_list")
        self.target = self._fixed_target or self.np_random.choice(self.word_list)
        self.step_count = 0
        self.done = False
        self.guesses = []
        self.feedbacks = []
        self.candidates = list(self.word_list)

        return self._get_obs(), self._get_info()

    def step(self, action: int):
        """Play one guess.

        Args:
            action: Index into ``self.word_list`` naming the guessed word.

        Returns:
            ``(observation, reward, terminated, truncated, info)``, per the
            Gymnasium API. ``terminated`` is True on a correct guess;
            ``truncated`` is True if ``max_steps`` is reached without success.
        """
        if self.done:
            raise RuntimeError(
                "Episode has ended — call reset() before stepping again."
            )

        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action}")
        guess = self.word_list[action]
        self.step_count += 1

        feedback = slv.determine_feedback(self.target, guess)
        self.guesses.append(guess)
        self.feedbacks.append(feedback)
        self.candidates = slv.filter_candidates(guess, feedback, self.candidates)

        won = feedback.count("g") == self.word_length
        terminated = won
        truncated = (not won) and (self.step_count >= self.max_steps)
        self.done = terminated or truncated

        reward = self._compute_reward(won, truncated)

        return self._get_obs(), reward, terminated, truncated, self._get_info()

    def _compute_reward(self, won: bool, truncated: bool) -> float:
        """Default reward: win big and early, small step cost, penalty on failure.

        Tune freely — this is deliberately simple:
            - Win: reward scales from 1.0 (found it on step 1) down to
              ~1/max_steps (found it on the last allowed step).
            - Fail (out of guesses): -1.0.
            - Otherwise: a small per-step cost to discourage stalling.
        """
        if won:
            return (self.max_steps - self.step_count + 1) / self.max_steps
        if truncated:
            return -1.0
        return -0.01

    def _get_obs(self) -> dict:
        letters = np.zeros((self.max_steps, self.word_length), dtype=np.int64)
        feedback_arr = np.zeros((self.max_steps, self.word_length), dtype=np.int64)
        for i, (guess, fb) in enumerate(zip(self.guesses, self.feedbacks)):
            letters[i] = [self.letter_to_idx[ch] for ch in guess]
            feedback_arr[i] = [_FEEDBACK_TO_CODE[c] for c in fb]
        return {"letters": letters, "feedback": feedback_arr}

    def _get_info(self) -> dict:
        candidate_set = set(self.candidates)
        mask = np.array([w in candidate_set for w in self.word_list], dtype=bool)
        return {
            "target": self.target,  # debugging/hints only — not part of the observation
            "num_candidates": len(self.candidates),
            "action_mask": mask,
            "step": self.step_count,
        }

    def render(self):
        """Return an ANSI-colored text rendering of the board so far."""
        codes = {
            FEEDBACK_GREEN: "\033[42;30m",
            FEEDBACK_YELLOW: "\033[43;30m",
            FEEDBACK_BLACK: "\033[100;37m",
        }
        reset = "\033[0m"
        lines = []
        for guess, fb in zip(self.guesses, self.feedbacks):
            cells = [
                f"{codes[_FEEDBACK_TO_CODE[code]]} {ch.upper()} {reset}"
                for ch, code in zip(guess, fb)
            ]
            lines.append("".join(cells))
        for _ in range(self.max_steps - len(self.guesses)):
            lines.append("".join(" _ " for _ in range(self.word_length)))
        return "\n".join(lines)
