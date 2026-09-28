from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_13 import (
    SCHEMA as SCHEMA_V13,
    validate_bridge_packet_v13,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.14"
INFO_MODE = "RELATIONAL_PROJECTOR_UMEGAKI_INFORMATION"
KAPPA = math.log(2.0)/(24.0*math.pi)


def validate_bridge_packet_v14(
    packet: Mapping[str,Any],
    *,
    tolerance: float=1e-10,
)->dict[str,Any]:
    if packet.get("schema")!=SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p13=dict(packet)
    p13["schema"]=SCHEMA_V13

    mode=packet.get("relational_information_mode")
    info_receipt=None

    if mode is not None and mode!=INFO_MODE:
        raise FractalMoire36Error("unknown relational_information_mode")

    out=validate_bridge_packet_v13(p13,tolerance=tolerance)

    if mode==INFO_MODE:
        op=out.get("relational_zero_operator_receipt")
        if op is None:
            raise FractalMoire36Error(
                "relational information requires relational-zero operator layer"
            )

        g0=int(op["base_subgroup_order"])
        gh=int(op["activity_subgroup_order"])
        ga=int(op["total_subgroup_order"])

        mh=gh//g0
        mz=ga//gh
        mt=ga//g0

        if mt!=mh*mz:
            raise FractalMoire36Error("relational enlargement factors lost multiplicativity")

        sh=1.0/mh
        sz=1.0/mz
        st=1.0/mt

        dh=math.log(mh)
        dz=math.log(mz)
        dt=math.log(mt)

        eh=1.0-sh
        ez=1.0-sz
        et=1.0-st

        add_res=abs(dt-(dh+dz))
        survival_res=abs(st-(sh*sz))
        defect_res=abs(et-(eh+ez-eh*ez))

        if add_res>tolerance:
            raise FractalMoire36Error("relative entropy additivity residual exceeds tolerance")
        if survival_res>tolerance:
            raise FractalMoire36Error("survival multiplication residual exceeds tolerance")
        if defect_res>tolerance:
            raise FractalMoire36Error("defect composition residual exceeds tolerance")

        phase_h=dh/(24.0*math.pi)
        phase_z=dz/(24.0*math.pi)
        phase_t=dt/(24.0*math.pi)

        binary_steps=[]
        if mh==2:
            binary_steps.append("ACTIVITY")
        if mz==2:
            binary_steps.append("DEPTH")
        if mt==2:
            binary_steps.append("TOTAL")

        for label,value in (
            ("ACTIVITY",phase_h),
            ("DEPTH",phase_z),
            ("TOTAL",phase_t),
        ):
            if label in binary_steps and not math.isclose(
                value,KAPPA,rel_tol=1e-14,abs_tol=1e-14
            ):
                raise FractalMoire36Error(
                    f"binary relational step {label} lost kappa normalization"
                )

        if packet.get("physical_thermodynamic_entropy_claim") is True:
            raise FractalMoire36Error(
                "physical thermodynamic entropy claim is not established"
            )

        info_receipt={
            "mode":INFO_MODE,
            "activity_enlargement_factor":mh,
            "depth_enlargement_factor":mz,
            "total_enlargement_factor":mt,
            "activity_survival_ratio":sh,
            "depth_survival_ratio":sz,
            "total_survival_ratio":st,
            "activity_information_nats":dh,
            "depth_information_nats":dz,
            "total_information_nats":dt,
            "information_additivity_residual":add_res,
            "survival_multiplication_residual":survival_res,
            "activity_normalized_defect":eh,
            "depth_normalized_defect":ez,
            "total_normalized_defect":et,
            "defect_composition_residual":defect_res,
            "activity_information_24pi":phase_h,
            "depth_information_24pi":phase_z,
            "total_information_24pi":phase_t,
            "kappa":KAPPA,
            "binary_kappa_steps":tuple(binary_steps),
            "normalization_status":"24PI_CANONICAL_PREEXISTING",
            "physical_thermodynamic_entropy_claim":False,
        }

    out["schema"]=SCHEMA
    out["relational_information_receipt"]=info_receipt
    out["canon_allowed"]=False
    return out
