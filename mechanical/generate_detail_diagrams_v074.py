#!/usr/bin/env python3
"""Generate current v0.7.4 mechanical technical diagrams as SVG and PNG."""
from pathlib import Path
import html
import re

from resvg_py import svg_to_bytes

from generate_models_v06 import CURRENT_VERSION, P, flag_loop_top_offsets

ROOT=Path(__file__).resolve().parent


def e(value):
    return html.escape(str(value), quote=True)


def png(svg: Path, out: Path):
    source = svg.read_text(encoding="utf-8")
    source = re.sub(
        r'(<svg\b[^>]*?)width="[^"]+"\s+height="[^"]+"',
        r'\1width="3508" height="2480"',
        source,
        count=1,
    )
    out.write_bytes(svg_to_bytes(svg_string=source))


BASE='''<defs>
 <marker id="arr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#176b87"/></marker>
 <marker id="dimarr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="#176b87"/></marker>
 <style>.title{font:700 7px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.sub{font:3.4px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}.h{font:700 4.4px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.t{font:3.1px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.small{font:2.8px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}.dim{font:700 3px 'DejaVu Sans',Arial,sans-serif;fill:#176b87}.petg{fill:#ee8a3d;stroke:#98521f;stroke-width:.7}.tpu95{fill:#929ca3;stroke:#4f5a61;stroke-width:.6}.tpu85{fill:#c2c9ce;stroke:#667178;stroke-width:.6}.metal{fill:#606c73;stroke:#222b30;stroke-width:.6}.nut{fill:#a5aaae;stroke:#252b2f;stroke-width:.65}.board{fill:#369662;stroke:#1c5f3d;stroke-width:.6}.esp{fill:#b44242;stroke:#6d2222;stroke-width:.6}.mos{fill:#4f65a9;stroke:#2c3868;stroke-width:.6}.buck{fill:#369662;stroke:#1c5f3d;stroke-width:.6}.window{fill:#92cceb;stroke:#316b8a;stroke-width:.5}.membrane{fill:#d9e6eb;stroke:#647a84;stroke-width:.5}.active{fill:#9ac8da;stroke:#416e80;stroke-width:.4}.air{fill:none;stroke:#176b87;stroke-width:.7;stroke-dasharray:2 1}.arrow{fill:none;stroke:#176b87;stroke-width:.8;marker-end:url(#arr)}.dimension{fill:none;stroke:#176b87;stroke-width:.7;marker-start:url(#dimarr);marker-end:url(#dimarr)}.note{fill:#fff;stroke:#c7d1d5;stroke-width:.45}.cut{fill:#fff6ef;stroke:#bd6b31;stroke-width:.55}.wire{fill:none;stroke:#23282c;stroke-width:1.4}.wire2{fill:none;stroke:#4d555a;stroke-width:1.4}.glue{fill:#f0b13e;stroke:#9a6812;stroke-width:.45}</style>
</defs>'''


def write(name, content):
    svg=ROOT/f'{name}.svg'
    out=ROOT/f'{name}.png'
    svg.write_text(content,'utf-8')
    png(svg,out)


def hex_points(cx,cy,r):
    import math
    return ' '.join(f'{cx+r*math.cos(math.radians(60*i-30)):.2f},{cy+r*math.sin(math.radians(60*i-30)):.2f}' for i in range(6))


