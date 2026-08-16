"""Automated and interactive Wordle game runners."""

from __future__ import annotations

from wordle.models import simple_solver as slv


class AutomatedGame:
    """Simulate Wordle games against known target words."""

    def __init__(self, word_list: list[str], first_guess: str, max_steps: int = 6):
        if not word_list:
            raise ValueError("word_list must not be empty")
        if first_guess not in word_list:
            raise ValueError(f"first_guess {first_guess!r} is not in the word list")
        self.word_list = list(word_list)
        self.first_guess = first_guess
        self.max_steps = max_steps

    def play(self, target: str) -> int:
        """Return guesses needed, or ``max_steps + 1`` if unsuccessful."""
        candidates = list(self.word_list)
        guess = self.first_guess

        for step in range(1, self.max_steps + 1):
            feedback = slv.determine_feedback(target, guess)
            if all(code == "g" for code in feedback):
                return step
            candidates, next_guess = slv.next_guess(guess, feedback, candidates)
            if next_guess is None:
                break
            guess = next_guess

        return self.max_steps + 1

    def run_simulation(self, n_games: int, verbose: bool = True) -> list[int]:
        """Simulate *n_games* against random targets."""
        if n_games <= 0:
            raise ValueError("n_games must be positive")
        results = []
        for _ in range(n_games):
            target = slv.choose_random_word(self.word_list)
            steps = self.play(target)
            if verbose:
                print(f"{steps}: {target}")
            results.append(steps)
        return results


class HumanGame:
    """Interactive assistant that suggests guesses based on user feedback."""

    def __init__(self, word_list: list[str], first_guess: str, max_steps: int = 6):
        if first_guess not in word_list:
            raise ValueError(f"first_guess {first_guess!r} is not in the word list")
        self.word_list = list(word_list)
        self.first_guess = first_guess
        self.max_steps = max_steps

    def play(self) -> str:
        """Run an interactive game and return the final status message."""
        print("g - Green, y - Yellow, b - Gray")
        candidates = list(self.word_list)
        guess = self.first_guess

        for step in range(1, self.max_steps + 1):
            print(
                f"\nAttempt {step}. Possible words: {len(candidates)}. Suggested: {guess}"
            )
            actual_guess = input("Your guess: ").strip().lower()
            feedback = self._read_feedback()
            if all(code == "g" for code in feedback):
                return "Congratulations!"
            candidates, guess = slv.next_guess(actual_guess, feedback, candidates)
            if guess is None:
                return "No candidates remain; please check the feedback."

        return "Better luck next time!"

    @staticmethod
    def _read_feedback() -> list[str]:
        """Read and validate a comma-separated feedback string."""
        while True:
            raw = input("Feedback (e.g. g,y,b,b,g): ").strip().lower()
            feedback = [part.strip() for part in raw.split(",")]
            if len(feedback) == 5 and all(code in {"g", "y", "b"} for code in feedback):
                return feedback
            print("Please enter exactly five codes, each g, y, or b.")
