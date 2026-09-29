from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_12 import (
    SCHEMA as SCHEMA_V12,
    validate_bridge_packet_v12,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.13"
OPERATOR_MODE = "ARPL_RELATIONAL_ZERO_PROJECTORS"
STORAGE_MODE = "UPSTREAM_WITNESS_ONLY"


def _text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _positive_int(x: Any, name: str) -> int:
    if not isinstance(x, int) or x < 1:
        raise FractalMoire36Error(f"{name} must be a positive integer")
    return x


def _nonnegative(x: Any, name: str) -> float:
    y=float(x)
    if not math.isfinite(y) or y<0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _optional_residual(
    packet: Mapping[str,Any],
    key: str,
    tolerance: float,
) -> float | None:
    if key not in packet:
        return None
    value=_nonnegative(packet.get(key),key)
    if value>tolerance:
        raise FractalMoire36Error(f"{key} exceeds tolerance")
    return value


def validate_bridge_packet_v13(
    packet: Mapping[str,Any],
    *,
    tolerance: float=1e-10,
)->dict[str,Any]:
    if packet.get("schema")!=SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p12=dict(packet)
    p12["schema"]=SCHEMA_V12

    mode=packet.get("relational_zero_operator_mode")
    operator_receipt=None

    if mode is not None and mode!=OPERATOR_MODE:
        raise FractalMoire36Error("unknown relational_zero_operator_mode")

    if mode==OPERATOR_MODE:
        if packet.get("relational_operator_storage")!=STORAGE_MODE:
            raise FractalMoire36Error(
                "relational_operator_storage must be UPSTREAM_WITNESS_ONLY"
            )
        if packet.get("physical_quantum_observable_claim") is not False:
            raise FractalMoire36Error(
                "physical quantum observable claim is not established"
            )

        source_ref=_text(
            packet.get("relational_zero_operator_source_ref"),
            "relational_zero_operator_source_ref",
        )

        n=_positive_int(packet.get("ambient_group_order"),"ambient_group_order")
        g0=_positive_int(packet.get("base_subgroup_order"),"base_subgroup_order")
        gh=_positive_int(packet.get("activity_subgroup_order"),"activity_subgroup_order")
        ga=_positive_int(packet.get("total_subgroup_order"),"total_subgroup_order")

        if n%ga or ga%gh or gh%g0:
            raise FractalMoire36Error(
                "subgroup orders must satisfy base | activity | total | ambient"
            )

        i0=n//g0
        ih=n//gh
        ia=n//ga

        rh=i0-ih
        rz=ih-ia
        rt=i0-ia

        if rt!=rh+rz:
            raise FractalMoire36Error("defect rank additivity failed")

        zero=(rt==0)
        enlargement=ga//g0
        normalized=rt/i0

        expected=1.0-(1.0/enlargement)
        if not math.isclose(
            normalized,
            expected,
            rel_tol=1e-14,
            abs_tol=1e-14,
        ):
            raise FractalMoire36Error(
                "normalized relational defect lost quantized enlargement identity"
            )

        if "declared_relational_zero" in packet:
            declared=packet.get("declared_relational_zero")
            if declared is not zero:
                raise FractalMoire36Error(
                    "declared_relational_zero contradicts computed zero gate"
                )

        if "declared_total_defect_rank" in packet:
            declared_rank=packet.get("declared_total_defect_rank")
            if declared_rank!=rt:
                raise FractalMoire36Error(
                    "declared_total_defect_rank contradicts computed rank"
                )

        residuals={
            "activity_projection_residual":_optional_residual(
                packet,"activity_projection_residual",tolerance
            ),
            "depth_projection_residual":_optional_residual(
                packet,"depth_projection_residual",tolerance
            ),
            "total_projection_residual":_optional_residual(
                packet,"total_projection_residual",tolerance
            ),
            "orthogonal_layer_residual":_optional_residual(
                packet,"orthogonal_layer_residual",tolerance
            ),
            "operator_decomposition_residual":_optional_residual(
                packet,"operator_decomposition_residual",tolerance
            ),
        }

        operator_receipt={
            "mode":OPERATOR_MODE,
            "source_ref":source_ref,
            "storage_contract":STORAGE_MODE,
            "ambient_group_order":n,
            "base_subgroup_order":g0,
            "activity_subgroup_order":gh,
            "total_subgroup_order":ga,
            "base_projection_rank":i0,
            "activity_projection_rank":ih,
            "total_projection_rank":ia,
            "activity_defect_rank":rh,
            "depth_defect_rank":rz,
            "total_defect_rank":rt,
            "rank_additivity":True,
            "relational_zero":zero,
            "quotient_enlargement_factor":enlargement,
            "normalized_relational_defect":normalized,
            "operator_spectrum_bound":(0,1),
            "activity_depth_orthogonal":True,
            "residual_witnesses":residuals,
            "physical_quantum_observable_claim":False,
            "phasenav_36d_is_full_operator_dimension":False,
        }

    out=validate_bridge_packet_v12(p12,tolerance=tolerance)
    out["schema"]=SCHEMA
    out["relational_zero_operator_receipt"]=operator_receipt
    out["canon_allowed"]=False
    return out
