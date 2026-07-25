"""PhaseNav graphics composer.

Builds vectorized graph scenes for relational maps, memory maps and operator
maps, then projects them onto a Bloch-style unit ball and renders SVG previews.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from hashlib import blake2b
from typing import Any, Iterable

import numpy as np

from ..phase_memory_adapter import query_phase_memory
from ..noema_surface_mmap import ensure_surface, read_surface_state
from .operator_algebra import ALL_OPERATOR_IDS, connection_matrix, generate_operator_map


VECTOR_DIM = 36


def _stable_seed(text: str) -> int:
    digest = blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=False) & 0x7FFFFFFF


def _as_36d(vec: Iterable[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(list(vec) if not isinstance(vec, np.ndarray) else vec, dtype=np.float64).ravel()
    if arr.size >= VECTOR_DIM:
        return arr[:VECTOR_DIM]
    return np.pad(arr, (0, VECTOR_DIM - arr.size))


def _unit_ball(vec3: np.ndarray, weight: float = 1.0) -> tuple[float, float, float, float]:
    vec3 = np.asarray(vec3, dtype=np.float64).ravel()
    if vec3.size < 3:
        vec3 = np.pad(vec3, (0, 3 - vec3.size))
    norm = float(np.linalg.norm(vec3))
    if norm <= 1e-12:
        return 0.0, 0.0, 1.0, 0.0
    unit = vec3[:3] / norm
    radius = float(np.clip(weight, 0.0, 1.0))
    xyz = unit * radius
    return float(xyz[0]), float(xyz[1]), float(xyz[2]), radius


def _phase_from_vec(vec: np.ndarray) -> float:
    a = np.asarray(vec, dtype=np.float64).ravel()
    if a.size == 0:
        return 0.0
    x = float(np.sum(a[0::3]))
    y = float(np.sum(a[1::3]))
    return float(math.atan2(y, x))


def _rgb_from_phase(phase: float, sat: int = 72, light: int = 56) -> str:
    deg = (math.degrees(phase) % 360.0 + 360.0) % 360.0
    return f"hsl({deg:.1f} {sat}% {light}%)"


def _node_radius(weight: float) -> float:
    return float(4.0 + 10.0 * np.clip(weight, 0.0, 1.0))


@dataclass
class PhaseNavGraphicNode:
    id: str
    label: str
    kind: str
    x: float
    y: float
    z: float
    radius: float
    phase: float
    weight: float
    color: str
    operator: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseNavGraphicEdge:
    source: str
    target: str
    weight: float
    phase_delta: float
    color: str
    opacity: float
    curvature: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseNavGraphicScene:
    scene_id: str
    title: str
    projection: str
    summary: dict[str, Any]
    nodes: list[PhaseNavGraphicNode]
    edges: list[PhaseNavGraphicEdge]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["svg"] = render_graph_svg(self)
        payload["scene_hash"] = _scene_hash(payload)
        return payload


def _scene_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return blake2b(raw, digest_size=16).hexdigest()


def _vector_embedding(matrix: np.ndarray) -> np.ndarray:
    sym = np.asarray(matrix, dtype=np.float64)
    if sym.ndim != 2:
        raise ValueError("matrix must be 2D")
    if sym.shape[0] != sym.shape[1]:
        raise ValueError("matrix must be square")
    sym = 0.5 * (sym + sym.T)
    evals, evecs = np.linalg.eigh(sym)
    order = np.argsort(np.abs(evals))[::-1]
    dims = min(3, sym.shape[0])
    selected = order[:dims]
    basis = evecs[:, selected] * np.sqrt(np.abs(evals[selected]) + 1e-12)
    if basis.shape[1] < 3:
        basis = np.pad(basis, ((0, 0), (0, 3 - basis.shape[1])))
    norms = np.linalg.norm(basis, axis=1)
    max_norm = float(np.max(norms)) if np.any(norms) else 1.0
    radii = np.clip(norms / max(max_norm, 1e-12), 0.15, 1.0)
    xyz = np.zeros((basis.shape[0], 3), dtype=np.float64)
    safe_norms = np.where(norms > 1e-12, norms, 1.0)
    xyz[:] = (basis[:, :3] / safe_norms[:, None]) * radii[:, None]
    return xyz


def _matrix_edges(matrix: np.ndarray, labels: list[str], *, top_k: int = 72) -> list[PhaseNavGraphicEdge]:
    sym = 0.5 * (np.asarray(matrix, dtype=np.float64) + np.asarray(matrix, dtype=np.float64).T)
    abs_sym = np.abs(sym)
    np.fill_diagonal(abs_sym, 0.0)
    flat = np.argsort(abs_sym.ravel())[::-1]
    edges: list[PhaseNavGraphicEdge] = []
    seen: set[tuple[int, int]] = set()
    for idx in flat:
        i = int(idx // sym.shape[1])
        j = int(idx % sym.shape[1])
        if i == j or (j, i) in seen:
            continue
        weight = float(sym[i, j])
        if abs(weight) <= 1e-12:
            continue
        seen.add((i, j))
        phase_delta = float(math.atan2(weight, 1.0))
        edges.append(
            PhaseNavGraphicEdge(
                source=labels[i],
                target=labels[j],
                weight=round(weight, 6),
                phase_delta=round(phase_delta, 6),
                color=_rgb_from_phase(phase_delta, sat=64, light=50),
                opacity=float(np.clip(abs(weight), 0.12, 0.95)),
                meta={"row": i, "col": j},
            )
        )
        if len(edges) >= top_k:
            break
    return edges


def _scene_from_nodes(
    *,
    scene_id: str,
    title: str,
    projection: str,
    nodes: list[PhaseNavGraphicNode],
    edges: list[PhaseNavGraphicEdge],
    summary: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> PhaseNavGraphicScene:
    return PhaseNavGraphicScene(
        scene_id=scene_id,
        title=title,
        projection=projection,
        summary=summary,
        nodes=nodes,
        edges=edges,
        metadata=metadata or {},
    )


def build_relational_scene(
    matrix: np.ndarray,
    labels: list[str],
    *,
    scene_id: str = "relations",
    title: str = "PhaseNav relational map",
) -> PhaseNavGraphicScene:
    coords = _vector_embedding(matrix)
    sym = 0.5 * (np.asarray(matrix, dtype=np.float64) + np.asarray(matrix, dtype=np.float64).T)
    diag = np.abs(np.diag(sym))
    diag_norm = diag / max(float(np.max(diag)) if np.any(diag) else 1.0, 1e-12)
    nodes: list[PhaseNavGraphicNode] = []
    for i, label in enumerate(labels):
        x, y, z = float(coords[i, 0]), float(coords[i, 1]), float(coords[i, 2])
        phase = float(math.atan2(y, x))
        weight = float(np.clip(diag_norm[i], 0.15, 1.0))
        nodes.append(
            PhaseNavGraphicNode(
                id=label,
                label=label,
                kind="relation",
                x=x,
                y=y,
                z=z,
                radius=_node_radius(weight),
                phase=phase,
                weight=weight,
                color=_rgb_from_phase(phase, sat=70, light=56),
                meta={"degree": float(np.sum(np.abs(sym[i]))), "index": i},
            )
        )
    edges = _matrix_edges(sym, labels)
    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "matrix_shape": list(sym.shape),
        "weight_mean": float(np.mean(np.abs(sym))) if sym.size else 0.0,
        "weight_max": float(np.max(np.abs(sym))) if sym.size else 0.0,
    }
    return _scene_from_nodes(
        scene_id=scene_id,
        title=title,
        projection="bloch-ball",
        nodes=nodes,
        edges=edges,
        summary=summary,
        metadata={"kind": "relational", "labels": labels},
    )


def _record_vector(record: dict[str, Any]) -> np.ndarray:
    if "vector" in record and record["vector"] is not None:
        return _as_36d(record["vector"])
    if "embedding" in record and record["embedding"] is not None:
        return _as_36d(record["embedding"])
    label = str(record.get("label") or record.get("text") or record.get("slot") or "memory")
    rng = np.random.default_rng(_stable_seed(label))
    return rng.uniform(-1.0, 1.0, VECTOR_DIM).astype(np.float64)


def build_memory_scene(
    records: list[dict[str, Any]],
    *,
    scene_id: str = "memory",
    title: str = "PhaseNav memory map",
) -> PhaseNavGraphicScene:
    if not records:
        summary = {"node_count": 0, "edge_count": 0, "mean_score": 0.0}
        return _scene_from_nodes(
            scene_id=scene_id,
            title=title,
            projection="bloch-ball",
            nodes=[],
            edges=[],
            summary=summary,
            metadata={"kind": "memory"},
        )

    vectors = np.vstack([_record_vector(record) for record in records])
    centers = np.vstack([_unit_ball(np.array([
        float(np.sum(v[0::3])),
        float(np.sum(v[1::3])),
        float(np.sum(v[2::3])),
    ]), weight=float(np.clip(np.linalg.norm(v) / math.sqrt(VECTOR_DIM), 0.15, 1.0)))[:3] for v in vectors])

    norms = np.linalg.norm(vectors, axis=1)
    safe_norms = np.where(norms > 1e-12, norms, 1.0)
    unit_vectors = vectors / safe_norms[:, None]
    similarity = np.clip(unit_vectors @ unit_vectors.T, -1.0, 1.0)
    np.fill_diagonal(similarity, 0.0)

    labels = []
    nodes: list[PhaseNavGraphicNode] = []
    for i, record in enumerate(records):
        label = str(record.get("label") or record.get("slot") or f"mem-{i}")
        labels.append(label)
        x, y, z = float(centers[i, 0]), float(centers[i, 1]), float(centers[i, 2])
        phase = float(record.get("phase", math.atan2(y, x)))
        score = float(record.get("score", record.get("coherence", 0.5)))
        weight = float(np.clip(score if score > 0 else np.linalg.norm(vectors[i]) / math.sqrt(VECTOR_DIM), 0.15, 1.0))
        nodes.append(
            PhaseNavGraphicNode(
                id=label,
                label=label,
                kind="memory",
                x=x,
                y=y,
                z=z,
                radius=_node_radius(weight),
                phase=phase,
                weight=weight,
                color=_rgb_from_phase(phase, sat=76, light=54),
                operator=str(record.get("operator")) if record.get("operator") else None,
                meta={k: v for k, v in record.items() if k not in {"vector", "embedding"}},
            )
        )

    flat = np.argsort(np.abs(similarity).ravel())[::-1]
    edges: list[PhaseNavGraphicEdge] = []
    seen: set[tuple[int, int]] = set()
    for idx in flat:
        i = int(idx // similarity.shape[1])
        j = int(idx % similarity.shape[1])
        if i == j or (j, i) in seen:
            continue
        weight = float(similarity[i, j])
        if abs(weight) <= 0.15:
            continue
        seen.add((i, j))
        phase_delta = float(math.atan2(weight, 1.0))
        edges.append(
            PhaseNavGraphicEdge(
                source=labels[i],
                target=labels[j],
                weight=round(weight, 6),
                phase_delta=round(phase_delta, 6),
                color=_rgb_from_phase(phase_delta, sat=68, light=48),
                opacity=float(np.clip(abs(weight), 0.12, 0.9)),
                meta={"similarity": round(weight, 6)},
            )
        )
        if len(edges) >= min(72, max(0, len(records) * 2)):
            break

    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "mean_score": float(np.mean([float(r.get("score", r.get("coherence", 0.0))) for r in records])),
        "max_score": float(np.max([float(r.get("score", r.get("coherence", 0.0))) for r in records])),
        "mean_similarity": float(np.mean(np.abs(similarity))) if similarity.size else 0.0,
    }
    return _scene_from_nodes(
        scene_id=scene_id,
        title=title,
        projection="bloch-ball",
        nodes=nodes,
        edges=edges,
        summary=summary,
        metadata={"kind": "memory"},
    )


def build_operator_scene(
    *,
    scene_id: str = "operators",
    title: str = "PhaseNav operator algebra",
) -> PhaseNavGraphicScene:
    ops = generate_operator_map()
    ids = list(ALL_OPERATOR_IDS)
    vectors = np.vstack([ops[op_id] for op_id in ids])
    coords = _vector_embedding(vectors @ vectors.T)
    conn = connection_matrix(ops)
    gram = vectors @ vectors.T

    nodes: list[PhaseNavGraphicNode] = []
    for i, op_id in enumerate(ids):
        raw = vectors[i]
        x, y, z, radius = _unit_ball(coords[i], weight=float(np.clip(np.linalg.norm(raw), 0.2, 1.0)))
        phase = _phase_from_vec(raw)
        nodes.append(
            PhaseNavGraphicNode(
                id=op_id,
                label=op_id,
                kind="operator",
                x=x,
                y=y,
                z=z,
                radius=_node_radius(radius),
                phase=phase,
                weight=radius,
                color=_rgb_from_phase(phase, sat=78, light=52),
                meta={"dim": VECTOR_DIM, "signature_norm": float(np.linalg.norm(raw))},
            )
        )

    edge_matrix = conn if np.any(np.abs(conn) > 1e-12) else gram
    edges = _matrix_edges(edge_matrix, ids, top_k=72)
    if not edges:
        for i in range(len(ids) - 1):
            left = vectors[i]
            right = vectors[i + 1]
            weight = float(np.dot(left, right))
            phase_delta = float(math.atan2(np.linalg.norm(left - right), 1.0))
            edges.append(
                PhaseNavGraphicEdge(
                    source=ids[i],
                    target=ids[i + 1],
                    weight=round(weight, 6),
                    phase_delta=round(phase_delta, 6),
                    color=_rgb_from_phase(phase_delta, sat=64, light=50),
                    opacity=float(np.clip(abs(weight), 0.15, 0.9)),
                    meta={"fallback": True, "index": i},
                )
            )
            if len(edges) >= 72:
                break
    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "operator_count": len(ids),
        "connection_mean": float(np.mean(np.abs(conn))),
        "connection_max": float(np.max(np.abs(conn))),
        "edge_source": "connection" if np.any(np.abs(conn) > 1e-12) else "gram",
    }
    return _scene_from_nodes(
        scene_id=scene_id,
        title=title,
        projection="bloch-ball",
        nodes=nodes,
        edges=edges,
        summary=summary,
        metadata={"kind": "operator"},
    )


def build_phasenav_graphics_bundle(
    *,
    query: str = "NOEMA",
    surface: dict[str, Any] | None = None,
    top_k_memory: int = 8,
) -> dict[str, Any]:
    if surface is None:
        surface = ensure_surface()
    surface_state = read_surface_state(surface)

    phi = np.asarray(surface["phi"], dtype=np.float64).ravel() if surface and "phi" in surface else np.zeros(VECTOR_DIM)
    omega = np.asarray(surface["omega"], dtype=np.float64).ravel() if surface and "omega" in surface else np.zeros(VECTOR_DIM)
    g = np.asarray(surface["g"], dtype=np.float64)[:VECTOR_DIM, :VECTOR_DIM] if surface and "g" in surface else np.zeros((VECTOR_DIM, VECTOR_DIM))

    relation_labels = [f"phi[{i:02d}]" for i in range(min(VECTOR_DIM, len(phi)))]
    relation_scene = build_relational_scene(g, relation_labels)

    memory_rows = query_phase_memory(query, top_k=top_k_memory) if query else query_phase_memory("NOEMA", top_k=top_k_memory)
    memory_records: list[dict[str, Any]] = []
    for row in memory_rows:
        memory_records.append(
            {
                "label": f"slot-{row.slot}",
                "slot": row.slot,
                "score": row.score,
                "coherence": row.coherence,
                "tick": row.tick,
                "phase_similarity": row.phase_similarity,
                "vector_similarity": row.vector_similarity,
                "flavor_similarity": row.flavor_similarity,
                "event_hash": row.event_hash_hex,
                "vector": np.roll(_as_36d(phi), row.slot % VECTOR_DIM).tolist() if phi.size else _as_36d(omega).tolist(),
            }
        )
    memory_scene = build_memory_scene(memory_records)
    operator_scene = build_operator_scene()

    if phi.size:
        surface_vector = np.stack([
            np.cos(phi),
            np.sin(phi),
            np.tanh(omega),
        ], axis=1)
        surface_labels = [f"osc-{i:02d}" for i in range(surface_vector.shape[0])]
        surface_nodes: list[PhaseNavGraphicNode] = []
        for i, label in enumerate(surface_labels):
            x, y, z = float(surface_vector[i, 0]), float(surface_vector[i, 1]), float(surface_vector[i, 2])
            phase = float(phi[i])
            weight = float(np.clip(abs(omega[i]) if omega.size > i else 0.4, 0.15, 1.0))
            surface_nodes.append(
                PhaseNavGraphicNode(
                    id=label,
                    label=label,
                    kind="surface",
                    x=x,
                    y=y,
                    z=z,
                    radius=_node_radius(weight),
                    phase=phase,
                    weight=weight,
                    color=_rgb_from_phase(phase, sat=62, light=58),
                    meta={"phi": float(phi[i]), "omega": float(omega[i]) if omega.size > i else 0.0},
                )
            )
        surface_edges = _matrix_edges(g, surface_labels, top_k=72)
        surface_scene = _scene_from_nodes(
            scene_id="surface",
            title="PhaseNav surface map",
            projection="bloch-ball",
            nodes=surface_nodes,
            edges=surface_edges,
            summary={
                "node_count": len(surface_nodes),
                "edge_count": len(surface_edges),
                "phi_mean": float(np.mean(phi)) if phi.size else 0.0,
                "omega_mean": float(np.mean(omega)) if omega.size else 0.0,
                "coherence": float(surface_state.get("coherence", 0.0)),
            },
            metadata={"kind": "surface"},
        )
    else:
        surface_scene = _scene_from_nodes(
            scene_id="surface",
            title="PhaseNav surface map",
            projection="bloch-ball",
            nodes=[],
            edges=[],
            summary={"node_count": 0, "edge_count": 0},
            metadata={"kind": "surface"},
        )

    bundle = {
        "status": "ok",
        "query": query,
        "surface": {
            "tick": surface_state.get("tick"),
            "coherence": surface_state.get("coherence"),
            "phi_mean": surface_state.get("phi_mean"),
            "tau_mean": surface_state.get("tau_mean"),
        },
        "scenes": {
            "surface": surface_scene.to_dict(),
            "relations": relation_scene.to_dict(),
            "memory": memory_scene.to_dict(),
            "operators": operator_scene.to_dict(),
        },
    }
    bundle["scene_counts"] = {
        name: {
            "nodes": len(scene["nodes"]),
            "edges": len(scene["edges"]),
        }
        for name, scene in bundle["scenes"].items()
    }
    return bundle


def render_graph_svg(scene: PhaseNavGraphicScene | dict[str, Any], width: int = 980, height: int = 640) -> str:
    if isinstance(scene, PhaseNavGraphicScene):
        nodes = scene.nodes
        edges = scene.edges
        title = scene.title
    else:
        nodes = [PhaseNavGraphicNode(**node) for node in scene.get("nodes", [])]
        edges = [PhaseNavGraphicEdge(**edge) for edge in scene.get("edges", [])]
        title = str(scene.get("title", "PhaseNav graphics"))

    cx = width / 2.0
    cy = height / 2.0
    scale = min(width, height) * 0.34

    def project(node: PhaseNavGraphicNode) -> tuple[float, float, float]:
        x = cx + node.x * scale
        y = cy - node.y * scale
        z = node.z
        return x, y, z

    node_lookup = {node.id: node for node in nodes}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
        "<defs>",
        '<radialGradient id="bgGlow" cx="50%" cy="45%" r="65%">',
        '<stop offset="0%" stop-color="#0f2a3b" stop-opacity="0.92"/>',
        '<stop offset="100%" stop-color="#05070a" stop-opacity="1"/>',
        "</radialGradient>",
        '<filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">',
        '<feGaussianBlur stdDeviation="6" result="blur"/>',
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        "</filter>",
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="url(#bgGlow)"/>',
        f'<text x="24" y="34" fill="#d8f8ff" font-size="18" font-family="JetBrains Mono, monospace">{title}</text>',
        f'<text x="24" y="58" fill="#89aebd" font-size="11" font-family="JetBrains Mono, monospace">bloch projection · vectorized phase map</text>',
    ]

    for edge in edges:
        src = node_lookup.get(edge.source)
        dst = node_lookup.get(edge.target)
        if src is None or dst is None:
            continue
        sx, sy, sz = project(src)
        tx, ty, tz = project(dst)
        midx = (sx + tx) / 2.0
        midy = (sy + ty) / 2.0
        delta = edge.curvature if edge.curvature else 18.0 * (1.0 - abs(edge.weight))
        parts.append(
            f'<path d="M {sx:.2f} {sy:.2f} Q {midx:.2f} {midy - delta:.2f} {tx:.2f} {ty:.2f}" '
            f'stroke="{edge.color}" stroke-opacity="{edge.opacity:.3f}" stroke-width="{1.0 + 3.0 * abs(edge.weight):.2f}" '
            f'fill="none" filter="url(#softGlow)"/>'
        )

    parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{scale:.2f}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1.2"/>')
    parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{scale * 0.5:.2f}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1.0"/>')

    for node in sorted(nodes, key=lambda n: n.z):
        x, y, z = project(node)
        r = node.radius * (0.75 + 0.25 * (1.0 + z))
        parts.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{node.color}" fill-opacity="0.9" '
            f'stroke="rgba(255,255,255,0.35)" stroke-width="1" filter="url(#softGlow)"/>'
        )
        parts.append(
            f'<text x="{x + r + 4:.2f}" y="{y + 3:.2f}" fill="#eef9ff" font-size="10" '
            f'font-family="JetBrains Mono, monospace">{node.label}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def build_graphics_svg(
    *,
    query: str = "NOEMA",
    scene_name: str = "surface",
    surface: dict[str, Any] | None = None,
) -> str:
    bundle = build_phasenav_graphics_bundle(query=query, surface=surface)
    scene = bundle["scenes"].get(scene_name) or bundle["scenes"]["surface"]
    return scene.get("svg", "")
