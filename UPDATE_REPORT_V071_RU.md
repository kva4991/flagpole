# Отчёт по доработке v0.7.1

Дата: 2026-08-02

## Что сделано

### 1. Идентификаторы деталей на чертежах

Введены стабильные ID вида:

- `#petg-1 ... #petg-8`
- `#tpu95-1 ... #tpu95-9`
- `#tpu85-1 ... #tpu85-4`

Они нанесены на актуальные v0.6-изображения:

- `mechanical/preview_v06_exploded_PETG_TPU_ids.png`
- `mechanical/preview_v06_print_PETG_ids.png`
- `mechanical/preview_v06_print_TPU95_ids.png`
- `mechanical/preview_v06_print_TPU85_ids.png`

Реестр:

- `mechanical/docs/PART_IDENTIFIERS_RU.md`
- `mechanical/part_id_registry_v06.json`

### 2. Раздельные очереди печати

Зафиксировано правило: за один запуск печатается только один основной пластик.

Отдельно вынесены:

- PETG
- TPU 95A
- TPU 85A

На сайт каталога после блока «Интерактивные 3D-модели» добавлен последний ряд:

- `Очередь печати PETG`
- `Очередь печати TPU 95A`
- `Очередь печати TPU 85A`

### 3. Белые детали на рендерах

Очень светлые детали в рендерах сделаны сероватыми, чтобы не сливаться с фоном.

### 4. Светоотражающая ткань

Добавлены характеристики:

- основа: нейлон
- покрытие: светоотражающее
- плотность: 180
- световозвращение: 320 кандел
- уход: протирание, допускается глажение

Обновлены:

- `catalog/components.json`
- `mechanical/docs/FLAG_ATTACHMENT_LOOPS_RU.md`

### 5. Пояснение по отверстию рядом со спицей

Зафиксировано объяснение: отверстие выше силовой зоны спицы — это кабельный выход к флагу под TPU95-разгрузку, а не вторая посадка под спицу.

Документировано в:

- `mechanical/docs/ASSEMBLY_PETG_TPU_RU.md`

### 6. Каталог и тесты

Обновлены:

- `catalog/drawings.json`
- `scripts/generateComponentCatalog.mjs`
- `catalog/catalog.html`
- `tests/componentCatalog.test.mjs`
- `CHANGELOG.md`
- `docs/NEXT_CHAT_START_HERE_RU.md`

Проверки:

- `npm test` — успешно
- `npm run quality:docs` — успешно
- `npm run catalog:check` — успешно
- `npm run checksums:check` — успешно
