# Как изменить название проекта и BLE-устройства

Название приложения и имя Bluetooth больше не разбросаны по исходникам. Единственный редактируемый источник:

```text
project_identity.json
```

В нём находятся две понятные переменные:

```json
{
  "projectDisplayName": "Crucian",
  "bluetoothDeviceName": "Crucian"
}
```

Их смысл:

- `projectDisplayName` — **имя вашего проекта**, показываемое в Android-приложении и локальном каталоге;
- `bluetoothDeviceName` — имя BLE-устройства, которое рекламирует ESP32-C3 и по которому Android его ищет.

После изменения выполнить из корня проекта:

```powershell
npm.cmd run identity:generate
npm.cmd run catalog:generate
```

Генератор обновит:

- `electronics/firmware/esp32_c3_crucian_v06/include/project_identity.h`;
- `android/crucian-control/app/src/main/java/ru/quicktickets/crucian/ProjectIdentity.kt`;
- `android/crucian-control/app/src/main/res/values/strings.xml`;
- заголовки локальной страницы при следующей генерации каталога.

Проверка синхронизации:

```powershell
npm.cmd run identity:check
npm.cmd run catalog:check
```

## Что намеренно не меняется автоматически

Android `applicationId` и Kotlin package остаются:

```text
ru.quicktickets.crucian
```

Это технический идентификатор приложения, а не видимое название. Его автоматическое изменение нарушило бы обновление уже установленного APK и потребовало бы переименования каталогов исходников. Другой разработчик может изменить его отдельно, но для обычной смены имени проекта это не требуется.