def longitudinal():
    loop_offsets=flag_loop_top_offsets()
    # Display flag is 80 mm tall; convert real offsets proportionally.
    flag_y=70
    flag_h=80
    loop_ys=[flag_y+off/P.flag_height*flag_h for off in loop_offsets]
    loop_paths=''.join(
        f'<path d="M176 {y:.2f} H151 Q139 {y:.2f} 139 {y+3.2:.2f} Q139 {y+6.4:.2f} 151 {y+6.4:.2f} H176"/>'
        for y in loop_ys
    )
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Crucian v{CURRENT_VERSION} — актуальная продольная схема узлов</text>
<text x="148.5" y="16" text-anchor="middle" class="sub">компоновочная схема; посадки, провода, гайки и платы подтверждаются измерениями и купонами</text>
<!-- pole and rotor -->
<rect x="78" y="39" width="18" height="136" rx="4" class="metal"/><rect x="83" y="39" width="8" height="136" fill="#f5f6f7" stroke="#222b30" stroke-width=".4"/>
<rect x="61" y="48" width="52" height="72" rx="15" class="petg" fill-opacity=".65"/>
<rect x="69" y="56" width="36" height="8" rx="2" class="metal"/><rect x="69" y="101" width="36" height="8" rx="2" class="metal"/>
<text x="116" y="62" class="t">верхний 6804-2RS</text><text x="116" y="107" class="t">нижний 6804-2RS</text>
<rect x="88" y="66" width="3" height="33" class="metal"/><text x="94" y="84" class="small">распорка внутренних колец</text>
<!-- spoke -->
<rect x="88" y="81" width="88" height="5" rx="2.5" fill="#22282c"/><rect x="104" y="76" width="13" height="15" class="tpu95"/>
<text x="119" y="70" class="dim">спица Ø5 мм между подшипниками</text><path d="M132 76 L132 81" class="arrow"/>
<!-- flag and loops -->
<rect x="176" y="{flag_y}" width="95" height="{flag_h}" fill="#c96931" stroke="#873d1a" stroke-width=".7"/><line x1="176" y1="{flag_y}" x2="271" y2="{flag_y+flag_h}" stroke="#9f4b20"/>
<g fill="none" stroke="#e26e25" stroke-width="4">{loop_paths}</g>
<line x1="176" y1="58.8" x2="271" y2="58.8" stroke="#c9362b" stroke-width=".8" stroke-dasharray="2 1"/><text x="181" y="56" class="small">нижняя кромка навершия</text>
<line x1="171" y1="58.8" x2="171" y2="{loop_ys[0]:.2f}" class="dimension"/><text x="165" y="{(58.8+loop_ys[0])/2:.2f}" class="dim" transform="rotate(-90 165 {(58.8+loop_ys[0])/2:.2f})">10 мм</text>
<text x="185" y="158" class="small">верхняя лямка привязана к низу навершия, не к верху полотна</text>
<!-- M125 -->
<rect x="84" y="43" width="6" height="13" rx="2" fill="#343a3e"/><rect x="85.5" y="39" width="3" height="5" fill="#343a3e"/><text x="45" y="43" class="t">M125-0205 внутри полого штока</text><path d="M73 44 H84" class="arrow"/>
<!-- electronics pod and carrier -->
<rect x="12" y="51" width="53" height="9" rx="2" class="petg"/><rect x="16" y="57" width="45" height="53" rx="4" class="petg"/><rect x="18" y="59" width="41" height="3" class="tpu85"/>
<rect x="20" y="78" width="37" height="25" rx="2" fill="#f6c39c" stroke="#98521f" stroke-width=".5"/><rect x="24" y="91" width="27" height="8" class="buck"/><rect x="24" y="72" width="5" height="18" class="esp"/><rect x="48" y="72" width="5" height="16" class="mos"/>
<text x="18" y="114" class="small">#petg-9: DC-DC снизу; ESP и MOSFET вертикально</text>
<!-- photo tunnel -->
<rect x="28" y="36" width="11" height="15" class="petg"/><rect x="25.5" y="49" width="16" height="3" class="petg"/><rect x="29.5" y="34" width="8" height="2" class="window"/><rect x="26.5" y="48.4" width="14" height="1" class="glue"/><rect x="21" y="60" width="25" height="12" rx="2" class="cut"/><rect x="25" y="63" width="17" height="7" class="board"/>
<polygon points="23,73 27,71 31,73 31,77 27,79 23,77" class="nut"/><polygon points="38,73 42,71 46,73 46,77 42,79 38,77" class="nut"/>
<text x="13" y="30" class="t">тоннель 15 мм, отдельная клеевая полка</text>
<!-- climate pocket -->
<rect x="20" y="119" width="38" height="25" class="petg"/><rect x="22" y="121" width="34" height="2" class="tpu85"/><rect x="30" y="128" width="18" height="7" class="board"/><circle cx="39" cy="143" r="8.8" class="membrane"/><circle cx="39" cy="143" r="4.4" class="active"/>
<g fill="#176b87"><circle cx="39" cy="143" r=".8"/><circle cx="39" cy="140.2" r=".8"/><circle cx="41.4" cy="141.6" r=".8"/><circle cx="41.4" cy="144.4" r=".8"/><circle cx="39" cy="145.8" r=".8"/><circle cx="36.6" cy="144.4" r=".8"/><circle cx="36.6" cy="141.6" r=".8"/></g>
<text x="16" y="156" class="small">самоклеящаяся мембрана Ø20; активный центр Ø10</text><text x="16" y="162" class="small">семь вентиляционных отверстий Ø2 мм</text>
<!-- external wires and guide -->
<path d="M174 96 L164 103 C150 110 137 121 113 126 C94 131 72 126 60 112" class="wire"/><path d="M174 99 L164 106 C150 113 137 124 113 129 C94 134 72 129 60 115" class="wire2"/>
<line x1="164" y1="103" x2="174" y2="96" stroke="#929ca3" stroke-width="6" stroke-linecap="round"/><text x="145" y="97" class="dim">#tpu95-10 ≈35° вниз</text>
<polygon points="133,105 137,103 141,105 141,109 137,111 133,109" class="nut"/><text x="119" y="117" class="small">M4 выше трассы</text>
<text x="101" y="140" class="dim">два провода Ø2 мм; просвет 4,2 мм; борта 2,5 мм</text>
<!-- notes -->
<rect x="12" y="166" width="273" height="32" rx="3" class="note"/>
<text x="17" y="174" class="t">1. Все винтовые соединения используют обслуживаемые закладные M4/M3; полный перечень приведён на карте крепежа 124.</text>
<text x="17" y="180" class="t">2. Кабель флага проходит снаружи ниже крепежа, через низкую точку и входит в сухой бокс только через #tpu95-3/#tpu95-4.</text>
<text x="17" y="186" class="t">3. Световой тоннель, сервисная крышка и климатический карман образуют независимые обслуживаемые барьеры.</text>
<text x="17" y="192" class="t">4. Ни геометрия, ни замкнутая STL-сетка не подтверждают IP-класс, посадку, прочность или тепловой режим без стенда.</text>
</svg>'''
    write('current_longitudinal_section_v074',s)


def photo():
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Световой тоннель и крепление VEML7700 v{CURRENT_VERSION}</text><text x="148.5" y="16" text-anchor="middle" class="sub">тоннель укорочен до 15 мм; отдельная клеевая закладная исключает попадание клея в оптический канал</text>
<text x="67" y="28" text-anchor="middle" class="h">A. Сечение тоннеля</text><rect x="15" y="32" width="106" height="124" rx="4" class="note"/>
<rect x="52" y="59" width="36" height="13" class="petg"/><rect x="64.5" y="35" width="11" height="34" class="petg"/><rect x="62" y="67" width="16" height="4" class="petg"/>
<rect x="66" y="34" width="8" height="2" class="window"/><rect x="65" y="36" width="10" height="1.5" class="tpu85"/><rect x="65" y="38" width="10" height="2" class="petg"/>
<line x1="70" y1="40" x2="70" y2="69" stroke="#fff" stroke-width="4.2"/>
<path d="M63.5 68.5 A6.5 2.2 0 0 0 76.5 68.5" class="glue"/><text x="25" y="82" class="t">цилиндр Ø11 × 15 мм</text><text x="25" y="89" class="t">внутренняя полка Ø16 × 2,2 мм</text><text x="25" y="96" class="t">кольцевой резервуар клея Ø12,2–14,2</text><text x="25" y="103" class="t">глубина резервуара 0,45 мм</text><text x="25" y="110" class="t">оптический проход Ø4,2 мм</text><text x="25" y="117" class="t">поле зрения ≈16,7°</text>
<text x="25" y="129" class="small">Клей наносить только в жёлтую кольцевую зону.</text><text x="25" y="135" class="small">Окно и проход не покрывать герметиком.</text><text x="25" y="141" class="small">Напечатать купон 15/18 мм и сравнить засветку.</text>
<text x="210" y="28" text-anchor="middle" class="h">B. Съёмная опора платы</text><rect x="128" y="32" width="155" height="124" rx="4" class="note"/>
<rect x="162" y="56" width="96" height="76" rx="3" class="petg" fill-opacity=".45"/><rect x="181" y="70" width="58" height="44" rx="2" class="cut"/><rect x="193" y="80" width="34" height="24" class="board"/>
<circle cx="198" cy="92" r="1.7" fill="#f5f6f7" stroke="#1c5f3d"/><circle cx="222" cy="92" r="1.7" fill="#f5f6f7" stroke="#1c5f3d"/><circle cx="198" cy="92" r="1.1" class="petg"/><circle cx="222" cy="92" r="1.1" class="petg"/>
<polygon points="166,118 170,116 174,118 174,122 170,124 166,122" class="nut"/><polygon points="246,118 250,116 254,118 254,122 250,124 246,122" class="nut"/>
<text x="140" y="138" class="t">#petg-10 крепится двумя M3 в закладные гайки</text><text x="140" y="145" class="t">бортик посадки: 17,1 × 17,1 мм</text><text x="140" y="152" class="t">2 конических штырька: предварительный шаг 11 мм</text><text x="140" y="159" class="t">сторона проводов открыта; плата снимается отдельно</text>
<rect x="12" y="169" width="273" height="28" rx="3" class="note"/><text x="17" y="177" class="t">1. Размеры платы, отверстий и положение чувствительного элемента измерить до печати полного каркаса.</text><text x="17" y="184" class="t">2. Тоннель 15 мм — текущий выбор; купон 15/18 мм позволяет вернуться к 18 мм без перепроектирования крышки.</text><text x="17" y="191" class="t">3. После установки окна и матирования внутренней поверхности повторно откалибровать DAY/NIGHT через BLE.</text></svg>'''
    write('photo_tunnel_veml_mount_A4_landscape',s)


