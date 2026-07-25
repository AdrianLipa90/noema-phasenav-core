from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import numpy as np

from ciel_geometry.noema_surface_mmap import MEMORY_CHANNEL_GROUPS, N_OSCILLATORS


SVG_NS = {"svg": "http://www.w3.org/2000/svg"}
CHANNEL_ORDER = tuple(MEMORY_CHANNEL_GROUPS.keys())
INVARIANT_HUB_ID = "metatron_center"


@dataclass(frozen=True)
class MetatronNode:
    node_id: str
    x: float
    y: float
    radius: float
    shell_index: int
    channel: str
    bloch_theta: float
    bloch_phi: float
    phase_vector_36d: tuple[float, ...]
    semantic_role: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["phase_vector_36d"] = list(self.phase_vector_36d)
        return data


@dataclass(frozen=True)
class MetatronThread:
    thread_id: str
    source_node_id: str
    target_node_id: str
    thread_kind: str
    phase_alignment: float
    coupling_weight: float
    semantic_friction_r: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetatronSurfaceMap:
    schema: str
    source_svg: str
    node_count: int
    thread_count: int
    invariant_hub: str
    nodes: tuple[MetatronNode, ...]
    threads: tuple[MetatronThread, ...]
    coupling_overlay_36x36: tuple[tuple[float, ...], ...]
    channel_routes: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_svg": self.source_svg,
            "node_count": self.node_count,
            "thread_count": self.thread_count,
            "invariant_hub": self.invariant_hub,
            "nodes": [item.to_dict() for item in self.nodes],
            "threads": [item.to_dict() for item in self.threads],
            "coupling_overlay_36x36": [list(row) for row in self.coupling_overlay_36x36],
            "channel_routes": dict(self.channel_routes),
        }


def _extract_circle_from_path(d: str) -> tuple[float, float, float]:
    tokens = d.replace(",", " ").split()
    if len(tokens) < 11 or tokens[0] != "M":
        raise ValueError(f"Unsupported circle path payload: {d}")
    x0 = float(tokens[1])
    y0 = float(tokens[2])
    radius = float(tokens[4])
    center_x = x0 - radius
    center_y = y0
    return center_x, center_y, radius


def _extract_line_points(d: str) -> list[tuple[float, float]]:
    clean = d.replace(",", " ").replace("z", "").replace("Z", "")
    tokens = clean.split()
    points: list[tuple[float, float]] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in {"M", "L"}:
            points.append((float(tokens[i + 1]), float(tokens[i + 2])))
            i += 3
            continue
        i += 1
    return points


