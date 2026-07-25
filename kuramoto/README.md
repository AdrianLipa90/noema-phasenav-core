# kuramoto — Synchronisation Substrate

Kuramoto oscillator network underlying PhaseNav's dynamic coherence.

## Overview

The Kuramoto model drives phase synchronisation across the 36D oscillator array.
Each dimension φᵢ is an oscillator with natural frequency ωᵢ.

Kuramoto equation:

```
dφᵢ/dt = ωᵢ + (K/N) · Σⱼ sin(φⱼ − φᵢ)
```

Order parameter (coherence):

```
R·e^(iΨ) = (1/N) · Σⱼ e^(iφⱼ)
phase_R = |R| ∈ [0, 1]
```

`phase_R = 1` → full synchronisation (maximally coherent semantic state).
`phase_R = 0` → incoherent (maximally diverse / entropic).

## Integration

PhaseNav uses Euler integration with adaptive step:

```
φᵢ(t+dt) = φᵢ(t) + dt · (ωᵢ + coupling)
```

The Kuramoto substrate runs as a background daemon (`noema-kuramoto.service`)
updating the shared memory surface at 1 Hz.

## Constants

| Constant | Value | Role |
|---|---|---|
| `KAPPA` | 0.009210... | Coupling constant per dimension |
| `TAU` | 2π | Period |
| `L3, L4, L5` | metatime constants | Higher-order Kuramoto terms |
