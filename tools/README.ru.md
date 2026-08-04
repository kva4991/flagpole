# Подготовка Windows для Super_pommels_and_flag

<!-- §toolwin -->

В репозитории закреплён воспроизводимый набор инструментов для документации,
Android и двух проектов ESP32-C3. Версии и компоненты объявлены в
`tools/toolchain.json`, установка выполняется сценариями из `tools/windows/`.

> **Обязательное правило:** не запускать Python и команды npm/Node, которые
> косвенно вызывают Python, из исходного Git-worktree даже один раз «для
> проверки». Сначала синхронизировать актуальное дерево в
> `%USERPROFILE%\Documents\pesochnica\flagpole\worktree`, затем выполнять их
> только оттуда. `spawnSync py EPERM` вне защищённой зоны означает ограничение
> места исполнения; повторять запуск в исходной папке не нужно.

Только проверить компьютер:

```powershell
powershell -ExecutionPolicy Bypass -File tools\windows\check.ps1
```

Установить отсутствующие компоненты, принять Android SDK licenses, прогреть
Gradle Wrapper и собрать обе прошивки:

```powershell
powershell -ExecutionPolicy Bypass -File tools\windows\setup.ps1 -Install -AcceptAndroidLicenses
```

Сценарий устанавливает Git/Git Bash, Python, Node.js, JDK 17, GitHub CLI,
7-Zip, ripgrep, Android SDK 35 и PlatformIO Core. PlatformIO устанавливается
официальным installer script в изолированную исполняемую зону
`%USERPROFILE%\Documents\pesochnica\flagpole\.platformio`; глобальный Python не
загрязняется пакетами. Зависимости генерации механики из
`mechanical/requirements.txt` устанавливаются в отдельную среду
`flagpole\.mechanical-venv`; в неё входит переносимый SVG-рендерер `resvg-py`,
поэтому системный Cairo не нужен. Туда же направлен Gradle-кэш, а результаты ручного
экспорта следует класть в `artifacts`. Антивирусное исключение должно
охватывать только папку `flagpole`, не весь каталог `Documents` или исходный
Git-репозиторий.

Скрипт сохраняет пользовательские переменные `FLAGPOLE_EXECUTION_ROOT`,
`PLATFORMIO_CORE_DIR` и `GRADLE_USER_HOME`. Другую папку внутри `pesochnica`
можно передать параметром `-ExecutionRoot`; путь за пределами этой зоны
отвергается.

Перед любой сборкой или проверкой с Python исходники синхронизируются без `.git`
и локальных кэшей в `flagpole\worktree`. Сборка и Python-проверки выполняются
только из этой одноразовой копии. Чистые Node-проверки, заведомо не запускающие
Python, можно выполнять в исходном Git-worktree.
Готовые файлы появляются в `flagpole\artifacts`:

- `crucian-control-debug.apk`;
- `crucian-v06-firmware.bin`;
- `flag-light-legacy-firmware.bin`.

После первого запуска следует открыть новый PowerShell или новый чат Codex,
чтобы процесс получил обновлённые `PATH`, `JAVA_HOME`, `ANDROID_HOME` и
`ANDROID_SDK_ROOT`.

## Единая сборка

После синхронизации исходников в `flagpole\worktree` регенерация канонических
build123d-деталей, постера #204, каталога и проверок выполняется одной командой:

```powershell
.\build.cmd all
```

Режимы `generate`, `validate` и `catalog` позволяют выполнить только нужный
слой. Старые справочные схемы и непечатные сцены в эти режимы не входят. Их
отдельный режим `legacy-references` запускается только по прямому запросу
владельца. `tools/windows/build.ps1` намеренно отказывается запускать
генераторы вне `%USERPROFILE%\Documents\pesochnica\flagpole`, использует
`.mechanical-venv` и `.venv-build123d`, задаёт UTF-8. §build01

