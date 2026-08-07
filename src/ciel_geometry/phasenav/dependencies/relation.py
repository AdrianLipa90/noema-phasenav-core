"""Typed relation graph for CIEL/PhaseNav semantic and holonomic closure."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
from typing import Iterable


class EpistemicStatus(str, Enum):
    EXACT = "exact"
    STANDARD = "standard"
    MODEL = "model"
    OPEN = "open"


class RelationKind(str, Enum):
    DUAL = "dual"
    FIXED_POINT = "fixed_point"
    IMPLIES = "implies"
    REPRESENTS = "represents"
    HOLONOMIC = "holonomic"
    CROSS_REFERENCE = "cross_reference"


@dataclass(frozen=True)
class RelationEdge:
    source: str
    target: str
    kind: RelationKind
    status: EpistemicStatus
    reversible: bool = False
    holonomy_turns: float | None = None
    provenance: str | None = None


class RelationGraph:
    """Small deterministic graph with epistemically gated implication closure."""

    def __init__(self, edges: Iterable[RelationEdge] = ()) -> None:
        self._edges: list[RelationEdge] = []
        for edge in edges:
            self.add(edge)

    @property
    def edges(self) -> tuple[RelationEdge, ...]:
        return tuple(self._edges)

    def add(self, edge: RelationEdge) -> None:
        self._edges.append(edge)

    def neighbours(self, node: str) -> tuple[RelationEdge, ...]:
        out: list[RelationEdge] = []
        for edge in self._edges:
            if edge.source == node:
                out.append(edge)
            if edge.reversible and edge.target == node:
                out.append(
                    RelationEdge(
                        source=edge.target,
                        target=edge.source,
                        kind=edge.kind,
                        status=edge.status,
                        reversible=True,
                        holonomy_turns=(
                            -edge.holonomy_turns if edge.holonomy_turns is not None else None
                        ),
                        provenance=edge.provenance,
                    )
                )
        return tuple(out)

    def implication_closure(self, seeds: Iterable[str], *, allow_model: bool = False) -> frozenset[str]:
        """Return nodes derivable through implication/fixed/dual edges.

        OPEN edges never close automatically. MODEL edges require allow_model=True.
        """
        allowed = {EpistemicStatus.EXACT, EpistemicStatus.STANDARD}
        if allow_model:
            allowed.add(EpistemicStatus.MODEL)
        reached = set(map(str, seeds))
        queue = deque(reached)
        while queue:
            node = queue.popleft()
            for edge in self.neighbours(node):
                if edge.status not in allowed:
                    continue
                if edge.kind not in {
                    RelationKind.IMPLIES,
                    RelationKind.FIXED_POINT,
                    RelationKind.DUAL,
                    RelationKind.REPRESENTS,
                }:
                    continue
                if edge.target not in reached:
                    reached.add(edge.target)
                    queue.append(edge.target)
        return frozenset(reached)

    def holonomy_sum(self, path: Iterable[str]) -> float | None:
        """Compose declared normalized holonomy turns along a directed path."""
        nodes = list(path)
        if len(nodes) < 2:
            return 0.0
        total = 0.0
        for source, target in zip(nodes, nodes[1:]):
            candidates = [e for e in self.neighbours(source) if e.target == target]
            if not candidates:
                return None
            with_holonomy = [e for e in candidates if e.holonomy_turns is not None]
            if not with_holonomy:
                return None
            total += with_holonomy[0].holonomy_turns or 0.0
        return total

    def degree(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for edge in self._edges:
            counts[edge.source] += 1
            counts[edge.target] += 1
        return dict(counts)
