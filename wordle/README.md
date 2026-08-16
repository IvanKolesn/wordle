# `wordle` package

The `wordle` package contains the game logic, solver, terminal interface, and Gymnasium environment.

## Modules

- `env.py` — Gymnasium-compatible Wordle environment
- `solver.py` — candidate filtering and guess selection algorithms
- `game.py` — human and automated game modes
- `terminal_ui.py` — Rich-based console interface
- `corpus.py` — loading and cleaning word lists
- `config.py` — language/game configuration
- `main.py` — command-line entry point
- `__init__.py` — package initializer; exports `WordleEnv`

## Running

From the project root:

```bash
python -m wordle.main --lang en
python -m wordle.main --lang ru
```

The default first guesses are `crane` for English and `отвар` for Russian.

## Implementation notes

Repeated-letter feedback follows the standard Wordle rules. The solver uses the same feedback calculation when filtering candidate words, so duplicate letters are handled consistently between gameplay and candidate selection.
