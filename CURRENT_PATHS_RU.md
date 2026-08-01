# Актуальные и исторические части проекта — v0.7.2

## Главные точки входа

- `AGENTS.md` — обязательные правила следующему агенту;
- `docs/NEXT_CHAT_START_HERE_RU.md` — полный handoff;
- `docs/current-implementation-status.ru.md` — что реально реализовано и что требует стенда;
- `docs/PROJECT_DECISIONS_RU.md` — сводка решений;
- `docs/architecture/decisions/` — история ADR;
- `docs/MECHANICAL_FITS_RU.md` и `MEASUREMENTS_REQUIRED_RU.md` — получение реальных посадок.

## Актуальная механика

- `mechanical/generate_models_v06.py` — источник геометрии;
- `mechanical/stl_petg_v06/` — жёсткие детали текущей PETG-сборки;
- `mechanical/stl_tpu95_v06/` — функциональные мягкие детали;
- `mechanical/stl_tpu85_v06/` — прокладки;
- `mechanical/test_coupons_v06/` — обязательные купоны;
- `mechanical/flagpole_finial_v0_6_*.glb` — интерактивные модели;
- `mechanical/VALIDATION_REPORT_V06_RU.md` — топологическая проверка STL.

## Прошивка и Android

- `electronics/firmware/esp32_c3_crucian_v06/` — текущая прошивка;
- `android/crucian-control/` — текущий Android-клиент;
- `project_identity.json` — видимое имя приложения и BLE-имя.

## Флаг

- `flag_with_attachment_loops_full_size_300x250.svg` — полный вид с четырьмя петлями;
- `flag_attachment_loop_pattern_A4_1to1.svg` — выкройка петель 1:1;
- `mechanical/docs/FLAG_ATTACHMENT_LOOPS_RU.md` — формула и пошив.

## Каталог

- `catalog/components.json`, `catalog/drawings.json` — источники;
- `scripts/generateComponentCatalog.mjs` — генератор;
- `catalog/catalog.html` — generated-страница со статическими картинками и fullscreen 3D.

## Исторические части

- `mechanical/generate_models_v05.py`, `mechanical/stl_petg/`, `mechanical/stl_tpu/` и v0.5 GLB сохраняются для сравнения;
- `electronics/firmware/esp32_c3_flag_light/` — историческая прошивка до BLE;
- `archive/legacy_v02_reference/` — старая компоновка;
- корневые старые handoff-файлы не имеют приоритета над `docs/NEXT_CHAT_START_HERE_RU.md`.
