# Railway CLI Configuration

Этот файл содержит команды для работы с Railway CLI.

## Установка Railway CLI

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 -useb | iex

# macOS
brew install railway

# Linux
curl -fsSL https://railway.app/install.sh | sh
```

## Основные команды

### Инициализация проекта
```bash
railway login
railway init
```

### Развертывание
```bash
# Развертывание текущего проекта
railway up

# Развертывание с указанием проекта
railway up --project your-project-name
```

### Переменные окружения
```bash
# Просмотр всех переменных
railway variables

# Добавление переменной
railway variables set SECRET_KEY=your-secret-key

# Удаление переменной
railway variables unset SECRET_KEY
```

### База данных
```bash
# Подключение к базе данных
railway connect

# Просмотр URL базы данных
railway variables get DATABASE_URL
```

### Логи
```bash
# Просмотр логов
railway logs

# Просмотр логов в реальном времени
railway logs --follow
```

### Статус
```bash
# Статус проекта
railway status

# Информация о проекте
railway info
```

## Полезные команды для разработки

```bash
# Локальный запуск с переменными Railway
railway run python app.py

# Открытие приложения в браузере
railway open

# Просмотр метрик
railway metrics
```

## Troubleshooting

### Проблемы с базой данных
```bash
# Проверка подключения к БД
railway connect

# Сброс базы данных (ОСТОРОЖНО!)
railway variables unset DATABASE_URL
# Затем добавьте новую БД через Dashboard
```

### Проблемы с развертыванием
```bash
# Просмотр логов сборки
railway logs --build

# Пересборка проекта
railway up --detach
```

### Проблемы с переменными окружения
```bash
# Проверка всех переменных
railway variables

# Синхронизация переменных
railway variables pull
```
