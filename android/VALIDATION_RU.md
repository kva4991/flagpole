# Проверка Android-клиента — v0.7.6

Исходники приложения синхронизированы с версией `0.7.6`: `versionCode = 5`, `versionName = "0.7.6"`, `applicationId = "ru.superpommelsandflag.crucian"`. Kotlin namespace и каталог исходников перенесены согласованно. Функциональный код BLE не менялся.

Сборка v0.7.6 должна быть подтверждена GitHub Actions в review-ветке. Последнее опубликованное доказательство для предыдущего package относится к v0.7.5 и не переносится на новый application ID.

Реальная проверка требует Android-телефон и ESP32-C3: сканирование, bonding, MTU, очередь GATT, смена PIN, команды AUTO/ON/OFF и отключение BLE.
