# Следующему чату: прочитать до изменений

## Текущая версия

```text
0.7.4
```

## Обязательный порядок чтения

1. `AGENTS.md`
2. `docs/current-implementation-status.ru.md`
3. `UPDATE_REPORT_V074_RU.md`
4. `docs/DRAWING_AUDIT_V074_RU.md`
5. `docs/PROJECT_DECISIONS_RU.md`
6. `docs/architecture/decisions/README.ru.md`
7. `MEASUREMENTS_REQUIRED_RU.md`
8. `mechanical/docs/CAPTIVE_NUT_POCKETS_RU.md`
9. `mechanical/docs/FLAG_POWER_CABLE_ROUTE_RU.md`
10. `mechanical/docs/FLAG_ATTACHMENT_LOOPS_RU.md`
11. `mechanical/docs/PHOTO_TUNNEL_AND_VEML_MOUNT_RU.md`
12. `mechanical/docs/ENV_SENSOR_POCKET_RU.md`
13. `mechanical/docs/ELECTRONICS_CARRIER_RU.md`
14. `mechanical/docs/HERMETICITY_V074_RU.md`

## Реализовано

- полностью параметрический генератор текущей механики;
- 40 топологически проверяемых STL и семь current GLB;
- 8×M4 и 10×M3 обслуживаемых закладных;
- дорожка двух проводов 4,2 × 2,5 мм ниже крепежа;
- `#tpu95-10` под 34,99° в отмеченной владельцем точке;
- верхняя лямка на 10 мм ниже нижней кромки навершия;
- тоннель VEML7700 15 мм с отдельной клеевой полкой;
- мембрана Ø20/Ø10 и семь отверстий Ø2;
- съёмный каркас электроники `#petg-9` и опора `#petg-10`;
- обновлённый каталог, карты крепежа и компоновки;
- единая терминология «рыба».

## Проверено программно

- 35/35 Node-тестов и 92 Markdown-файла;
- 40/40 STL по топологии;
- локальная Android-сборка;
- GitHub Actions run [`30753133808`](https://github.com/kva4991/flagpole/actions/runs/30753133808) для commit `a80263a` в `main`: quality, механика, Android и обе PlatformIO-сборки успешны.

## Требует стенда

- все реальные размеры и посадочные купоны;
- печать и затяжка M3/M4;
- провод, направляющая и дождевой тест;
- VEML7700, AHT20+BMP280 и мембрана;
- нагрев DC-DC/MOSFET;
- BLE/Android/прошивка на реальных устройствах;
- солнце, конденсация, нагрузка и долговечность PETG.

## Не потерять

- печатается уже купленный оранжевый PETG;
- ASA — только будущая замена после повторных купонов;
- переходные сетки v0.7.3 архивные и не являются источником;
- имена файлов `v0_6` сохранены только для совместимости;
- зелёный тест не доказывает IP-класс, посадку или прочность.
