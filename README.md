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

Select game mode with `--test` (test model or play yourself): 

```bash
python -m wordle.main --mode test
python -m wordle.main --mode human
```

## Project structure

Can be found in README in main folder

## Game rules

Standard NYT wordle rules: https://www.nytimes.com/2023/08/01/crosswords/how-to-talk-about-wordle.html

## Future plans:

1. Train RL model (Q-learner, DQN, etc)
2. Expand game to 4 and 6 letter versions

## Extending the project

To add another language, add a corpus under `wordle/corpus/` and an appropriate language entry to `wordle/config.yaml`.
