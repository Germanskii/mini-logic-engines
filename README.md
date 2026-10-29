# Mini Logic Engines

[![Checks](https://github.com/Germanskii/mini-logic-engines/actions/workflows/checks.yml/badge.svg)](https://github.com/Germanskii/mini-logic-engines/actions/workflows/checks.yml)
Explore propositional logic and a small Prolog-style inference engine implemented in Python.

## Engines

- **MiniLogic:** Boolean-expression parsing, truth tables, satisfiability, tautologies, equivalence and propositional inference.
- **MiniProlog:** terms, facts, Horn-style rules, unification with an occurs check, substitutions and depth-limited backward chaining.

The included fictional flight-document scenarios demonstrate positive and negative queries and variable bindings. Depth exhaustion returns an explicit unknown/incomplete-search message instead of claiming the goal is false. Depth-first search is incomplete under a finite bound; this educational engine is not a complete Prolog implementation.

## Quick start

Use **Python 3.12** for the pinned environment. The October recheck used Python
3.12.10 on Windows CPU. Run commands from the repository root.

```bash
git clone https://github.com/Germanskii/mini-logic-engines.git
cd mini-logic-engines
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m src.minilogic examples/scenario_flight_simple.txt
python -m src.miniprolog examples/scenario_pr2_flight.txt
```

The engines use only the Python standard library.

### Rule syntax and variable scope

In MiniProlog, each `_` is an independent anonymous variable: `pair(_,_)` can
match `pair(alice,bob)`. Repeated named variables, including `_Same`, must agree.
Anonymous bindings are omitted from query results.

MiniLogic has a teaching-specific rule shorthand: `axi(a -> b+c)` adds both
`a -> b` and `a -> c`. This rule command does **not** implement classical
disjunctive inference. The Boolean-expression commands (`truth`, `sat`, `valid`
and `equiv`) still interpret `+` as OR. Use the engines to explore these explicit
semantics rather than treating the rule language as a general theorem prover.

[Open in Colab](https://colab.research.google.com/github/Germanskii/mini-logic-engines/blob/main/notebooks/experiment.ipynb). The cleaned Colab/Jupyter experiment is in [`notebooks/experiment.ipynb`](notebooks/experiment.ipynb). To open it locally, install Jupyter separately (`python -m pip install jupyterlab`) and run `jupyter lab`.

## Data

The examples are fictional symbolic facts, not personal travel records. No external dataset is required.

## Validation and results

Both included scenarios execute locally. Tests cover Boolean laws, occurs-check rejection, variable substitution and depth-exhaustion reporting. See [VALIDATION.md](VALIDATION.md) for exactly what was checked. No historical notebook output is used as evidence for the corrected implementation.

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

GitHub Actions runs the regression tests, both example scripts and notebook format checks.

## Repository layout

- `src/`: importable implementation and command-line entry points.
- `notebooks/`: cleaned experiment notebook; original explanatory notes are in Russian.
- `tests/`: focused regression checks.
- `requirements.txt`: documents that the engines need only the standard library.
- `DATA.md`: data access and redistribution notes.

This project was developed from a university Colab experiment and subsequently cleaned up for reproducibility. Generated data, trained weights and local paths are excluded from version control.


The portfolio cleanup and packaging used AI-assisted development. The notebooks derive from the original university work; validation limits are documented above.
