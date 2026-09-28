from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_10 import (
    SCHEMA as SCHEMA_V10,
    _validate_arpl_source_pin,
    validate_bridge_packet_v10,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.11"
SUBTYPE = "ARPL_CLOCK_FIBRE_MATRIX_GRAM"


def _text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _nonnegative(x: Any, name: str) -> float:
    y=float(x)
    if not math.isfinite(y) or y<0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _is_prime(n:int)->bool:
    if n<2: return False
    if n%2==0: return n==2
    d=3
    while d*d<=n:
        if n%d==0: return False
        d+=2
    return True


def _order4(p:int)->int:
    if not _is_prime(p) or p<5:
        raise FractalMoire36Error("ARPL support must contain primes >= 5")
    x=4%p
    order=1
    while x!=1:
        x=(x*4)%p
        order+=1
        if order>p:
            raise FractalMoire36Error("failed to resolve ord_p(4)")
    return order


def _hit_phase(p:int,h:int,e:int)->int|None:
    if h%p==0:
        return None
    target=4%p
    u=(h*h)%p
    for r in range(e):
        if u==target:
            return r
        u=(4*u)%p
    return None


def _visible_modes(periods:tuple[int,...],i:int)->tuple[int,...]:
    e=periods[i]
    visible:set[int]=set()
    for j,f in enumerate(periods):
        if i==j: continue
        g=math.gcd(e,f)
        visible.update(k*(e//g) for k in range(g))
    return tuple(sorted(visible))


def validate_bridge_packet_v11(
    packet: Mapping[str,Any],
    *,
    tolerance: float=1e-10,
)->dict[str,Any]:
    if packet.get("schema")!=SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p10=dict(packet)
    p10["schema"]=SCHEMA_V10

    subtype=packet.get("matrix_overlap_source_subtype")
    matrix_receipt=None

    if subtype is not None and subtype!=SUBTYPE:
        raise FractalMoire36Error("unknown matrix_overlap_source_subtype")

    if subtype==SUBTYPE:
        if packet.get("ifs_covariance_mode")!="OVERLAP_GRAM_COVARIANT":
            raise FractalMoire36Error(
                "ARPL clock-fibre matrix Gram requires OVERLAP_GRAM_COVARIANT"
            )

        pin=_validate_arpl_source_pin(packet)

        theorem_ref=_text(
            packet.get("orbital_heterogeneous_theorem_ref"),
            "orbital_heterogeneous_theorem_ref",
        )
        if packet.get("matrix_storage_contract")!="UPSTREAM_WITNESS_ONLY":
            raise FractalMoire36Error(
                "matrix_storage_contract must be UPSTREAM_WITNESS_ONLY"
            )

        h=packet.get("arpl_separation_h")
        if not isinstance(h,int) or h<6 or h%6:
            raise FractalMoire36Error(
                "arpl_separation_h must be an integer >=6 divisible by 6"
            )

        support=packet.get("arpl_prime_support")
        if not isinstance(support,list) or not support:
            raise FractalMoire36Error("arpl_prime_support must be non-empty")
        if len(set(support))!=len(support):
            raise FractalMoire36Error("arpl_prime_support must be distinct")
        if not all(isinstance(p,int) and _is_prime(p) and p>=5 for p in support):
            raise FractalMoire36Error("arpl_prime_support must be primes >=5")

        periods=tuple(_order4(p) for p in support)
        phases=tuple(_hit_phase(p,h,e) for p,e in zip(support,periods))
        if any(r is None for r in phases):
            raise FractalMoire36Error(
                "every declared ARPL clock-fibre channel must be active"
            )

        inter=_nonnegative(
            packet.get("max_pair_odometer_intertwiner_residual"),
            "max_pair_odometer_intertwiner_residual",
        )
        mismatch=_nonnegative(
            packet.get("max_pair_mismatch_intertwiner_residual"),
            "max_pair_mismatch_intertwiner_residual",
        )
        if inter>tolerance:
            raise FractalMoire36Error("odometer intertwiner residual exceeds tolerance")
        if mismatch>tolerance:
            raise FractalMoire36Error("mismatch intertwiner residual exceeds tolerance")

        ledger=packet.get("heterogeneous_fibre_information_loss_ledger")
        if not isinstance(ledger,list) or not ledger:
            raise FractalMoire36Error(
                "heterogeneous_fibre_information_loss_ledger must be non-empty"
            )
        loss=tuple(_text(v,f"heterogeneous_fibre_information_loss_ledger[{i}]")
                   for i,v in enumerate(ledger))

        ranks=[]
        left_kernels=[]
        right_kernels=[]
        for i,e in enumerate(periods):
            rr=[]; lk=[]; rk=[]
            for j,f in enumerate(periods):
                g=math.gcd(e,f)
                rr.append(g)
                lk.append(e-g)
                rk.append(f-g)
            ranks.append(tuple(rr))
            left_kernels.append(tuple(lk))
            right_kernels.append(tuple(rk))

        visible=tuple(_visible_modes(periods,i) for i in range(len(periods)))
        hidden=tuple(
            tuple(m for m in range(periods[i]) if m not in set(visible[i]))
            for i in range(len(periods))
        )

        matrix_receipt={
            "subtype":SUBTYPE,
            "arpl_source_pin":pin,
            "orbital_heterogeneous_theorem_ref":theorem_ref,
            "arpl_separation_h":h,
            "arpl_prime_support":tuple(support),
            "local_clock_periods":periods,
            "active_pulse_phases":phases,
            "common_clock_size":math.lcm(*periods),
            "local_fibre_dimension_sum":sum(periods),
            "pair_rank_matrix":tuple(ranks),
            "left_kernel_dimension_matrix":tuple(left_kernels),
            "right_kernel_dimension_matrix":tuple(right_kernels),
            "network_visible_modes":visible,
            "network_hidden_modes":hidden,
            "network_hidden_dimensions":tuple(len(x) for x in hidden),
            "max_pair_odometer_intertwiner_residual":inter,
            "max_pair_mismatch_intertwiner_residual":mismatch,
            "matrix_storage_contract":"UPSTREAM_WITNESS_ONLY",
            "heterogeneous_fibre_information_loss_ledger":loss,
            "infinite_support_persistence":"OPEN",
            "phasenav_dimension_identified_with_fibre_sum":False,
            "phasenav_dimension_identified_with_common_clock":False,
        }

    out=validate_bridge_packet_v10(p10,tolerance=tolerance)
    out["schema"]=SCHEMA
    out["heterogeneous_arpl_matrix_receipt"]=matrix_receipt
    out["canon_allowed"]=False
    return out
