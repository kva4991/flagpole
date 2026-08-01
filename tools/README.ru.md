# Подготовка Windows для Crucian

<!-- §toolwin -->

В репозитории закреплён воспроизводимый набор инструментов для документации,
Android и двух проектов ESP32-C3. Версии и компоненты объявлены в
`tools/toolchain.json`, установка выполняется сценариями из `tools/windows/`.

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
загрязняется пакетами. Туда же направлен Gradle-кэш, а результаты ручного
экспорта следует класть в `artifacts`. Антивирусное исключение должно
охватывать только папку `flagpole`, не весь каталог `Documents` или исходный
Git-репозиторий.

Скрипт сохраняет пользовательские переменные `FLAGPOLE_EXECUTION_ROOT`,
`PLATFORMIO_CORE_DIR` и `GRADLE_USER_HOME`. Другую папку внутри `pesochnica`
можно передать параметром `-ExecutionRoot`; путь за пределами этой зоны
отвергается.

Перед сборкой исходники синхронизируются без `.git` и локальных кэшей в
`flagpole\worktree`. Сборка выполняется только из этой одноразовой копии.
Готовые файлы появляются в `flagpole\artifacts`:

- `crucian-control-debug.apk`;
- `crucian-v06-firmware.bin`;
- `flag-light-legacy-firmware.bin`.

После первого запуска следует открыть новый PowerShell или новый чат Codex,
чтобы процесс получил обновлённые `PATH`, `JAVA_HOME`, `ANDROID_HOME` и
`ANDROID_SDK_ROOT`.

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

Установка инструментов и успешная компиляция не заменяют тесты на ESP32-C3,
телефоне, датчике VEML7700 и силовой нагрузке. §status1

## GitHub Actions

`.github/workflows/validate.yml` повторяет проверки независимо от Windows:

- запускает `npm run quality:gate`;
- собирает Android debug APK через Wrapper;
- собирает оба проекта PlatformIO в матрице;
- публикует APK и два `firmware.bin` как workflow artifacts.

Это основной резервный путь, если локальный антивирус или сетевой фильтр
блокирует загрузку крупного ESP32 toolchain. Зелёная компиляция в GitHub также
не заменяет аппаратный стенд.
