# Политика актуальных чертежей, 3D-моделей и ID-выносок

<!-- §catalog -->

## Что считается рабочим каталогом

`catalog/catalog.html` — оперативная страница для сборки и проверки текущей версии. Она не является музеем всех выпущенных вариантов. В ней публикуются только записи `status: "current"`, версия каждой записи обязана совпадать с `VERSION.txt`.

Исторические файлы допустимо сохранять в Git, `archive/`, отчётах прошлых выпусков и ссылках changelog. Добавлять их в массивы `drawings`, `models` или `printSessions` нельзя.

## Обязательное правило подписей

<!-- v076-thumbnail-policy:start -->
## Правило миниатюр и управления метками

- `thumbnail` обязателен для каждой 2D-карточки и не может ссылаться на `catalog/annotated/` либо файл `_ids.png`;
- `annotatedPreview` используется только при открытии полного overlay-чертежа;
- embedded-документы получают отдельную чистую миниатюру;
- hotspots непечатных GLB скрыты в карточке и видны в полноэкранном viewer;
- рядом с крестиком полноэкранного viewer обязательна доступная кнопка `ID` с `aria-pressed`;
- `labelPosition` — только предпочтительное направление, фактическая рамка размещается автоматическим resolver рядом с `target`;
- отчёт `mechanical/CALLOUT_LAYOUT_REPORT_V076.json` является производным проверяемым артефактом.
<!-- v076-thumbnail-policy:end -->

Все текущие чертежи и 3D-модели должны показывать ID изображённых деталей. Единственное исключение — раскладки для печати.

### Двухмерные чертежи

Для обычного чертежа используется:

```json
{
  "kind": "drawing",
  "calloutMode": "overlay",
  "preview": "mechanical/example.png",
  "annotatedPreview": "catalog/annotated/123_example_ids.png",
  "callouts": [
    {
      "id": "#petg-5",
      "label": "Сервисная крышка",
      "target": [0.52, 0.31],
      "labelPosition": [0.78, 0.12]
    }
  ]
}
```

Координаты нормированы от `0` до `1`: `[0, 0]` — левый верхний угол, `[1, 1]` — правый нижний. Исходный SVG/PNG не редактируется ради подписей. Подписанная копия строится командой:

```powershell
python mechanical/render_catalog_part_callouts_v075.py
```

Если документ сам является таблицей ID или уже имеет встроенные корректные выноски, используется `calloutMode: "embedded"` и непустой массив `partIds`.

### Интерактивные 3D-модели

Для обычной модели используется `calloutMode: "hotspots"`. `position` задаётся в метрах в системе координат GLB, `normal` определяет сторону метки:

```json
{
  "id": "#petg-9",
  "label": "Каркас электроники",
  "position": [-0.047, 0.0, 0.030],
  "normal": [0, 1, 0]
}
```

Нельзя добавлять текстовые сетки в GLB ради подписей: они увеличивают файл, засоряют сцену и могут быть приняты за печатную геометрию. Подписи принадлежат каталогу и автоматически копируются в полноэкранный viewer.

### Раскладки для печати

Для 2D- и 3D-раскладок:

```json
{
  "kind": "print-layout",
  "calloutMode": "exempt",
  "calloutExemptReason": "Раскладка печати должна оставаться без перекрывающих подписей."
}
```

`callouts`, `partIds` и `annotatedPreview` у такой записи не задаются. Состав очереди сверяется по таблице ID и именам STL, а не по подписям поверх стола.

## Допустимые ID

- Компоненты и покупные детали: строки `001`…`099` из `catalog/components.json`.
- Печатные детали: ID из `mechanical/part_id_registry_v06.json`.
- Свободные подписи без ID запрещены: сначала нужно создать или выбрать канонический ID.

## Добавление нового вида

1. Создать или обновить первичный генератор/SVG/GLB.
2. Добавить только текущую карточку в `catalog/drawings.json`.
3. Нанести метаданные выносок либо оформить исключение `print-layout`.
4. Для 2D выполнить `python mechanical/render_catalog_part_callouts_v075.py`.
5. Выполнить `npm.cmd run catalog:generate`.
6. Открыть локальную страницу и проверить, что линии указывают на нужные детали, hotspots не перекрывают друг друга при основных ракурсах, а полноэкранный режим сохраняет ID.
7. Выполнить проверки и обновить контрольные суммы.

## Запрет дублирования презентационных деталей

Разнесение или поднятие детали выполняется трансформацией единственного канонического объекта. Нельзя сначала включить объект в базовый набор сцены, а затем добавить его копию под другим presentation-именем. Для модели 210 это проверяет `mechanical/validate_catalog_model_semantics_v075.py`.

## Команды выпуска

```powershell
python mechanical/generate_models_v06.py
python mechanical/validate_models_v06.py
python mechanical/validate_catalog_model_semantics_v075.py
python mechanical/render_previews_v06.py
python mechanical/render_flag_power_route_v06.py
python mechanical/generate_reference_diagrams_v06.py
python mechanical/generate_detail_diagrams_v075.py
python mechanical/generate_hermeticity_diagram_v075.py
python electronics/generate_electronics_diagrams_v075.py
python mechanical/render_catalog_part_callouts_v075.py
npm.cmd run catalog:generate
npm.cmd run checksums:update
npm.cmd run quality:gate
```
