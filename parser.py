import logging
from typing import Tuple, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Конфигурация парсера
REQUEST_TIMEOUT = 10
MAX_TEXT_LENGTH = 4000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_article_text(url: str) -> Tuple[str, str]:
    """
    Парсит статью по URL, извлекая заголовок и основной текст.
    
    Args:
        url: URL статьи
        
    Returns:
        Кортеж (title, text) или ("", error_message) при ошибке
    """
    if not url:
        logger.warning("Пустой URL для парсинга")
        return "", "Ошибка: пустой URL"
    
    if not (url.startswith("http://") or url.startswith("https://")):
        logger.warning(f"Некорректный URL: {url[:50]}")
        return "", "Ошибка: URL должен начинаться с http:// или https://"
    
    try:
        headers = {"User-Agent": USER_AGENT}
        logger.info(f"Парсинг статьи: {url[:80]}...")
        
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Извлечение заголовка
        title_tag = soup.find("title")
        title_text = title_tag.get_text().strip() if title_tag else "Без заголовка"
        
        # Удаление ненужных элементов
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()
        
        # Извлечение основного текста
        paragraphs = soup.find_all(["p", "h2", "h3", "h4"])
        text_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        text = "\n".join(text_parts)
        
        if not text:
            logger.warning(f"Не удалось извлечь текст из {url[:50]}")
            return title_text, "Ошибка: не удалось извлечь текст статьи"
        
        # Ограничение длины
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH] + "..."
            logger.info(f"Текст обрезан до {MAX_TEXT_LENGTH} символов")
        
        logger.info(f"Статья распарсена: '{title_text}', {len(text)} символов")
        return title_text, text
        
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут при парсинге {url[:50]}")
        return "", "Ошибка: превышено время ожидания сайта"
    except requests.exceptions.ConnectionError:
        logger.error(f"Ошибка подключения к {url[:50]}")
        return "", "Ошибка: не удалось подключиться к сайту"
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка {e.response.status_code} для {url[:50]}")
        return "", f"Ошибка: HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к {url[:50]}: {e}")
        return "", f"Ошибка сети: {type(e).__name__}"
    except Exception as e:
        logger.error(f"Неожиданная ошибка парсинга {url[:50]}: {e}")
        return "", f"Ошибка парсинга: {type(e).__name__}"