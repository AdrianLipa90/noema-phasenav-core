# solver

Executable repository-level façade for `ciel_geometry.phasenav.solver`.

Files:
- `runtime.py` — load and trace helpers;
- `cli.py` — command-line trace entry point;
- `__init__.py` — import surface.

The solver no longer returns synthetic zero orbit vectors. Missing orbit/operator
records raise, while the loader reconstructs missing runtime tables from canonical cards.
