# Архитектурные решения

Принятые решения не переписываются задним числом. Изменение оформляется новым последовательным ADR. §adrproc

| ADR | Статус | Решение |
| --- | --- | --- |
| [0001](0001-power-and-load-path.ru.md) | Принято | Внешняя 6×18650-подсистема предоставляет стабилизированные 12 В |
| [0002](0002-ble-service-window.ru.md) | Принято | BLE-окно один час после настоящего включения питания |
| [0003](0003-structural-material-boundaries.ru.md) | Принято | Два подшипника, боковая спица и границы TPU |
| [0004](0004-documentation-process.ru.md) | Принято | Управляемая документация и quality gate |
| [0005](0005-asa-preferred-outdoor-material.ru.md) | Принято | ASA как возможный наружный материал |
| [0006](0006-environment-sensors.ru.md) | Заменено 0007 | Переход от NTC к цифровым датчикам |
| [0007](0007-combined-aht20-bmp280.ru.md) | Принято | Комбинированный AHT20+BMP280 |
| [0008](0008-environment-sensor-pocket.ru.md) | Принято | Нижний защищённый карман датчика |
| [0009](0009-electronics-vent-membrane.ru.md) | Заменено 0023 | Предварительный малый формат vent-мембраны |
| [0010](0010-cut-light-well-window.ru.md) | Принято | Вырезаемое прозрачное окно VEML7700 |
| [0011](0011-flag-sewing-thread.ru.md) | Принято | УФ-стойкая полиэстеровая нить |
| [0012](0012-petg-now-asa-later.ru.md) | Принято | PETG сейчас, ASA позднее после купонов |
| [0013](0013-project-identity-source.ru.md) | Принято | Единый источник имени проекта и BLE |
| [0014](0014-captive-nut-pockets.ru.md) | Принято | Параметрические закладные карманы |
| [0015](0015-flag-attachment-loops.ru.md) | Принято | Четыре тканевые лямки |
| [0016](0016-android-ble-state-machine.ru.md) | Принято | Android BLE state machine и очередь GATT |
| [0017](0017-external-flag-power-cable-route.ru.md) | Заменено 0022 | Базовый наружный маршрут питания |
| [0018](0018-multibarrier-weatherproofing.ru.md) | Принято | Независимые обслуживаемые барьеры |
| [0019](0019-flag-loop-placement.ru.md) | Заменено 0021 | Старое положение лямок относительно полотна |
| [0020](0020-drawing-status-and-canonical-meshes.ru.md) | Заменено 0025 | Переходные канонические сетки v0.7.3 |
| [0021](0021-flag-loop-datum-below-finial.ru.md) | Принято | Верхняя лямка на 10 мм ниже низа навершия |
| [0022](0022-angled-flag-wire-guide.ru.md) | Принято | `#tpu95-10` под 35° в отмеченной точке |
| [0023](0023-adhesive-membrane-20mm-seven-holes.ru.md) | Принято | Мембрана Ø20 и семь отверстий Ø2 |
| [0024](0024-removable-electronics-carrier.ru.md) | Принято | Съёмный двухуровневый каркас электроники |
| [0025](0025-fully-parametric-current-mechanics.ru.md) | Принято | Полностью параметрическая current-механика |
| [0026](0026-current-only-catalog-and-part-id-callouts.ru.md) | Принято | Только актуальные карточки и обязательные ID-выноски вне раскладок печати |
- [ADR-0027: чистые миниатюры и управляемые ID-метки](0027-clean-thumbnails-and-controllable-id-callouts.ru.md)
- [ADR-0028: компактные одно-материальные раскладки](0028-compact-single-material-print-layouts.ru.md)
- [ADR-0029: build123d-mcp как вспомогательный CAD-контур](0029-build123d-mcp-pilot.ru.md)
