# Актуальные и исторические части проекта — v0.7.6

## Главные точки входа

- `AGENTS.md` — правила работы с репозиторием;
- `docs/current-implementation-status.ru.md` — фактический статус;
- `UPDATE_REPORT_V075_RU.md` — изменения текущей версии;
- `docs/CATALOG_MEDIA_POLICY_RU.md` — правила актуального каталога, 2D-выносок и 3D-hotspots;
- `MEASUREMENTS_REQUIRED_RU.md` — размеры, которые нужно получить с реальных деталей;
- `docs/architecture/decisions/README.ru.md` — история устойчивых решений.

## Текущая механика

- `mechanical/generate_build123d_canonical_v076.py` — канонический build123d-источник 23 печатных деталей и #204;
- `mechanical/cad_drafts/petg_6806_adapter_v076.json` и `mechanical/generate_petg_6806_adapter_coupons_v076.py` — исходная заготовка #401 новой PETG-втулки и пробников; производные файлы ещё не создавались;
- `mechanical/cad_drafts/tpu85_lower_pole_strain_relief_v076.json` и `mechanical/generate_tpu85_lower_pole_strain_relief_v076.py` — source-only заготовка #402 нижней гибкой разгрузки двух жил; производные файлы ещё не создавались;
- `mechanical/generate_models_v06.py` — только три актуальные непечатные справочные сцены и общие параметры старых 2D-генераторов; запуск по прямому запросу владельца;
- `mechanical/stl_petg_v06/` — 10 текущих жёстких деталей;
- `mechanical/stl_tpu95_v06/` — 10 функциональных мягких деталей;
- `mechanical/stl_tpu85_v06/` — 3 статические прокладки;
- `mechanical/test_coupons_v06/` — 17 купонов;
- `mechanical/flagpole_finial_v0_6_*.glb` — 7 текущих интерактивных моделей;
- `mechanical/VALIDATION_REPORT_V06_RU.md` — результат топологической проверки 40 STL.

Переходные сетки v0.7.3, бинарные файлы v0.5 и завершённый трёхдетальный
build123d-пилот удалены из рабочего дерева: они не участвуют в текущей сборке,
а при необходимости доступны в истории Git.

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

- `catalog/components.json` — назначения, названия, характеристики и ссылки покупных компонентов;
- `catalog/physical-components.json` — единственный источник их физических размеров, массы, статуса и происхождения значений; §physicalcomponents1
- `catalog/drawings.json` — структура карточек чертежей и моделей;
- CAD-заготовки #401 и #402 из `catalogPolicy.cadDraftSources` показываются текстом и HTML-схемой в той же вкладке, не создавая фиктивных медиафайлов;
- `scripts/generateComponentCatalog.mjs` — генератор;
- `catalog/catalog.html` — производная локальная страница.

## История

- история удалённых бинарных генераций хранится в Git, а не дублируется в текущем дереве;
- отчёты `UPDATE_REPORT_V070_RU.md`…`UPDATE_REPORT_V074_RU.md` остаются лёгкими текстовыми свидетельствами предыдущих срезов и не задают текущую публикацию.
