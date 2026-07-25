# encryption — Collatz Hash & Phase Encoding

Deterministic text-to-phase encoding via Collatz sequence.

## Collatz Hash

```python
from ciel_geometry.phasenav.pnv_runtime import M_collatz_hash

h = M_collatz_hash("word")  # → deterministic int
```

Algorithm:

```
n = sum(ord(c) for c in word) + len(word) * 17 + 1
steps = 0
while n != 1:
    n = n // 2 if n % 2 == 0 else 3 * n + 1
    steps += 1
return steps + len(word) * 31 + ord(word[0]) * 7 + ord(word[-1]) * 13
```

Properties:
- **Deterministic**: same word → same hash always
- **Chaotic**: small changes in word → large changes in hash
- **Fast**: O(log n) average, stdlib only, no dependencies

## Phase Encoding

From hash to 36 phases:

```
φᵢ = (h · κ · τ · (i+1)) mod τ    for i ∈ {0, ..., 35}
```

where `κ = KAPPA ≈ 0.00921` and `τ = 2π`.

## Sentence Encoding

For a sentence of N words, phases accumulate via circular mean:

```python
# After word k:
sums_s[i] += sin(phi_i)
sums_c[i] += cos(phi_i)
V_k[i] = atan2(sums_s[i] / (k+1), sums_c[i] / (k+1)) % TAU
```

This is a **running circular mean** — invariant to word order perturbations
and robust to out-of-vocabulary words.

## Security Note

This is **semantic encoding**, not cryptographic encryption.
Do not use for security-sensitive applications.
