# Быстрый вход в проект для нового чата

<!-- §faststart -->

## Сначала

1. Прочитать корневой [`AGENTS.md`](../AGENTS.md): там находятся полный рабочий процесс и условия синхронизации карточек, чертежей, GLB и HTML-каталога.
2. Выполнить `git status --short --branch` и подтвердить реальную ветку.
3. Прочитать [`current-implementation-status.ru.md`](current-implementation-status.ru.md).
4. Прочитать разделы затронутой подсистемы в [`AUDIT_V061_RU.md`](AUDIT_V061_RU.md).
5. Найти нужный §-тег в [`dev/tag-map.md`](dev/tag-map.md).
6. Для архитектурного изменения открыть [`architecture/decisions/README.ru.md`](architecture/decisions/README.ru.md).
7. Для любого чертежа, 3D-модели или печатной раскладки определить ID в `catalog/drawings.json` и до правки полностью прочитать `../catalog/media-descriptions/<ID>.md`. §mediarationale1

## Маршрут по типу задачи

| Задача | Читать | Минимальная проверка |
| --- | --- | --- |
| Документация | `DOCUMENTATION_WORKFLOW_RU.md` | `npm.cmd run quality:docs:all` |
| Каталог компонентов или физические размеры | `catalog/README_RU.md`, `catalog/physical-components.json` | `npm.cmd run catalog:check` |
| CAD-заготовка без генерации | `mechanical/cad_drafts/*.json`, связанный документ, ADR и `catalogPolicy.cadDraftSources` | `npm.cmd run catalog:check`; убедиться, что planned outputs отсутствуют |
| Чертёж, 3D-модель или раскладка | `catalog/media-descriptions/<ID>.md`, `CATALOG_MEDIA_POLICY_RU.md` | `npm.cmd run media:descriptions:check` |
| Прошивка BLE/PWM | `electronics/README_V06_RU.md`, ADR-0001/0002 | PlatformIO build и стенд |
| Android BLE | `android/README_RU.md`, аудит v0.6.1 | Gradle build и реальный телефон |
| Механика | `MEASUREMENTS_REQUIRED_RU.md`, `mechanical/docs/` | генерация, STL-аудит, купоны |

## Перед завершением

### Обязательное правило Windows

На Windows не запускать Python и команды, которые вызывают его через npm/Node,
из исходного Git-worktree даже для пробной проверки. Сначала синхронизировать
актуальное дерево в `%USERPROFILE%\Documents\pesochnica\flagpole\worktree`, затем
выполнять проверку только из этой защищённой копии. При `spawnSync py EPERM`
не повторять запуск в исходной папке: это ограничение места исполнения.

Из защищённой синхронизированной копии выполнить единый режим:

```powershell
.\build.cmd validate
```

Эквивалентные узкие команды для диагностики:

```powershell
npm.cmd run review:impact
npm.cmd run media:descriptions:check
npm.cmd run quality:docs:all
npm.cmd run catalog:check
npm.cmd test
npm.cmd run checksums:check
git diff --check
```

Windows-компьютер готовится и проверяется через `tools/windows/setup.ps1` и
`tools/windows/check.ps1`. GitHub Actions независимо повторяет quality gate,
Android-сборку и обе PlatformIO-сборки. §toolwin

Ручные и аппаратные проверки из `review:impact` нельзя заменять зелёным Node-тестом. §status1
