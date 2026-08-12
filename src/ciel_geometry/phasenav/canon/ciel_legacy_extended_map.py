"""Extended legacy CIEL executable-source bindings for PhaseNav concepts.

These mappings expose additional callable symbols recovered from the same frozen
legacy CIEL/Ω source anchor used by ``ciel_executable_map``.  They remain legacy
routing references: no import, execution, scientific promotion, or legacy-to-
current promotion occurs here.
"""
from __future__ import annotations

from .ciel_executable_map import (
    CielExecutableBinding,
    LEGACY_CIEL_COMMIT,
    LEGACY_CIEL_REPO,
)


CIEL_LEGACY_EXTENDED_MAP_VERSION = "0.13.0"
CIEL_LEGACY_EXTENDED_MAP_STATUS = "LEGACY_EXECUTABLE_INVENTORY_NO_PROMOTION"
LEGACY_OPERATOR_PATH = "paradoxes/ultimate_operators.py"
LEGACY_OPERATOR_BLOB = "ba3d8d48a40306a50dc67835419c43e130adf705"


def _legacy(
    binding_id: str,
    family: str,
    symbol: str,
    concepts: tuple[str, ...],
    role: str,
    *,
    side_effect: str = "PURE",
    priority: int = 40,
) -> CielExecutableBinding:
    return CielExecutableBinding(
        binding_id=binding_id,
        family=family,
        source_repo=LEGACY_CIEL_REPO,
        source_commit=LEGACY_CIEL_COMMIT,
        source_blob_sha=LEGACY_OPERATOR_BLOB,
        source_path=LEGACY_OPERATOR_PATH,
        symbol=symbol,
        provenance_class="LEGACY_EXECUTABLE_SOURCE",
        side_effect=side_effect,  # type: ignore[arg-type]
        concept_ids=tuple(str(cid).zfill(3) for cid in concepts),
        priority=priority,
        semantic_role=role,
    )


_EXTENDED: tuple[CielExecutableBinding, ...] = (
    _legacy(
        "CIEL.QUANTUM.SUPERPOSITION.LEGACY",
        "quantum",
        "UltimateParadoxOperators.schrodinger_superposition_operator",
        ("082", "081", "119"),
        "legacy superposition-state operator routed to possibility/probability/paradox",
    ),
    _legacy(
        "CIEL.UNCERTAINTY.HEISENBERG.LEGACY",
        "uncertainty",
        "UltimateParadoxOperators.heisenberg_uncertainty_operator",
        ("041", "118"),
        "legacy uncertainty operator; explicitly distinct from the v0.12 PhaseNav soft reciprocal",
    ),
    _legacy(
        "CIEL.PARADOX.BANACH_TARSKI.LEGACY",
        "paradox",
        "UltimateParadoxOperators.banach_tarski_creation_operator",
        ("119", "106", "070"),
        "legacy decomposition/recomposition creation paradox operator",
    ),
    _legacy(
        "CIEL.ZETA.PROTECTION.LEGACY",
        "mathematics",
        "UltimateParadoxOperators.riemann_zeta_protection",
        ("117", "039"),
        "legacy zeta-related protective operator; no RH or arithmetic promotion",
    ),
    _legacy(
        "CIEL.PARADOX.HILBERT_HOTEL.LEGACY",
        "paradox",
        "UltimateParadoxOperators.hilbert_hotel_operator",
        ("119", "082"),
        "legacy countable-infinity accommodation paradox operator",
    ),
    _legacy(
        "CIEL.COHERENCE.WATANABE.LEGACY",
        "coherence",
        "UltimateParadoxOperators.watanabe_coherence_operator",
        ("003",),
        "legacy coherence operator routed to the PhaseNav Coherence concept",
    ),
    _legacy(
        "CIEL.OBSERVER.QUANTUM_CREATION.LEGACY",
        "observer",
        "UltimateParadoxOperators.quantum_observer_creation",
        ("031", "077"),
        "legacy observer/state construction operator",
    ),
    _legacy(
        "CIEL.COSMOS.SELF_UNIVERSE.LEGACY",
        "cosmos",
        "UltimateParadoxOperators.self_universe_equation",
        ("032", "094"),
        "legacy self/universe relation operator",
    ),
    _legacy(
        "CIEL.PARADOX.FERMI.LEGACY",
        "paradox",
        "UltimateParadoxOperators.fermi_paradox_field",
        ("119", "094", "081"),
        "legacy Fermi-paradox field routed to paradox/cosmos/probability",
    ),
    _legacy(
        "CIEL.PARADOX.EPR.LEGACY",
        "paradox",
        "UltimateParadoxOperators.epr_paradox_operator",
        ("119", "003"),
        "legacy EPR-style paradox operator routed to paradox/coherence",
    ),
    _legacy(
        "CIEL.PARADOX.WIGNER_FRIEND.LEGACY",
        "paradox",
        "UltimateParadoxOperators.wigners_friend_operator",
        ("119", "077", "031"),
        "legacy nested-observer paradox operator",
    ),
    _legacy(
        "CIEL.PARADOX.OLBERS.LEGACY",
        "paradox",
        "UltimateParadoxOperators.olbers_paradox_field",
        ("119", "016", "094"),
        "legacy Olbers-paradox field routed to paradox/light/cosmos",
    ),
    _legacy(
        "CIEL.PARADOX.MORAVEC.LEGACY",
        "paradox",
        "UltimateParadoxOperators.moravecs_paradox_operator",
        ("119", "066", "107"),
        "legacy Moravec-paradox operator routed to paradox/mind/techne",
    ),
    _legacy(
        "CIEL.PARADOX.FIELD_INIT.LEGACY",
        "paradox",
        "UltimateUniversalLawEngine4D.initialize_paradox_field",
        ("119", "080"),
        "initialize the legacy paradox phase field",
        side_effect="STATEFUL",
        priority=15,
    ),
    _legacy(
        "CIEL.PARADOX.FIELD_EVOLVE.LEGACY",
        "paradox",
        "UltimateUniversalLawEngine4D.evolve_paradox_field",
        ("119", "080"),
        "evolve the legacy paradox phase field",
        side_effect="STATEFUL",
        priority=25,
    ),
)


def extended_legacy_bindings() -> tuple[CielExecutableBinding, ...]:
    return _EXTENDED


def extended_legacy_bindings_for_concept(
    concept_id: str | int,
) -> tuple[CielExecutableBinding, ...]:
    key = str(concept_id).zfill(3)
    return tuple(
        sorted(
            (binding for binding in _EXTENDED if key in binding.concept_ids),
            key=lambda row: (row.priority, row.binding_id),
        )
    )


def extended_legacy_bindings_for_family(
    family: str,
) -> tuple[CielExecutableBinding, ...]:
    key = str(family).strip().lower()
    return tuple(
        sorted(
            (binding for binding in _EXTENDED if binding.family == key),
            key=lambda row: (row.priority, row.binding_id),
        )
    )
