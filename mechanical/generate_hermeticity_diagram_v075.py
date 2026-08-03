#!/usr/bin/env python3
"""Generate the current v0.7.6 weatherproofing overview as SVG and PNG."""
from pathlib import Path
import re

from resvg_py import svg_to_bytes

from generate_models_v06 import CURRENT_VERSION

ROOT = Path(__file__).resolve().parent
SVG = ROOT / "hermeticity_design_A4_landscape.svg"
PNG = ROOT / "hermeticity_design_A4_landscape.png"

BASE = '''<defs>
 <style>
 .title{font:700 6.4px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.sub{font:3.2px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}.h{font:700 4.2px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.t{font:3px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.small{font:2.65px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}.petg{fill:#ee8a3d;stroke:#98521f;stroke-width:.7}.tpu85{fill:#c2c9ce;stroke:#667178;stroke-width:.6}.metal{fill:#606c73;stroke:#222b30;stroke-width:.6}.nut{fill:#a5aaae;stroke:#252b2f;stroke-width:.65}.board{fill:#369662;stroke:#1c5f3d;stroke-width:.6}.window{fill:#92cceb;stroke:#316b8a;stroke-width:.5}.membrane{fill:#d9e6eb;stroke:#647a84;stroke-width:.5}.active{fill:#9ac8da;stroke:#416e80;stroke-width:.4}.glue{fill:#f0b13e;stroke:#9a6812;stroke-width:.45}.air{fill:none;stroke:#176b87;stroke-width:.7;stroke-dasharray:2 1}.note{fill:#fff;stroke:#c7d1d5;stroke-width:.45}.cut{fill:#fff6ef;stroke:#bd6b31;stroke-width:.55}
 </style>
</defs>'''

svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}
<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Герметичность электронного отсека, VEML7700 и климатического кармана</text>
<text x="148.5" y="16" text-anchor="middle" class="sub">проектные сечения v{CURRENT_VERSION}; независимые барьеры обслуживаются отдельно, подтверждённый IP-класс не заявляется</text>
<rect x="8" y="27" width="90" height="121" rx="4" class="note"/><rect x="103" y="27" width="90" height="121" rx="4" class="note"/><rect x="198" y="27" width="91" height="121" rx="4" class="note"/>
<text x="12" y="37" class="h">A. Крышка электронного бокса</text><text x="107" y="37" class="h">B. Тоннель и VEML7700</text><text x="202" y="37" class="h">C. Карман AHT20+BMP280</text>
<!-- lid -->
<rect x="22" y="58" width="62" height="13" rx="3" class="petg"/><path d="M25 71 V83 H29 V74 H77 V83 H81 V71" fill="none" stroke="#98521f" stroke-width="2"/><rect x="29" y="72" width="48" height="3" class="tpu85"/><rect x="32" y="75" width="42" height="53" class="petg" fill-opacity=".72"/>
<line x1="31" y1="52" x2="31" y2="83" class="metal"/><line x1="75" y1="52" x2="75" y2="83" class="metal"/><polygon points="27,78 31,76 35,78 35,82 31,84 27,82" class="nut"/><polygon points="71,78 75,76 79,78 79,82 75,84 71,82" class="nut"/>
<circle cx="53" cy="135" r="6" class="membrane"/><circle cx="53" cy="135" r="1.2" fill="#176b87"/><path d="M48 135 H42 M58 135 H64" class="air"/>
<text x="15" y="92" class="t">TPU85: 2,0 → 1,5 мм; сжатие 25%</text><text x="15" y="100" class="t">свес + юбка + внутренний язычок</text><text x="15" y="108" class="t">PETG-упоры ограничивают затяжку</text><text x="15" y="116" class="t">M3 и загрузочные пазы вне сухого контура</text><text x="15" y="144" class="small">отдельный нижний ePTFE vent электронного бокса</text>
<!-- tunnel -->
<rect x="132" y="55" width="18" height="15" class="petg"/><rect x="137" y="43" width="8" height="28" class="petg"/><rect x="134" y="69" width="14" height="3" class="petg"/><rect x="138" y="41" width="6" height="2" class="window"/><rect x="137" y="43" width="8" height="1.4" class="tpu85"/><line x1="141" y1="45" x2="141" y2="70" stroke="#fff" stroke-width="4.2"/><path d="M135 70 Q141 73 147 70" class="glue"/>
<rect x="125" y="81" width="32" height="19" rx="2" class="cut"/><rect x="132" y="86" width="18" height="8" class="board"/><polygon points="124,101 128,99 132,101 132,105 128,107 124,105" class="nut"/><polygon points="150,101 154,99 158,101 158,105 154,107 150,105" class="nut"/>
<text x="110" y="114" class="t">длина 15 мм; проход Ø4,2; поле ≈16,7°</text><text x="110" y="122" class="t">клеевая полка + резервуар Ø12,2–14,2</text><text x="110" y="130" class="t">съёмная опора платы на двух M3</text><text x="110" y="138" class="t">оптический канал не покрывается клеем</text>
<!-- climate pocket -->
<rect x="215" y="55" width="58" height="61" class="petg"/><rect x="220" y="61" width="48" height="43" class="cut"/><rect x="230" y="72" width="28" height="9" class="board"/><rect x="229" y="81" width="3" height="13" class="petg"/><rect x="256" y="81" width="3" height="13" class="petg"/><rect x="215" y="55" width="58" height="3" class="tpu85"/>
<circle cx="244" cy="113" r="10" class="membrane"/><circle cx="244" cy="113" r="5" class="active"/><g fill="#176b87"><circle cx="244" cy="113" r=".8"/><circle cx="244" cy="110" r=".8"/><circle cx="246.6" cy="111.5" r=".8"/><circle cx="246.6" cy="114.5" r=".8"/><circle cx="244" cy="116" r=".8"/><circle cx="241.4" cy="114.5" r=".8"/><circle cx="241.4" cy="111.5" r=".8"/></g>
<circle cx="265" cy="68" r="6" fill="#f6c39c" stroke="#98521f" stroke-width=".7"/><circle cx="265" cy="68" r="2.5" fill="#fff" stroke="#98521f" stroke-width=".6"/><polygon points="211,105 215,103 219,105 219,109 215,111 211,109" class="nut"/><polygon points="269,105 273,103 277,105 277,109 273,111 269,109" class="nut"/>
<text x="205" y="128" class="t">самоклеящаяся мембрана Ø20 / актив Ø10</text><text x="205" y="136" class="t">7 отверстий Ø2 + смещённая перегородка</text><text x="205" y="144" class="t">potting-well Ø8; корпус крепится двумя M3</text>
<!-- notes -->
<rect x="8" y="154" width="281" height="46" rx="3" class="note"/>
<text x="13" y="163" class="t">1. Ни один узел пока не имеет подтверждённого IP-класса: обязательны полив, конденсация, обдув и температурные циклы без питания.</text>
<text x="13" y="171" class="t">2. Крышка, световой тоннель и климатический карман не делят один герметик или одну прокладку: отказ одного барьера локализуется.</text>
<text x="13" y="179" class="t">3. Самоклеящаяся мембрана Ø20 клеится полным кольцом; активный центр Ø10 и семь вентиляционных отверстий не покрывать RTV.</text>
<text x="13" y="187" class="t">4. Окно VEML7700 герметизируется по периметру, а тоннель — только по отдельной внутренней клеевой полке; проход остаётся чистым.</text>
<text x="13" y="195" class="t">5. Все винты используют закладные M3/M4 вне сухих контуров; расположение и количество приведены на карте крепежа 124.</text>
</svg>'''

SVG.write_text(svg, encoding="utf-8")
render_source = re.sub(
    r'(<svg\b[^>]*?)width="[^"]+"\s+height="[^"]+"',
    r'\1width="3508" height="2480"',
    svg,
    count=1,
)
PNG.write_bytes(svg_to_bytes(svg_string=render_source))
print(f"Generated v{CURRENT_VERSION} {SVG.name} and {PNG.name}")
