#!/usr/bin/env python3
"""Generate current v0.7.3 mechanical technical diagrams as SVG and PNG."""
from pathlib import Path
import html
import re

from resvg_py import svg_to_bytes

ROOT=Path(__file__).resolve().parent

def e(value): return html.escape(str(value), quote=True)
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
 <style>.title{font:700 7px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.sub{font:3.4px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}.h{font:700 4.4px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.t{font:3.1px 'DejaVu Sans',Arial,sans-serif;fill:#172126}.small{font:2.8px 'DejaVu Sans',Arial,sans-serif;fill:#52616a}.dim{font:700 3px 'DejaVu Sans',Arial,sans-serif;fill:#176b87}.petg{fill:#ee8a3d;stroke:#98521f;stroke-width:.7}.tpu95{fill:#929ca3;stroke:#4f5a61;stroke-width:.6}.tpu85{fill:#c2c9ce;stroke:#667178;stroke-width:.6}.metal{fill:#606c73;stroke:#222b30;stroke-width:.6}.board{fill:#369662;stroke:#1c5f3d;stroke-width:.6}.window{fill:#92cceb;stroke:#316b8a;stroke-width:.5}.membrane{fill:#d9e6eb;stroke:#647a84;stroke-width:.5}.air{fill:none;stroke:#176b87;stroke-width:.7;stroke-dasharray:2 1}.arrow{fill:none;stroke:#176b87;stroke-width:.8;marker-end:url(#arr)}.note{fill:#fff;stroke:#c7d1d5;stroke-width:.45}.cut{fill:#fff6ef;stroke:#bd6b31;stroke-width:.55}</style>
</defs>'''

def write(name, content):
    svg=ROOT/f'{name}.svg'; out=ROOT/f'{name}.png'; svg.write_text(content,'utf-8'); png(svg,out)


def longitudinal():
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Crucian v0.7.3 — актуальная продольная схема узлов</text>
<text x="148.5" y="16" text-anchor="middle" class="sub">схема объясняет компоновку; окончательные посадки зависят от фактических измерений и купонов</text>
<!-- pole and rotor -->
<rect x="78" y="40" width="18" height="135" rx="4" class="metal"/><rect x="83" y="40" width="8" height="135" fill="#f5f6f7" stroke="#222b30" stroke-width=".4"/>
<rect x="61" y="48" width="52" height="72" rx="15" class="petg" fill-opacity=".65"/>
<rect x="69" y="56" width="36" height="8" rx="2" class="metal"/><rect x="69" y="101" width="36" height="8" rx="2" class="metal"/>
<text x="116" y="62" class="t">верхний 6804-2RS</text><text x="116" y="107" class="t">нижний 6804-2RS</text>
<rect x="88" y="66" width="3" height="33" class="metal"/><text x="94" y="84" class="small">металлическая распорка внутренних колец</text>
<!-- spoke -->
<rect x="88" y="81" width="88" height="5" rx="2.5" fill="#22282c"/><rect x="104" y="76" width="13" height="15" class="tpu95"/>
<text x="119" y="70" class="dim">спица Ø5 мм</text><text x="119" y="75" class="dim">между подшипниками</text><path d="M132 76 L132 81" class="arrow"/>
<!-- flag and loops -->
<rect x="176" y="72" width="95" height="80" fill="#c96931" stroke="#873d1a" stroke-width=".7"/><line x1="176" y1="72" x2="271" y2="152" stroke="#9f4b20"/><g fill="none" stroke="#e26e25" stroke-width="4"><path d="M176 76 H151 Q139 76 139 84 Q139 92 151 92 H176"/><path d="M176 99 H151 Q139 99 139 107 Q139 115 151 115 H176"/><path d="M176 122 H151 Q139 122 139 130 Q139 138 151 138 H176"/><path d="M176 136 H151 Q139 136 139 144 Q139 152 151 152 H176"/></g>
<!-- M125 -->
<rect x="84" y="43" width="6" height="13" rx="2" fill="#343a3e"/><rect x="85.5" y="39" width="3" height="5" fill="#343a3e"/><text x="45" y="43" class="t">M125-0205 внутри полого штока</text><path d="M73 44 H84" class="arrow"/>
<!-- electronics pod -->
<rect x="16" y="57" width="45" height="53" rx="4" class="petg"/><rect x="12" y="52" width="53" height="8" rx="2" class="petg"/><rect x="18" y="59" width="41" height="3" class="tpu85"/><text x="17" y="49" class="t">сервисная крышка</text><path d="M31 50 V52" class="arrow"/><text x="18" y="75" class="small">TPU85 2,0 → 1,5 мм</text><rect x="22" y="81" width="13" height="8" fill="#355c9a"/><rect x="39" y="81" width="13" height="8" fill="#2f8f6b"/><rect x="22" y="94" width="30" height="7" fill="#b24a36"/><text x="18" y="107" class="small">ESP / DC-DC / MOSFET</text>
<!-- photo tunnel -->
<rect x="28" y="34" width="11" height="18" class="petg"/><rect x="25.5" y="49" width="16" height="3" class="petg"/><rect x="29.5" y="33" width="8" height="2" class="window"/><rect x="21" y="58" width="25" height="13" rx="2" class="cut"/><rect x="25" y="61" width="17" height="7" class="board"/><text x="13" y="29" class="t">тоннель VEML7700: 18 мм</text><path d="M31 31 V34" class="arrow"/>
<!-- climate pocket -->
<rect x="20" y="119" width="38" height="25" class="petg"/><rect x="22" y="121" width="34" height="2" class="tpu85"/><rect x="30" y="128" width="18" height="7" class="board"/><circle cx="39" cy="143" r="7" class="membrane"/><circle cx="35" cy="143" r="1" fill="#176b87"/><circle cx="39" cy="140" r="1" fill="#176b87"/><circle cx="43" cy="143" r="1" fill="#176b87"/><text x="16" y="151" class="small">нижний карман AHT20+BMP280</text><text x="16" y="156" class="small">мембрана Ø12; 3×Ø2,5 после печати</text>
<!-- external wires -->
<path d="M174 91 C150 102 135 118 113 123 C96 127 72 124 60 112" fill="none" stroke="#1d2225" stroke-width="1.4"/><path d="M174 95 C150 106 135 122 113 127 C96 131 72 128 60 116" fill="none" stroke="#3b4247" stroke-width="1.4"/><text x="117" y="137" class="dim">два провода Ø2 мм ниже гайки, между бортами 4,2 × 2,5 мм</text>
<!-- notes -->
<rect x="12" y="166" width="273" height="32" rx="3" class="note"/>
<text x="17" y="174" class="t">1. Токосъёмник передаёт ток и не несёт механическую нагрузку.</text><text x="17" y="180" class="t">2. Кабель флага не проходит через спицу: снаружи идёт ниже крепежа и входит в сухой бокс только у электроники.</text><text x="17" y="186" class="t">3. Климатический карман сообщается с наружным воздухом, но отделён от сухого электронного отсека TPU85-прокладкой.</text><text x="17" y="192" class="t">4. Старые v0.5-разрезы сохраняются только как история и не задают текущую геометрию.</text>
</svg>'''
    write('current_longitudinal_section_v073',s)


def photo():
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title">Световой тоннель и крепление VEML7700 v0.7.3</text><text x="148.5" y="16" text-anchor="middle" class="sub">тоннель вставляется изнутри наружу; одна утолщённая шайба остаётся внутри электронного бокса</text>
<text x="68" y="28" text-anchor="middle" class="h">A. Сечение тоннеля</text><rect x="18" y="32" width="101" height="122" rx="4" class="note"/>
<rect x="55" y="58" width="30" height="13" class="petg"/><rect x="64.5" y="35" width="11" height="38" class="petg"/><rect x="62" y="69" width="16" height="3" class="petg"/>
<rect x="66" y="34" width="8" height="2" class="window"/><rect x="65" y="36" width="10" height="1.5" class="tpu85"/><rect x="65" y="38" width="10" height="2" class="petg"/>
<line x1="70" y1="40" x2="70" y2="69" stroke="#fff" stroke-width="4.2"/><path d="M70 106 V73" class="arrow"/><text x="75" y="100" class="dim">монтаж изнутри наружу</text>
<text x="25" y="83" class="t">цилиндр Ø11 × 18 мм</text><text x="25" y="90" class="t">отверстие крышки Ø11,4 мм</text><text x="25" y="97" class="t">внутренняя шайба Ø16 × 2,2 мм</text><text x="25" y="104" class="t">оптический проход Ø4,2 мм</text><text x="25" y="111" class="t">окно Ø8 мм, паз Ø8,3 мм</text><text x="25" y="118" class="t">поле зрения ≈13,3°</text><text x="25" y="128" class="small">Клей — тонким непрерывным кольцом</text><text x="25" y="133" class="small">между внутренней шайбой и крышкой.</text><text x="25" y="138" class="small">Оптический проход не заливать.</text>
<text x="211" y="28" text-anchor="middle" class="h">B. Посадка платы</text><rect x="132" y="32" width="153" height="122" rx="4" class="note"/>
<rect x="166" y="55" width="90" height="74" rx="3" class="petg" fill-opacity=".45"/><rect x="181" y="68" width="60" height="46" rx="2" class="cut"/><rect x="192" y="79" width="38" height="24" class="board"/><circle cx="198" cy="91" r="1.8" fill="#f5f6f7" stroke="#1c5f3d"/><circle cx="224" cy="91" r="1.8" fill="#f5f6f7" stroke="#1c5f3d"/>
<circle cx="198" cy="91" r="1.1" class="petg"/><circle cx="224" cy="91" r="1.1" class="petg"/><rect x="205" y="82" width="12" height="8" fill="#222"/><circle cx="211" cy="91" r="4" fill="#111"/>
<text x="145" y="140" class="t">бортик посадки: 17,1 × 17,1 мм</text><text x="145" y="146" class="t">плата: предварительно 16,5 × 16,5 мм</text><text x="145" y="152" class="t">2 конических штырька: шаг 11 мм</text><text x="145" y="158" class="t">4 опорные площадки; сторона проводов открыта</text>
<path d="M211 90 V56" class="air"/><text x="218" y="60" class="small">чувствительный элемент</text><text x="218" y="65" class="small">совмещается с осью тоннеля</text>
<rect x="12" y="166" width="273" height="31" rx="3" class="note"/><text x="17" y="174" class="t">1. Штырьки и бортик являются предварительными: до полноразмерной печати измерить реальную плату, отверстия и смещение сенсора.</text><text x="17" y="181" class="t">2. Внутренний светозащитный пояс должен быть матово-чёрным после проверки: он не должен касаться платы или перекрывать I²C-провода.</text><text x="17" y="188" class="t">3. Тоннель длиной 18 мм выбран вместо прежних ≈26 мм, чтобы расширить поле зрения при сохранении защиты от боковой засветки.</text><text x="17" y="195" class="t">4. После установки конкретного окна обязательно повторно откалибровать DAY/NIGHT через BLE.</text></svg>'''
    write('photo_tunnel_veml_mount_A4_landscape',s)


def environment():
    s=f'''<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">{BASE}<rect width="297" height="210" fill="#f5f6f7"/>
<text x="148.5" y="10" text-anchor="middle" class="title" style="font-size:5.7px">Карман AHT20+BMP280 v0.7.3 — вентиляция, мембрана и кабельный проход</text><text x="148.5" y="16" text-anchor="middle" class="sub">размеры предварительные; малые отверстия сверлятся после печати по утончённым площадкам</text>
<text x="75" y="28" text-anchor="middle" class="h">A. Вид снизу на мембрану</text><rect x="16" y="33" width="118" height="106" rx="4" class="note"/><rect x="38" y="49" width="75" height="60" rx="3" class="petg"/><circle cx="75.5" cy="79" r="22" fill="#f2a66e" stroke="#98521f" stroke-width=".7"/><circle cx="75.5" cy="79" r="16.5" class="membrane"/><circle cx="75.5" cy="79" r="15" fill="#e7f0f3" stroke="#647a84" stroke-width=".4"/>
<circle cx="70" cy="82" r="2.2" fill="#176b87"/><circle cx="75.5" cy="73" r="2.2" fill="#176b87"/><circle cx="81" cy="82" r="2.2" fill="#176b87"/>
<text x="25" y="119" class="t">мембрана Ø12 мм</text><text x="25" y="125" class="t">углубление Ø13,4 × 0,7 мм</text><text x="25" y="131" class="t">защитный бортик Ø18 × 2,5 мм</text>
<text x="210" y="28" text-anchor="middle" class="h">B. Сечение кармана</text><rect x="145" y="33" width="136" height="106" rx="4" class="note"/>
<rect x="166" y="48" width="92" height="68" class="petg"/><rect x="174" y="56" width="76" height="45" class="cut"/><rect x="188" y="66" width="48" height="18" class="board"/><rect x="187" y="84" width="4" height="10" class="petg"/><rect x="233" y="84" width="4" height="10" class="petg"/>
<path d="M200 101 V116" class="petg"/><path d="M224 101 V116" class="petg"/><circle cx="212" cy="113" r="9" class="membrane"/><circle cx="208" cy="113" r="1.2" fill="#176b87"/><circle cx="212" cy="109" r="1.2" fill="#176b87"/><circle cx="216" cy="113" r="1.2" fill="#176b87"/>
<rect x="166" y="48" width="92" height="3" class="tpu85"/><circle cx="250" cy="62" r="8" fill="#f6c39c" stroke="#98521f"/><circle cx="250" cy="62" r="3.5" fill="#fff" stroke="#98521f"/>
<text x="153" y="124" class="t">наружный габарит ≈34 × 30 × 17,5 мм</text><text x="153" y="130" class="t">камера платы: 15,6 × 15,6 мм</text><text x="153" y="136" class="t">TPU85 1,6 мм в пазу 1,2 мм → сжатие 25%</text>
<rect x="12" y="150" width="273" height="47" rx="3" class="note"/>
<text x="17" y="158" class="t">1. Три отверстия Ø2,5 мм сверлятся после печати через остаточную кожу 0,8 мм; до сверления проверить отдельный купон.</text><text x="17" y="165" class="t">2. Смещённая внутренняя перегородка исключает прямой продув порта BMP280 и прямую струю воды к плате.</text><text x="17" y="172" class="t">3. Самоклеящаяся PTFE/ePTFE-мембрана клеится кольцом на ровную обезжиренную площадку; активную область не мазать RTV.</text><text x="17" y="179" class="t">4. Четыре I²C-провода проходят через отдельный potting-well Ø8 мм; герметик заполняет только колодец, а не камеру датчика.</text><text x="17" y="186" class="t">5. Карман располагается снизу, но требует испытаний: обдув, дождь, конденсат, пыль, отклик влажности и дрейф давления.</text><text x="17" y="193" class="t">6. Крепёжные винты и их уплотняющие уши находятся за пределами основной камеры датчика.</text></svg>'''
    write('environment_sensor_pocket_A4_landscape',s)

if __name__=='__main__':
    longitudinal(); photo(); environment(); print('Generated v0.7.3 current mechanical detail diagrams.')
