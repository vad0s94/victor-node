# Runbook: що робити, якщо щось не так

Спершу визначи, на якому відрізку обрив:
```bash
tools/mqtt-sub.sh 'victor/bridge/state' 10      # 1 = міст дім↔flespi працює
tools/mqtt-sub.sh 'victor/node/status' 10        # online / offline (LWT вузла)
tools/mqtt-sub.sh 'victor/node/#' 30             # чи йдуть дані взагалі
```
Панель flespi → MQTT → Sessions: видно, чи підключені `victor-node` і `ha-home-bridge`.

| Симптом | Ймовірна причина | Що робити |
|---|---|---|
| `bridge/state` = 0 або порожньо | Mosquitto не підключився до flespi | Settings → Add-ons → Mosquitto → Log. Неправильний токен `home-bridge`, токен прострочений, або вимкнено `customize`. `tools/ha-enable-bridge.sh` ще раз |
| Міст 1, вузол `offline`, у flespi сесії `victor-node` немає | На об'єкті немає світла / Wi-Fi / інтернету | Спитати про світлодіод ([onsite-uk.md](onsite-uk.md)). Швидке блимання = Wi-Fi: через «Victor Setup» |
| Вузол online, сутностей в HA немає | Discovery не дійшов | Перезапустити HA (він шле `homeassistant/status`, міст передає, вузол перевідправляє discovery). Перевірити `tools/mqtt-sub.sh 'homeassistant/+/victor/#' 20` |
| `Inverter Link` = off | Не той протокол / TX-RX навпаки / кабель | [firmware.md](firmware.md) → «Якщо Victor не відповідає» |
| Дані є, зміни налаштувань не застосовуються | Інвертор хоче Modbus 0x10 | `modbus_write_multiple: "true"`, зібрати, `tools/ota-remote.sh` |
| `BMS Online Status` = off | Не той MAC, хтось підключений застосунком JK, або протокол | `sensor.victor_bms_found_devices` → вписати MAC у `text.victor_bms_mac`. Попросити закрити застосунок JK. HW < 11: `bms_protocol: JK02_24S` |
| Енергія за день стрибнула в нуль | Перезавантаження після >5 хв без збереження | Норма: втрачаються максимум останні 5 хв. Довгострокова статистика HA не ламається |
| Правило не спрацьовує | Вимкнене, немає свіжих даних BMS чи зв'язку з інвертором, або 5-хв пауза між записами | `sensor.victor_rules_last_action`, `binary_sensor.victor_bms_online_status`, `binary_sensor.victor_inverter_link` |
| Акаунт flespi зник | 60 днів без входу в панель (умова Free) | Створити заново, нові токени, `secrets.yaml` + OTA, `ha-enable-bridge.sh`. Заходити в панель раз на місяць |
| Після OTA вузол не повернувся | Новий образ не стартує | Почекати ~10 хв: `safe_mode` повертає попередню прошивку. Якщо ні — перезапустити живлення на місці (вийняти RJ45 на 10 с) |

## Заміна токенів flespi
1. Створити нові токени (`victor-node`, `home-bridge`), старі видалити.
2. `esphome/secrets.yaml` → новий `flespi_token`, `tools/build.sh victor.yaml`.
3. **Спершу** OTA вузла старим каналом (`tools/ota-remote.sh`), **потім** видаляти старий `victor-node`: інакше вузол втратить зв'язок і оновитися не зможе.
4. `tools/ha-enable-bridge.sh` з новим `home-bridge`.

## Сертифікат flespi
Прошивка довіряє GlobalSign Root R6 (до 2034) і R1 (до 2028). Якщо flespi змінить центр сертифікації, MQTT перестане підключатись. Перевірка:
```bash
echo | openssl s_client -connect mqtt.flespi.io:8883 -CAfile esphome/certs/flespi-ca.pem 2>/dev/null | grep "Verify return code"
```
`0 (ok)` = усе добре. Інакше: `tools/update-flespi-ca.sh`, зібрати й прошити **до** того, як старий сертифікат перестане діяти.
