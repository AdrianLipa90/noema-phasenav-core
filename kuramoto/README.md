# kuramoto

Executable Kuramoto synchronization surface for PhaseNav oscillator populations.

The implementation enforces at least three oscillators and uses the project baseline
frequency 7.83 Hz when no per-oscillator natural frequency is supplied.

Files:
- `synchronizer.py` — order parameter, integration step and simulation;
- `diagnostics.py` — coherence/convergence reports;
- `__init__.py` — import surface.
