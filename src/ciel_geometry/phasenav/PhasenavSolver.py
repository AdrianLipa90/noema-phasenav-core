# Compatibility shim: PhasenavSolver (lowercase n) -> PhaseNavSolver
# Used by noema_surface_mcp_server.py which has a case typo.
# Python imports this as a submodule when getattr fails on the package.
from .solver import PhaseNavSolver

load = PhaseNavSolver.load
