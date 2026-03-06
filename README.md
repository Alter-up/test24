# X Automation Bot 🤖

Аналог TwittyX для автоматизации X (Twitter) через Telegram-бота. Backend работает локально на Mac, без подписок и облачных сервисов.

## ✨ Возможности

### Управление аккаунтами
- 👤 Добавление нескольких X-аккаунтов
- 🌐 Назначение прокси для каждого аккаунта
- 🍪 Автоматическое сохранение сессий (cookies)
- 📊 Отслеживание лимитов действий

### Действия
- ❤️ **Like** — лайкать твиты по URL или из поиска
- 🔁 **Retweet** — ретвитить
- 💬 **Reply** — отвечать на твиты (вручную или через AI)
- 👤 **Follow** — подписываться на пользователей
- 📝 **Post** — публиковать твиты с изображениями
- 🚀 **Boost** — комплексное продвижение постов

### Автоматизация
- 📋 **Lists** — авто-действия из списков X
- 🔍 **Search** — авто-действия по поисковым запросам
- 📝 **Autopost** — отложенный постинг по расписанию
- ⏰ **Scheduler** — настройка интервалов между действиями

### AI-функции
- 🤖 Генерация ответов через OpenAI GPT
- 🎨 Настраиваемый тон (friendly, professional, enthusiastic, etc.)

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                          │
│              (python-telegram-bot)                       │
│         Доступ для 2 человек (whitelist)                 │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│              BACKEND API (FastAPI)                       │
│                    localhost:8000                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Accounts   │  │  Actions    │  │  Scheduler      │ │
│  │  Manager    │  │  Executor   │  │  (APScheduler)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│           BROWSER AUTOMATION (Playwright)                │
│         Эмуляция человеческого поведения                 │
│              (без X API, как в TwittyX)                  │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│              SQLITE DATABASE (local)                     │
│    accounts, proxies, posts, actions, logs               │
└─────────────────────────────────────────────────────────┘
```

## 📋 Требования

- macOS (или Linux/Windows)
- Python 3.9+
- Telegram Bot Token
- (Опционально) OpenAI API Key для AI-функций

## 🚀 Установка

### 1. Клонирование и настройка окружения

```bash
cd x_automation_bot
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Настройка переменных окружения

```bash
cp .env.example .env
nano .env  # или откройте в редакторе
```

Заполните `.env`:

```env
# Обязательно
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
ALLOWED_USERS=123456789,987654321  # ID двух пользователей через запятую

# Опционально (для AI-ответов)
OPENAI_API_KEY=your_openai_key

# Настройки сервера
HOST=127.0.0.1
PORT=8000
```

