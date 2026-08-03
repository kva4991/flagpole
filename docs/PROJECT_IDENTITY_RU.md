# Как изменить название проекта и BLE-устройства

Название приложения и имя Bluetooth больше не разбросаны по исходникам. Единственный редактируемый источник:

```text
project_identity.json
```

В нём находятся две понятные переменные:

```json
{
  "projectDisplayName": "Super_pommels_and_flag",
  "bluetoothDeviceName": "Crucian"
}
```


> В текущем выпуске публичное имя — `Super_pommels_and_flag`, а BLE-имя намеренно остаётся `Crucian`. Android package приведён к публичному имени в допустимом формате без подчёркиваний: `ru.superpommelsandflag.crucian`.

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
- `android/crucian-control/app/src/main/java/ru/superpommelsandflag/crucian/ProjectIdentity.kt`;
- `android/crucian-control/app/src/main/res/values/strings.xml`;
- заголовки локальной страницы при следующей генерации каталога.

Проверка синхронизации:

```powershell
npm.cmd run identity:check
npm.cmd run catalog:check
```

## Android-идентификатор

Android `applicationId`, `namespace` и Kotlin package:

```text
ru.superpommelsandflag.crucian
```

Он адаптирован из публичного имени: только нижний регистр и без подчёркиваний. Это новый Android application ID, поэтому он устанавливается отдельно от APK со старым `ru.quicktickets.crucian`; миграции данных между ними автоматически нет.
