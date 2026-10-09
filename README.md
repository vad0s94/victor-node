# Solar Inverter & Battery Gateway (victor-node)

Універсальний шлюз та автономний контролер для сонячних гібридних інверторів (**PowMr, Victor, Voltronic, EASun**) та акумуляторів з **JK BMS** на базі ESP32 та ESPHome.

Підтримує як **локальний Home Assistant** (Native API без брокера), так і **віддалені об'єкти за CGNAT** через MQTT мости будь-якого хмарного провайдера (flespi, HiveMQ Cloud, EMQX, власний Mosquitto VPS тощо).

---

## Архітектура

```
[Сонячний інвертор] ──RJ45/RS232──┐
(PowMr / Victor / Voltronic)      │
                                  ├─ ESP32 ── Wi-Fi ──► [Home Assistant] (Локальна мережа / VPN)
[LiFePO4 Батарея] ────Bluetooth───┘   │              або
(JK BMS JK-B1A24S15P / JK-B2A...)     │             ──► [Хмарний MQTT] ◄── Міст ──► [Home Assistant]
                                      │                                             (за CGNAT)
                                      └─ Автономні правила захисту та заряду
                                         (працюють локально на ESP32 без інтернету)
```

---

## Особливості та можливості

* **Підтримка інверторів:**
  * **Modbus RTU (протокол 2341)**: PowMr POW-HVM серії, Victor NM-ECO PLUS, EASun тощо.
  * **Voltronic PI30 (Q-команди)**: Axpert, MPP Solar, EASun, SP-3200 тощо.
  * **Діагностичний сканер (`probe`)**: автоматичний перебір протоколів та швидкостей baud rate для невідомих інверторів.
* **Підтримка батарей (JK BMS):**
  * Підключення по Bluetooth Low Energy (BLE) через компонент `syssi/esphome-jk-bms`.
  * Усі 45+ параметрів та 17 перемикачів налаштувань доступні в Home Assistant без застосунку JK.
  * Вибір MAC-адреси BMS безпосередньо з інтерфейсу Home Assistant без перепрошивки.
  * Підтримка роботи взагалі **без BMS** (тільки моніторинг інвертора).
* **Канал зв'язку на вибір:**
  * **Home Assistant Native API**: пряме підключення в локальній мережі або через VPN, автоматичне виявлення mDNS без жодного MQTT-брокера.
  * **Універсальний MQTT**: робота з будь-яким брокером (локальний Mosquitto, EMQX, HiveMQ, AWS IoT).
  * **Хмарний MQTT міст (Bridge)**: для об'єктів без білої IP / за CGNAT (докладніше у [docs/mqtt-bridges.md](docs/mqtt-bridges.md)).
* **Автономні правила на ESP32 ([`packages/rules-soc.yaml`](esphome/packages/rules-soc.yaml)):**
  * Струм заряду від мережі автоматично регулюється за діапазонами SOC батареї.
  * Резервне перемикання на мережу при критично низькому заряді.
  * Працюють на самому мікроконтролері навіть коли зник інтернет або завис сервер.
  * Бережне ставлення до EEPROM інвертора (захист від частих записів, інтервал не менше 5 хв).