def environment():
    holes=[]
    import math
    for i in range(6):
        a=math.radians(i*60-90)
        holes.append((75.5+8*math.cos(a),79+8*math.sin(a)))
    hole_svg='<circle cx="75.5" cy="79" r="2.2" fill="#176b87"/>'+''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.2" fill="#176b87"/>' for x,y in holes)
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title" style="font-size:5.7px">Карман AHT20+BMP280 v{CURRENT_VERSION} — мембрана Ø20, семь отверстий и кабельный колодец</text><text x="148.5" y="16" text-anchor="middle" class="sub">рабочая область мембраны Ø10 мм; клеевое кольцо остаётся на сплошной ровной площадке</text>
<text x="75" y="28" text-anchor="middle" class="h">A. Вид снизу</text><rect x="16" y="33" width="118" height="108" rx="4" class="note"/><rect x="38" y="49" width="75" height="60" rx="3" class="petg"/><circle cx="75.5" cy="79" r="24" fill="#f2a66e" stroke="#98521f" stroke-width=".7"/><circle cx="75.5" cy="79" r="20.4" class="membrane"/><circle cx="75.5" cy="79" r="10" class="active"/>{hole_svg}
<text x="24" y="116" class="t">полный самоклеящийся диск Ø20 мм</text><text x="24" y="123" class="t">функциональный центр Ø10 мм</text><text x="24" y="130" class="t">1 центральное + 6 отверстий Ø2 мм на R3,2</text><text x="24" y="137" class="t">защитный бортик Ø23 с нижними дренажными разрывами</text>
<text x="210" y="28" text-anchor="middle" class="h">B. Сечение кармана</text><rect x="145" y="33" width="136" height="108" rx="4" class="note"/>
<rect x="166" y="48" width="92" height="68" class="petg"/><rect x="174" y="56" width="76" height="45" class="cut"/><rect x="188" y="66" width="48" height="18" class="board"/><rect x="187" y="84" width="4" height="10" class="petg"/><rect x="233" y="84" width="4" height="10" class="petg"/>
<path d="M200 101 V116" class="petg"/><path d="M224 101 V116" class="petg"/><circle cx="212" cy="114" r="10" class="membrane"/><circle cx="212" cy="114" r="5" class="active"/>
<rect x="166" y="48" width="92" height="3" class="tpu85"/><circle cx="250" cy="62" r="8" fill="#f6c39c" stroke="#98521f"/><circle cx="250" cy="62" r="3.5" fill="#fff" stroke="#98521f"/>
<polygon points="160,104 164,102 168,104 168,108 164,110 160,108" class="nut"/><polygon points="256,104 260,102 264,104 264,108 260,110 256,108" class="nut"/>
<text x="153" y="124" class="t">наружный габарит ≈34 × 30 × 17,5 мм</text><text x="153" y="131" class="t">TPU85-прокладка корпуса: 1,6 → 1,2 мм</text><text x="153" y="138" class="t">2×M3 в обслуживаемые закладные корпуса</text>
<rect x="12" y="151" width="273" height="47" rx="3" class="note"/>
<text x="17" y="159" class="t">1. Семь отверстий Ø2 мм сверлятся после печати через остаточную кожу 0,8 мм; открытая площадь ≈22 мм².</text><text x="17" y="166" class="t">2. Все отверстия находятся внутри активного круга Ø10 мм; клеевое кольцо диска Ø20 остаётся на сплошном PETG.</text><text x="17" y="173" class="t">3. Самоклеящаяся мембрана устанавливается без отдельной TPU-прокладки; активный центр не покрывать RTV.</text><text x="17" y="180" class="t">4. Смещённая перегородка исключает прямой продув BMP280 и прямую струю воды к плате.</text><text x="17" y="187" class="t">5. Четыре I²C-провода проходят через potting-well Ø8 мм; герметик заполняет только колодец.</text><text x="17" y="194" class="t">6. Допускается обрезать наружный край наклейки, но нельзя резать активную область или нарушать клеевое кольцо.</text></svg>'''
    write('environment_sensor_pocket_A4_landscape',s)


def fasteners():
    # Schematic positions, not a manufacturing projection.
    m4=[(55,58),(78,58),(55,90),(78,90),(115,67),(115,87),(145,67),(145,87)]
    lid=[(205,53),(255,53),(205,84),(255,84)]
    sensor=[(205,123),(255,123)]
    collar=[(65,164),(95,164)]
    cradle=[(210,170),(255,170)]
    def nuts(points,r,cls,label):
        return ''.join(f'<polygon points="{hex_points(x,y,r)}" class="{cls}"/><text x="{x}" y="{y+1}" text-anchor="middle" class="small">{label}</text>' for x,y in points)
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Карта закладных гаек и крепежа v{CURRENT_VERSION}</text><text x="148.5" y="16" text-anchor="middle" class="sub">все текущие винтовые соединения имеют обслуживаемую закладную; точный натяг проверяется отдельными купонами M4 и M3</text>
<rect x="12" y="28" width="164" height="103" rx="4" class="note"/><text x="20" y="38" class="h">A. Ротор и зажим спицы — 8×M4</text><circle cx="69" cy="74" r="33" class="petg" fill-opacity=".6"/><rect x="91" y="53" width="67" height="43" rx="7" class="petg" fill-opacity=".6"/><rect x="28" y="48" width="29" height="50" rx="5" class="petg" fill-opacity=".6"/>{nuts(m4,5.1,'nut','M4')}
<path d="M115 100 C104 112 93 117 75 119" class="arrow"/><text x="20" y="122" class="t">6 гаек стягивают корпус; 2 гайки зажимают втулку спицы.</text><text x="20" y="128" class="small">Загрузочные горловины и доступ к гайкам не перекрываются дорожкой проводов.</text>
<rect x="183" y="28" width="102" height="73" rx="4" class="note"/><text x="191" y="38" class="h">B. Крышка — 4×M3</text><rect x="198" y="47" width="64" height="43" rx="5" class="petg" fill-opacity=".55"/>{nuts(lid,4.2,'nut','M3')}<text x="191" y="96" class="small">гайки находятся вне сухого контура прокладки</text>
<rect x="183" y="106" width="102" height="38" rx="4" class="note"/><text x="191" y="116" class="h">C. Карман датчика — 2×M3</text>{nuts(sensor,4.2,'nut','M3')}<text x="191" y="139" class="small">крепёжные уши вне воздушной камеры</text>
<rect x="12" y="137" width="164" height="42" rx="4" class="note"/><text x="20" y="147" class="h">D. Неподвижный воротник — 2×M3</text><rect x="45" y="154" width="70" height="18" rx="9" class="petg" fill-opacity=".55"/>{nuts(collar,4.2,'nut','M3')}<text x="122" y="161" class="t">гайки в ответной половине;</text><text x="122" y="167" class="t">не использовать саморезы в PETG</text>
<rect x="183" y="149" width="102" height="30" rx="4" class="note"/><text x="191" y="158" class="h">E. Опора VEML7700 — 2×M3</text>{nuts(cradle,4.2,'nut','M3')}
<rect x="12" y="184" width="273" height="15" rx="3" class="note"/><text x="17" y="191" class="t">Итого: 8×M4 + 10×M3. Гайки устанавливаются после примерки купона; карман удерживает гайку, но позволяет заменить её при обслуживании.</text><text x="17" y="197" class="small">Флаг, шаблон рыбы и электрическая схема не используют собственные гайки; их механические ссылки ведут на эту карту.</text></svg>'''
    write('fastener_captive_nut_map_A4_landscape',s)


