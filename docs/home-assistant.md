# Home Assistant

## 1. HACS-картки
HACS → Frontend → встановити:
- **Sunsynk Power Flow Card** (slipx06)
- **JK BMS Card** (Pho3niX90; якщо немає в каталозі: Custom repositories → `https://github.com/Pho3niX90/jk-bms-card`, тип Dashboard)

Mushroom уже стоїть, але для дашборда він не потрібен.

## 2. Пакет зі сповіщеннями
1. У `configuration.yaml` додати (якщо ще немає):
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Скопіювати `homeassistant/packages/victor.yaml` у `/config/packages/victor.yaml`.
3. Developer tools → YAML → Check configuration → Restart.

Сповіщення йдуть у `notify.all_devices`. Щоб отримували інші користувачі: після встановлення застосунку HA додати їхній `notify.mobile_app_<телефон>` у цю групу або в дії автоматизацій.

| Подія | Коли |
|---|---|
| Блок офлайн / знову онлайн | 10 хв без зв'язку / зв'язок повернувся |
| Батарея розряджена | SOC < 20 % 5 хв |
| Зникла / повернулась мережа | 1 хв |
| Помилка інвертора / BMS | будь-яка нова помилка |
| Блок не чує інвертор або BMS | 5 хв |

## 3. Дашборд «Сонячна станція»
Settings → Dashboards → Add dashboard → New dashboard from scratch → назва «СЕС» → відкрити → ⋮ → Edit → ⋮ → Raw configuration editor → вставити `homeassistant/dashboards/solar.yaml`.

Замінити в ньому:
- `ADMIN_USER_ID` на свій id (Settings → People → Users → твій користувач, id в адресі сторінки): вкладку «Налаштування» бачитимеш лише ти;
- `battery.energy` на ємність батареї у Вт·год.

## 4. Зона і мітка
- Зона створиться автоматично відповідно до `area` у прошивці.
- Settings → Labels → створити `victor`, позначити нею пристрій і автоматизації.

## 5. Додатковий користувач (неадміністратор)
1. Settings → People → Add person → увімкнути «Allow person to login», **без** «Administrator».
2. Dashboards → «СЕС» → ⋮ → увімкнути «Show in sidebar». Інші дашборди (Overview, Energy тощо) → «Admin only» або сховати з бокової панелі в профілі користувача.
3. Заходить через вашу адресу або застосунок HA.

## 6. Перевірити назви сутностей
Після першого підключення блоку: Settings → Devices → Victor. Дашборд і пакет розраховані на `sensor.victor_<назва>` (`discovery_object_id_generator: device_name`). Якщо HA назвав щось інакше, виправ у `solar.yaml` / `victor.yaml`.
