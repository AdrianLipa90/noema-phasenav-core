from __future__ import annotations

import math
import re
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_11 import (
    SCHEMA as SCHEMA_V11,
    validate_bridge_packet_v11,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.12"
VISIBILITY_MODE = "GRH_SOURCE_PRIME_REPLICATION"
ARPL_REPOSITORY = "AdrianLipa90/On-Primes"
_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")


def _text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def _prime_factors(n: int) -> tuple[int, ...]:
    n = int(n)
    if n < 1:
        raise FractalMoire36Error("factor input must be positive")
    out: list[int] = []
    if n % 2 == 0:
        out.append(2)
        while n % 2 == 0:
            n //= 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            out.append(d)
            while n % d == 0:
                n //= d
        d += 2
    if n > 1:
        out.append(n)
    return tuple(out)


def _valuation(n: int, ell: int) -> int:
    n = abs(int(n))
    ell = int(ell)
    if n == 0 or ell < 2:
        raise FractalMoire36Error("invalid valuation input")
    out = 0
    while n % ell == 0:
        n //= ell
        out += 1
    return out


def _divisors(n: int) -> tuple[int, ...]:
    n = int(n)
    if n < 1:
        raise FractalMoire36Error("period must be positive")
    lo: list[int] = []
    hi: list[int] = []
    d = 1
    while d * d <= n:
        if n % d == 0:
            lo.append(d)
            if d * d != n:
                hi.append(n // d)
        d += 1
    return tuple(lo + list(reversed(hi)))


def _order_mod(a: int, p: int) -> int:
    a = int(a) % int(p)
    p = int(p)
    if not _is_prime(p) or a == 0:
        raise FractalMoire36Error("multiplicative order requires a nonzero prime residue")
    order = p - 1
    for ell in _prime_factors(order):
        while order % ell == 0 and pow(a, order // ell, p) == 1:
            order //= ell
    return order


def _frontier_pin(packet: Mapping[str, Any]) -> dict[str, Any]:
    repo = _text(
        packet.get("arpl_visibility_repository"),
        "arpl_visibility_repository",
    )
    if repo != ARPL_REPOSITORY:
        raise FractalMoire36Error(
            f"arpl_visibility_repository must be {ARPL_REPOSITORY}"
        )
    branch = _text(
        packet.get("arpl_visibility_branch"),
        "arpl_visibility_branch",
    )
    sha = _text(
        packet.get("arpl_visibility_commit_sha"),
        "arpl_visibility_commit_sha",
    ).lower()
    if not _SHA40.fullmatch(sha):
        raise FractalMoire36Error(
            "arpl_visibility_commit_sha must be exactly 40 hexadecimal characters"
        )
    files = packet.get("arpl_visibility_source_files")
    if not isinstance(files, list) or not files:
        raise FractalMoire36Error(
            "arpl_visibility_source_files must be a non-empty list"
        )
    normalized = tuple(
        _text(v, f"arpl_visibility_source_files[{i}]")
        for i, v in enumerate(files)
    )
    witness = _text(
        packet.get("arpl_visibility_pin_witness_ref"),
        "arpl_visibility_pin_witness_ref",
    )
    return {
        "repository": repo,
        "branch": branch,
        "commit_sha": sha,
        "source_files": normalized,
        "pin_witness_ref": witness,
        "immutable_pin": True,
    }


def _certificate(h: int, p: int, d: int) -> dict[str, Any]:
    e4 = _order_mod(4, p)
    eh = _order_mod(h * h, p)
    if e4 % eh:
        raise FractalMoire36Error(
            "declared source channel is not active under the order criterion"
        )
    if e4 % d:
        raise FractalMoire36Error(
            "local denominator does not divide source ord_p(4)"
        )

    i4 = (p - 1) // e4
    ih = (p - 1) // eh
    if ih % i4:
        raise FractalMoire36Error("source index tuple lost activity divisibility")

    modulus = 1
    valuation_ledger = []
    for ell in _prime_factors(d):
        t = _valuation(p - 1, ell)
        modulus *= ell ** (t + 1)
        valuation_ledger.append((ell, t))

    if math.gcd(p, modulus) != 1:
        raise FractalMoire36Error(
            "source prime unexpectedly ramifies in certificate cyclotomic field"
        )

    return {
        "source_prime": p,
        "denominator": d,
        "ord4": e4,
        "ord_h2": eh,
        "index4": i4,
        "index_h2": ih,
        "cyclotomic_modulus": modulus,
        "frobenius_residue": p % modulus,
        "p_minus_1_valuation_ledger": tuple(valuation_ledger),
    }


def validate_bridge_packet_v12(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p11 = dict(packet)
    p11["schema"] = SCHEMA_V11

    mode = packet.get("infinite_support_visibility_mode")
    visibility_receipt = None

    if mode is not None and mode != VISIBILITY_MODE:
        raise FractalMoire36Error("unknown infinite_support_visibility_mode")

    if mode == VISIBILITY_MODE:
        if packet.get("grh_assumption_declared") is not True:
            raise FractalMoire36Error(
                "GRH_SOURCE_PRIME_REPLICATION requires grh_assumption_declared=true"
            )
        if packet.get("unconditional_infinite_exposure_claim") is not False:
            raise FractalMoire36Error(
                "unconditional infinite exposure is not established"
            )
        if packet.get("physical_observability_claim") is not False:
            raise FractalMoire36Error(
                "arithmetic infinite exposure is not physical observability"
            )

        theorem_ref = _text(
            packet.get("grh_visibility_theorem_ref"),
            "grh_visibility_theorem_ref",
        )
        pin = _frontier_pin(packet)

        support = packet.get("arpl_prime_support")
        h = packet.get("arpl_separation_h")
        if not isinstance(h, int) or h < 6 or h % 6:
            raise FractalMoire36Error(
                "arpl_separation_h must remain an integer >=6 divisible by 6"
            )
        if not isinstance(support, list) or not support:
            raise FractalMoire36Error("arpl_prime_support must remain non-empty")

        certificate_rows = []
        periods = []
        denominator_sets = []
        for p in support:
            if not isinstance(p, int) or not _is_prime(p) or p < 5:
                raise FractalMoire36Error("ARPL support must contain primes >=5")
            e = _order_mod(4, p)
            periods.append(e)
            ds = tuple(d for d in _divisors(e) if d > 1)
            denominator_sets.append(ds)
            for d in ds:
                certificate_rows.append(_certificate(h, p, d))

        expected_hidden = tuple(0 for _ in support)

        out = validate_bridge_packet_v11(p11, tolerance=tolerance)
        finite = out.get("heterogeneous_arpl_matrix_receipt")
        if finite is None:
            raise FractalMoire36Error(
                "GRH visibility mode requires the v0.11 ARPL matrix source subtype"
            )
        if tuple(finite["local_clock_periods"]) != tuple(periods):
            raise FractalMoire36Error(
                "visibility periods do not match v0.11 matrix-source periods"
            )

        visibility_receipt = {
            "mode": VISIBILITY_MODE,
            "grh_assumption_declared": True,
            "grh_visibility_theorem_ref": theorem_ref,
            "arpl_visibility_source_pin": pin,
            "local_clock_periods": tuple(periods),
            "required_denominator_sets": tuple(denominator_sets),
            "replication_certificate_count": len(certificate_rows),
            "replication_certificates": tuple(certificate_rows),
            "finite_support_hidden_dimensions": tuple(
                finite["network_hidden_dimensions"]
            ),
            "infinite_support_hidden_dimensions_under_grh": expected_hidden,
            "infinite_support_hidden_subspace_under_grh": "ZERO_FOR_EACH_FIXED_LOCAL_FIBRE",
            "full_exposure_set_natural_density_claim": False,
            "positive_lower_density_exposure_claim_under_grh": True,
            "unconditional_infinite_exposure_claim": False,
            "unconditional_status": "OPEN",
            "physical_observability_claim": False,
        }

        out["schema"] = SCHEMA
        out["grh_infinite_visibility_receipt"] = visibility_receipt
        out["canon_allowed"] = False
        return out

    out = validate_bridge_packet_v11(p11, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["grh_infinite_visibility_receipt"] = None
    out["canon_allowed"] = False
    return out