**Как получить Telegram Bot Token:**
1. Напишите [@BotFather](https://t.me/botfather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

**Как узнать Telegram ID:**
1. Напишите [@userinfobot](https://t.me/userinfobot)
2. Он покажет ваш ID

### 4. Запуск

```bash
python main.py
```

Или отдельно:

```bash
# Только Telegram бот
python telegram_bot.py

# Только API сервер
python api.py
```

## 📱 Использование Telegram Bot

### Начало работы

Отправьте `/start` боту для получения меню.

### Основные команды

| Команда | Описание |
|---------|----------|
| `/accounts` | Список аккаунтов |
| `/add_account` | Добавить X-аккаунт |
| `/proxies` | Список прокси |
| `/add_proxy` | Добавить прокси |
| `/like` | Лайкнуть твиты |
| `/follow` | Подписаться на пользователей |
| `/reply` | Ответить на твит |
| `/post` | Создать пост |
| `/schedule` | Запланировать пост |
| `/automation` | Настроить автоматизацию |
| `/status` | Активные автоматизации |
| `/logs` | История действий |
| `/help` | Справка |

### Добавление аккаунта

1. Отправьте `/add_account`
2. Введите username (без @)
3. Введите email
4. Введите пароль

### Добавление прокси

Формат: `name|host:port:username:password`

Примеры:
```
US Proxy|192.168.1.10:1080:myuser:mypass
EU Proxy|192.168.1.20:1080
```

### Лайк твитов

**По URL:**
```
https://x.com/username/status/1234567890
```

**Из поиска:**
```
#bitcoin
```

### Ответы с AI

Формат: `tweet_url|AI: tone`

Примеры:
```
https://x.com/user/status/123|AI: friendly
https://x.com/user/status/123|AI: professional
https://x.com/user/status/123|AI: enthusiastic
```

## 🌐 API Endpoints

API доступен по адресу: `http://localhost:8000`

### Документация
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Основные эндпоинты

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/accounts` | Список аккаунтов |
| POST | `/api/accounts` | Создать аккаунт |
| GET | `/api/proxies` | Список прокси |
| POST | `/api/proxies` | Создать прокси |
| POST | `/api/actions/execute` | Выполнить действие |
| GET | `/api/posts/scheduled` | Запланированные посты |
| POST | `/api/posts/scheduled` | Создать запланированный пост |
| GET | `/api/automation/tasks` | Список задач |
| POST | `/api/automation/tasks` | Создать задачу |
| GET | `/api/logs` | Логи действий |
| GET | `/api/stats` | Статистика |

## ⚙️ Настройки автоматизации

### Lists Automation

Автоматические действия из X-списка:

```json
{
  "list_url": "https://x.com/i/lists/123456789",
  "actions": ["like", "retweet"],
  "max_items": 10
}
```

### Search Automation

Автоматические действия по поиску:

```json
{
  "query": "#crypto",
  "action": "like",
  "max_results": 5
}
```

### Autopost

Автоматический постинг:

```json
{
  "interval_minutes": 360  // Каждые 6 часов
}
```

## 🔒 Безопасность

- ✅ Доступ только для 2 указанных пользователей
- ✅ Прокси для каждого аккаунта
- ✅ Эмуляция человеческого поведения
- ✅ Рандомные задержки между действиями
- ✅ Лимиты на количество действий в день
- ✅ Хранение паролей в локальной БД (SQLite)

## ⚠️ Важно

1. **Используйте прокси** — это снижает риск блокировки
2. **Начинайте медленно** — новые аккаунты нужно "прогревать"
3. **Соблюдайте лимиты** — не более 30-50 действий в час
4. **Разнообразьте действия** — не делайте только лайки
5. **Проверяйте логи** — следите за ошибками

## 🛠️ Технологии

- **Python 3.9+**
- **python-telegram-bot** — Telegram Bot API
- **FastAPI** — Web API
- **Playwright** — Browser automation
- **APScheduler** — Task scheduling
- **SQLAlchemy** — ORM для БД
- **SQLite** — Локальная база данных

## 📁 Структура проекта

```
x_automation_bot/
├── main.py              # Точка входа
├── telegram_bot.py      # Telegram бот
├── api.py               # FastAPI сервер
├── x_automation.py      # Автоматизация X
├── scheduler.py         # Планировщик задач
├── database.py          # Модели базы данных
├── requirements.txt     # Зависимости
├── .env.example         # Пример конфигурации
└── README.md            # Документация
```

## 🐛 Отладка

### Просмотр логов

```bash
tail -f x_automation.log
```

### Проверка базы данных

```bash
sqlite3 x_automation.db
.tables
SELECT * FROM accounts;
```

### Тестирование в headless-режиме

В `x_automation.py` измените:
```python
browser_args = {
    'headless': True,  # Без отображения браузера
    ...
}
```

## 📝 Лицензия

MIT License — используйте на свой страх и риск.

**Важно:** Автоматизация X может нарушать Terms of Service. Используйте ответственно.

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи
2. Убедитесь, что прокси работают
3. Проверьте, что аккаунт не заблокирован
4. Попробуйте обновить cookies через `/test_login`
