#!/usr/bin/env python3
"""Compare a regenerated v0.7.6 mechanics snapshot with a reference tree.

The comparison is deliberately binary-aware:
- byte-identical files pass immediately;
- STL and GLB files are compared by stable geometry/scene metrics;
- JSON reports are compared after recursively normalizing path separators,
  because the generator intentionally emits host-native paths.

The script does not regenerate the mechanics itself. Run the generator in an
isolated full copy first, then point this script at both roots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

STL_DIRECTORIES = (
    "mechanical/stl_petg_v06",
    "mechanical/stl_tpu95_v06",
    "mechanical/stl_tpu85_v06",
    "mechanical/test_coupons_v06",
)
GLB_FILES = tuple(
    f"mechanical/flagpole_finial_v0_6_{name}.glb"
    for name in (
        "assembly",
        "flag_power_route",
        "electronics_layout",
        "exploded",
        "print_layout_PETG",
        "print_layout_TPU95",
        "print_layout_TPU85",
    )
)
JSON_FILES = (
    "mechanical/model_parameters_and_diagnostics_v06.json",
    "mechanical/project_manifest_v06.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--regenerated-root", type=Path, required=True)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("mechanical/LEGACY_REGENERATION_AUDIT_V076.json"),
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=Path("docs/LEGACY_CAD_REGENERATION_AUDIT_RU.md"),
    )
    parser.add_argument("--generator-exit-code", type=int, default=0)
    parser.add_argument("--elapsed-seconds", type=float)
    parser.add_argument("--peak-rss-kb", type=int)
    parser.add_argument("--date", default="2026-08-04")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mesh_metrics(mesh: trimesh.Trimesh) -> dict[str, Any]:
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "bounds": np.round(mesh.bounds, 5).tolist(),
        "area": round(float(mesh.area), 5),
        "volumeAbs": round(abs(float(mesh.volume)), 5),
        "watertight": bool(mesh.is_watertight),
        "windingConsistent": bool(mesh.is_winding_consistent),
        "identifierHash": str(mesh.identifier_hash),
    }


def scene_metrics(path: Path) -> dict[str, Any]:
    scene = trimesh.load(path, force="scene", process=False)
    items: list[dict[str, Any]] = []
    for node in sorted(scene.graph.nodes_geometry):
        transform, geometry_name = scene.graph.get(node)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        metrics = mesh_metrics(mesh)
        metrics["node"] = node
        metrics["geometry"] = geometry_name
        items.append(metrics)
    return {"nodeCount": len(items), "nodes": items}


def normalize_json(value: Any) -> Any:
    """Normalize only cross-platform serialization details, not engineering data."""
    if isinstance(value, dict):
        return {key: normalize_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    if isinstance(value, str):
        return value.replace("\\", "/")
    return value


def file_list(reference_root: Path) -> list[str]:
    files: list[str] = []
    for directory in STL_DIRECTORIES:
        files.extend(
            sorted(str(path.relative_to(reference_root)).replace("\\", "/")
                   for path in (reference_root / directory).glob("*.stl"))
        )
    files.extend(GLB_FILES)
    files.extend(JSON_FILES)
    return files


def compare_file(reference: Path, regenerated: Path, relative_path: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": relative_path,
        "existsOriginal": reference.exists(),
        "existsRegenerated": regenerated.exists(),
    }
    if not reference.exists() or not regenerated.exists():
        result["equivalent"] = False
        result["equivalenceBasis"] = "missing-file"
        return result

    result.update(
        originalBytes=reference.stat().st_size,
        regeneratedBytes=regenerated.stat().st_size,
        originalSha256=sha256(reference),
        regeneratedSha256=sha256(regenerated),
    )
    result["byteIdentical"] = result["originalSha256"] == result["regeneratedSha256"]
    if result["byteIdentical"]:
        result["equivalent"] = True
        result["equivalenceBasis"] = "sha256"
        return result

    try:
        if relative_path.endswith(".stl"):
            result["originalMetrics"] = mesh_metrics(
                trimesh.load(reference, force="mesh", process=False)
            )
            result["regeneratedMetrics"] = mesh_metrics(
                trimesh.load(regenerated, force="mesh", process=False)
            )
            result["equivalent"] = result["originalMetrics"] == result["regeneratedMetrics"]
            result["equivalenceBasis"] = "normalized-mesh-metrics"
        elif relative_path.endswith(".glb"):
            result["originalMetrics"] = scene_metrics(reference)
            result["regeneratedMetrics"] = scene_metrics(regenerated)
            result["equivalent"] = result["originalMetrics"] == result["regeneratedMetrics"]
            result["equivalenceBasis"] = "normalized-scene-metrics"
        elif relative_path.endswith(".json"):
            original_json = normalize_json(json.loads(reference.read_text(encoding="utf-8-sig")))
            regenerated_json = normalize_json(json.loads(regenerated.read_text(encoding="utf-8-sig")))
            result["equivalent"] = original_json == regenerated_json
            result["equivalenceBasis"] = "parsed-json-with-path-separator-normalization"
        else:
            result["equivalent"] = False
            result["equivalenceBasis"] = "unsupported-type"
    except Exception as error:  # pragma: no cover - retained in audit output
        result["equivalent"] = False
        result["equivalenceBasis"] = "comparison-error"
        result["error"] = f"{type(error).__name__}: {error}"
    return result


def markdown_report(report: dict[str, Any], date: str) -> str:
    status = "PASS" if report["allEquivalent"] else "FAIL"
    elapsed = report.get("elapsedSeconds")
    peak_rss = report.get("peakRssKb")
    lines = [
        "# Повторная проверка канонической SDF/trimesh-линии v0.7.6",
        "",
        f"Дата проверки: {date}.",
        "",
        "Генератор `mechanical/generate_models_v06.py` запущен в отдельной полной копии рабочего дерева. Канонические файлы основного дерева во время проверки не перезаписывались. Сравнение выполнено скриптом `mechanical/audit_legacy_regeneration_v076.py`.",
        "",
        "## Результат",
        "",
        f"- код завершения генератора: **{report['generatorExitCode']}**;",
    ]
    if elapsed is not None:
        lines.append(f"- время выполнения: **{elapsed:.2f} с**;")
    if peak_rss is not None:
        lines.append(f"- пиковая память: **{peak_rss / 1024:.1f} МиБ**;")
    lines.extend(
        [
            f"- проверено файлов: **{report['fileCount']}**;",
            f"- STL: **{report['stlCount']}**;",
            f"- GLB: **{report['glbCount']}**;",
            f"- JSON-отчёты: **{report['jsonCount']}**;",
            f"- побитово совпали: **{report['byteIdenticalCount']}/{report['fileCount']}**;",
            f"- геометрически либо семантически эквивалентны: **{report['geometricallyOrSemanticallyEquivalentCount']}/{report['fileCount']}**;",
            f"- итог: **{status}**.",
            "",
            "Для побитово отличающихся STL и узлов GLB сравнивались число вершин/граней, AABB, площадь, абсолютный объём, замкнутость, согласованность обхода и инвариантный `trimesh.identifier_hash`. JSON сравнивался после разбора; только разделители путей `\\` и `/` нормализовались как платформенное представление. Инженерные значения, имена, числа и структура не нормализовались.",
            "",
            "## Побитово отличающиеся файлы",
            "",
        ]
    )
    changed = [item for item in report["files"] if not item.get("byteIdentical")]
    if changed:
        for item in changed:
            result = "PASS" if item.get("equivalent") else "FAIL"
            lines.append(
                f"- `{item['path']}`: {item.get('originalBytes', '—')} → "
                f"{item.get('regeneratedBytes', '—')} байт; "
                f"нормализованная эквивалентность: **{result}**; "
                f"основание: `{item.get('equivalenceBasis', '—')}`."
            )
    else:
        lines.append("Все файлы совпали побитово.")
    lines.extend(
        [
            "",
            "## Среда сравнения",
            "",
            f"- Python: `{report['environment']['python']}`;",
            f"- платформа: `{report['environment']['platform']}`;",
            f"- NumPy: `{report['environment']['numpy']}`;",
            f"- trimesh: `{report['environment']['trimesh']}`.",
            "",
            "## Граница доказательства",
            "",
            "Проверка подтверждает воспроизводимость текущего цифрового SDF/trimesh-слоя в указанной среде. Она не подтверждает физические посадки, прочность, герметичность, нагрев, работоспособность электроники или долговечность на улице.",
            "",
            "Полные метрики и хеши находятся в `mechanical/LEGACY_REGENERATION_AUDIT_V076.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    reference_root = args.reference_root.resolve()
    regenerated_root = args.regenerated_root.resolve()
    results = [
        compare_file(reference_root / relative, regenerated_root / relative, relative)
        for relative in file_list(reference_root)
    ]
    equivalent_count = sum(bool(item.get("equivalent")) for item in results)
    report = {
        "schemaVersion": 2,
        "generator": "mechanical/generate_models_v06.py",
        "comparisonScript": "mechanical/audit_legacy_regeneration_v076.py",
        "generatorExitCode": args.generator_exit_code,
        "fileCount": len(results),
        "stlCount": sum(item["path"].endswith(".stl") for item in results),
        "glbCount": sum(item["path"].endswith(".glb") for item in results),
        "jsonCount": sum(item["path"].endswith(".json") for item in results),
        "byteIdenticalCount": sum(bool(item.get("byteIdentical")) for item in results),
        "geometricallyOrSemanticallyEquivalentCount": equivalent_count,
        "allEquivalent": equivalent_count == len(results) and args.generator_exit_code == 0,
        "elapsedSeconds": args.elapsed_seconds,
        "peakRssKb": args.peak_rss_kb,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "trimesh": trimesh.__version__,
        },
        "jsonNormalization": "recursive path separator normalization only",
        "files": results,
    }

    output_json = args.output_json
    output_markdown = args.output_markdown
    if not output_json.is_absolute():
        output_json = reference_root / output_json
    if not output_markdown.is_absolute():
        output_markdown = reference_root / output_markdown
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_markdown.write_text(markdown_report(report, args.date), encoding="utf-8")

    summary = {
        key: report[key]
        for key in (
            "fileCount",
            "stlCount",
            "glbCount",
            "jsonCount",
            "byteIdenticalCount",
            "geometricallyOrSemanticallyEquivalentCount",
            "allEquivalent",
        )
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report["allEquivalent"] else 2


if __name__ == "__main__":
    sys.exit(main())
