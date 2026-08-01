# Быстрый вход в проект для нового чата

<!-- §faststart -->

## Сначала

1. Выполнить `git status --short --branch` и подтвердить реальную ветку.
2. Прочитать [`current-implementation-status.ru.md`](current-implementation-status.ru.md).
3. Прочитать разделы затронутой подсистемы в [`AUDIT_V061_RU.md`](AUDIT_V061_RU.md).
4. Найти нужный §-тег в [`dev/tag-map.md`](dev/tag-map.md).
5. Для архитектурного изменения открыть [`architecture/decisions/README.ru.md`](architecture/decisions/README.ru.md).

## Маршрут по типу задачи

| Задача | Читать | Минимальная проверка |
| --- | --- | --- |
| Документация | `DOCUMENTATION_WORKFLOW_RU.md` | `npm.cmd run quality:docs:all` |
| Каталог компонентов | `catalog/README_RU.md` | `npm.cmd run catalog:check` |
| Прошивка BLE/PWM | `electronics/README_V06_RU.md`, ADR-0001/0002 | PlatformIO build и стенд |
| Android BLE | `android/README_RU.md`, аудит v0.6.1 | Gradle build и реальный телефон |
| Механика | `MEASUREMENTS_REQUIRED_RU.md`, `mechanical/docs/` | генерация, STL-аудит, купоны |

## Перед завершением

```powershell
npm.cmd run review:impact
npm.cmd run quality:docs:all
npm.cmd run catalog:check
npm.cmd test
npm.cmd run checksums:check
git diff --check
```

Ручные и аппаратные проверки из `review:impact` нельзя заменять зелёным Node-тестом. §status1
