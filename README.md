# Wordle solver

A Python implementation of Wordle with:

- interactive terminal game
- heuristic solver
- Gymnasium environment for reinforcement learning experiments
- English and Russian corpora support
- correct handling of repeated letters in Wordle feedback

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

Run the package from the project root:

```bash
python -m wordle.main
```

Select a language explicitly with `--lang`:

```bash
python -m wordle.main --lang en
python -m wordle.main --lang ru
```

The default first guesses are:

- English: `crane`
- Russian: `отвар`

You can also specify the number of automated games with `--games`.

## Project structure

- `wordle/` — application package
- `wordle/corpus/` — English and Russian word lists
- `wordle/main.py` — command-line entry point
- `wordle/game.py` — human and automated game modes
- `wordle/solver.py` — candidate filtering and guess selection
- `wordle/env.py` — Gymnasium-compatible environment
- `wordle/terminal_ui.py` — Rich-based console interface
- `wordle/corpus.py` — word-list loading and cleaning
- `wordle/config.py` — language and game configuration
- `wordle/config.yaml` — default configuration
- `wordle/__init__.py` — package initializer and public package exports

## Development notes

The project uses package-relative imports and should be run with `python -m wordle.main` from the project root. The package initializer (`wordle/__init__.py`) exposes `WordleEnv` as the main public environment class.

The Wordle feedback implementation correctly handles repeated letters: a letter is marked yellow only when an unmatched occurrence remains in the target word. Candidate filtering uses the same feedback logic.

The Python source files have been compilation-checked for syntax/import issues. The full Gymnasium environment was not executed in the development sandbox because its external dependencies could not be installed there; install `requirements.txt` before running the environment locally.

## Extending the project

To add another language, add a corpus under `wordle/corpus/` and an appropriate language entry to `wordle/config.yaml`.
