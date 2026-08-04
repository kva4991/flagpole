# Карта стабильных тегов документации

§-тег связывает правило, rationale, аудит и тест без привязки к номеру строки. Новый тег добавляется только для устойчивого контракта. §docqa01

| Тег | Контракт | Основной документ |
| --- | --- | --- |
| `§faststart` | Короткий маршрут нового чата | `docs/agent-fast-start.ru.md` |
| `§status1` | Граница между кодом, локальной проверкой и физическим доказательством | `docs/current-implementation-status.ru.md` |
| `§audit61` | Датированный аудит handoff v0.6.1 | `docs/AUDIT_V061_RU.md` |
| `§docqa01` | Уровни документации и локальный аудит | `docs/DOCUMENTATION_WORKFLOW_RU.md` |
| `§adrproc` | Неизменяемая последовательная история ADR | `docs/architecture/decisions/README.ru.md` |
| `§impact` | Карта влияния путей и обязательных проверок | `docs/quality-assistants/change-impact.ru.md` |
| `§toolwin` | Windows toolchain и изолированная исполняемая зона | `tools/README.ru.md` |
| `§checksum` | SHA-256 manifest публикуемого дерева | `docs/DOCUMENTATION_WORKFLOW_RU.md` |
| `§catalog` | JSON — источник HTML-каталога | `catalog/README_RU.md` |
| `§physicalcomponents1` | Физические размеры покупных компонентов редактируются один раз и доступны по стабильным ссылкам карточек | `catalog/physical-components.json`; `catalog/README_RU.md`; ADR-0034 |
| `§bearingadapter1` | Два 6806 получают жёсткие PETG-втулки без TPU; независимые пробники посадок строятся из одного файла размеров | `mechanical/cad_drafts/petg_6806_adapter_v076.json`; `mechanical/docs/PETG_6806_BEARING_ADAPTER_RU.md`; ADR-0035 |
| `§lowercablestrain1` | Нижний торец секции получает закрытую TPU85-разгрузку с двумя каналами Ø2 мм, гибким хвостом и обязательным свободным запасом провода | `mechanical/cad_drafts/tpu85_lower_pole_strain_relief_v076.json`; `mechanical/docs/LOWER_POLE_CABLE_STRAIN_RELIEF_RU.md`; ADR-0036 |
| `§meas001` | Геометрия меняется только по реальным измерениям | `MEASUREMENTS_REQUIRED_RU.md` |
| `§mech001` | Спица между подшипниками, токосъёмник не несущий | `docs/architecture/decisions/0003-structural-material-boundaries.ru.md` |
| `§mat0001` | Купленный оранжевый PETG используется сейчас; ASA возможна позднее после повторной проверки посадок | `docs/architecture/decisions/0012-petg-now-asa-later.ru.md` |
| `§power01` | 6×18650 и регулируемая 12-вольтовая шина | `docs/architecture/decisions/0001-power-and-load-path.ru.md` |
| `§slip001` | M125-0205 предпочтителен, M125U-06 резервный | `docs/AUDIT_V061_RU.md` |
| `§ble0001` | Часовое BLE-окно только после настоящего включения питания | `docs/architecture/decisions/0002-ble-service-window.ru.md` |
| `§blesec1` | PIN и bond не раскрываются через GATT | `docs/AUDIT_V061_RU.md` |
| `§fwfail1` | Ошибка датчика и неверная калибровка выключают нагрузку безопасно | `docs/AUDIT_V061_RU.md` |
| `§env001` | Комбинированный AHT20+BMP280 питается от 3,3 В и измеряет температуру, влажность и давление | `docs/architecture/decisions/0007-combined-aht20-bmp280.ru.md` |
| `§envmech1` | Карман использует мембрану Ø20/Ø10 и семь послепечатных отверстий Ø2 | `mechanical/docs/ENV_SENSOR_POCKET_RU.md` |
| `§lightwell1` | Окно VEML7700 вырезается из имеющегося прозрачного PET либо имеющегося УФ-стойкого поликарбоната и калибруется после установки | `docs/architecture/decisions/0010-cut-light-well-window.ru.md` |
| `§flagsew1` | Флаг шьётся УФ-стойкой bonded-полиэстеровой нитью Tex 45; Tex 70 допускается только после пробы машины и ткани | `docs/architecture/decisions/0011-flag-sewing-thread.ru.md` |
| `§android1` | Android требует воспроизводимой сборки и последовательного GATT | `docs/AUDIT_V061_RU.md` |
| `§flagpower1` | Два провода проходят ниже крепежа через направляющую около 35° и единственный TPU95-ввод | `docs/architecture/decisions/0017-external-flag-power-cable-route.ru.md` |
| `§partid1` | Стабильные ID печатных деталей синхронизируются с реестром, чертежами и STL | `mechanical/docs/PART_IDENTIFIERS_RU.md` |
| `§weather73` | Крышка, световой тоннель и климатический карман используют независимые обслуживаемые барьеры | `docs/architecture/decisions/0018-multibarrier-weatherproofing.ru.md` |
| `§flagloop73` | Верхняя лямка привязана к низу навершия, нижняя — к низу флага | `docs/architecture/decisions/0021-flag-loop-datum-below-finial.ru.md` |
| `§drawstatus73` | Изготовление ведётся только по current-карточкам; current-механика полностью параметрическая | `docs/architecture/decisions/0025-fully-parametric-current-mechanics.ru.md` |
| `§cadworkflow` | Пилотный точный CAD-контур build123d-mcp | `mechanical/docs/BUILD123D_MCP_WORKFLOW_RU.md`; ADR-0029 |
| `§build01` | Единая сборка и экономная загрузка Git LFS в CI | `docs/architecture/decisions/0030-git-lfs-and-unified-build.ru.md` |
| `§prunegen1` | Устаревшие бинарные генерации не дублируются в текущем дереве и доступны через историю Git | `docs/architecture/decisions/0037-prune-superseded-generated-binaries.ru.md` |
| `§license01` | Аппаратный источник использует CERN-OHL-S-2.0, собственное ПО — MIT, сторонние материалы сохраняют исходные условия | `LICENSE.md`; ADR-0031 |
| `§mediarationale1` | Для каждого рисунка, 3D-модели и очереди печати существует один одноимённый подробный Markdown-файл, обновляемый вместе с медиа | `catalog/media-descriptions/README_RU.md`; ADR-0032 |
| `§mediacontract1` | Каждый медиа-ID начинается с краткого проверяемого контракта: сохранить, запрещено, проверить | `catalog/media-descriptions/README_RU.md`; ADR-0033 |
