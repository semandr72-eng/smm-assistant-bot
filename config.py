import os
import sys
from dotenv import load_dotenv

load_dotenv()

# === Обязательные переменные ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    print("[ERROR] BOT_TOKEN не найден в .env")
    sys.exit(1)

if not OPENAI_API_KEY:
    print("[ERROR] OPENAI_API_KEY не найден в .env")
    sys.exit(1)

# === Google Sheets ===
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "ваш_id_таблицы")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "credentials.json")

# Имена листов базы знаний
SHEET_TOPICS = "topics"
SHEET_HASHTAGS = "hashtags"
SHEET_CTA = "cta"
LOG_SHEET_NAME = "logs"

# === Контроль доступа ===
# Список разрешённых user_id (через запятую)
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "")
ADMIN_IDS = os.getenv("ADMIN_IDS", "")

# === Настройки LLM ===
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.8"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))