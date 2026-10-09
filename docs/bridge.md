# Міст flespi ↔ домашній Mosquitto

## Топіки
| Де | Топік | Напрям |
|---|---|---|
| Стан і команди вузла | `victor/node/...` | в обидва боки |
| Discovery для HA | `victor/ha/<component>/victor/...` у хмарі → `homeassistant/<component>/victor/...` вдома | хмара → дім |
| Статус HA (birth) | `homeassistant/status` → `victor/ha/status` | дім → хмара |
| Стан мосту | `victor/bridge/state` (1 = підключено) | лише вдома |

Домашні Zigbee, JK gateway і Solar2MQTT у хмару не потрапляють: міст пропускає лише ці шаблони, а токени flespi мають доступ лише до `victor/#`.

## 1. Токени flespi
Панель flespi.io → Tokens → **+** → шаблон **MQTT ACL token**. Два токени:

| Info | Для чого |
|---|---|
| `victor-node` | прошивка ESP (`flespi_token` у `esphome/secrets.yaml`) |
| `home-bridge` | міст (`tools/ha-enable-bridge.sh` спитає його) |

Для обох: Expire вимкнути, TTL максимальний, ACL → MQTT → topic `victor/#`, усі дії (publish, subscribe, retained, LWT).

Токен — це пароль. У чат і в git його не класти.

## 2. Встановити міст
З Mac у домашній мережі (скрипт ходить через Proxmox `root@192.168.31.215`, HA = VM 105):

```bash
tools/ha-enable-bridge.sh
```

Скрипт:
1. питає токен `home-bridge` (без відображення),
2. кладе `flespi-bridge.conf` з токеном у `/share/mosquitto/` HA,
3. вмикає в Mosquitto add-on опцію `customize` і перезапускає його. **На ~10 с зникнуть усі MQTT-пристрої вдома**, потім підключаться самі.

## 3. Перевірити
```bash
tools/mqtt-sub.sh 'victor/bridge/state' 10
```
Очікувано `victor/bridge/state 1`.

Перевірка в обидва боки без ESP: у панелі flespi → MQTT Board підпишись на `victor/#` і опублікуй `victor/node/test` = `hello`; вдома `tools/mqtt-sub.sh 'victor/node/test'` має його показати. Потім навпаки (на HA `mosquitto_pub` у той самий топік, у MQTT Board має з'явитись).

## Відкат
Settings → Add-ons → Mosquitto broker → Configuration → `customize.active: false` → Restart. Файл `/share/mosquitto/flespi-bridge.conf` можна видалити.
