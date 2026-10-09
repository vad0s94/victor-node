# Прошивка

## Варіанти
| Файл | Інвертор | Коли |
|---|---|---|
| `victor-pi30.yaml` | PI30 (`pipsolar`) | Прототип на домашньому SP-3200; запасний варіант, якщо Victor раптом PI30 |
| `victor.yaml` | Modbus 2341 (aver-ua) | Основна прошивка для дачі |
| `victor-probe.yaml` | перебір протоколів | Якщо Victor не відповідає ні на Modbus, ні на PI30 |

Усі три мають однакове ім'я вузла `victor`, MQTT-префікс і токен, тож міст і дашборд працюють з будь-якою.

## Підготовка (один раз)
```bash
cd ~/WebstormProjects/victor-node
cp esphome/secrets.example.yaml esphome/secrets.yaml   # заповнити
```
У `secrets.yaml`: домашній Wi-Fi, Wi-Fi дачі (якщо відомий), пароль точки доступу, пароль OTA, логін вебсторінки, токен flespi `victor-node`.

ESPHome уже встановлено в `.venv` (2026.9.1). Перша збірка качає тулчейн ESP-IDF і бібліотеки (~1 ГБ, 10–20 хв).

## Збірка
```bash
tools/build.sh victor-pi30.yaml
```
Результат: `esphome/build/victor-pi30.factory.bin` (для USB), `.ota.bin` (для OTA) і `.ota.md5`.

## Перша прошивка по USB
```bash
.venv/bin/esphome run esphome/victor-pi30.yaml --device /dev/cu.usbserial-XXXX
```
Порт видно в `ls /dev/cu.*`. Якщо Mac не бачить плату: драйвер WCH CH34x (для CH9102) або Silicon Labs CP210x. Кабель має передавати дані.

Альтернатива без терміналу: https://web.esphome.io → Connect → завантажити `*.factory.bin`.

## Оновлення в домашній мережі
```bash
.venv/bin/esphome run esphome/victor.yaml --device victor.local
```

## Оновлення через інтернет (блок на дачі)
Блок сам завантажує прошивку за HTTPS-посиланням. Посилання дає твій HA через cloudflared (`/local/...` віддається без логіну):

```bash
tools/build.sh victor.yaml
HA_PUBLIC_URL=https://<твій-домен-HA> tools/ota-remote.sh esphome/build/victor.ota.bin
tools/mqtt-sub.sh 'victor/node/status' 180    # offline -> online = перезавантажився
tools/ota-remote.sh --cleanup                  # обов'язково: образ містить паролі
```
Якщо новий образ не стартує, `safe_mode` відкотить на попередній після кількох невдалих завантажень.

## Якщо Victor не відповідає (немає даних інвертора, `Inverter Link` = off)
1. Поміняти TX/RX: у `victor.yaml` переставити `inverter_tx_pin` / `inverter_rx_pin`, зібрати, `ota-remote.sh`.
2. Не допомогло: прошити `victor-probe.yaml` і читати логи:
   ```bash
   tools/build.sh victor-probe.yaml
   HA_PUBLIC_URL=... tools/ota-remote.sh esphome/build/victor-probe.ota.bin
   tools/mqtt-log.sh 300
   ```
   Рядок `RX` після `>>>>> PI30` означає PI30 (`victor-pi30.yaml`; для 48 В розширити `possible_values` і `max_value` струму в `packages/inverter-pi30.yaml` до 100 А). Після `>>>>> Modbus RTU` — Modbus (лишаємо `victor.yaml`, перевірити адресу/швидкість).
3. Дані читаються, але зміни налаштувань ігноруються: у `victor.yaml` поставити `modbus_write_multiple: "true"` (Modbus функція 0x10, так треба деяким прошивкам PowMr).

## Правила на блоці (`packages/rules-soc.yaml`)
Після прошивки обидва правила **вимкнені**. Увімкнути на дашборді «Дача» → «Автоматика на блоці», коли переконаєшся, що інвертор читається і селекти працюють вручну.

| Правило | Що робить |
|---|---|
| Струм заряду від мережі за SOC | SOC < нижнього → великий струм, між → середній, вище верхнього → малий (гістерезис 2 %) |
| Мережа при низькому заряді | SOC ≤ «увімкнути» і є мережа → пріоритет виходу Utility, заряд Solar+Utility; SOC ≥ «вимкнути» → повертає звичайні режими |

Кожне налаштування інвертора змінюється не частіше ніж раз на 5 хв і лише якщо значення справді інше: налаштування пишуться в EEPROM.
