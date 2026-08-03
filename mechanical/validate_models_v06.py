#!/usr/bin/env python3
"""Validate printable STL meshes generated for the current v0.7.6 handoff."""
from pathlib import Path
import json
import trimesh

ROOT=Path(__file__).resolve().parent
FOLDERS=['stl_petg_v06','stl_tpu95_v06','stl_tpu85_v06','test_coupons_v06']
records=[]
for folder in FOLDERS:
    for path in sorted((ROOT/folder).glob('*.stl')):
        mesh=trimesh.load(path,force='mesh')
        components=len(mesh.split(only_watertight=False))
        records.append({
            'file':str(path.relative_to(ROOT.parent)).replace('\\','/'),
            'watertight':bool(mesh.is_watertight),
            'winding_consistent':bool(mesh.is_winding_consistent),
            'components':int(components),
            'vertices':int(len(mesh.vertices)),
            'faces':int(len(mesh.faces)),
            'bounds_mm':mesh.bounds.tolist(),
            'volume_mm3':float(mesh.volume),
        })
summary={
    'schemaVersion':1,
    'version':'0.7.6 cumulative mechanical update',
    'checkedFiles':len(records),
    'allWatertight':all(r['watertight'] for r in records),
    'allWindingConsistent':all(r['winding_consistent'] for r in records),
    'allSingleComponent':all(r['components']==1 for r in records),
    'records':records,
}
(ROOT/'VALIDATION_REPORT_V06.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[
    '# Проверка STL актуальной механики v0.7.6',
    '',
    f'- Проверено STL: **{summary["checkedFiles"]}**',
    f'- Все замкнуты: **{"да" if summary["allWatertight"] else "нет"}**',
    f'- Направление граней согласовано: **{"да" if summary["allWindingConsistent"] else "нет"}**',
    f'- Каждый файл состоит из одного связного объёма: **{"да" if summary["allSingleComponent"] else "нет"}**',
    '',
    'Проверка охватывает PETG, TPU 95A, TPU 85A и тестовые купоны.',
    '',
    'В этой версии заново проверены половины корпуса, крышка, укороченный световой тоннель, карман AHT20+BMP280, TPU-манжеты, направляющая двух проводов, прокладки и тестовые купоны.',
    '',
    '> Замкнутая STL-сетка не доказывает правильность физических посадок, прочность, герметичность или печатаемость без поддержек. Эти свойства проверяются купонами и стендом.',
    '',
    '## Файлы',
    '',
    '| Файл | Замкнут | Связных объёмов | Грани |',
    '| --- | ---: | ---: | ---: |',
]
for r in records:
    lines.append(f'| `{r["file"]}` | {"да" if r["watertight"] else "нет"} | {r["components"]} | {r["faces"]} |')
(ROOT/'VALIDATION_REPORT_V06_RU.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='records'},ensure_ascii=False,indent=2))
