#!/usr/bin/env python3
"""Render compact, deterministic ID callouts for current 2D drawings.

The engineering sources and card thumbnails stay clean. This script creates
annotated full-size PNG companions under ``catalog/annotated`` from metadata in
``catalog/drawings.json``. ``labelPosition`` is treated as a preferred direction,
not as an absolute box location: the resolver keeps labels close to their target,
avoids other labels and discourages leader crossings.

Print layouts are exempt because labels can hide orientation, spacing and bed
clearance information.

Use:
    python mechanical/render_catalog_part_callouts_v075.py
    python mechanical/render_catalog_part_callouts_v075.py --check
    python mechanical/render_catalog_part_callouts_v075.py --self-test
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
MEDIA_PATH = ROOT / "catalog" / "drawings.json"
OUTPUT_DIR = ROOT / "catalog" / "annotated"
REPORT_PATH = ROOT / "mechanical" / "CALLOUT_LAYOUT_REPORT_V076.json"
REPORT_SCHEMA_VERSION = 1


# Tiny built-in 5×7 glyphs make the overlay pixel-stable on Windows and Linux.
# Only characters used by component/part IDs are included; human-readable names
# remain in the HTML legend. No host font is required.
GLYPHS: dict[str, tuple[str, ...]] = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "#": ("01010", "11111", "01010", "01010", "11111", "01010", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "p": ("00000", "11110", "10001", "11110", "10000", "10000", "10000"),
    "e": ("00000", "01110", "10001", "11111", "10000", "10001", "01110"),
    "t": ("00100", "11111", "00100", "00100", "00100", "00101", "00010"),
    "g": ("00000", "01111", "10001", "01111", "00001", "10001", "01110"),
    "u": ("00000", "10001", "10001", "10001", "10001", "10011", "01101"),
}

Point = tuple[float, float]
Rect = tuple[float, float, float, float]
Segment = tuple[Point, Point]


@dataclass(frozen=True)
class Placement:
    text: str
    target: Point
    hint: Point
    center: Point
    box: Rect
    leader: Segment
    old_length: float
    new_length: float


def bitmap_size(text: str, scale: int) -> tuple[int, int]:
    if not text:
        return 0, 7 * scale
    return ((5 * len(text) + max(0, len(text) - 1)) * scale, 7 * scale)


def draw_bitmap_text(draw: ImageDraw.ImageDraw, xy: Point, text: str, scale: int) -> None:
    x0, y0 = (round(xy[0]), round(xy[1]))
    for char_index, char in enumerate(text.lower()):
        glyph = GLYPHS.get(char)
        if glyph is None:
            raise ValueError(f"ID содержит неподдерживаемый символ {char!r}: {text}")
        glyph_x = x0 + char_index * 6 * scale
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    left = glyph_x + column * scale
                    top = y0 + row * scale
                    draw.rectangle((left, top, left + scale - 1, top + scale - 1), fill=(18, 24, 28, 255))


def point(value: object, place: str) -> Point:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{place} должен быть массивом [x, y]")
    x, y = value
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y)):
        raise ValueError(f"{place} должен содержать конечные числа")
    if not (0.0 <= float(x) <= 1.0 and 0.0 <= float(y) <= 1.0):
        raise ValueError(f"{place} должен находиться в диапазоне 0…1")
    return float(x), float(y)


def expected_overlay_items(media: dict) -> list[dict]:
    items: list[dict] = []
    for index, item in enumerate(media.get("drawings", [])):
        place = f"drawings[{index}]"
        if item.get("status") != "current":
            raise ValueError(f"{place}: каталог допускает только status=current")
        mode = item.get("calloutMode")
        if item.get("kind") == "print-layout":
            if mode != "exempt" or item.get("callouts"):
                raise ValueError(f"{place}: раскладка печати должна быть exempt и без callouts")
            continue
        if mode == "embedded":
            if not item.get("partIds"):
                raise ValueError(f"{place}: embedded-вид требует partIds")
            continue
        if mode != "overlay":
            raise ValueError(f"{place}: ожидается calloutMode=overlay или embedded")
        if not item.get("callouts"):
            raise ValueError(f"{place}: непечатный чертёж требует хотя бы одну выноску")
        if not item.get("annotatedPreview"):
            raise ValueError(f"{place}: overlay-вид требует annotatedPreview")
        for callout_index, callout in enumerate(item["callouts"]):
            if not str(callout.get("id", "")).strip():
                raise ValueError(f"{place}.callouts[{callout_index}].id обязателен")
            point(callout.get("target"), f"{place}.callouts[{callout_index}].target")
            point(callout.get("labelPosition"), f"{place}.callouts[{callout_index}].labelPosition")
        items.append(item)
    return items


def rect_from_center(center: Point, size: tuple[float, float]) -> Rect:
    width, height = size
    return (center[0] - width / 2, center[1] - height / 2, center[0] + width / 2, center[1] + height / 2)


def rect_overlap_area(a: Rect, b: Rect, margin: float = 0.0) -> float:
    left = max(a[0] - margin, b[0] - margin)
    top = max(a[1] - margin, b[1] - margin)
    right = min(a[2] + margin, b[2] + margin)
    bottom = min(a[3] + margin, b[3] + margin)
    return max(0.0, right - left) * max(0.0, bottom - top)


def point_in_rect(p: Point, rect: Rect, margin: float = 0.0) -> bool:
    return rect[0] - margin <= p[0] <= rect[2] + margin and rect[1] - margin <= p[1] <= rect[3] + margin


def orient(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def proper_segment_intersection(a: Segment, b: Segment) -> bool:
    """Return true only for a proper interior crossing, not shared endpoints."""
    a1, a2 = a
    b1, b2 = b
    eps = 1e-7
    if any(math.dist(p, q) <= eps for p in a for q in b):
        return False
    o1, o2 = orient(a1, a2, b1), orient(a1, a2, b2)
    o3, o4 = orient(b1, b2, a1), orient(b1, b2, a2)
    return o1 * o2 < -eps and o3 * o4 < -eps


def segment_intersects_rect(segment: Segment, rect: Rect, margin: float = 0.0) -> bool:
    expanded = (rect[0] - margin, rect[1] - margin, rect[2] + margin, rect[3] + margin)
    a, b = segment
    if point_in_rect(a, expanded) or point_in_rect(b, expanded):
        return True
    corners = (
        (expanded[0], expanded[1]),
        (expanded[2], expanded[1]),
        (expanded[2], expanded[3]),
        (expanded[0], expanded[3]),
    )
    edges = tuple((corners[i], corners[(i + 1) % 4]) for i in range(4))
    return any(proper_segment_intersection(segment, edge) for edge in edges)


def segment_edge_density(segment: Segment, edge_map: Image.Image | None) -> float:
    """Estimate how much of a leader crosses visible source-drawing contours.

    The final part of the leader is ignored because it intentionally terminates
    on the target geometry. The metric is only a soft penalty: a short line can
    still cross a local contour when no cleaner nearby route exists.
    """
    if edge_map is None:
        return 0.0
    start, end = segment
    length = math.dist(start, end)
    samples = max(8, min(96, int(length / 5.0)))
    hits = 0.0
    considered = 0
    for index in range(1, samples):
        t = index / samples
        if t >= 0.82:
            break
        x = int(round(start[0] + (end[0] - start[0]) * t))
        y = int(round(start[1] + (end[1] - start[1]) * t))
        x = min(max(x, 1), edge_map.width - 2)
        y = min(max(y, 1), edge_map.height - 2)
        value = max(
            edge_map.getpixel((x + dx, y + dy))
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
        )
        hits += min(1.0, float(value) / 96.0)
        considered += 1
    return hits / considered if considered else 0.0


def nearest_rect_point(rect: Rect, target: Point) -> Point:
    """Choose the nearest perimeter point, avoiding a leader through the box."""
    x = min(max(target[0], rect[0]), rect[2])
    y = min(max(target[1], rect[1]), rect[3])
    if not point_in_rect(target, rect):
        return x, y
    distances = (
        (abs(target[0] - rect[0]), (rect[0], target[1])),
        (abs(target[0] - rect[2]), (rect[2], target[1])),
        (abs(target[1] - rect[1]), (target[0], rect[1])),
        (abs(target[1] - rect[3]), (target[0], rect[3])),
    )
    return min(distances, key=lambda entry: entry[0])[1]


def unit(vector: Point, fallback: Point = (1.0, -1.0)) -> Point:
    length = math.hypot(vector[0], vector[1])
    if length <= 1e-9:
        vector = fallback
        length = math.hypot(vector[0], vector[1])
    return vector[0] / length, vector[1] / length


def direction_candidates(hint_vector: Point) -> list[Point]:
    hint = unit(hint_vector)
    directions = [
        (1.0, 0.0), (math.sqrt(0.5), math.sqrt(0.5)), (0.0, 1.0),
        (-math.sqrt(0.5), math.sqrt(0.5)), (-1.0, 0.0),
        (-math.sqrt(0.5), -math.sqrt(0.5)), (0.0, -1.0),
        (math.sqrt(0.5), -math.sqrt(0.5)),
    ]
    return sorted(
        directions,
        key=lambda d: (
            1.0 - (d[0] * hint[0] + d[1] * hint[1]),
            directions.index(d),
        ),
    )


def clamp_center(center: Point, size: tuple[float, float], width: int, height: int, margin: float) -> Point:
    half_w, half_h = size[0] / 2, size[1] / 2
    return (
        min(max(center[0], margin + half_w), width - margin - half_w),
        min(max(center[1], margin + half_h), height - margin - half_h),
    )


def candidate_centers(
    target: Point,
    hint: Point,
    size: tuple[float, float],
    width: int,
    height: int,
    dot_radius: float,
    edge_margin: float,
) -> list[Point]:
    directions = direction_candidates((hint[0] - target[0], hint[1] - target[1]))
    half_w, half_h = size[0] / 2, size[1] / 2
    clearance = dot_radius + max(7.0, min(width, height) * 0.008)
    rings = (1.0, 1.32, 1.68, 2.08, 2.55)
    result: list[Point] = []
    seen: set[tuple[int, int]] = set()
    for ring in rings:
        for dx, dy in directions:
            offset_x = dx * (half_w + clearance) * ring
            offset_y = dy * (half_h + clearance) * ring
            center = clamp_center((target[0] + offset_x, target[1] + offset_y), size, width, height, edge_margin)
            key = (round(center[0] * 10), round(center[1] * 10))
            if key not in seen:
                result.append(center)
                seen.add(key)
    return result


def score_candidate(
    center: Point,
    size: tuple[float, float],
    target: Point,
    hint: Point,
    placed: Sequence[Placement],
    all_targets: Sequence[Point],
    width: int,
    height: int,
    box_margin: float,
    edge_map: Image.Image | None = None,
) -> tuple[float, Segment, Rect]:
    box = rect_from_center(center, size)
    start = nearest_rect_point(box, target)
    leader = (start, target)
    diagonal = math.hypot(width, height)
    score = math.dist(start, target) / diagonal * 100.0
    # Softly prefer leaders that do not run across contrast edges of the
    # underlying drawing. Shortness remains dominant.
    score += segment_edge_density(leader, edge_map) * 18.0

    # Prefer the side indicated by the legacy metadata without preserving its
    # excessive distance from the actual part.
    hint_dir = unit((hint[0] - target[0], hint[1] - target[1]))
    candidate_dir = unit((center[0] - target[0], center[1] - target[1]))
    score += (1.0 - (hint_dir[0] * candidate_dir[0] + hint_dir[1] * candidate_dir[1])) * 9.0

    for previous in placed:
        overlap = rect_overlap_area(box, previous.box, margin=box_margin)
        if overlap > 0:
            score += 1_000_000.0 + overlap * 1000.0
        if segment_intersects_rect(leader, previous.box, margin=box_margin * 0.5):
            score += 200_000.0
        if proper_segment_intersection(leader, previous.leader):
            score += 100_000.0

    # Do not cover another callout target with the ID box.
    for other_target in all_targets:
        if math.dist(other_target, target) > 1e-7 and point_in_rect(other_target, box, margin=box_margin):
            score += 150_000.0

    # Small preference for unused screen areas and non-clamped candidates.
    if box[0] <= box_margin or box[1] <= box_margin or box[2] >= width - box_margin or box[3] >= height - box_margin:
        score += 12.0
    return score, leader, box


def resolve_placements(
    callouts: Sequence[dict],
    width: int,
    height: int,
    glyph_scale: int,
    dot_radius: int,
    pad_x: int,
    pad_y: int,
    line_width: int,
    edge_map: Image.Image | None = None,
) -> list[Placement]:
    specs: list[dict] = []
    for index, callout in enumerate(callouts):
        text = str(callout["id"])
        target_norm = point(callout["target"], f"callouts[{index}].target")
        hint_norm = point(callout["labelPosition"], f"callouts[{index}].labelPosition")
        target = (target_norm[0] * width, target_norm[1] * height)
        hint = (hint_norm[0] * width, hint_norm[1] * height)
        text_w, text_h = bitmap_size(text, glyph_scale)
        size = (text_w + 2 * pad_x, text_h + 2 * pad_y)
        nearest_target = min(
            (math.dist(target, (point(other["target"], "target")[0] * width, point(other["target"], "target")[1] * height))
             for other in callouts if other is not callout),
            default=math.hypot(width, height),
        )
        specs.append({
            "index": index,
            "text": text,
            "target": target,
            "hint": hint,
            "size": size,
            "nearest_target": nearest_target,
        })

    # Densest targets are placed first, where candidate freedom matters most.
    placement_order = sorted(specs, key=lambda spec: (spec["nearest_target"], spec["index"]))
    all_targets = [spec["target"] for spec in specs]
    placed: list[Placement] = []
    placed_by_index: dict[int, Placement] = {}
    edge_margin = max(3.0, line_width + 1.0)
    box_margin = max(3.0, line_width + 1.0)

    for spec in placement_order:
        best: tuple[float, Point, Segment, Rect] | None = None
        for center in candidate_centers(
            spec["target"], spec["hint"], spec["size"], width, height, dot_radius, edge_margin
        ):
            score, leader, box = score_candidate(
                center, spec["size"], spec["target"], spec["hint"], placed, all_targets,
                width, height, box_margin, edge_map,
            )
            candidate = (score, center, leader, box)
            if best is None or candidate[0] < best[0] - 1e-9:
                best = candidate
        assert best is not None
        _, center, leader, box = best
        placement = Placement(
            text=spec["text"],
            target=spec["target"],
            hint=spec["hint"],
            center=center,
            box=box,
            leader=leader,
            old_length=math.dist(spec["hint"], spec["target"]),
            new_length=math.dist(leader[0], leader[1]),
        )
        placed.append(placement)
        placed_by_index[spec["index"]] = placement

    # Preserve source order for deterministic drawing and report rows.
    return [placed_by_index[spec["index"]] for spec in specs]


def crossing_count_segments(segments: Sequence[Segment]) -> int:
    count = 0
    for index, first in enumerate(segments):
        for second in segments[index + 1:]:
            if proper_segment_intersection(first, second):
                count += 1
    return count


def crossing_count(placements: Sequence[Placement]) -> int:
    return crossing_count_segments([placement.leader for placement in placements])


def render(item: dict) -> tuple[bytes, dict]:
    preview_path = ROOT / item["preview"]
    if not preview_path.is_file():
        raise FileNotFoundError(f"Не найден исходный preview: {item['preview']}")

    with Image.open(preview_path) as opened:
        image = opened.convert("RGBA")

    width, height = image.size
    if width < 50 or height < 50:
        raise ValueError(f"Слишком маленькое изображение {item['preview']}: {width}×{height}")

    draw = ImageDraw.Draw(image, "RGBA")
    short_side = min(width, height)
    glyph_scale = max(2, min(6, round(short_side * 0.003)))
    line_width = max(2, round(short_side * 0.0032))
    dot_radius = max(4, round(short_side * 0.006))
    pad_x = max(7, 3 * glyph_scale)
    pad_y = max(4, 2 * glyph_scale)

    edge_map = image.convert("L").filter(ImageFilter.FIND_EDGES)
    placements = resolve_placements(
        item["callouts"], width, height, glyph_scale, dot_radius, pad_x, pad_y, line_width, edge_map
    )

    # Short leaders and target dots are drawn first; boxes remain on top.
    for placement in placements:
        (sx, sy), (tx, ty) = placement.leader
        draw.line((sx, sy, tx, ty), fill=(18, 24, 28, 235), width=line_width)
        draw.ellipse(
            (tx - dot_radius, ty - dot_radius, tx + dot_radius, ty + dot_radius),
            fill=(255, 255, 255, 245),
            outline=(18, 24, 28, 255),
            width=line_width,
        )

    for placement in placements:
        left, top, right, bottom = placement.box
        shadow = max(2, line_width)
        box_h = bottom - top
        draw.rounded_rectangle(
            (left + shadow, top + shadow, right + shadow, bottom + shadow),
            radius=box_h / 3,
            fill=(0, 0, 0, 75),
        )
        draw.rounded_rectangle(
            (left, top, right, bottom),
            radius=box_h / 3,
            fill=(255, 255, 255, 244),
            outline=(18, 24, 28, 255),
            width=line_width,
        )
        draw_bitmap_text(draw, (left + pad_x, top + pad_y), placement.text, glyph_scale)

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=False, compress_level=9)
    diagonal = math.hypot(width, height)
    old_lengths = [placement.old_length / diagonal for placement in placements]
    new_lengths = [placement.new_length / diagonal for placement in placements]
    metrics = {
        "id": item["id"],
        "preview": item["preview"],
        "calloutCount": len(placements),
        "legacyMeanLeaderLengthNormalized": round(sum(old_lengths) / len(old_lengths), 6),
        "resolvedMeanLeaderLengthNormalized": round(sum(new_lengths) / len(new_lengths), 6),
        "legacyMaxLeaderLengthNormalized": round(max(old_lengths), 6),
        "resolvedMaxLeaderLengthNormalized": round(max(new_lengths), 6),
        "legacyLeaderCrossings": crossing_count_segments([(placement.hint, placement.target) for placement in placements]),
        "resolvedLeaderCrossings": crossing_count(placements),
        "resolvedPositions": [
            {
                "id": placement.text,
                "target": [round(placement.target[0] / width, 6), round(placement.target[1] / height, 6)],
                "labelCenter": [round(placement.center[0] / width, 6), round(placement.center[1] / height, 6)],
            }
            for placement in placements
        ],
    }
    return output.getvalue(), metrics


def relative_output(item: dict) -> Path:
    path = Path(item["annotatedPreview"])
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Небезопасный annotatedPreview: {path}")
    if path.suffix.lower() != ".png" or path.parts[:2] != ("catalog", "annotated"):
        raise ValueError(f"annotatedPreview должен находиться в catalog/annotated и быть PNG: {path}")
    return path


def report_bytes(metrics: Sequence[dict]) -> bytes:
    old_total = sum(item["legacyMeanLeaderLengthNormalized"] * item["calloutCount"] for item in metrics)
    new_total = sum(item["resolvedMeanLeaderLengthNormalized"] * item["calloutCount"] for item in metrics)
    count = sum(item["calloutCount"] for item in metrics)
    report = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "version": "0.7.6",
        "purpose": "Deterministic compact placement of drawing ID callouts",
        "summary": {
            "drawingCount": len(metrics),
            "calloutCount": count,
            "legacyMeanLeaderLengthNormalized": round(old_total / count, 6) if count else 0.0,
            "resolvedMeanLeaderLengthNormalized": round(new_total / count, 6) if count else 0.0,
            "legacyLeaderCrossings": sum(item["legacyLeaderCrossings"] for item in metrics),
            "resolvedLeaderCrossings": sum(item["resolvedLeaderCrossings"] for item in metrics),
        },
        "drawings": list(metrics),
    }
    return (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def images_equal(actual_path: Path, expected: bytes) -> bool:
    try:
        with Image.open(actual_path) as actual_opened, Image.open(io.BytesIO(expected)) as expected_opened:
            actual = actual_opened.convert("RGB")
            expected_image = expected_opened.convert("RGB")
            return actual.size == expected_image.size and ImageChops.difference(actual, expected_image).getbbox() is None
    except OSError:
        return False


def run(check: bool) -> int:
    media = json.loads(MEDIA_PATH.read_text(encoding="utf-8"))
    items = expected_overlay_items(media)
    expected_paths = {ROOT / relative_output(item) for item in items}

    existing = set(OUTPUT_DIR.glob("*.png")) if OUTPUT_DIR.exists() else set()
    stale = sorted(existing - expected_paths)
    failures: list[str] = []

    if check and stale:
        failures.extend(f"Лишняя аннотированная копия: {path.relative_to(ROOT)}" for path in stale)
    elif not check:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for path in stale:
            path.unlink()

    metrics: list[dict] = []
    for item in items:
        output_path = ROOT / relative_output(item)
        expected, item_metrics = render(item)
        metrics.append(item_metrics)
        if check:
            if not output_path.is_file():
                failures.append(f"Не создана аннотированная копия: {output_path.relative_to(ROOT)}")
            elif not images_equal(output_path, expected):
                failures.append(
                    f"Аннотированная копия устарела: {output_path.relative_to(ROOT)}; "
                    "запустите mechanical/render_catalog_part_callouts_v075.py"
                )
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(expected)
            print(f"Rendered {output_path.relative_to(ROOT)}")

    expected_report = report_bytes(metrics)
    if check:
        if not REPORT_PATH.is_file() or REPORT_PATH.read_bytes() != expected_report:
            failures.append(
                f"Отчёт компоновки выносок устарел: {REPORT_PATH.relative_to(ROOT)}; "
                "запустите mechanical/render_catalog_part_callouts_v075.py"
            )
    else:
        REPORT_PATH.write_bytes(expected_report)
        print(f"Rendered {REPORT_PATH.relative_to(ROOT)}")

    if failures:
        print("Ошибки слоя выносок:\n- " + "\n- ".join(failures), file=sys.stderr)
        return 1

    report = json.loads(expected_report)
    summary = report["summary"]
    print(
        f"Проверено аннотированных чертежей: {len(items)}; "
        f"средняя нормированная длина выноски "
        f"{summary['legacyMeanLeaderLengthNormalized']:.4f} → "
        f"{summary['resolvedMeanLeaderLengthNormalized']:.4f}; "
        f"пересечений линий: {summary['legacyLeaderCrossings']} → {summary['resolvedLeaderCrossings']}"
    )
    return 0


def self_test() -> int:
    callouts = [
        {"id": "#petg-1", "target": [0.48, 0.48], "labelPosition": [0.03, 0.08]},
        {"id": "#petg-2", "target": [0.52, 0.50], "labelPosition": [0.03, 0.24]},
        {"id": "001", "target": [0.50, 0.44], "labelPosition": [0.78, 0.10]},
        {"id": "002", "target": [0.56, 0.54], "labelPosition": [0.78, 0.34]},
    ]
    width, height = 1200, 800
    placements = resolve_placements(callouts, width, height, 4, 6, 12, 8, 3)
    assert len(placements) == len(callouts)
    for placement in placements:
        assert 0 <= placement.box[0] < placement.box[2] <= width
        assert 0 <= placement.box[1] < placement.box[3] <= height
        assert placement.new_length < placement.old_length
    for index, first in enumerate(placements):
        for second in placements[index + 1:]:
            assert rect_overlap_area(first.box, second.box, margin=2) == 0
    assert crossing_count(placements) == 0
    print("Self-test compact callout placement: PASS")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="не записывать файлы, а проверить точное соответствие")
    parser.add_argument("--self-test", action="store_true", help="проверить геометрический resolver без файлов проекта")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.self_test:
            return self_test()
        return run(check=args.check)
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Не удалось обработать выноски: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