def electronics():
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Компоновка модулей электроники в боксе v{CURRENT_VERSION}</text><text x="148.5" y="16" text-anchor="middle" class="sub">двухуровневый съёмный каркас исключает пересечения условных объёмов и оставляет доступ к USB-C, кнопкам и клеммам</text>
<text x="77" y="29" text-anchor="middle" class="h">A. Вид сверху, крышка снята</text><rect x="12" y="34" width="132" height="104" rx="4" class="note"/><rect x="24" y="45" width="108" height="78" rx="6" class="petg" fill-opacity=".45"/><rect x="33" y="53" width="90" height="62" rx="4" fill="#f6c39c" stroke="#98521f" stroke-width=".6"/>
<rect x="40" y="72" width="50" height="28" rx="2" class="buck"/><text x="65" y="87" text-anchor="middle" class="t" fill="#fff">DC-DC 12→5 В</text><rect x="93" y="56" width="24" height="8" class="esp"/><text x="105" y="54" text-anchor="middle" class="small">ESP32-C3 на +Y стенке</text><rect x="44" y="105" width="46" height="8" class="mos"/><text x="67" y="120" text-anchor="middle" class="small">MOSFET на −Y стенке</text>
<path d="M30 86 H40" class="wire"/><text x="27" y="82" class="small">12 В</text><path d="M90 86 C102 86 105 70 105 64" class="wire2"/><path d="M90 92 C100 104 90 109 90 109" class="wire2"/><text x="35" y="132" class="small">силовые провода идут вдоль −Y; I²C — вдоль +Y</text>
<text x="220" y="29" text-anchor="middle" class="h">B. Вид сбоку, два уровня</text><rect x="151" y="34" width="134" height="104" rx="4" class="note"/><rect x="163" y="49" width="110" height="75" rx="5" class="petg" fill-opacity=".45"/><rect x="171" y="96" width="94" height="17" class="buck"/><text x="218" y="107" text-anchor="middle" class="small">нижний уровень: DC-DC</text><rect x="178" y="66" width="8" height="30" class="esp"/><rect x="250" y="70" width="8" height="26" class="mos"/><text x="191" y="62" class="small">ESP вертикально</text><text x="237" y="62" class="small">MOSF вертикально</text>
<rect x="190" y="47" width="58" height="11" class="petg"/><rect x="203" y="42" width="32" height="8" class="board"/><polygon points="190,55 194,53 198,55 198,59 194,61 190,59" class="nut"/><polygon points="240,55 244,53 248,55 248,59 244,61 240,59" class="nut"/><text x="218" y="38" text-anchor="middle" class="small">верхний уровень: #petg-10 + VEML7700</text><text x="218" y="130" text-anchor="middle" class="small">AHT20+BMP280 остаётся в отдельном нижнем кармане</text>
<rect x="12" y="147" width="273" height="50" rx="3" class="note"/>
<text x="17" y="156" class="t">1. #petg-9 — единая съёмная деталь: нижняя площадка DC-DC, две вертикальные рамки, прорези под стяжки и опоры #petg-10.</text><text x="17" y="163" class="t">2. ESP32-C3 развёрнута антенной в сторону флага и от силового DC-DC, MOSFET, проводов и металлических гаек.</text><text x="17" y="170" class="t">3. MOSFET стоит на противоположной стенке; клеммы и отвод тепла доступны после снятия крышки.</text><text x="17" y="177" class="t">4. Два M3 удерживают съёмную опору VEML7700; другие платы фиксируются регулируемыми упорами и TPU-стяжками после измерения.</text><text x="17" y="184" class="t">5. Вход двух проводов флага разгружается до силовых клемм; USB-C и кнопки ESP32 остаются доступны сверху.</text><text x="17" y="191" class="t">6. До финальной печати измерить каждую фактическую плату, высоту компонентов, направление проводов и допустимый радиус изгиба.</text></svg>'''
    write('electronics_layout_A4_landscape',s)


if __name__=='__main__':
    longitudinal()
    photo()
    environment()
    fasteners()
    electronics()
    print(f'Generated v{CURRENT_VERSION} mechanical detail diagrams.')
