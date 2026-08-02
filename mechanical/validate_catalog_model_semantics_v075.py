#!/usr/bin/env python3
"""Validate semantic node multiplicity of current catalogue GLB files.

This catches presentation bugs that watertightness checks cannot see, notably the
former duplicate service lid in the electronics-layout scene.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "catalog" / "drawings.json"


def scene_instances(path: Path) -> list[dict[str, str]]:
    loaded = trimesh.load(path, force="scene", process=False)
    if not isinstance(loaded, trimesh.Scene):
        loaded = trimesh.Scene(loaded)

    instances: list[dict[str, str]] = []
    for node_name in loaded.graph.nodes_geometry:
        try:
            _, geometry_name = loaded.graph.get(node_name)
        except Exception:
            geometry_name = node_name
        geometry = loaded.geometry.get(geometry_name)
        metadata_name = "" if geometry is None else str(geometry.metadata.get("name") or "")
        instances.append({
            "node": str(node_name),
            "geometry": str(geometry_name),
            "metadata": metadata_name,
        })

    # A malformed exporter can leave geometry without a graph node. Count it as
    # an instance too so duplicate logical parts are not hidden by set/dedup logic.
    referenced_geometry = {item["geometry"] for item in instances}
    for geometry_name, geometry in loaded.geometry.items():
        name = str(geometry_name)
        if name not in referenced_geometry:
            instances.append({
                "node": "",
                "geometry": name,
                "metadata": str(geometry.metadata.get("name") or ""),
            })
    return instances


def instance_matches(instance: dict[str, str], expected: str) -> bool:
    values = instance.values()
    return any(value == expected or value.startswith(expected) for value in values if value)


def describe(instance: dict[str, str]) -> str:
    return "/".join(value for value in (instance["node"], instance["geometry"], instance["metadata"]) if value)


def main() -> int:
    media = json.loads(MEDIA.read_text(encoding="utf-8"))
    model = next((item for item in media["models"] if item["id"] == "210"), None)
    if model is None:
        print("В catalog/drawings.json отсутствует модель 210", file=sys.stderr)
        return 1
    path = ROOT / model["file"]
    if not path.is_file():
        print(f"Не найден GLB: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    instances = scene_instances(path)
    failures: list[str] = []
    lids = [item for item in instances if any("PETG_service_lid" in value for value in item.values())]
    if len(lids) != 1:
        failures.append(
            "в модели 210 должна быть ровно одна сервисная крышка, "
            f"найдено {len(lids)}: {[describe(item) for item in lids]}"
        )
    elif not instance_matches(lids[0], "PETG_service_lid"):
        failures.append("единственная крышка не имеет канонического имени PETG_service_lid")
    if any("raised" in value.lower() for item in lids for value in item.values()):
        failures.append("крышка должна сохранять каноническое имя PETG_service_lid без presentation-суффикса")

    required = {
        "PETG_service_lid",
        "PETG_electronics_carrier",
        "PETG_VEML7700_cradle",
        "PETG_rotor_half_A_retracted",
        "PETG_rotor_half_B_retracted",
    }
    for required_name in sorted(required):
        if not any(instance_matches(item, required_name) for item in instances):
            failures.append(f"в модели 210 отсутствует узел {required_name}")

    if failures:
        print("Ошибки семантики GLB:\n- " + "\n- ".join(failures), file=sys.stderr)
        return 1
    print("Модель 210: одна каноническая сервисная крышка; обязательные узлы присутствуют.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
