# victor-node

Моніторинг і керування віддаленим інвертором **Victor NM-ECO 6.2KW PLUS** та батареєю з **JK BMS (JK-B1A24S15P)** з домашнього Home Assistant. Інвертор стоїть за ~300 км, на місці є лише Wi-Fi, а вдома CGNAT.

```
Дача                                         Інтернет                  Дім
Victor ─RJ45/RS232─┐                                                   ┌─ Mosquitto (HA add-on)
                   ├─ ESP32 ── Wi-Fi ── MQTT/TLS ──► flespi ◄── міст ──┤
JK BMS ─Bluetooth──┘   │                                               └─ Home Assistant: дашборд «Дача»,
                       └─ локальні правила заряду (працюють без інтернету)   сповіщення, користувач-родич
```

Для агентів (Codex, Antigravity, Claude): [AGENTS.md](AGENTS.md). Поточний стан і наступні кроки: [docs/STATUS.md](docs/STATUS.md).

## Що в репозиторії
| Шлях | Що це |
|---|---|
| `esphome/victor.yaml` | Прошивка для дачі: Modbus 2341 + JK BMS + правила |
| `esphome/victor-pi30.yaml` | Прототип для домашнього SP-3200 (PI30), той самий канал зв'язку |
| `esphome/victor-probe.yaml` | Пошук протоколу інвертора, логи через MQTT |
| `esphome/packages/` | Частини прошивки (база, MQTT, OTA, світлодіод, інвертор, BMS, правила) |
| `mosquitto/flespi-bridge.conf` | Міст домашнього Mosquitto з flespi |
| `homeassistant/packages/victor.yaml` | Сповіщення |
| `homeassistant/dashboards/dacha.yaml` | Дашборд «Дача» |
| `tools/` | Збірка, встановлення мосту, віддалене OTA, читання MQTT |
| `docs/` | Залізо, міст, прошивка, тест вдома, інструкція для родича, runbook |

## Порядок робіт
1. [Залізо](docs/hardware.md): зібрати блок, виставити 5 В на MINI-360.
2. [Міст](docs/bridge.md): токени flespi, `tools/ha-enable-bridge.sh`.
3. [Прошивка](docs/firmware.md): `tools/build.sh victor-pi30.yaml`, перша прошивка по USB.
4. [Тест вдома](docs/home-test.md) на SP-3200 за чек-листом.
5. [Home Assistant](docs/home-assistant.md): пакет, дашборд, користувач для родича.
6. Прошити `victor.yaml`, відправити блок, [інструкція для родича](docs/onsite-uk.md).
7. Якщо щось не так: [runbook](docs/runbook.md).

## Open source, на якому це стоїть
| Проєкт | Що беремо | Як підключено |
|---|---|---|
| [ESPHome](https://esphome.io) 2026.9 | Прошивка, `pipsolar`, `modbus_controller`, OTA, BLE | Встановлено в `.venv` |
| [aver-ua/esphome-hybrid-inverter-2341](https://github.com/aver-ua/esphome-hybrid-inverter-2341) (fork [odya](https://github.com/odya/esphome-powmr-hybrid-inverter)) | Регістри Modbus 2341, сенсори, селекти, добові лічильники, приклад дашборда | Копія в `esphome/vendor/aver-ua` (commit `9c607d6`) + патч на 1 рядок під ESPHome 2026.9 |
| [syssi/esphome-jk-bms](https://github.com/syssi/esphome-jk-bms) | JK BMS по BLE | External component з GitHub, commit `59c994e` |
| [Travis90x/esphome-pipsolar](https://github.com/Travis90x/esphome-pipsolar) | Перебір протоколів і швидкостей | Скопійовано в `victor-probe.yaml` з атрибуцією |
| [flespi](https://flespi.com/kb/mosquitto-flespi-mqtt-bridge) | Шаблон мосту Mosquitto | `mosquitto/flespi-bridge.conf` |
| [sunsynk-power-flow-card](https://github.com/slipx06/sunsynk-power-flow-card), [jk-bms-card](https://github.com/Pho3niX90/jk-bms-card) | Картки дашборда | HACS |

Своє написано лише там, де готового не знайшлося: правила заряду на самому блоці (`packages/rules-soc.yaml`), вибір BMS з HA без перепрошивки, світлодіод стану, віддалене OTA через HA, оцінка енергії з мережі та сповіщення.
