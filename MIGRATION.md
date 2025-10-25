# Миграция данных для Railway

Этот файл содержит инструкции по миграции данных из SQLite в PostgreSQL при развертывании на Railway.

## Автоматическая миграция

Приложение автоматически определяет тип базы данных и создает соответствующие таблицы:

- **SQLite** (локальная разработка): Использует `INTEGER PRIMARY KEY AUTOINCREMENT`
- **PostgreSQL** (Railway): Использует `SERIAL PRIMARY KEY`

## Ручная миграция данных (если необходимо)

Если у вас есть существующие данные в SQLite, которые нужно перенести в PostgreSQL:

### 1. Экспорт данных из SQLite

```bash
# Создайте SQL дамп
sqlite3 data.db .dump > data_export.sql

# Или экспортируйте в CSV
sqlite3 -header -csv data.db "SELECT * FROM slider_news;" > slider_news.csv
sqlite3 -header -csv data.db "SELECT * FROM feed_news;" > feed_news.csv
sqlite3 -header -csv data.db "SELECT * FROM job_applications;" > job_applications.csv
sqlite3 -header -csv data.db "SELECT * FROM employees;" > employees.csv
sqlite3 -header -csv data.db "SELECT * FROM documents;" > documents.csv
sqlite3 -header -csv data.db "SELECT * FROM leaders;" > leaders.csv
sqlite3 -header -csv data.db "SELECT * FROM notifications;" > notifications.csv
sqlite3 -header -csv data.db "SELECT * FROM contacts;" > contacts.csv
sqlite3 -header -csv data.db "SELECT * FROM complaints;" > complaints.csv
sqlite3 -header -csv data.db "SELECT * FROM documents_drafts;" > documents_drafts.csv
sqlite3 -header -csv data.db "SELECT * FROM user_accounts;" > user_accounts.csv
sqlite3 -header -csv data.db "SELECT * FROM organs_units;" > organs_units.csv
sqlite3 -header -csv data.db "SELECT * FROM app_settings;" > app_settings.csv
```

### 2. Импорт в PostgreSQL

```bash
# Подключитесь к PostgreSQL базе данных Railway
psql $DATABASE_URL

# Импортируйте данные (пример для одной таблицы)
\copy slider_news FROM 'slider_news.csv' WITH CSV HEADER;
\copy feed_news FROM 'feed_news.csv' WITH CSV HEADER;
# ... и так далее для всех таблиц
```

### 3. Проверка миграции

После импорта проверьте:
- Количество записей в каждой таблице
- Корректность данных
- Работу приложения

## Важные замечания

1. **ID последовательности**: После импорта данных в PostgreSQL нужно обновить последовательности:
   ```sql
   SELECT setval('slider_news_id_seq', (SELECT MAX(id) FROM slider_news));
   SELECT setval('feed_news_id_seq', (SELECT MAX(id) FROM feed_news));
   -- и так далее для всех таблиц с SERIAL PRIMARY KEY
   ```

2. **Файлы загрузок**: Убедитесь, что папка `uploads/` и все файлы в ней доступны в production среде.

3. **Статические файлы**: Проверьте, что все статические файлы (CSS, JS, изображения) корректно обслуживаются.

## Автоматическое создание таблиц

При первом запуске на Railway приложение автоматически:
- Определит наличие переменной `DATABASE_URL`
- Создаст все необходимые таблицы PostgreSQL
- Настроит правильные типы данных и ограничения

Никаких дополнительных действий не требуется!
