import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

from sheets import read_sheet_data
from config import SHEET_TOPICS, SHEET_HASHTAGS, SHEET_CTA

logger = logging.getLogger(__name__)

# Кэш для данных базы знаний (обновляется при перезапуске)
# В production можно добавить TTL или обновление по расписанию


@lru_cache(maxsize=1)
def load_topics() -> List[Dict[str, Any]]:
    """Загружает темы из Google Sheets с кэшированием."""
    try:
        records = read_sheet_data(SHEET_TOPICS)
        logger.info(f"Загружено {len(records)} тем из базы знаний")
        return records
    except Exception as e:
        logger.error(f"Ошибка загрузки тем: {e}")
        return []


@lru_cache(maxsize=4)
def load_hashtags(platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """Загружает хештеги из Google Sheets с кэшированием по платформе."""
    try:
        all_records = read_sheet_data(SHEET_HASHTAGS)
        
        if platform:
            filtered = [
                r for r in all_records 
                if r.get("платформа", "").lower() == platform.lower()
            ]
            logger.info(f"Загружено {len(filtered)} хештегов для платформы '{platform}'")
            return filtered
        
        logger.info(f"Загружено {len(all_records)} хештегов (все платформы)")
        return all_records
    except Exception as e:
        logger.error(f"Ошибка загрузки хештегов: {e}")
        return []


@lru_cache(maxsize=1)
def load_cta() -> List[str]:
    """Загружает призывы к действию (CTA) из Google Sheets."""
    try:
        records = read_sheet_data(SHEET_CTA)
        cta_list = [r["фраза"] for r in records if "фраза" in r]
        logger.info(f"Загружено {len(cta_list)} CTA фраз")
        return cta_list
    except Exception as e:
        logger.error(f"Ошибка загрузки CTA: {e}")
        return []


def clear_cache():
    """Очищает кэш базы знаний (для принудительного обновления)."""
    load_topics.cache_clear()
    load_hashtags.cache_clear()
    load_cta.cache_clear()
    logger.info("Кэш базы знаний очищен")