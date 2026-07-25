"""PhaseNav 36D — basic usage examples."""

from ciel_geometry.phasenav import (
    M_sentence_phase,
    M_sentence_phase_trajectory,
    M_36d_distance,
    PhaseMemoryHypercrystal,
    PhaseNavSolver,
)


def example_encoding():
    print("=== Encoding ===")
    v = M_sentence_phase("the nature of consciousness")
    print(f"36D vector, first 4 dims: {[round(x, 3) for x in v[:4]]}")

    v2 = M_sentence_phase("awareness and perception")
    d = M_36d_distance(v, v2)
    print(f"distance('consciousness', 'awareness'): {d:.4f}")


def example_trajectory():
    print("\n=== Trajectory + Berry Holonomy ===")
    v_final, traj, holonomy = M_sentence_phase_trajectory("words carry semantic weight")
    print(f"words: {len(traj)}, holonomy Γ: {holonomy:.4f}")
    for k, v in enumerate(traj):
        print(f"  V_{k}: [{', '.join(f'{x:.2f}' for x in v[:3])}, ...]")


def example_crystal():
    print("\n=== Crystal Retrieval ===")
    crystal = PhaseMemoryHypercrystal()
    crystal.load()
    print(f"crystal facets: {len(crystal)}")

    results = crystal.retrieve("Berry connection semantic holonomy", top_k=3)
    for r in results:
        print(f"  [{r.get('m_score', 0):.4f}] d={r['distance']:.4f}  {r['text'][:70]}")


def example_trajectory_retrieval():
    print("\n=== Trajectory Retrieval (Ω narrowing) ===")
    crystal = PhaseMemoryHypercrystal()
    crystal.load()

    out = crystal.retrieve_trajectory("meaning derived from operator composition", top_k=3)
    print(f"Ω-sizes: {out['omega_sizes']}")
    print(f"holonomy: {out['holonomy']:.4f}")
    for r in out["results"]:
        print(f"  [{r.get('m_score', 0):.4f}] {r['text'][:70]}")


def example_solver():
    print("\n=== Solver ===")
    # PhaseNavSolver.load() reads NOEMA data files from /dev/shm/ciel_noema/phasenav/
    # Those files are written by pnv_runtime._init() on import when NOEMA is running.
    # Without NOEMA, the solver loads but may find no edges (empty trace).
    try:
        solver = PhaseNavSolver.load()
    except Exception as e:
        print(f"  Solver unavailable (requires NOEMA data files): {e}")
        return
    # trace() takes a list of card IDs (concept strings or glossary IDs)
    trace = solver.trace(["curiosity", "understanding"])
    print(f"steps: {len(trace.steps)}, total path integral: {trace.total_path_integral:.4f}")
    for step in trace.steps[:3]:
        print(f"  {step.operator_hook:12s}  Δφ={step.phase_delta:.4f}  viscosity={step.holonomic_viscosity:.4f}")


if __name__ == "__main__":
    example_encoding()
    example_trajectory()
    example_crystal()
    example_trajectory_retrieval()
    example_solver()
