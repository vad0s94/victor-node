# Підключення до будь-якого MQTT брокера та налаштування мостів

Цей модуль може передавати дані до Home Assistant двома основними шляхами:
1. **Нативний Home Assistant API** (`transport-api.yaml`) — для роботи в одній локальній мережі або через VPN (WireGuard/Tailscale). Брокер взагалі не потрібен.
2. **MQTT** (`transport-mqtt.yaml` або `transport-mqtt-tls.yaml`) — для віддалених об'єктів або роботи через хмару.

---

## Варіант 1: Локальний Home Assistant (Native API)
Якщо ваш ESP32 і сервер Home Assistant знаходяться в одній локальній мережі:
* Використовуйте пресет з API (наприклад, `powmr-jk-api.yaml` або `voltronic-jk-api.yaml`).
* Після підключення ESP32 до Wi-Fi, Home Assistant автоматично знайде пристрій через mDNS у **Settings → Devices & Services**.
* Не потрібно налаштовувати жодних MQTT брокерів чи мостів!

---

## Варіант 2: Пряме підключення до вашого MQTT брокера
Якщо у вас є власний Mosquitto або EMQX з відкритою IP-адресою:
1. Задайте `mqtt_broker` (IP або хост) та `mqtt_port` (1883 для TCP або 8883 для TLS).
2. За потреби вкажіть `mqtt_username` та `mqtt_password`.
3. Вкажіть `discovery_prefix: homeassistant` — сенсори самі з'являться в Home Assistant.

---

## Варіант 3: Хмарний міст (коли дім за CGNAT / без білої IP)
Якщо інвертор стоїть на віддаленому об'єкті (дача, село), а домашній сервер Home Assistant знаходиться за сірою IP (CGNAT), пряме підключення додому неможливе.

Рішення: ESP32 надсилає дані у зовнішній хмарний MQTT-брокер, а домашній Mosquitto підключається до нього **мостом (MQTT bridge)** і забирає топіки до себе.

```
Віддалений вузол               Хмарний брокер                 Домашній HA (за CGNAT)
ESP32 (дача)  ──MQTT/TLS──►  [Хмара / Брокер]  ◄──MQTT міст──  Mosquitto (HA Add-on)
```

Шаблон конфігурації мосту знаходиться у файлі [`mosquitto/bridge-universal.conf.example`](../mosquitto/bridge-universal.conf.example).

### Популярні безкоштовні хмарні провайдери:
| Провайдер | Безкоштовний тариф | Тип авторизації | Підходить для |
|---|---|---|---|
| **flespi.io** | 100 МБ трафіку, 100 токенів | Токен (як логін) | Ідеально для одного або кількох вузлів |
| **HiveMQ Cloud** | До 100 пристроїв безкоштовно | Логін / Пароль (TLS) | Хмарний кластер з публічним CA |
| **EMQX Cloud Serverless** | 1 млн повідомлень/місяць | Логін / Пароль | Повноцінний брокер з підтримкою правил |
| **Власний VPS (Mosquitto)** | Від \$3/міс | Будь-який | Повний контроль над портами та сертифікатами |

---

### Як підняти міст у Home Assistant (Mosquitto Broker add-on)

1. Відкрийте файл конфігурації мосту (наприклад, [`mosquitto/bridge-universal.conf.example`](../mosquitto/bridge-universal.conf.example) або [`mosquitto/flespi-bridge.conf`](../mosquitto/flespi-bridge.conf)).
2. Заповніть адресу зовнішнього брокера, порт (8883) та облікові дані (токен або логін/пароль).
3. Скопіюйте налаштований файл у теку `/share/mosquitto/bridge.conf` на вашому Home Assistant.
4. У Home Assistant:
   * **Settings → Add-ons → Mosquitto broker → Configuration**.
   * Увімкніть опцію:
     ```yaml
     customize:
       active: true
       folder: mosquitto
     ```
   * Збережіть та перезапустіть Mosquitto broker add-on.
5. Перевірте статус мосту: підпишіться на топік повідомлень стану (наприклад, `solar/bridge/state` або `victor/bridge/state`) — значення `1` свідчить про успішне з'єднання.