Git for Windows должен предоставлять `git lfs`. STL и GLB хранятся через LFS, PNG остаются в обычном Git. CI выполняет `git lfs pull` только в одной условной механической задаче; Android и PlatformIO не скачивают модели.

## Точный CAD: build123d/OCP, FreeCAD и OpenSCAD

FreeCAD и OpenSCAD устанавливаются штатно в стандартные папки Windows через
winget. build123d и OCP являются Python-пакетами, поэтому устанавливаются не как
Windows-программы, а в отдельную среду
`%USERPROFILE%\Documents\pesochnica\flagpole\.venv-build123d`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\windows\setup-cad.ps1 -Install
```

Сценарий повторяет фактически проверенную установку:

```powershell
winget install --id FreeCAD.FreeCAD --exact --source winget
winget install --id OpenSCAD.OpenSCAD --exact --source winget
py -3.12 -m venv "$env:USERPROFILE\Documents\pesochnica\flagpole\.venv-build123d"
& "$env:USERPROFILE\Documents\pesochnica\flagpole\.venv-build123d\Scripts\python.exe" -m pip install build123d==0.11.1 cadquery-ocp-novtk==7.9.3.1.1 trimesh==5.0.0
```

На проверенном компьютере установлены FreeCAD 1.1.3, OpenSCAD 2021.01,
build123d 0.11.1 и OCP 7.9.3.1.1. Повторный запуск без `-Install` только
проверяет наличие программ и импорт модулей. Общий `setup.ps1 -Install` теперь
также вызывает этот CAD-установщик. §cadworkflow

Android собирается закреплённым Wrapper:

```powershell
android\crucian-control\gradlew.bat -p android\crucian-control :app:assembleDebug
```

Прошивка Crucian v0.6:

```powershell
pio run --project-dir electronics\firmware\esp32_c3_crucian_v06
```

Историческая прошивка подсветки:

```powershell
pio run --project-dir electronics\firmware\esp32_c3_flag_light
```

Генерация и проверка актуальной механики из защищённой зоны:

```powershell
& "$env:FLAGPOLE_EXECUTION_ROOT\.venv-build123d\Scripts\python.exe" mechanical\generate_build123d_canonical_v076.py
& "$env:FLAGPOLE_EXECUTION_ROOT\.mechanical-venv\Scripts\python.exe" mechanical\generate_reference_diagrams_v06.py
& "$env:FLAGPOLE_EXECUTION_ROOT\.mechanical-venv\Scripts\python.exe" mechanical\generate_detail_diagrams_v075.py
& "$env:FLAGPOLE_EXECUTION_ROOT\.mechanical-venv\Scripts\python.exe" mechanical\generate_hermeticity_diagram_v075.py
& "$env:FLAGPOLE_EXECUTION_ROOT\.mechanical-venv\Scripts\python.exe" electronics\generate_electronics_diagrams_v075.py
& "$env:FLAGPOLE_EXECUTION_ROOT\.mechanical-venv\Scripts\python.exe" mechanical\validate_models_v06.py
```

`mechanical/generate_models_v06.py` не является генератором актуальных печатных
STL. Он оставлен только для непечатных справочных сцен `#205`, `#209`, `#210` и
не запускается в обычной регенерации печатного комплекта.

Установка инструментов и успешная компиляция не заменяют тесты на ESP32-C3,
телефоне, датчике VEML7700 и силовой нагрузке. §status1

## GitHub Actions

`.github/workflows/validate.yml` повторяет проверки независимо от Windows:

- запускает `npm run quality:core` без скачивания LFS;
- при изменениях механики один раз загружает STL/GLB и запускает `npm run build:ci`;
- собирает Android debug APK через Wrapper;
- собирает оба проекта PlatformIO в матрице;
- публикует APK и два `firmware.bin` как workflow artifacts.

Это основной резервный путь, если локальный антивирус или сетевой фильтр
блокирует загрузку крупного ESP32 toolchain. Зелёная компиляция в GitHub также
не заменяет аппаратный стенд.
