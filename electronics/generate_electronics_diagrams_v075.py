#!/usr/bin/env python3
"""Generate current v0.7.6 electronics SVG/PNG diagrams.

The diagrams intentionally start at the stabilized 12 V input boundary. The
6x18650 topology, BMS and charger remain outside the Crucian finial project.
"""
from pathlib import Path
import html
import re

from resvg_py import svg_to_bytes

CURRENT_VERSION = '0.7.6'

ROOT = Path(__file__).resolve().parent


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def svg_to_png(svg_path: Path, png_path: Path) -> None:
    svg = svg_path.read_text(encoding="utf-8")
    svg = re.sub(
        r'(<svg\b[^>]*?)width="[^"]+"\s+height="[^"]+"',
        r'\1width="3508" height="2480"',
        svg,
        count=1,
    )
    png_path.write_bytes(svg_to_bytes(svg_string=svg))


def box(x, y, w, h, title, lines=(), cls="module") -> str:
    body = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" class="{cls}"/>',
            f'<text x="{x+w/2}" y="{y+8}" text-anchor="middle" class="bh">{esc(title)}</text>']
    for index, line in enumerate(lines):
        body.append(f'<text x="{x+4}" y="{y+16+index*5}" class="bt">{esc(line)}</text>')
    return "\n".join(body)


def arrow(x1, y1, x2, y2, label="", cls="wire") -> str:
    out = [f'<path d="M{x1} {y1} L{x2} {y2}" class="{cls}" marker-end="url(#arrow)"/>']
    if label:
        tx=(x1+x2)/2; ty=(y1+y2)/2-2
        out.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" class="lab">{esc(label)}</text>')
    return "\n".join(out)


