# Validation

Validated on 2026-09-27 with Python 3.12 on Linux CPU.

- The cleaned source notebook passed notebook schema checks and sequential execution.
- Both fictional flight scenarios run through the extracted command-line modules.
- Four unit tests cover Boolean laws, rejection of cyclic unification, multi-rule variable substitution, and unknown/incomplete search when the depth bound is reached.
- No external data or trained models are needed.

Run `python -m unittest discover -s tests -v` from the repository root.

The finite-depth, depth-first inference engine is educational and incomplete. Passing these examples does not establish full Prolog compatibility or theorem-prover completeness.