* **Прошивка через браузер та Improv Serial:**
  * Підтримка [ESPHome Web](https://web.esphome.io) — прошивка в один клік через Chrome/Edge та введення Wi-Fi прямо через USB або вбудований Captive Portal (`Setup`).
* **Хмарна збірка в GitHub Actions:**
  * Автоматична збірка бінарників при релізах.
  * Можливість зібрати власну прошивку через вкладку Actions у браузері без встановлення Python чи ESPHome!

---

## Швидкий старт

### Спосіб 1: Готові прошивки з GitHub Releases (без компіляції)
Завантажте готовий файл `.factory.bin` зі сторінки **Releases**:

| Профіль | Інвертор | BMS | Зв'язок | Для чого |
|---|---|---|---|---|
| `powmr-jk-api` | PowMr / Victor (Modbus) | JK BMS (BLE) | Home Assistant API | Найпопулярніший домашній варіант |
| `powmr-jk-mqtt` | PowMr / Victor (Modbus) | JK BMS (BLE) | Універсальний MQTT | Для систем з MQTT |
| `powmr-nobms-api` | PowMr / Victor (Modbus) | Немає | Home Assistant API | Тільки інвертор PowMr |
| `voltronic-jk-api` | Voltronic (PI30) | JK BMS (BLE) | Home Assistant API | Інвертори Axpert з JK BMS |
| `voltronic-nobms-api` | Voltronic (PI30) | Немає | Home Assistant API | Тільки інвертор Voltronic |
| `probe-mqtt` | Сканер | Немає | MQTT | Пошук протоколу інвертора |

1. Відкрийте [web.esphome.io](https://web.esphome.io) у Chrome або Edge.
2. Підключіть ESP32 через USB-кабель до комп'ютера та натисніть **Connect**.
3. Оберіть завантажений файл `*.factory.bin` та натисніть **Install**.
4. Після прошивки браузер запропонує ввести ім'я та пароль вашого Wi-Fi.

---

### Спосіб 2: Онлайн-конструктор у GitHub Actions
Якщо вам потрібна прошивка з іншими пінами або налаштуваннями, але ви не хочете ставити розробницьке оточення:
1. Зробіть **Fork** цього репозиторію.
2. Перейдіть у вкладку **Actions → Build Custom Firmware → Run workflow**.
3. Оберіть у випадаючому списку вашу плату, тип інвертора, тип BMS, спосіб зв'язку.
4. За кілька хвилин завантажте скомпільований `.bin` прямо з артефактів збірки!

---

### Спосіб 3: Локальний конструктор конфігурацій (`constructor.py`)
Якщо ви клонували репозиторій собі:

```bash
# 1. Запустити інтерактивний майстер (покрокові запитання):
python3 tools/constructor.py -i

# Або згенерувати конфіг через пресет:
python3 tools/constructor.py --preset powmr-jk-api -o esphome/my-inverter.yaml

# Або вказати всі параметри прапорцями:
python3 tools/constructor.py \
  --name my-solar \
  --board esp32dev \
  --inverter powmr_2341 \
  --bms jk_ble \
  --transport api \
  --rules \
  -o esphome/my-solar.yaml
```

Для збірки:
```bash
cp esphome/secrets.example.yaml esphome/secrets.yaml   # заповнити паролі
tools/build.sh esphome/my-solar.yaml
```

---

## Структура репозиторію

| Каталог / Файл | Призначення |
|---|---|
| `esphome/packages/` | Модульні блоки конфігурації: база, API, MQTT, інвертори, BMS, правила |
| `tools/constructor.py` | Інтерактивний та CLI генератор індивідуальних прошивок |
| `tools/build.sh` | Кросплатформний скрипт збірки прошивок (`.factory.bin`, `.ota.bin`, `.md5`) |
| `tools/check-entities.py` | Валідатор сутностей між ESPHome та Home Assistant |
| `mosquitto/` | Шаблони налаштування мостів Mosquitto ([`bridge-universal.conf.example`](mosquitto/bridge-universal.conf.example)) |
| `homeassistant/dashboards/` | Готовий дашборд «Дача» ([`dacha.yaml`](homeassistant/dashboards/dacha.yaml)) з картками Sunsynk та JK BMS |
| `homeassistant/packages/` | Пакет автоматизацій та сповіщень ([`victor.yaml`](homeassistant/packages/victor.yaml)) |
| `.github/workflows/` | CI валідація, реліз матриця та онлайн-конструктор прошивок |
| `docs/` | Повна документація: [залізо](docs/hardware.md), [мости](docs/mqtt-bridges.md), [тест](docs/home-test.md), [інструкція для родича](docs/onsite-uk.md), [runbook](docs/runbook.md) |

---

## Залізо та схема підключення

Детальний опис заліза, схемотехніки та налаштування понижувача MINI-360 дивіться у [docs/hardware.md](docs/hardware.md).

* **Плата:** ESP32-WROOM-32U (з зовнішньою антеною) або Wemos D1 Mini ESP32.
* **Перетворювач інтерфейсу:** Модуль RS232↔TTL на чіпі **MAX3232** (живлення 3.3 В).
* **Живлення:** DC-DC перетворювач **MH-MINI-360** (вхід від порту інвертора ~12 В, вихід налаштувати рівно на **5.0 В**).
* **Кабель RJ45 до інвертора:**
  * Pin 1: TX інвертора → вхід R1IN MAX3232
  * Pin 2: RX інвертора → вихід T1OUT MAX3232
  * Pin 4: +12V інвертора → MINI-360 IN+
  * Pin 8: GND інвертора → MINI-360 IN− та GND MAX3232

---

## Документація

1. [docs/hardware.md](docs/hardware.md) — Підбір компонентів, розпіновка RJ45, пайка та регулювання живлення.
2. [docs/mqtt-bridges.md](docs/mqtt-bridges.md) — Підключення до Home Assistant: Native API, локальний MQTT, хмарні мости (flespi, HiveMQ тощо).
3. [docs/firmware.md](docs/firmware.md) — Робота з прошивками, OTA через інтернет, пошук протоколу.
4. [docs/home-assistant.md](docs/home-assistant.md) — Встановлення карток HACS, імпорт дашборда та сповіщень.
5. [docs/onsite-uk.md](docs/onsite-uk.md) — Проста пам'ятка для родича на місці (як встромити кабель і підключити Wi-Fi).
6. [docs/runbook.md](docs/runbook.md) — Алгоритм діагностики та вирішення можливих проблем.

---

## Ліцензія та подяки

Проєкт поширюється під ліцензією [Apache 2.0](LICENSE).
Подяки авторам відкритих компонентів перелічені у [NOTICE.md](NOTICE.md).