def wiring() -> None:
    W,H=297,210
    parts=[f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">
<defs>
 <marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#34535c"/></marker>
 <style>
 .title{{font:700 7px 'DejaVu Sans',Arial,sans-serif;fill:#172126}}.sub{{font:3.4px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}}
 .module{{fill:#fff;stroke:#4a6972;stroke-width:.7}}.power{{fill:#fff1e4;stroke:#a95619;stroke-width:.8}}.sensor{{fill:#e9f5ef;stroke:#26714d;stroke-width:.7}}.load{{fill:#fff9d9;stroke:#94751a;stroke-width:.7}}.boundary{{fill:#eef1f3;stroke:#7b8b92;stroke-width:.7;stroke-dasharray:2 1}}
 .bh{{font:700 4px 'DejaVu Sans',Arial,sans-serif;fill:#172126}}.bt{{font:3px 'DejaVu Sans',Arial,sans-serif;fill:#26343a}}.lab{{font:2.8px 'DejaVu Sans',Arial,sans-serif;fill:#1d4f5e}}
 .wire{{fill:none;stroke:#34535c;stroke-width:1.05}}.wire12{{fill:none;stroke:#d45d00;stroke-width:1.25}}.gnd{{fill:none;stroke:#20272c;stroke-width:1.15}}.i2c{{fill:none;stroke:#237d61;stroke-width:1.0}}.pwm{{fill:none;stroke:#8a2f6c;stroke-width:1.0}}
 .note{{font:3px 'DejaVu Sans',Arial,sans-serif;fill:#172126}}.warn{{font:700 3px 'DejaVu Sans',Arial,sans-serif;fill:#8b3f00}}
 </style>
</defs>
<rect width="{W}" height="{H}" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Crucian v{CURRENT_VERSION} — актуальная схема соединений электроники</text>
<text x="148.5" y="16" text-anchor="middle" class="sub">внешний аккумуляторный блок заканчивается стабилизированным входом 12 В; измерения напряжения аккумулятора в проекте нет</text>
''']
    parts.append(box(8,28,42,28,"Внешняя подсистема",["6 × 18650","BMS / заряд / 12 В стабилизатор","вне границ Crucian"],"boundary"))
    parts.append(box(60,28,42,28,"Ввод в шток",["предохранитель по току ленты","2 жилы: +12 В / GND","проверить под нагрузкой"],"power"))
    parts.append(box(112,28,42,28,"M125-0205",["статор в штоке","ротор во вращающейся части","2 канала; ток проверить"],"module"))
    parts.append(box(164,25,48,34,"12 В STAR",["+12 В: неон, DC-DC, C1","GND: DC-DC, MOSFET Source","C1 1000–2200 µF / 25 В"],"power"))
    parts.append(box(224,28,60,28,"DC-DC 12 → 5 В",["5 В на ESP32-C3","GND общий с силовой частью","выход проверить до подключения"],"power"))
    parts.append(arrow(50,42,60,42,"стаб. 12 В","wire12"))
    parts.append(arrow(102,42,112,42,"2 жилы","wire12"))
    parts.append(arrow(154,42,164,42,"+12/GND","wire12"))
    parts.append(arrow(212,42,224,42,"12 В","wire12"))

    parts.append(box(105,78,58,42,"ESP32-C3 Mini Plus",["5V / GND от DC-DC","GPIO3 = PWM","GPIO4 = SDA","GPIO5 = SCL","BLE имя из project_identity.json"],"module"))
    parts.append(arrow(254,56,163,78,"5 В + GND","wire"))

    parts.append(box(15,84,62,34,"VEML7700",["3,3 В / GND","SDA GPIO4 / SCL GPIO5","освещённость + fail-safe","калибровка через BLE"],"sensor"))
    parts.append(box(15,132,62,34,"AHT20 + BMP280",["3,3 В / GND","общая I²C-шина","AHT20: 0x38","BMP280: 0x76 / 0x77"],"sensor"))
    parts.append(arrow(105,95,77,99,"3,3 В + I²C","i2c"))
    parts.append(arrow(105,109,77,149,"3,3 В + I²C","i2c"))

    parts.append(box(176,82,48,38,"LR7843 MOSFET",["низкобоковый ключ","Gate: GPIO3 через 100 Ω","Gate → GND: 100 kΩ","Source → GND STAR"],"module"))
    parts.append(arrow(163,94,176,94,"PWM GPIO3","pwm"))
    parts.append(box(236,84,48,34,"Герморазъём J1",["2 pin, внешний","Pin +: +12 В STAR","Pin −: Drain MOSFET","под спицей у флага"],"module"))
    parts.append(arrow(212,59,260,84,"+12 В напрямую","wire12"))
    parts.append(arrow(224,101,236,101,"LOAD−","gnd"))
    parts.append(box(224,137,60,30,"XUNATA 12 В Ø16",["одноцветный круглый неон","по контуру рыбы","ток и нагрев измерить"],"load"))
    parts.append(arrow(260,118,254,137,"2 провода","wire12"))

    parts.append('<rect x="8" y="174" width="276" height="30" rx="3" fill="#fff" stroke="#c6d0d4" stroke-width=".5"/>')
    notes=[
        "1. Никакого BAT/ADC: приложение и прошивка не показывают фиктивное напряжение аккумулятора.",
        "2. Цвета проводов M125 и разъёма фиксируются только после прозвонки реальных деталей.",
        "3. +12 В неона не коммутируется; MOSFET коммутирует только минус. Иначе PWM работать не будет.",
        "4. I²C-модули питаются от 3,3 В. Проверить, к какому напряжению подключены их встроенные подтяжки.",
        "5. Механические M3/M4-закладные, каркас плат и кабельная трасса показаны на чертежах 124 и 125.",
    ]
    for i,n in enumerate(notes): parts.append(f'<text x="13" y="{181+i*4.0}" class="note">{esc(n)}</text>')
    parts.append('</svg>')
    svg=ROOT/'electronics_wiring_diagram_A4.svg'; png=ROOT/'electronics_wiring_diagram_A4.png'
    svg.write_text("\n".join(parts),'utf-8'); svg_to_png(svg,png)


def terminal_map() -> None:
    W,H=297,210
    rows=[
        ("Вход Crucian", "+12 В", "стабилизированные 12 В после внешней 6×18650-подсистемы"),
        ("Вход Crucian", "GND", "общий минус; второй канал через M125"),
        ("M125-0205", "канал A", "+12 В; цвет определить прозвонкой"),
        ("M125-0205", "канал B", "GND; цвет определить прозвонкой"),
        ("DC-DC", "VIN+ / VIN−", "+12 В STAR / GND STAR"),
        ("DC-DC", "VOUT+ / VOUT−", "5 В / GND на ESP32-C3"),
        ("ESP32-C3", "GPIO3", "PWM → 100 Ω → Gate LR7843"),
        ("ESP32-C3", "GPIO4", "SDA общей I²C-шины"),
        ("ESP32-C3", "GPIO5", "SCL общей I²C-шины"),
        ("ESP32-C3", "3V3", "питание VEML7700 и AHT20+BMP280"),
        ("VEML7700", "VIN/GND/SDA/SCL", "3,3 В / GND / GPIO4 / GPIO5"),
        ("AHT20+BMP280", "VDD/GND/SDA/SCL", "3,3 В / GND / GPIO4 / GPIO5"),
        ("LR7843", "Source", "GND STAR"),
        ("LR7843", "Drain", "J1 Pin − → минус неона"),
        ("LR7843", "Gate", "GPIO3 через 100 Ω; 100 kΩ на GND"),
        ("J1 2-pin", "Pin +", "+12 В STAR → плюс неона"),
        ("J1 2-pin", "Pin −", "Drain LR7843 → минус неона"),
    ]
    parts=[f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">
<style>.title{{font:700 7px 'DejaVu Sans',Arial,sans-serif;fill:#172126}}.sub{{font:3.3px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}}.th{{font:700 3.6px 'DejaVu Sans',Arial,sans-serif;fill:white}}.td{{font:3.1px 'DejaVu Sans',Arial,sans-serif;fill:#172126}}.note{{font:3px 'DejaVu Sans',Arial,sans-serif;fill:#172126}}</style>
<rect width="{W}" height="{H}" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Crucian v{CURRENT_VERSION} — карта клемм, GPIO и разъёмов</text>
<text x="148.5" y="16" text-anchor="middle" class="sub">карта функциональная: физические цвета M125, J1 и маркировки китайских модулей подтверждаются прозвонкой</text>
<rect x="10" y="24" width="277" height="9" rx="2" fill="#234f59"/>
<text x="14" y="30" class="th">Узел</text><text x="67" y="30" class="th">Контакт</text><text x="116" y="30" class="th">Назначение</text>
''']
    y=33; row_h=7.5
    for i,(node,pin,purpose) in enumerate(rows):
        fill='#ffffff' if i%2==0 else '#eaf0f2'
        parts.append(f'<rect x="10" y="{y}" width="277" height="{row_h}" fill="{fill}" stroke="#ccd5d9" stroke-width=".3"/>')
        parts.append(f'<line x1="63" y1="{y}" x2="63" y2="{y+row_h}" stroke="#ccd5d9" stroke-width=".3"/>')
        parts.append(f'<line x1="112" y1="{y}" x2="112" y2="{y+row_h}" stroke="#ccd5d9" stroke-width=".3"/>')
        parts.append(f'<text x="14" y="{y+4.9}" class="td">{esc(node)}</text>')
        parts.append(f'<text x="67" y="{y+4.9}" class="td">{esc(pin)}</text>')
        parts.append(f'<text x="116" y="{y+4.9}" class="td">{esc(purpose)}</text>')
        y+=row_h
    parts.append(f'<rect x="10" y="{y+5}" width="277" height="31" rx="3" fill="#fff" stroke="#ccd5d9" stroke-width=".5"/>')
    notes=[
      "Монтажная проверка: сначала прозвонить M125 и J1; затем проверить DC-DC без ESP; после этого подключать датчики и MOSFET.",
      "Герметичный J1 находится снаружи у флага. От него два провода идут по открытой обслуживаемой дорожке ниже спицы.",
      "Единственный ввод в сухой электронный бокс — TPU95-манжета #tpu95-3/#tpu95-4; внутри оставить сервисную петлю 30–40 мм.",
      "Значения 3,3 В, GPIO3/4/5 и адреса датчиков являются текущей схемой прошивки v0.7.6.",
      "Полярность конкретного MOSFET-модуля и возможность прямой пайки к Gate подтвердить по реальной плате.",
      "Механическое крепление модулей и все закладные M3/M4 показаны на чертежах 124 и 125.",
    ]
    for i,n in enumerate(notes): parts.append(f'<text x="15" y="{y+12+i*4.5}" class="note">{esc(n)}</text>')
    parts.append('</svg>')
    svg=ROOT/'electronics_terminal_map_A4.svg'; png=ROOT/'electronics_terminal_map_A4.png'
    svg.write_text("\n".join(parts),'utf-8'); svg_to_png(svg,png)


if __name__ == '__main__':
    wiring(); terminal_map(); print(f'Generated v{CURRENT_VERSION} electronics diagrams.')
