import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from functools import lru_cache

import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import DefaultCredentialsError

from config import SPREADSHEET_ID, GOOGLE_CREDS_FILE, LOG_SHEET_NAME

logger = logging.getLogger(__name__)

# Кэширование клиента Google Sheets
_client_cache: Optional[gspread.Client] = None


def get_client() -> Optional[gspread.Client]:
    """Получает авторизованный клиент Google Sheets с кэшированием."""
    global _client_cache
    
    if _client_cache is not None:
        return _client_cache
    
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDS_FILE,
            scopes=scope
        )
        _client_cache = gspread.authorize(creds)
        logger.info("Google Sheets клиент успешно инициализирован")
        return _client_cache
    except FileNotFoundError:
        logger.error(f"Файл credentials '{GOOGLE_CREDS_FILE}' не найден")
        return None
    except DefaultCredentialsError as e:
        logger.error(f"Ошибка авторизации Google Sheets: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при инициализации Google Sheets: {e}")
        return None


def get_sheet(sheet_name: str) -> Optional[gspread.Worksheet]:
    """Получает лист по имени, создаёт если не существует."""
    client = get_client()
    if client is None:
        logger.warning("Клиент Google Sheets недоступен")
        return None
    
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error(f"Таблица с ID '{SPREADSHEET_ID}' не найдена")
        return None
    except Exception as e:
        logger.error(f"Ошибка открытия таблицы: {e}")
        return None
    
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        try:
            ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=10)
            logger.info(f"Создан новый лист: {sheet_name}")
            
            # Инициализация заголовков для логов
            if sheet_name == LOG_SHEET_NAME:
                ws.append_row([
                    "timestamp", "user_id", "username", 
                    "scenario", "input", "output", "status"
                ])
        except Exception as e:
            logger.error(f"Ошибка создания листа '{sheet_name}': {e}")
            return None
    
    return ws


def log_interaction(
    user_id: int,
    username: str,
    scenario: str,
    user_input: str,
    output: str,
    status: str = "success"
) -> bool:
    """Логирует взаимодействие пользователя с ботом в Google Sheets."""
    ws = get_sheet(LOG_SHEET_NAME)
    if ws is None:
        return False
    
    try:
        # Ограничиваем длину строк для избежания ошибок API
        max_len = 5000
        ws.append_row([
            datetime.now().isoformat(),
            str(user_id),
            username[:100] if username else "unknown",
            scenario[:100],
            user_input[:max_len],
            output[:max_len],
            status
        ])
        logger.debug(f"Лог записан: user={user_id}, scenario={scenario}")
        return True
    except Exception as e:
        logger.error(f"Ошибка записи лога: {e}")
        return False


def read_sheet_data(sheet_name: str) -> List[Dict[str, Any]]:
    """Читает все данные из листа как список словарей."""
    ws = get_sheet(sheet_name)
    if ws is None:
        return []
    
    try:
        records = ws.get_all_records()
        logger.debug(f"Прочитано {len(records)} записей из листа '{sheet_name}'")
        return records
    except Exception as e:
        logger.error(f"Ошибка чтения листа '{sheet_name}': {e}")
        return []