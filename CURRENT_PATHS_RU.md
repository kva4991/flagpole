# Актуальные и исторические части проекта — v0.7.6

## Главные точки входа

- `AGENTS.md` — правила работы с репозиторием;
- `docs/current-implementation-status.ru.md` — фактический статус;
- `UPDATE_REPORT_V075_RU.md` — изменения текущей версии;
- `docs/CATALOG_MEDIA_POLICY_RU.md` — правила актуального каталога, 2D-выносок и 3D-hotspots;
- `MEASUREMENTS_REQUIRED_RU.md` — размеры, которые нужно получить с реальных деталей;
- `docs/architecture/decisions/README.ru.md` — история устойчивых решений.

## Текущая механика

- `mechanical/generate_models_v06.py` — полностью параметрический источник геометрии v0.7.6;
- `mechanical/stl_petg_v06/` — 10 текущих жёстких деталей;
- `mechanical/stl_tpu95_v06/` — 10 функциональных мягких деталей;
- `mechanical/stl_tpu85_v06/` — 3 статические прокладки;
- `mechanical/test_coupons_v06/` — 17 купонов;
- `mechanical/flagpole_finial_v0_6_*.glb` — 7 текущих интерактивных моделей;
- `mechanical/VALIDATION_REPORT_V06_RU.md` — результат топологической проверки 40 STL.

Переходные сетки v0.7.3 перемещены в `archive/legacy_v073_reference/canonical_meshes/` и не используются генератором.

## Текущие генераторы изображений

- `mechanical/render_previews_v06.py`;
- `mechanical/render_part_id_drawings_v06.py`;
- `mechanical/render_catalog_part_callouts_v075.py`;
- `mechanical/render_flag_power_route_v06.py`;
- `mechanical/generate_reference_diagrams_v06.py`;
- `mechanical/generate_detail_diagrams_v075.py`;
- `mechanical/generate_hermeticity_diagram_v075.py`;
- `electronics/generate_electronics_diagrams_v075.py`.

## Каталог

- `catalog/components.json` и `catalog/drawings.json` — источники;
- `scripts/generateComponentCatalog.mjs` — генератор;
- `catalog/catalog.html` — производная локальная страница.

## История

- `archive/` — устаревшие справочные материалы;
- `mechanical/stl_petg/`, `mechanical/stl_tpu/`, `mechanical/test_coupons/` и GLB v0.5 — историческая линия;
- отчёты `UPDATE_REPORT_V070_RU.md`…`UPDATE_REPORT_V074_RU.md` описывают предыдущие срезы и не задают текущую публикацию.
