# Проверка прошивки ESP32-C3 — v0.7.4

Код прошивки в механическом обновлении v0.7.4 функционально не изменялся. GitHub Actions run [`30753133808`](https://github.com/kva4991/flagpole/actions/runs/30753133808) для commit `a80263a` успешно собрал и опубликовал артефакты обеих линий:

- `electronics/firmware/esp32_c3_crucian_v06`;
- `electronics/firmware/esp32_c3_flag_light`.

Успешная компиляция не подтверждает PWM, MOSFET, VEML7700, AHT20+BMP280, bonding/PIN или BLE на реальном оборудовании. Нужен электрический стенд с фактическими платами и новой компоновкой бокса.
