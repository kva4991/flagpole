# Повторная проверка канонической SDF/trimesh-линии v0.7.6

Дата проверки: 2026-08-04.

Генератор `mechanical/generate_models_v06.py` запущен в отдельной полной копии рабочего дерева. Канонические файлы основного дерева во время проверки не перезаписывались. Сравнение выполнено скриптом `mechanical/audit_legacy_regeneration_v076.py`.

## Результат

- код завершения генератора: **0**;
- время выполнения: **25.98 с**;
- пиковая память: **1964.4 МиБ**;
- проверено файлов: **49**;
- STL: **40**;
- GLB: **7**;
- JSON-отчёты: **2**;
- побитово совпали: **39/49**;
- геометрически либо семантически эквивалентны: **49/49**;
- итог: **PASS**.

Для побитово отличающихся STL и узлов GLB сравнивались число вершин/граней, AABB, площадь, абсолютный объём, замкнутость, согласованность обхода и инвариантный `trimesh.identifier_hash`. JSON сравнивался после разбора; только разделители путей `\` и `/` нормализовались как платформенное представление. Инженерные значения, имена, числа и структура не нормализовались.

## Побитово отличающиеся файлы

- `mechanical/stl_petg_v06/rotor_half_B_print_flat.stl`: 11776284 → 11776284 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-mesh-metrics`.
- `mechanical/flagpole_finial_v0_6_assembly.glb`: 21181452 → 21181484 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/flagpole_finial_v0_6_flag_power_route.glb`: 13397364 → 13397400 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/flagpole_finial_v0_6_electronics_layout.glb`: 13236584 → 13236616 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/flagpole_finial_v0_6_exploded.glb`: 21048992 → 21049028 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/flagpole_finial_v0_6_print_layout_PETG.glb`: 16068100 → 16068136 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/flagpole_finial_v0_6_print_layout_TPU95.glb`: 3968584 → 3968616 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/flagpole_finial_v0_6_print_layout_TPU85.glb`: 1012384 → 1012416 байт; нормализованная эквивалентность: **PASS**; основание: `normalized-scene-metrics`.
- `mechanical/model_parameters_and_diagnostics_v06.json`: 33866 → 32482 байт; нормализованная эквивалентность: **PASS**; основание: `parsed-json-with-path-separator-normalization`.
- `mechanical/project_manifest_v06.json`: 2943 → 2845 байт; нормализованная эквивалентность: **PASS**; основание: `parsed-json-with-path-separator-normalization`.

## Среда сравнения

- Python: `3.13.5`;
- платформа: `Linux-6.12.13-x86_64-with-glibc2.41`;
- NumPy: `2.3.5`;
- trimesh: `4.11.1`.

## Граница доказательства

Проверка подтверждает воспроизводимость текущего цифрового SDF/trimesh-слоя в указанной среде. Она не подтверждает физические посадки, прочность, герметичность, нагрев, работоспособность электроники или долговечность на улице.

Полные метрики и хеши находятся в `mechanical/LEGACY_REGENERATION_AUDIT_V076.json`.
