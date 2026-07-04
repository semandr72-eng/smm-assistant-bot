# SMM Assistant Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/bot-aiogram%203.x-orange.svg)](https://docs.aiogram.dev/)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI%201.x-green.svg)](https://platform.openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Асинхронный Telegram-бот для помощи контент-менеджерам и малому бизнесу в создании контента.

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        bot.py                               │
│  (aiogram 3.x - асинхронный обработчик сообщений)          │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    llm.py       │  │   parser.py     │  │   sheets.py     │
│  (AsyncOpenAI)  │  │  (requests +    │  │ (gspread +      │
│                 │  │   BeautifulSoup)│  │  google-auth)   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────┐                    ┌─────────────────┐
│ knowledge_base  │                    │  Google Sheets  │
│   (кэширование) │                    │   (база знаний) │
└─────────────────┘                    └─────────────────┘
```

## 📁 Структура проекта

| Файл | Описание |
|------|----------|
| `bot.py` | Основной файл бота (aiogram 3.x) |
| `llm.py` | Асинхронная работа с OpenAI API |
| `parser.py` | Парсинг статей из интернета |
| `sheets.py` | Работа с Google Sheets (логи + база знаний) |
| `knowledge_base.py` | Кэширование данных из Google Sheets |
| `config.py` | Конфигурация и валидация переменных |
| `requirements.txt` | Зависимости Python |

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Токен Telegram-бота (@BotFather)
- API-ключ OpenAI
- Google Sheets + сервисный аккаунт

### 1. Клонирование и установка

```bash
git clone https://github.com/USERNAME/smm-assistant-bot.git
cd smm-assistant-bot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

**Обязательные переменные:**
- `BOT_TOKEN` — токен от @BotFather
- `OPENAI_API_KEY` — API ключ OpenAI
- `SPREADSHEET_ID` — ID Google таблицы
- `GOOGLE_CREDS_FILE` — путь к `credentials.json`

### 3. Настройка Google Sheets

1. Создайте новую Google Таблицу
2. Создайте листы: `topics`, `hashtags`, `cta`, `logs`
3. Настройте заголовки:
   - **topics**: `ниша`, `рубрика`, `пример_темы`
   - **hashtags**: `платформа`, `категория`, `хештеги`
   - **cta**: `фраза`
   - **logs**: `timestamp`, `user_id`, `username`, `scenario`, `input`, `output`, `status`
4. Создайте сервисный аккаунт в [Google Cloud Console](https://console.cloud.google.com/)
5. Скачайте JSON-ключ как `credentials.json`
6. Дайте доступ сервисному аккаунту к таблице (email из JSON)

### 4. Запуск бота

```bash
python bot.py
```

## 🔧 Сценарии использования

1. **💡 Идея поста** — генерация идей по теме
2. **✍️ Черновик текста** — структура: проблема → решение → призыв
3. **#️⃣ Хештеги** — подбор 10-20 хештегов
4. **📱 Адаптация** — адаптация поста под платформу
5. **🔗 Парсинг статьи** — создание поста из статьи по URL

## 🔒 Безопасность

- Токены и ключи только в `.env` (не коммитить!)
- `credentials.json` в `.gitignore`
- Контроль доступа по `user_id`
- Валидация входных данных

## 📊 Мониторинг

Все взаимодействия логируются в Google Sheets (лист `logs`):
- Время запроса
- ID и username пользователя
- Сценарий
- Входные данные
- Ответ бота
- Статус (success/fail)

## 🚨 Troubleshooting

**Бот не запускается:**
```bash
# Проверьте переменные окружения
python -c "from config import *; print('OK')"
```

**Ошибка Google Sheets:**
- Проверьте `credentials.json`
- Дайте доступ сервисному аккаунту к таблице
- Убедитесь, что `SPREADSHEET_ID` верный

**Ошибка OpenAI:**
- Проверьте баланс API ключа
- Убедитесь, что модель доступна

## 👨‍💻 Автор

**Semandr | AI Developer**

Начинающий ИИ-разработчик. Строю чат-ботов, API-обёртки и RAG-системы. Открыт к заказам.

[![GitHub](https://img.shields.io/badge/GitHub-semandr72__eng-181717?style=flat&logo=github)](https://github.com/semandr72-eng)

> _От MVP до продакшена — от промпт-инжиниринга до No-code и API-интеграций._

## 📝 License

[MIT License](LICENSE)
