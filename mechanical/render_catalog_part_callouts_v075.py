#!/usr/bin/env python3
"""Render stable part/component-ID callouts for every current 2D drawing.

The engineering SVG/PNG sources stay clean.  This script creates deterministic
annotated PNG companions under ``catalog/annotated`` from metadata stored in
``catalog/drawings.json``.  Print layouts are deliberately exempt because
labels can hide orientation, spacing and bed-clearance information.

Use:
    python mechanical/render_catalog_part_callouts_v075.py
    python mechanical/render_catalog_part_callouts_v075.py --check
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MEDIA_PATH = ROOT / "catalog" / "drawings.json"
OUTPUT_DIR = ROOT / "catalog" / "annotated"


# Tiny built-in 5×7 glyphs make the overlay pixel-stable on Windows and Linux.
# Only characters used by component/part IDs are included; human-readable names
# are rendered by HTML next to the drawing. No external font file is required.
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


def bitmap_size(text: str, scale: int) -> tuple[int, int]:
    if not text:
        return 0, 7 * scale
    return ((5 * len(text) + max(0, len(text) - 1)) * scale, 7 * scale)


def draw_bitmap_text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, scale: int) -> None:
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


def point(value: object, place: str) -> tuple[float, float]:
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


def render(item: dict) -> bytes:
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
    line_width = max(2, round(short_side * 0.004))
    dot_radius = max(4, round(short_side * 0.007))
    pad_x = max(7, 3 * glyph_scale)
    pad_y = max(4, 2 * glyph_scale)

    # Lines are drawn first, so every label remains readable above its leader.
    labels: list[tuple[str, tuple[float, float], tuple[float, float]]] = []
    for callout in item["callouts"]:
        target = point(callout["target"], "target")
        label_pos = point(callout["labelPosition"], "labelPosition")
        tx, ty = target[0] * width, target[1] * height
        lx, ly = label_pos[0] * width, label_pos[1] * height
        draw.line((lx, ly, tx, ty), fill=(18, 24, 28, 235), width=line_width)
        draw.ellipse(
            (tx - dot_radius, ty - dot_radius, tx + dot_radius, ty + dot_radius),
            fill=(255, 255, 255, 245),
            outline=(18, 24, 28, 255),
            width=line_width,
        )
        labels.append((str(callout["id"]), (lx, ly), (tx, ty)))

    for text, (lx, ly), _ in labels:
        text_w, text_h = bitmap_size(text, glyph_scale)
        box_w = text_w + 2 * pad_x
        box_h = text_h + 2 * pad_y
        left = max(2, min(width - box_w - 2, lx - box_w / 2))
        top = max(2, min(height - box_h - 2, ly - box_h / 2))
        right, bottom = left + box_w, top + box_h
        shadow = max(2, line_width)
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
        draw_bitmap_text(draw, (left + pad_x, top + pad_y), text, glyph_scale)

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def relative_output(item: dict) -> Path:
    path = Path(item["annotatedPreview"])
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Небезопасный annotatedPreview: {path}")
    if path.suffix.lower() != ".png" or path.parts[:2] != ("catalog", "annotated"):
        raise ValueError(f"annotatedPreview должен находиться в catalog/annotated и быть PNG: {path}")
    return path


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

    for item in items:
        output_path = ROOT / relative_output(item)
        expected = render(item)
        if check:
            if not output_path.is_file():
                failures.append(f"Не создана аннотированная копия: {output_path.relative_to(ROOT)}")
            else:
                try:
                    with Image.open(output_path) as actual_opened, Image.open(io.BytesIO(expected)) as expected_opened:
                        actual = actual_opened.convert("RGB")
                        expected_image = expected_opened.convert("RGB")
                        pixels_match = actual.size == expected_image.size and ImageChops.difference(actual, expected_image).getbbox() is None
                except OSError:
                    pixels_match = False
                if not pixels_match:
                    failures.append(
                        f"Аннотированная копия устарела: {output_path.relative_to(ROOT)}; "
                        "запустите mechanical/render_catalog_part_callouts_v075.py"
                    )
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(expected)
            print(f"Rendered {output_path.relative_to(ROOT)}")

    if failures:
        print("Ошибки слоя выносок:\n- " + "\n- ".join(failures), file=sys.stderr)
        return 1
    print(f"Проверено аннотированных чертежей: {len(items)}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="не записывать файлы, а проверить точное соответствие")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return run(check=args.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Не удалось обработать выноски: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
