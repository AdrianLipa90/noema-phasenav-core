"""PhaseNav PNV Benchmark — efficiency & cost of computation on NOEMA.

Measures: microseconds per call, ops/sec, memory, total throughput.
Tests both MuInterpreter (.pnv) and HTRIEngine (C extension) paths.
Zero external deps. Pure stdlib.
"""
import sys, os, time, json, statistics

sys.path.insert(0, '/home/adrian/pnv/bin')
import mu

PNV_DIR = os.path.dirname(os.path.abspath(__file__))
ITERATIONS = 500
WARMUP = 50

# ── Helpers ───────────────────────────────────────────────────────────

def bench(label, fn, n=ITERATIONS, warmup=WARMUP):
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        times.append(t1 - t0)
    med = statistics.median(times)
    mean = statistics.mean(times)
    mn = min(times)
    p95 = sorted(times)[int(n * 0.95)]
    ops_sec = 1e9 / mean if mean > 0 else float('inf')
    return {
        "label": label,
        "n": n,
        "median_ns": round(med),
        "mean_ns": round(mean),
        "min_ns": mn,
        "p95_ns": p95,
        "ops_per_sec": round(ops_sec),
    }

# ── Load .pnv via MuInterpreter ──────────────────────────────────────

interp = mu.MuInterpreter()
metatime_pnv = os.path.join(PNV_DIR, 'metatime.pnv')
vector_pnv = os.path.join(PNV_DIR, 'vector.pnv')
distance_pnv = os.path.join(PNV_DIR, 'distance.pnv')
solver_pnv = os.path.join(PNV_DIR, 'solver.pnv')

print("Loading .pnv files...")
interp.load(metatime_pnv)
interp.load(vector_pnv)
interp.load(distance_pnv)
interp.load(solver_pnv)
print("  metatime + vector + distance + solver loaded")

# ── HTRIEngine baseline ──────────────────────────────────────────────

eng = mu.HTRIEngine()
eng.tick()

# ── Benchmark suite ───────────────────────────────────────────────────

results = []

# 1. HTRIEngine.tick
results.append(bench("HTRIEngine.tick", lambda: eng.tick()))

# 2. HTRIEngine.coherence
results.append(bench("HTRIEngine.coherence", lambda: eng.coherence()))

# 3. HTRIEngine.kuramoto_step
results.append(bench("HTRIEngine.kuramoto_step", lambda: eng.kuramoto_step()))

# 4. HTRIEngine.berry_connection (2 oscillator pair)
phi = eng.phi
results.append(bench(
    "HTRIEngine.berry_connection",
    lambda: eng.berry_connection(0, 1)
))

# 5. HTRIEngine.angular_distance
results.append(bench(
    "HTRIEngine.angular_distance",
    lambda: eng.angular_distance(0, 1)
))

# 6. HTRIEngine.holonomy (3 oscillators)
results.append(bench(
    "HTRIEngine.holonomy",
    lambda: eng.holonomy([0, 1, 2])
))

# 7. HTRIEngine.bloch
results.append(bench("HTRIEngine.bloch", lambda: eng.bloch(0)))

# 8. HTRIEngine.energy
results.append(bench("HTRIEngine.energy", lambda: eng.energy()))

# 9. HTRIEngine.state (full state dict)
results.append(bench("HTRIEngine.state", lambda: eng.state()))

# 10. MuInterpreter.eval — simple constant
results.append(bench("Mu.eval(KAPPA)", lambda: interp.eval("KAPPA")))

# 11. MuInterpreter.eval — order_parameter on phi
phi_list = list(phi)
results.append(bench(
    "Mu.eval(order_parameter)",
    lambda: interp.call("order_parameter", phi_list)
))

# 12. MuInterpreter.eval — mean_phase
results.append(bench(
    "Mu.eval(mean_phase)",
    lambda: interp.call("mean_phase", phi_list)
))

# 13. MuInterpreter.eval — inner_product_36
v2 = list(phi)
results.append(bench(
    "Mu.eval(inner_product_36)",
    lambda: interp.call("inner_product_36", phi_list, v2)
))

# 14. MuInterpreter.eval — berry_connection_36
results.append(bench(
    "Mu.eval(berry_connection_36)",
    lambda: interp.call("berry_connection_36", phi_list, v2)
))

# 15. MuInterpreter.eval — angular_distance_36
results.append(bench(
    "Mu.eval(angular_distance_36)",
    lambda: interp.call("angular_distance_36", phi_list, v2)
))

# 16. MuInterpreter.eval — edge_weight_36
results.append(bench(
    "Mu.eval(edge_weight_36)",
    lambda: interp.call("edge_weight_36", phi_list, v2)
))

# 17. MuInterpreter.eval — semantic_mass
results.append(bench(
    "Mu.eval(semantic_mass)",
    lambda: interp.call("semantic_mass", 1, phi_list)
))

# 18. MuInterpreter.eval — phase36_from_id
results.append(bench(
    "Mu.eval(phase36_from_id)",
    lambda: interp.call("phase36_from_id", 42)
))

# 19. MuInterpreter.eval — holonomy_36 (3 vectors)
v3 = list(phi)
results.append(bench(
    "Mu.eval(holonomy_36)",
    lambda: interp.call("holonomy_36", [phi_list, v2, v3])
))

# 20. Full evolve cycle (tick + kuramoto + sync)
def full_cycle():
    eng.tick()
    eng.kuramoto_step()
    eng.coherence()
results.append(bench("HTRIEngine.full_cycle", full_cycle, n=200))

# ── Aggregate ─────────────────────────────────────────────────────────

total_ns = sum(r["mean_ns"] for r in results)
total_per_call = total_ns

report = {
    "benchmark": "PhaseNav PNV Efficiency & Cost",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "iterations": ITERATIONS,
    "warmup": WARMUP,
    "total_mean_ns": round(total_ns),
    "total_mean_us": round(total_ns / 1000, 1),
    "results": results,
}

# ── Print ─────────────────────────────────────────────────────────────

print()
print(f"{'='*78}")
print(f"  PhaseNav PNV Benchmark — {ITERATIONS} iterations, {WARMUP} warmup")
print(f"{'='*78}")
print(f"{'Operation':<40s} {'median':>10s} {'mean':>10s} {'min':>10s} {'p95':>10s} {'ops/s':>10s}")
print(f"{'-'*78}")
for r in results:
    label = r["label"]
    print(f"{label:<40s} {r['median_ns']:>8d}ns {r['mean_ns']:>8d}ns {r['min_ns']:>8d}ns {r['p95_ns']:>8d}ns {r['ops_per_sec']:>9d}")
print(f"{'-'*78}")
print(f"{'TOTAL per full pass':<40s} {total_ns/1000:>8.1f}µs")
print(f"{'='*78}")

# Cost estimate: assuming 1s loop, how many full cycles per second
cycles_per_sec = 1e9 / total_ns if total_ns > 0 else 0
print(f"\nCost estimate:")
print(f"  Full benchmark pass: {total_ns/1000:.1f}µs")
print(f"  Theoretical full passes/sec: {cycles_per_sec:.0f}")
print(f"  HTRIEngine tick+kuramoto+coherence: {results[-1]['mean_ns']/1000:.1f}µs")
print(f"  HTRIEngine ticks/sec (theoretical): {1e9/results[-1]['mean_ns']:.0f}")

# Save JSON
out_path = os.path.join(PNV_DIR, 'benchmark_results.json')
with open(out_path, 'w') as f:
    json.dump(report, f, indent=2)
print(f"\nResults saved: {out_path}")
