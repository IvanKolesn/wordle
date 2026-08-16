# `wordle` package

The `wordle` package contains the game logic, solver, terminal interface, and Gymnasium environment.

## Sub folders:

- models - automated models capable of playing the game
- corpus - words that can be played

## Modules

- `config.py` — language/game configuration (goes with config.yaml)
- `corpus.py` — loading and cleaning word lists
- `env.py` — Gymnasium-compatible Wordle environment (for future model development)
- `game.py` — code for human and automated game modes
- `main.py` — actual game launcher. Command-line entry point
- `terminal_ui.py` — console interface for human playing in terminal
- `web_ui.py` — HTML interface for human playing in browser
- `__init__.py` — well, you know :)

## Running

From the project root:

```bash
python -m wordle.main --lang en
python -m wordle.main --lang ru
```

More in main README.md

The default first guesses are `crane` for English and `отвар` for Russian.

## Implementation notes

Repeated-letter feedback follows the standard Wordle rules. The solver uses the same feedback calculation when filtering candidate words, so duplicate letters are handled consistently between gameplay and candidate selection.
