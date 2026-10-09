# Status (2026-10-09)

## Зроблено
- [x] Архітектура й рішення (див. AGENTS.md): flespi + міст, ESPHome, один HA, окремий доступ для спостерігача.
- [x] Прошивки `victor.yaml`, `victor-pi30.yaml`, `victor-probe.yaml`: валідні, компілюються (ESPHome 2026.9.1, ESP-IDF 5.5.5).
  - victor.yaml: Flash 81.7 %, RAM (static) 87.3 %
  - victor-pi30.yaml: Flash 78.9 %, RAM 73.5 %
  - victor-probe.yaml: Flash 53.8 %, RAM 28.4 %
- [x] JK BMS: усі 45 параметрів і 17 перемикачів доступні з HA (крім `shutdown`), вибір BMS за MAC з HA.
- [x] Правила на блоці (струм заряду за SOC, мережа при низькому SOC), за замовчуванням вимкнені.
- [x] HA: пакет сповіщень, дашборд СЕС, вкладка налаштувань для адміна. `tools/check-entities.py` = 0 пропусків.
- [x] Міст `mosquitto/flespi-bridge.conf`, скрипти встановлення, віддаленого OTA, читання MQTT.
- [x] Документація для власника й інструкція для людини на місці.
- [x] **Відкритий конструктор для масового користувача:**
  - `tools/constructor.py` — інтерактивний wizard та CLI генератор конфігурацій (будь-який інвертор, BMS, плата, транспорт, правила).
  - Транспорти на вибір: Native HA API (без брокера), Universal MQTT (будь-який брокер), TLS MQTT, flespi.
  - Готові профілі: `powmr-jk-api`, `powmr-jk-mqtt`, `powmr-nobms-api`, `voltronic-jk-api`, `voltronic-nobms-api`.
  - Підтримка Improv Serial та ESPHome Web Tools для прошивки з браузера.
- [x] **GitHub Actions CI/CD:**
  - `.github/workflows/ci.yml` — валідація конфігурацій та сутностей.
  - `.github/workflows/release.yml` — збірка матриці бінарників (`.factory.bin`, `.ota.bin`, `.md5`) та публікація в GitHub Releases.
  - `.github/workflows/build-custom.yml` — онлайн-конструктор прошивок через браузер (workflow_dispatch) без встановлення ESPHome.
- [x] **Open Source готовність:** ліцензія Apache 2.0 (`LICENSE`), подяки (`NOTICE.md`), універсальний шаблон мосту (`mosquitto/bridge-universal.conf.example`), оновлений `README.md`.

## Не перевірено / відкрито
- [ ] Жодна прошивка ще не запускалась на залізі (ESP32U і D1 Mini ESP32 замовлені).
- [ ] `tools/ha-enable-bridge.sh`, `tools/ota-remote.sh`, `tools/mqtt-sub.sh` не запускались проти живого HA.
- [ ] Протокол Victor (Modbus 2341 — найімовірніше) підтвердиться лише на місці.
- [ ] Реальні entity id в HA: прогнозовані `victor_*`, перевірити після першого підключення.
- [ ] Heap на залізі при BLE + TLS + web_server (static RAM 87 %).
- [ ] `HA_PUBLIC_URL` (адреса cloudflared) для OTA через інтернет — власник знає, у репо не записано.

## Наступні кроки (по черзі)
1. Власник: токени flespi `victor-node`, `home-bridge`; заповнити `esphome/secrets.yaml`.
2. `tools/ha-enable-bridge.sh` (з дозволу власника), перевірка за docs/bridge.md.
3. Коли приїде ESP32: зібрати блок (docs/hardware.md), `victor-pi30.yaml` по USB, чек-лист docs/home-test.md.
4. HA: HACS-картки, пакет, дашборд (docs/home-assistant.md); звірити entity id.
5. Прошити `victor.yaml`, відправити блок, docs/onsite-uk.md людині на місці.
6. На місці: якщо `Inverter Link` = off → docs/firmware.md → «Якщо Victor не відповідає».
7. Потім: InfluxDB + Grafana для довгої історії (ще не почато).
