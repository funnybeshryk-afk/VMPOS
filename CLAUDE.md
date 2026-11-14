# VMPOS — касса для магазина «Vodiy Market»

> Сначала прочитай [`STATE.md`](STATE.md): что выпущено, что в каких ветках, что открыто.
> Если STATE.md и этот файл расходятся — прав STATE.md. Устарел — спроси владельца, не угадывай.

Десктопная POS-программа на Python для одного реального магазина (Фергана). Работает на Windows
у кассиров, данные локально в SQLite. Интерфейс **на узбекском (латиница)**; общаемся с владельцем по-русски.

## Стек
- Python 3.12+, **PySide6** (Widgets + QSS, не QML), **SQLAlchemy 2** + SQLite, `python-barcode`.
- Сборка: PyInstaller + Inno Setup (`packaging/`, `installer/vmpos.iss`), CI на GitHub Actions.
- Тесты: `pytest` (+ `Pillow`, `zxing-cpp` как независимый декодер штрихкодов).

## Структура
```
main.py            точка входа
app/database/      base, database, migrations (PRAGMA user_version)
app/models/        SQLAlchemy-модели
app/services/      бизнес-логика (sale, refund, shift, receipt, update, backup, fiscal …)
app/ui/            страницы и диалоги (sale_page, main_window, settings_page …)
app/widgets/       общие виджеты (cart_list, badge, app_status_bar …)
app/utils/         форматтеры, печать этикеток/чеков, scan_burst, paths …
assets/styles/     style.qss — вся тема; токены цветов — только здесь
tests/             pytest; conftest.py: qapp, анимации выключены, чистая БД на тест
docs/FISCAL.md     модель данных фискализации
```

## Команды
```bash
pip install -r requirements.txt -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen python -m pytest -q     # без экрана; ВСЕГДА проверяй код выхода (=0)
python main.py                                    # запуск
```
Данные по умолчанию в `%LOCALAPPDATA%\VMPOS`; для тестов/песочницы — `VMPOS_DATA_DIR=<папка>`.

## Правила
1. **Не ломать данные магазина.** Любое изменение схемы БД: поднять `SCHEMA_VERSION` в
   `app/version.py` + миграция в `app/database/migrations.py` (аддитивная, перед ней авто-бэкап).
   Старое приложение отказывается открывать базу новее себя — выпуск схемы v2 надо согласовать с владельцем.
2. **Релиз только по явному «го» владельца.** Версия = `APP_VERSION` в `app/version.py`, плюс
   актуальный `release-notes.md`. Релиз: Actions → «Build Windows (test)» с `publish=true` и `version`
   (должна совпасть с `app/version.py`). Авто-обновление в программах читает именно GitHub Releases.
3. **Работаем в ветках `claude/*`, в `main` не пушим.** Теги из сессии не пушатся — релиз через workflow_dispatch.
4. **Весь текст интерфейса — на узбекском латиницей**, без эмодзи вместо иконок.
5. **Дизайн:** изумрудный акцент `#059669`, тёмные «чернила» `#1c1917`, фон `#f6f3ee`, шрифт Segoe UI.
   Цвета/размеры только токенами в `style.qss`, в виджетах не хардкодить. Тач-цели ≥ 44px;
   кнопки на Sotuv — `NoFocus`, иначе сканер теряет фокус.
6. **Тесты:** маленькие шаги, после каждого полный прогон. Новое поведение — тест + проверка мутацией
   (сломай логику, убедись, что тест падает). Не использовать константы кода внутри собственных проверок.
7. **Qt в тестах:** `QT_QPA_PLATFORM=offscreen`, `qapp` из conftest (чистое завершение), анимации выключены;
   при `deleteLater` в grab-снимках бывают «призраки» — учитывай.
8. **Штрихкоды** — Code128, рисуются прямоугольниками (`label_printing.paint_barcode`): тихая зона ≥ 10 модулей,
   модуль — целое число пикселей устройства. Внутренние 13-значные коды (`2000000000000+`) — не валидный EAN-13.
9. **Апдейтер** скачивает только с `https://github.com/funnybeshryk-afk/VMPOS/releases/download/` и проверяет SHA-256.
10. Фискальные поля готовы, но ничего не отправляется (`fiscal_mode = "off"`). Печатаемый чек **не фискальный**.

## Как отчитываться
В конце задачи: что сделано, что проверено (число тестов, код выхода), что **не** проверено
(реальный принтер/сканер/Windows), есть ли миграция БД, что нужно от владельца.