def _phase36(theta: float, phi: float, shell_index: int, channel_index: int) -> tuple[float, ...]:
    vec: list[float] = []
    for dim in range(N_OSCILLATORS):
        local = (dim % 3) / 3.0
        channel_phase = (channel_index / max(1, len(CHANNEL_ORDER))) * math.tau
        harmonic = ((dim // 3) % 12) * (math.tau / 12.0)
        value = (theta + phi + shell_index * 0.25 + channel_phase + harmonic + local) % math.tau
        vec.append(round(value, 10))
    return tuple(vec)


def _mean_circular_distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    acc = 0.0
    for left, right in zip(a, b):
        delta = (left - right) % math.tau
        if delta > math.pi:
            delta = math.tau - delta
        acc += delta
    return acc / max(1, len(a))


def _order_parameter(vec: tuple[float, ...]) -> float:
    re = sum(math.cos(v) for v in vec) / max(1, len(vec))
    im = sum(math.sin(v) for v in vec) / max(1, len(vec))
    return math.sqrt(re * re + im * im)


def _nearest_node_id(nodes: list[tuple[str, float, float]], point: tuple[float, float]) -> str:
    px, py = point
    best = min(nodes, key=lambda item: ((item[1] - px) ** 2 + (item[2] - py) ** 2))
    return best[0]


def _assign_shell_index(cx: float, cy: float, origin_x: float, origin_y: float) -> int:
    dist = math.sqrt((cx - origin_x) ** 2 + (cy - origin_y) ** 2)
    if dist < 1.0:
        return 0
    if dist < 100.0:
        return 1
    if dist < 190.0:
        return 2
    return 3


def parse_metatron_svg(svg_path: str | Path) -> tuple[list[tuple[float, float, float]], list[list[tuple[float, float]]]]:
    root = ET.fromstring(Path(svg_path).read_text(encoding="utf-8"))
    circles: list[tuple[float, float, float]] = []
    polylines: list[list[tuple[float, float]]] = []
    for path in root.findall(".//svg:path", SVG_NS):
        d = str(path.attrib.get("d", "")).strip()
        if "A " in d:
            circles.append(_extract_circle_from_path(d))
        elif "L" in d:
            points = _extract_line_points(d)
            if len(points) >= 2:
                polylines.append(points)
    return circles, polylines


def build_metatron_surface_map(svg_path: str | Path) -> MetatronSurfaceMap:
    circles, polylines = parse_metatron_svg(svg_path)
    if len(circles) != 13:
        raise ValueError(f"Expected 13 Metatron circles, got {len(circles)}")
    origin_x = sum(item[0] for item in circles) / len(circles)
    origin_y = sum(item[1] for item in circles) / len(circles)
    sorted_circles = sorted(circles, key=lambda item: (round(math.sqrt((item[0] - origin_x) ** 2 + (item[1] - origin_y) ** 2), 6), item[1], item[0]))
    nodes: list[MetatronNode] = []
    node_lookup: list[tuple[str, float, float]] = []
    channel_routes: dict[str, str] = {}
    channel_index = 0
    for idx, (cx, cy, radius) in enumerate(sorted_circles):
        shell_index = _assign_shell_index(cx, cy, origin_x, origin_y)
        if shell_index == 0:
            node_id = INVARIANT_HUB_ID
            channel = "M6_Identity"
            semantic_role = "invariant_hub"
        else:
            node_id = f"metatron_node_{idx:02d}"
            channel = CHANNEL_ORDER[channel_index % len(CHANNEL_ORDER)]
            channel_index += 1
            semantic_role = "memory_channel_router"
            channel_routes[channel] = node_id
        dx = cx - origin_x
        dy = cy - origin_y
        norm = math.sqrt(dx * dx + dy * dy)
        bloch_theta = 0.0 if norm == 0.0 else min(math.pi, (norm / max(1.0, max(abs(origin_x), abs(origin_y)))) * math.pi)
        bloch_phi = 0.0 if norm == 0.0 else math.atan2(dy, dx) % math.tau
        channel_pos = CHANNEL_ORDER.index(channel) if channel in CHANNEL_ORDER else CHANNEL_ORDER.index("M6_Identity")
        phase_vector = _phase36(bloch_theta, bloch_phi, shell_index, channel_pos)
        node = MetatronNode(
            node_id=node_id,
            x=round(cx, 6),
            y=round(cy, 6),
            radius=round(radius, 6),
            shell_index=shell_index,
            channel=channel,
            bloch_theta=round(bloch_theta, 10),
            bloch_phi=round(bloch_phi, 10),
            phase_vector_36d=phase_vector,
            semantic_role=semantic_role,
        )
        nodes.append(node)
        node_lookup.append((node.node_id, node.x, node.y))

    node_by_id = {node.node_id: node for node in nodes}
    edges_seen: set[tuple[str, str]] = set()
    threads: list[MetatronThread] = []
    for polyline in polylines:
        for left, right in zip(polyline, polyline[1:]):
            source_id = _nearest_node_id(node_lookup, left)
            target_id = _nearest_node_id(node_lookup, right)
            if source_id == target_id:
                continue
            key = tuple(sorted((source_id, target_id)))
            if key in edges_seen:
                continue
            edges_seen.add(key)
            source = node_by_id[source_id]
            target = node_by_id[target_id]
            dist = _mean_circular_distance(source.phase_vector_36d, target.phase_vector_36d)
            alignment = max(0.0, 1.0 - (dist / math.pi))
            coupling = 0.35 + alignment * 0.65
            friction = abs(_order_parameter(source.phase_vector_36d) - _order_parameter(target.phase_vector_36d))
            threads.append(
                MetatronThread(
                    thread_id=f"thread_{source_id}_{target_id}",
                    source_node_id=source_id,
                    target_node_id=target_id,
                    thread_kind="metatron_geodesic",
                    phase_alignment=round(alignment, 10),
                    coupling_weight=round(coupling, 10),
                    semantic_friction_r=round(friction, 10),
                )
            )

    overlay = np.zeros((N_OSCILLATORS, N_OSCILLATORS), dtype=np.float64)
    groups = MEMORY_CHANNEL_GROUPS
    for thread in threads:
        source = node_by_id[thread.source_node_id]
        target = node_by_id[thread.target_node_id]
        if source.channel not in groups or target.channel not in groups:
            continue
        for i in groups[source.channel]:
            for j in groups[target.channel]:
                if i == j:
                    continue
                overlay[i, j] = max(overlay[i, j], thread.coupling_weight)
                overlay[j, i] = max(overlay[j, i], thread.coupling_weight)
    for i in range(N_OSCILLATORS):
        overlay[i, i] = 1.0

    return MetatronSurfaceMap(
        schema="noema/metatron-surface-mmap/v1",
        source_svg=str(Path(svg_path).resolve()),
        node_count=len(nodes),
        thread_count=len(threads),
        invariant_hub=INVARIANT_HUB_ID,
        nodes=tuple(nodes),
        threads=tuple(threads),
        coupling_overlay_36x36=tuple(tuple(round(float(value), 10) for value in row) for row in overlay),
        channel_routes=channel_routes,
    )


def export_metatron_surface_map(svg_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    payload = build_metatron_surface_map(svg_path).to_dict()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


__all__ = [
    "INVARIANT_HUB_ID",
    "MetatronNode",
    "MetatronSurfaceMap",
    "MetatronThread",
    "build_metatron_surface_map",
    "export_metatron_surface_map",
    "parse_metatron_svg",
]
