# Mini Logic Engines

Explore propositional logic and a small Prolog-style inference engine implemented in Python.

## Engines

- **MiniLogic:** Boolean-expression parsing, truth tables, satisfiability, tautologies, equivalence and propositional inference.
- **MiniProlog:** terms, facts, Horn-style rules, unification with an occurs check, substitutions and depth-limited backward chaining.

The included fictional flight-document scenarios demonstrate positive and negative queries and variable bindings. Depth exhaustion returns an explicit unknown/incomplete-search message instead of claiming the goal is false. Depth-first search is incomplete under a finite bound; this educational engine is not a complete Prolog implementation.

## Quick start

Python 3.12 was used for local validation. Run commands from the repository root.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.minilogic examples/scenario_flight_simple.txt
python -m src.miniprolog examples/scenario_pr2_flight.txt
```

The engines use only the Python standard library.

```bash
python -m src.miniprolog examples/scenario_pr2_flight.txt
```

The cleaned Colab/Jupyter experiment is in [`notebooks/experiment.ipynb`](notebooks/experiment.ipynb). To open it locally, install Jupyter separately (`python -m pip install jupyterlab`) and run `jupyter lab`. Command-line runs save figures instead of requiring an interactive window.

## Data

The examples are fictional symbolic facts, not personal travel records. No external dataset is required.

## Validation and results

Both included scenarios execute locally. Tests cover Boolean laws, occurs-check rejection, variable substitution and depth-exhaustion reporting. See [VALIDATION.md](VALIDATION.md) for exactly what was checked. No historical notebook output is used as evidence for the corrected implementation.

```bash
python -m unittest discover -s tests -v
```

## Repository layout

- `src/`: importable implementation and command-line entry points.
- `notebooks/`: cleaned experiment notebook; original explanatory notes are in Russian.
- `tests/`: focused regression checks.
- `requirements.txt`: direct dependency versions used during validation.
- `DATA.md`: data access and redistribution notes.

This project was developed from a university Colab experiment and subsequently cleaned up for reproducibility. Generated data, trained weights and local paths are excluded from version control.
