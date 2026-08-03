#!/usr/bin/env python3
"""Deterministic compact packing for single-material print-layout GLB scenes.

The helper preserves each part's already selected print orientation. It uses
axis-aligned bounds, a fixed edge reserve and a named inter-part clearance.
No build plate, brim, raft or sacrificial PETG backing is added to printable
geometry: those are slicer settings, not canonical project parts.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import trimesh


@dataclass
class PackedItem:
    name: str
    key: str
    mesh: trimesh.Trimesh
    width: float
    depth: float
    area: float
    source_index: int


@dataclass
class Shelf:
    y: float
    height: float
    used_width: float
    items: list[tuple[PackedItem, float]]


def _put_on_bed(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    result.apply_translation([0.0, 0.0, -float(result.bounds[0][2])])
    return result


def _xy_clearance(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    ab, bb = a.bounds, b.bounds
    dx = max(float(ab[0][0] - bb[1][0]), float(bb[0][0] - ab[1][0]), 0.0)
    dy = max(float(ab[0][1] - bb[1][1]), float(bb[0][1] - ab[1][1]), 0.0)
    if dx == 0.0 and dy == 0.0:
        return 0.0
    if dx == 0.0:
        return dy
    if dy == 0.0:
        return dx
    return math.hypot(dx, dy)


def pack_print_layout(
    parts: Mapping[str, trimesh.Trimesh],
    entries: Sequence[tuple[str, str]],
    *,
    bed_size_mm: float = 256.0,
    edge_mm: float = 8.0,
    gap_mm: float = 6.0,
) -> tuple[dict[str, trimesh.Trimesh], dict]:
    """Pack pre-oriented parts onto one square bed using first-fit shelves.

    Returns a scene-name -> transformed mesh mapping and reproducible metrics.
    The packed scene is centred around X/Y=0 for convenient GLB viewing while
    diagnostics retain the physical 0..bed coordinate system.
    """
    if bed_size_mm <= 0 or edge_mm < 0 or gap_mm < 0:
        raise ValueError("bed_size_mm must be positive; edge_mm/gap_mm must be non-negative")
    usable = bed_size_mm - 2.0 * edge_mm
    if usable <= 0:
        raise ValueError("edge reserve leaves no printable area")
    if not entries:
        raise ValueError("print layout must contain at least one part")

    items: list[PackedItem] = []
    for index, (name, key) in enumerate(entries):
        if key not in parts:
            raise KeyError(f"unknown print part key: {key}")
        mesh = _put_on_bed(parts[key])
        bounds = mesh.bounds
        width = float(bounds[1][0] - bounds[0][0])
        depth = float(bounds[1][1] - bounds[0][1])
        if width <= 0 or depth <= 0:
            raise ValueError(f"part {key} has invalid XY bounds")
        if width > usable + 1e-6 or depth > usable + 1e-6:
            raise ValueError(
                f"part {key} ({width:.2f} × {depth:.2f} mm) does not fit "
                f"the {usable:.2f} mm usable bed span"
            )
        items.append(PackedItem(name, key, mesh, width, depth, width * depth, index))

    # Large/deep parts first makes shelf use stable and avoids a tall late row.
    items.sort(key=lambda item: (-item.depth, -item.width, item.source_index, item.name))
    shelves: list[Shelf] = []
    for item in items:
        selected: Shelf | None = None
        for shelf in shelves:
            required = item.width if not shelf.items else gap_mm + item.width
            if shelf.used_width + required <= usable + 1e-6 and item.depth <= shelf.height + 1e-6:
                selected = shelf
                break
        if selected is None:
            y = 0.0 if not shelves else shelves[-1].y + shelves[-1].height + gap_mm
            if y + item.depth > usable + 1e-6:
                raise ValueError(
                    f"all parts do not fit one {bed_size_mm:.0f} × {bed_size_mm:.0f} mm bed "
                    f"with {edge_mm:.1f} mm edge reserve and {gap_mm:.1f} mm gap"
                )
            selected = Shelf(y=y, height=item.depth, used_width=0.0, items=[])
            shelves.append(selected)
        x = selected.used_width + (gap_mm if selected.items else 0.0)
        selected.items.append((item, x))
        selected.used_width = x + item.width

    packed_bed: dict[str, trimesh.Trimesh] = {}
    item_records: list[dict] = []
    for shelf in shelves:
        for item, local_x in shelf.items:
            result = item.mesh.copy()
            bounds = result.bounds
            target_min_x = edge_mm + local_x
            target_min_y = edge_mm + shelf.y
            result.apply_translation([
                target_min_x - float(bounds[0][0]),
                target_min_y - float(bounds[0][1]),
                -float(bounds[0][2]),
            ])
            packed_bed[item.name] = result
            final_bounds = result.bounds
            item_records.append({
                "name": item.name,
                "sourceKey": item.key,
                "boundsOnBedMm": np.round(final_bounds, 4).tolist(),
            })

    scene_bounds = np.array([
        np.min([mesh.bounds[0] for mesh in packed_bed.values()], axis=0),
        np.max([mesh.bounds[1] for mesh in packed_bed.values()], axis=0),
    ])
    used_width = float(scene_bounds[1][0] - scene_bounds[0][0])
    used_depth = float(scene_bounds[1][1] - scene_bounds[0][1])
    centre_x = float((scene_bounds[0][0] + scene_bounds[1][0]) / 2.0)
    centre_y = float((scene_bounds[0][1] + scene_bounds[1][1]) / 2.0)

    centred: dict[str, trimesh.Trimesh] = {}
    for name, mesh in packed_bed.items():
        result = mesh.copy()
        result.apply_translation([-centre_x, -centre_y, 0.0])
        centred[name] = result

    names = list(packed_bed)
    clearances = [
        _xy_clearance(packed_bed[names[i]], packed_bed[names[j]])
        for i in range(len(names))
        for j in range(i + 1, len(names))
    ]
    min_clearance = min(clearances, default=bed_size_mm)
    if min_clearance + 1e-6 < gap_mm:
        raise AssertionError(
            f"packing clearance {min_clearance:.3f} mm is below requested {gap_mm:.3f} mm"
        )

    diagnostics = {
        "bedSizeMm": bed_size_mm,
        "edgeReserveMm": edge_mm,
        "requestedGapMm": gap_mm,
        "partCount": len(entries),
        "shelfCount": len(shelves),
        "usedBoundsOnBedMm": np.round(scene_bounds, 4).tolist(),
        "usedWidthMm": round(used_width, 4),
        "usedDepthMm": round(used_depth, 4),
        "minimumAabbClearanceMm": round(min_clearance, 4),
        "aabbOccupancyRatio": round(sum(item.area for item in items) / (used_width * used_depth), 6),
        "containsCanonicalBackingGeometry": False,
        "note": "Brim/raft is a slicer setting; no sacrificial PETG backing is part of the canonical STL/GLB layout.",
        "items": sorted(item_records, key=lambda record: record["name"]),
    }
    return centred, diagnostics


def self_test() -> int:
    parts = {
        "large_a": trimesh.creation.box([110, 72, 10]),
        "large_b": trimesh.creation.box([110, 72, 8]),
        "small_a": trimesh.creation.box([42, 32, 5]),
        "small_b": trimesh.creation.box([36, 28, 4]),
        "small_c": trimesh.creation.box([30, 20, 3]),
    }
    entries = [(name, name) for name in parts]
    packed, diagnostics = pack_print_layout(parts, entries, bed_size_mm=256, edge_mm=8, gap_mm=6)
    assert len(packed) == len(parts)
    assert diagnostics["minimumAabbClearanceMm"] >= 6
    assert diagnostics["usedWidthMm"] <= 240
    assert diagnostics["usedDepthMm"] <= 240
    assert diagnostics["containsCanonicalBackingGeometry"] is False
    for mesh in packed.values():
        assert abs(float(mesh.bounds[0][2])) < 1e-8
    print(json.dumps({key: value for key, value in diagnostics.items() if key != "items"}, indent=2))
    print("Self-test compact print-layout packing: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    parser.error("This module is imported by generate_models_v06.py; use --self-test for a standalone check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
