# Индекс подробных описаний чертежей и 3D-моделей

<!-- generated: scripts/generateMediaDescriptionIndex.mjs -->

Этот файл генерируется из `catalog/drawings.json` и одноимённых Markdown-файлов. Вручную его не редактировать. Полный контракт находится в [README_RU.md](README_RU.md), решение — в [ADR-0032](../../docs/architecture/decisions/0032-one-media-id-one-rationale-file.ru.md). §mediarationale1

## Сводка

- всего медиа-ID: **29**;
- карточек 2D: **19**;
- текущих карточек 3D: **7**;
- экспериментальных карточек CAD: **0**;
- операционных карточек очередей: **3**;
- каждый ID имеет ровно один файл, а подробный текст в `catalog/drawings.json` отсутствует.

## Реестр

| ID | Тип | Название | Основной файл | Источник истины | Байт | SHA-256 файла |
| --- | --- | --- | --- | --- | ---: | --- |
| [#101](101.md) | 2D-чертёж/схема | Схема соединений электроники v0.7.6 — A4 | `electronics/electronics_wiring_diagram_A4.svg` | `electronics/generate_electronics_diagrams_v075.py` | 18 806 | `a12ffb4ca557…` |
| [#102](102.md) | 2D-чертёж/схема | Карта клемм, GPIO и разъёмов v0.7.6 — A4 | `electronics/electronics_terminal_map_A4.svg` | `electronics/generate_electronics_diagrams_v075.py` | 16 880 | `193c8a6670ef…` |
| [#109](109.md) | 2D-чертёж/схема | Флаг 300 × 250 мм с четырьмя лямками v0.7.6 | `flag_with_attachment_loops_full_size_300x250.svg` | `flag_with_attachment_loops_full_size_300x250.svg` | 16 842 | `44167e26c6dd…` |
| [#110](110.md) | 2D-чертёж/схема | Выкройка четырёх лямок v0.7.6 — A4, предварительно 220 × 30 мм | `flag_attachment_loop_pattern_A4_1to1.svg` | `flag_attachment_loop_pattern_A4_1to1.svg` | 15 145 | `48a2cf58bdd1…` |
| [#111](111.md) | 2D-чертёж/схема | Общий вид сборки v0.7.6 | `mechanical/preview_v06_assembly.png` | `mechanical/render_previews_v06.py` | 16 568 | `b61f388369d2…` |
| [#112](112.md) | 2D-чертёж/схема | Разнесённый вид PETG/TPU v0.7.6 с ID | `mechanical/preview_v06_exploded_PETG_TPU_ids.png` | `mechanical/render_previews_v06.py` | 20 582 | `3e82f1d81ceb…` |
| [#113](113.md) | раскладка/очередь печати | Раскладка PETG v0.7.6 | `mechanical/preview_v06_print_PETG.png` | `mechanical/render_previews_v06.py` | 16 558 | `fd302f47a901…` |
| [#114](114.md) | раскладка/очередь печати | Раскладка TPU 95A v0.7.6 | `mechanical/preview_v06_print_TPU95.png` | `mechanical/render_previews_v06.py` | 16 239 | `d9ed2f77a0d7…` |
| [#115](115.md) | раскладка/очередь печати | Раскладка TPU 85A v0.7.6 | `mechanical/preview_v06_print_TPU85.png` | `mechanical/render_previews_v06.py` | 13 874 | `f34da778b9c7…` |
| [#116](116.md) | 2D-чертёж/схема | Маршрут двух проводов питания флага v0.7.6 | `mechanical/flag_power_cable_route_A4_landscape.svg` | `mechanical/generate_reference_diagrams_v06.py` | 16 957 | `3effe103d274…` |
| [#117](117.md) | 2D-чертёж/схема | Таблица идентификаторов печатных деталей v0.7.6 | `mechanical/part_id_table_v06.svg` | `mechanical/generate_reference_diagrams_v06.py` | 20 187 | `9ac2dbf7b16e…` |
| [#118](118.md) | 2D-чертёж/схема | Актуальная продольная схема узлов v0.7.6 | `mechanical/current_longitudinal_section_v075.svg` | `mechanical/generate_detail_diagrams_v075.py` | 17 746 | `d45ba159d82b…` |
| [#119](119.md) | 2D-чертёж/схема | Герметичность электронного отсека и датчиков v0.7.6 | `mechanical/hermeticity_design_A4_landscape.svg` | `mechanical/generate_hermeticity_diagram_v075.py` | 16 659 | `02c2c0a41694…` |
| [#120](120.md) | 2D-чертёж/схема | Световой тоннель и крепление VEML7700 v0.7.6 | `mechanical/photo_tunnel_veml_mount_A4_landscape.svg` | `mechanical/generate_detail_diagrams_v075.py` | 16 357 | `8f4621d6f8c6…` |
| [#121](121.md) | 2D-чертёж/схема | Карман AHT20+BMP280 v0.7.6 | `mechanical/environment_sensor_pocket_A4_landscape.svg` | `mechanical/generate_detail_diagrams_v075.py` | 16 632 | `29fba451ab99…` |
| [#122](122.md) | 2D-чертёж/схема | Чистый шаблон рыбы для 16-мм неона v0.7.6 — A4 | `fish_template_clean_A4_landscape.svg` | `fish_template_clean_A4_landscape.svg` | 15 594 | `d978afe557f3…` |
| [#123](123.md) | 2D-чертёж/схема | Размерный шаблон рыбы для 16-мм неона v0.7.6 — A4 | `fish_template_dimensioned_A4_landscape.svg` | `fish_template_dimensioned_A4_landscape.svg` | 14 798 | `aa3400867e34…` |
| [#124](124.md) | 2D-чертёж/схема | Карта закладных гаек и крепежа v0.7.6 | `mechanical/fastener_captive_nut_map_A4_landscape.svg` | `mechanical/generate_detail_diagrams_v075.py` | 17 731 | `19aaf470529a…` |
| [#125](125.md) | 2D-чертёж/схема | Компоновка электроники в боксе v0.7.6 | `mechanical/electronics_layout_A4_landscape.svg` | `mechanical/generate_detail_diagrams_v075.py` | 16 796 | `80f683d93c18…` |
| [#204](204.md) | интерактивная 3D-модель | Разнесённый вид PETG/TPU v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_exploded.glb` | `mechanical/generate_build123d_canonical_v076.py` | 29 135 | `b744eb99ad55…` |
| [#205](205.md) | интерактивная 3D-модель | Общий вид сборки v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_assembly.glb` | `mechanical/generate_models_v06.py` | 22 402 | `d8163050d4dc…` |
| [#206](206.md) | раскладка/очередь печати | Раскладка PETG v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_print_layout_PETG.glb` | `mechanical/generate_build123d_canonical_v076.py` | 17 150 | `b912f998c858…` |
| [#207](207.md) | раскладка/очередь печати | Раскладка TPU 95A v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_print_layout_TPU95.glb` | `mechanical/generate_build123d_canonical_v076.py` | 16 872 | `317088f86549…` |
| [#208](208.md) | раскладка/очередь печати | Раскладка TPU 85A v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_print_layout_TPU85.glb` | `mechanical/generate_build123d_canonical_v076.py` | 13 970 | `eb37c8c76808…` |
| [#209](209.md) | интерактивная 3D-модель | Маршрут двух проводов питания флага v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_flag_power_route.glb` | `mechanical/generate_models_v06.py` | 18 991 | `598c1f57d0fb…` |
| [#210](210.md) | интерактивная 3D-модель | Компоновка электроники v0.7.6 — интерактивно | `mechanical/flagpole_finial_v0_6_electronics_layout.glb` | `mechanical/generate_models_v06.py` | 17 630 | `66e7463ba36d…` |
| [#301](301.md) | раскладка/очередь печати | Очередь печати PETG v0.7.6 | `mechanical/preview_v06_print_PETG.png` | `mechanical/render_build123d_exploded_preview_v076.py` | 15 874 | `31700f1f9085…` |
| [#302](302.md) | раскладка/очередь печати | Очередь печати TPU 95A v0.7.6 | `mechanical/preview_v06_print_TPU95.png` | `mechanical/render_build123d_exploded_preview_v076.py` | 15 224 | `dcd247b5ddab…` |
| [#303](303.md) | раскладка/очередь печати | Очередь печати TPU 85A v0.7.6 | `mechanical/preview_v06_print_TPU85.png` | `mechanical/render_build123d_exploded_preview_v076.py` | 13 010 | `1a9036a7c154…` |

## Как пользоваться

Перед изменением конкретного рисунка или модели открыть файл по его ID и прочитать его полностью. После изменения обновить этот файл, первичный CAD/SVG-источник, производные медиа, запись каталога и проверки в одной правке. Затем выполнить `npm.cmd run media:descriptions:check`.
