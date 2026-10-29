# Validation

## Isolated recheck: 29 October 2026

A fresh per-project virtual environment was created on Windows with Python
3.12.10. The pinned runtime and development dependencies installed from wheels;
`pip check` passed. The environment's pip was updated to 26.2.2. The final
`pip-audit` scan reported no known vulnerabilities in that installed package
set at the time of the check. This is a dated advisory check, not a security guarantee.

- Six unit tests passed, including two new regressions for independent anonymous
  variables and hiding internal anonymous bindings from result output.
- Before the fix, `pair(_, _)` returned no solution for the fact
  `pair(alice, bob)`. After the fix it succeeds, while repeated named variables
  such as `_Same` still require equal values.
- Both supplied example scripts completed. Notebook format/syntax passed and
  every code cell ran sequentially, generating and exercising the embedded
  scripts in an ignored results directory.
- The notebook's embedded MiniProlog implementation was synchronized with the
  corrected module. No external dataset or third-party runtime dependency is needed.

MiniLogic's `axi(a -> b+c)` expands to two rules; it is a teaching shorthand,
not classical disjunctive inference. The README now makes this explicit.
Finite-depth DFS remains incomplete. These checks do not establish full Prolog
compatibility, interactive Jupyter behavior or theorem-prover completeness.
Remote CI has not yet run on these prepared changes.

## Earlier preparation record: 27 September 2026

Validated on 2026-09-27 with Python 3.12 on Linux CPU.

- The cleaned source notebook passed notebook schema checks and sequential execution.
- Both fictional flight scenarios run through the extracted command-line modules.
- Four unit tests cover Boolean laws, rejection of cyclic unification, multi-rule variable substitution, and unknown/incomplete search when the depth bound is reached.
- No external data or trained models are needed.

Run `python -m unittest discover -s tests -v` from the repository root.

The finite-depth, depth-first inference engine is educational and incomplete. Passing these examples does not establish full Prolog compatibility or theorem-prover completeness.
