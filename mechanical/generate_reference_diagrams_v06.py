#!/usr/bin/env python3
"""Generate the v0.7.3 part-ID table and twin-wire route diagrams.

Sources of truth:
- mechanical/part_id_registry_v06.json
- mechanical/generate_models_v06.py::Params

Outputs:
- mechanical/part_id_table_v06.svg / .png
- mechanical/flag_power_cable_route_A4_landscape.svg / .png
"""
from __future__ import annotations

from pathlib import Path
import json
import re

from generate_models_v06 import P

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "part_id_registry_v06.json"


def escape(value: object) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def wrap(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if len(candidate) > max_chars and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines[:2]


def generate_part_table() -> None:
    registry = json.loads(REGISTRY.read_text("utf-8"))
    rows: list[dict[str, str]] = []
    material_labels = {"petg": "PETG", "tpu95": "TPU 95A", "tpu85": "TPU 85A"}
    for group in ("petg", "tpu95", "tpu85"):
        for item in registry["groups"][group]:
            rows.append({
                "id": item["id"],
                "material": item.get("material", material_labels[group]),
                "label": item["label"],
                "qty": str(item.get("quantity", item.get("printQuantity", 1))),
                "description": item.get("description", ""),
                "stl": item["stl"].replace("mechanical/", ""),
            })

    width, height = 420, 297
    header_y = 29
    row_h = 10.7
    cols = [12, 45, 78, 160, 178, 302, 408]
    colors = {"PETG": "#e98638", "TPU 95A": "#8b949b", "TPU 85A": "#b9c1c8"}

    svg = [f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" fill="#f4f5f6"/>
<text x="{width/2}" y="16" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="8" font-weight="700" fill="#172126">Таблица идентификаторов печатных деталей v0.7.3</text>
<text x="{width/2}" y="22" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="4" fill="#52616a">Одинаковая деталь сохраняет один и тот же ID на всех актуальных чертежах</text>
<rect x="{cols[0]}" y="{header_y}" width="{cols[-1]-cols[0]}" height="9" rx="1.5" fill="#193f46"/>
''']
    for index, title in enumerate(["ID", "Материал", "Деталь", "Кол-во", "Назначение", "STL-файл"]):
        svg.append(f'<text x="{cols[index]+2}" y="{header_y+6}" font-family="DejaVu Sans,Arial,sans-serif" font-size="4.3" font-weight="700" fill="#fff">{escape(title)}</text>')

    y = header_y + 9
    for index, row in enumerate(rows):
        fill = "#ffffff" if index % 2 == 0 else "#e9edef"
        svg.append(f'<rect x="{cols[0]}" y="{y}" width="{cols[-1]-cols[0]}" height="{row_h}" fill="{fill}" stroke="#c7d0d4" stroke-width="0.35"/>')
        svg.append(f'<rect x="{cols[1]+1}" y="{y+1.2}" width="5" height="{row_h-2.4}" rx="1" fill="{colors[row["material"]]}" stroke="#6e777d" stroke-width="0.25"/>')
        values = [row["id"], row["material"], row["label"], row["qty"], row["description"], row["stl"]]
        limits = [14, 18, 30, 5, 48, 42]
        for column, value in enumerate(values):
            lines = wrap(value, limits[column])
            x = cols[column] + (8 if column == 1 else 2)
            if column == 3:
                x = cols[column] + 4
            for line_index, line in enumerate(lines):
                font_size = 3.6 if column not in (4, 5) else (3.0 if column == 4 else 2.8)
                weight = "700" if column == 0 else "400"
                svg.append(f'<text x="{x}" y="{y+4.5+line_index*3.8}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{font_size}" font-weight="{weight}" fill="#172126">{escape(line)}</text>')
        for column_x in cols[1:-1]:
            svg.append(f'<line x1="{column_x}" y1="{y}" x2="{column_x}" y2="{y+row_h}" stroke="#c7d0d4" stroke-width="0.35"/>')
        y += row_h

    footer_y = height - 15
    svg.append(f'<rect x="12" y="{footer_y}" width="396" height="10" rx="2" fill="#fff" stroke="#c7d0d4" stroke-width="0.4"/>')
    legend = [
        ("PETG", "#e98638", "жёсткие детали; текущая чистовая печать"),
        ("TPU 95A", "#8b949b", "втулки, демпферы и разгрузки"),
        ("TPU 85A", "#b9c1c8", "мягкие статические уплотнения"),
    ]
    x = 18
    for name, color, description in legend:
        svg.append(f'<rect x="{x}" y="{footer_y+2}" width="5" height="6" rx="1" fill="{color}" stroke="#555" stroke-width="0.25"/>')
        svg.append(f'<text x="{x+7}" y="{footer_y+4.2}" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.4" font-weight="700" fill="#172126">{name}</text>')
        svg.append(f'<text x="{x+7}" y="{footer_y+7.8}" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.0" fill="#52616a">{description}</text>')
        x += 130
    svg.append("</svg>")

    svg_path = ROOT / "part_id_table_v06.svg"
    png_path = ROOT / "part_id_table_v06.png"
    svg_path.write_text("\n".join(svg), "utf-8")
    render_png(svg_path, png_path, 2480, 1754)


def generate_cable_route() -> None:
    width, height = 297, 210
    sx0, sx1, sz0, sz1 = -80, 90, 0, 60
    bx0, bx1, by0, by1 = 12, 143, 42, 148
    sx = lambda x: bx0 + (x-sx0)/(sx1-sx0)*(bx1-bx0)
    sy = lambda z: by1 - (z-sz0)/(sz1-sz0)*(by1-by0)
    tx0, tx1, ty0, ty1 = -80, 90, -28, 28
    tbx0, tbx1, tby0, tby1 = 154, 285, 42, 148
    tx = lambda x: tbx0 + (x-tx0)/(tx1-tx0)*(tbx1-tbx0)
    ty = lambda y: tby1 - (y-ty0)/(ty1-ty0)*(tby1-tby0)

    route = [tuple(point) for point in P.external_cable_route_points]
    route += [(-18.0, 0.0, P.flag_cable_center_z), (-28.0, -5.0, P.flag_cable_center_z + 4.0)]

    svg = [f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">
<defs><marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#176b87"/></marker></defs>
<rect width="{width}" height="{height}" fill="#f4f5f6"/>
<text x="148.5" y="11" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="6.6" font-weight="700" fill="#172126">Маршрут двух проводов питания флага v0.7.3</text>
<text x="148.5" y="18" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="4.6" fill="#52616a">герморазъём → наружная открытая канавка → TPU95-ввод у электронного бокса</text>
<text x="77" y="31" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="5" font-weight="700" fill="#1f4c55">Вид сбоку</text>
<text x="220" y="31" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="5" font-weight="700" fill="#1f4c55">Вид сверху</text>
''']
    # Side view.
    svg.append(f'<rect x="{sx(P.pod_x_min)}" y="{sy(P.pod_z_max)}" width="{sx(P.pod_x_max)-sx(P.pod_x_min)}" height="{sy(P.pod_z_min)-sy(P.pod_z_max)}" rx="2" fill="#ee9958" stroke="#9b5728" stroke-width="0.7"/>')
    svg.append(f'<rect x="{sx(-2)}" y="{sy(60)}" width="{sx(2)-sx(-2)}" height="{sy(0)-sy(60)}" fill="#4f5961"/>')
    svg.append(f'<rect x="{sx(P.arm_x_min)}" y="{sy(P.arm_z_max)}" width="{sx(P.arm_x_max)-sx(P.arm_x_min)}" height="{sy(P.arm_z_min)-sy(P.arm_z_max)}" rx="2" fill="#ee9958" stroke="#9b5728" stroke-width="0.7"/>')
    svg.append(f'<line x1="{sx(P.spoke_insert_x_min)}" y1="{sy(P.spoke_center_z)}" x2="{sx(90)}" y2="{sy(P.spoke_center_z)}" stroke="#20272c" stroke-width="2.5"/>')
    svg.append(f'<text x="{sx(47)}" y="{sy(P.spoke_center_z)-3}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.7" fill="#20272c">спица Ø{P.spoke_diameter:g} мм</text>')
    side_points = " ".join(f'{sx(x)},{sy(z)}' for x, _, z in route)
    svg.append(f'<polyline points="{side_points}" fill="none" stroke="#176b87" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arr)"/>')
    svg.append(f'<rect x="{sx(76)}" y="{sy(21)}" width="{sx(88)-sx(76)}" height="{sy(15)-sy(21)}" rx="1.5" fill="#39434a" stroke="#111" stroke-width="0.5"/>')
    svg.append(f'<text x="{sx(82)}" y="{sy(11)}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.1" fill="#172126">герморазъём</text>')
    svg.append(f'<line x1="{sx(61)}" y1="{sy(P.spoke_center_z)}" x2="{sx(61)}" y2="{sy(P.flag_cable_center_z)}" stroke="#9b4d00" stroke-width="0.8" marker-end="url(#arr)"/>')
    svg.append(f'<text x="{sx(64)}" y="{(sy(P.spoke_center_z)+sy(P.flag_cable_center_z))/2-1}" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.0" fill="#9b4d00">≈{P.spoke_center_z-P.flag_cable_center_z:g} мм ниже</text>')
    svg.append(f'<text x="{sx(40)}" y="{sy(15)+5}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.2" fill="#176b87">канавка Ø{P.external_cable_groove_radius*2:g} мм открыта наружу</text>')
    svg.append(f'<text x="{sx(-42)}" y="{sy(7)}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.2" fill="#172126">электронный бокс</text>')

    # Top view.
    svg.append(f'<rect x="{tx(P.pod_x_min)}" y="{ty(P.pod_y_half)}" width="{tx(P.pod_x_max)-tx(P.pod_x_min)}" height="{ty(-P.pod_y_half)-ty(P.pod_y_half)}" rx="2" fill="#ee9958" stroke="#9b5728" stroke-width="0.7"/>')
    svg.append(f'<circle cx="{tx(0)}" cy="{ty(0)}" r="{tx(P.body_radius)-tx(0)}" fill="#ee9958" stroke="#9b5728" stroke-width="0.7"/>')
    svg.append(f'<rect x="{tx(P.arm_x_min)}" y="{ty(P.arm_half_width)}" width="{tx(P.arm_x_max)-tx(P.arm_x_min)}" height="{ty(-P.arm_half_width)-ty(P.arm_half_width)}" rx="2" fill="#ee9958" stroke="#9b5728" stroke-width="0.7"/>')
    top_points = " ".join(f'{tx(x)},{ty(y)}' for x, y, _ in route)
    svg.append(f'<polyline points="{top_points}" fill="none" stroke="#176b87" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arr)"/>')
    for x, y, _ in route[:5]:
        svg.append(f'<circle cx="{tx(x)}" cy="{ty(y)}" r="1.4" fill="#fff" stroke="#176b87" stroke-width="0.7"/>')
    svg.append(f'<rect x="{tx(P.flag_cable_x_min)}" y="{ty(4)}" width="{tx(P.flag_cable_x_max)-tx(P.flag_cable_x_min)}" height="{ty(-4)-ty(4)}" rx="1" fill="#9ba4aa" stroke="#4f5961" stroke-width="0.5"/>')
    svg.append(f'<text x="{tx(-29)}" y="{ty(-8)}" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.0" fill="#172126">ввод через</text>')
    svg.append(f'<text x="{tx(-29)}" y="{ty(-11)}" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.0" font-weight="700" fill="#172126">#tpu95-3 / #tpu95-4</text>')
    svg.append(f'<text x="219" y="155" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.05" fill="#176b87">маршрут проходит снаружи;</text>')
    svg.append(f'<text x="219" y="159" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.05" fill="#176b87">подшипники и спица не пересекаются</text>')

    box_y = 164
    svg.append(f'<rect x="12" y="{box_y}" width="273" height="34" rx="3" fill="#fff" stroke="#c3cdd2" stroke-width="0.5"/>')
    notes = [
        "1. Герметичный 2-контактный разъём расположен у флага ниже спицы.",
        f"2. Кабель Ø≈{P.flag_cable_inner_diameter:g} мм укладывается в открытую наружную канавку радиусом {P.external_cable_groove_radius:g} мм.",
        "3. Канавка огибает корпус снаружи и не ослабляет подшипниковые посадки.",
        "4. Вход в бокс расположен у его флаговой стенки и уплотнён разрезной TPU95-разгрузкой.",
        "5. Внутри оставить короткую сервисную петлю до клеммы/MOSFET. Размеры уточнить по фактическим кабелю и разъёму.",
    ]
    for index, note in enumerate(notes):
        svg.append(f'<text x="17" y="{box_y+6+index*5.2}" font-family="DejaVu Sans,Arial,sans-serif" font-size="3.4" fill="#172126">{escape(note)}</text>')
    svg.append("</svg>")

    svg_path = ROOT / "flag_power_cable_route_A4_landscape.svg"
    png_path = ROOT / "flag_power_cable_route_A4_landscape.png"
    svg_path.write_text("\n".join(svg), "utf-8")
    render_png(svg_path, png_path, 3508, 2480)


def render_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    try:
        from resvg_py import svg_to_bytes
    except ImportError as exc:
        raise SystemExit(
            "Для PNG нужен resvg-py из mechanical/requirements.txt; "
            "SVG уже создан как основной редактируемый источник"
        ) from exc
    svg_source = svg_path.read_text("utf-8")
    svg_source = re.sub(
        r'(<svg\b[^>]*?)width="[^"]+"\s+height="[^"]+"',
        rf'\1width="{width}" height="{height}"',
        svg_source,
        count=1,
    )
    png_path.write_bytes(svg_to_bytes(
        svg_string=svg_source,
        background="#f4f5f6",
        text_rendering="optimize_legibility",
    ))


def main() -> None:
    generate_part_table()
    generate_cable_route()
    print("Generated part ID table and flag power cable route diagrams.")


if __name__ == "__main__":
    main()
