# Прокуратура - Система управления

Веб-приложение для управления прокуратурой с административной панелью, системой жалоб и заявок на работу.

## 🚀 Развертывание на Railway

### Предварительные требования
- Аккаунт на [Railway.app](https://railway.app)
- Git репозиторий с кодом

### Шаги развертывания

1. **Подключите репозиторий к Railway**
   - Войдите в Railway Dashboard
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите ваш репозиторий

2. **Добавьте PostgreSQL базу данных**
   - В Railway Dashboard нажмите "New"
   - Выберите "Database" → "PostgreSQL"
   - Railway автоматически создаст переменную `DATABASE_URL`

3. **Настройте переменные окружения**
   В Railway Dashboard → Settings → Variables добавьте:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-very-secure-secret-key-here
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-admin-password
   PROSECUTOR_USERNAME=proc
   PROSECUTOR_PASSWORD=your-secure-prosecutor-password
   MAX_CONTENT_LENGTH=16777216
   ```

4. **Развертывание**
   - Railway автоматически обнаружит `Procfile` и `requirements.txt`
   - Приложение будет развернуто с Gunicorn
   - База данных будет автоматически инициализирована

### Локальная разработка

1. **Клонируйте репозиторий**
   ```bash
   git clone <your-repo-url>
   cd procuratyra-main
   ```

2. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate  # Windows
   ```

3. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте переменные окружения**
   ```bash
   cp env.example .env
   # Отредактируйте .env файл с вашими настройками
   ```

5. **Запустите приложение**
   ```bash
   python app.py
   ```

## 📁 Структура проекта

```
procuratyra-main/
├── app.py                 # Основное приложение Flask
├── requirements.txt       # Python зависимости
├── Procfile             # Конфигурация для Railway
├── railway.json         # Дополнительная конфигурация Railway
├── env.example          # Пример переменных окружения
├── .gitignore           # Исключения для Git
├── templates/           # HTML шаблоны
├── static/             # Статические файлы
├── uploads/            # Загруженные файлы
├── pdf/               # PDF документы
└── logo/              # Логотипы
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `FLASK_ENV` | Режим Flask (development/production) | `development` |
| `SECRET_KEY` | Секретный ключ для сессий | `change-me-in-production` |
| `ADMIN_USERNAME` | Логин администратора | `admin` |
| `ADMIN_PASSWORD` | Пароль администратора | `admin123` |
| `PROSECUTOR_USERNAME` | Логин прокурора | `proc` |
| `PROSECUTOR_PASSWORD` | Пароль прокурора | `proc123` |
| `DATABASE_URL` | URL базы данных (автоматически для Railway) | SQLite локально |
| `PORT` | Порт для запуска | `8080` |
| `MAX_CONTENT_LENGTH` | Максимальный размер загружаемых файлов | `16777216` (16MB) |

### База данных

Приложение поддерживает:
- **SQLite** для локальной разработки
- **PostgreSQL** для production (Railway)

База данных автоматически инициализируется при первом запуске.

## 🔐 Безопасность

В production режиме включены:
- HTTPS-only cookies
- Security headers (HSTS, CSP, X-Frame-Options и др.)
- Защита от XSS и CSRF
- Ограничения на загрузку файлов

## 📝 Функциональность

- **Публичные страницы**: Новости, документы, контакты, жалобы
- **Административная панель**: Управление контентом, пользователями, заявками
- **Панель прокурора**: Обработка жалоб, создание документов
- **Система уведомлений**: Уведомления для админов и прокуроров
- **Загрузка файлов**: Изображения для новостей и жалоб

## 🛠 Технологии

- **Backend**: Flask, Python
- **Database**: PostgreSQL (production), SQLite (development)
- **WSGI Server**: Gunicorn
- **Deployment**: Railway.app
- **Frontend**: HTML, CSS, JavaScript

## 📞 Поддержка

Для вопросов по развертыванию или использованию создайте issue в репозитории.
