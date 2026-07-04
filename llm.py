import logging
from typing import Optional
import asyncio
from openai import AsyncOpenAI, Timeout
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from knowledge_base import load_topics, load_hashtags, load_cta

logger = logging.getLogger(__name__)

# Инициализация async клиента OpenAI
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT_BASE = """
Ты — креативный SMM-ассистент. Помогаешь контент-менеджерам и малому бизнесу.

Стиль: дружелюбный, живой, с эмодзи, без канцелярита.

Ограничения:
- Не публикуй контент от имени пользователя.
- Не используй непроверенные факты. Если сомневаешься, напиши "проверьте актуальность".
- На запросы "идея поста" и "адаптация" давай ровно 5 вариантов.
- На запрос "черновик текста" давай 1 вариант, но по структуре: проблема → решение → призыв.
- На запрос "хештеги" дай 10-20 хештегов.

Ниже — база знаний (темы, хештеги, CTA), используй их для вдохновения, но не копируй слепо.
"""


def build_system_prompt(scenario: str) -> str:
    """Формирует системный промпт для заданного сценария."""
    try:
        topics_sample = load_topics()[:5]
        hashtags_sample = load_hashtags()[:10]
        cta_sample = load_cta()
        
        cta_text = "\n".join([f"- {c}" for c in cta_sample[:5]])
        
        topics_text = "\n".join([
            f"- {t.get('ниша', 'N/A')}: {t.get('рубрика', 'N/A')} -> {t.get('пример_темы', 'N/A')}"
            for t in topics_sample
        ])
        
        hashtags_text = "\n".join([
            f"- {h.get('платформа', 'N/A')} {h.get('категория', 'N/A')}: {h.get('хештеги', 'N/A')}"
            for h in hashtags_sample
        ])
    except Exception as e:
        logger.error(f"Ошибка загрузки базы знаний: {e}")
        topics_text = hashtags_text = cta_text = "(база знаний недоступна)"
    
    scenario_instruction = {
        "idea": "Пользователь хочет 3-5 идей поста. Учитывай тему и нишу. Выдай нумерованный список.",
        "text": "Пользователь хочет черновик поста. Используй структуру: заголовок, проблема, решение, призыв к действию. Длина до 2000 знаков.",
        "hashtags": "Подбери 10-20 хештегов (широкие+нишевые+вовлекающие).",
        "adapt": "Адаптируй указанный пользователем пост под платформу (Telegram, VK, Instagram). Дай 5 вариантов для этой платформы.",
        "parse": "Пользователь дал текст статьи. Напиши на его основе пост (как в сценарии 'text')."
    }.get(scenario, "Ответь полезно и по делу.")
    
    return f"""{SYSTEM_PROMPT_BASE}

## Сценарий: {scenario}
{scenario_instruction}

## База знаний (примеры тем):
{topics_text}

## Примеры хештегов:
{hashtags_text}

## Примеры призывов (CTA):
{cta_text}

## Помни: выдавай 3-5 вариантов, где сказано; не выдумывай факты.
"""


async def generate_response(scenario: str, user_input: str) -> str:
    """Генерирует ответ через LLM асинхронно."""
    system_prompt = build_system_prompt(scenario)
    
    # Настройка токенов в зависимости от сценария
    max_tokens = LLM_MAX_TOKENS if scenario != "hashtags" else 400
    
    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=max_tokens,
            timeout=Timeout(timeout=30.0)
        )
        
        if not response.choices or not response.choices[0].message.content:
            logger.warning("Пустой ответ от LLM")
            return "⚠️ Не удалось сгенерировать ответ. Попробуйте ещё раз."
        
        content = response.choices[0].message.content
        logger.info(f"LLM ответ для сценария '{scenario}': {len(content)} символов")
        return content
        
    except asyncio.TimeoutError:
        logger.error("Таймаут запроса к LLM")
        return "⏱️ Превышено время ожидания ответа. Попробуйте ещё раз."
    except Exception as e:
        logger.error(f"Ошибка LLM: {type(e).__name__}: {e}")
        return f"⚠️ Ошибка генерации: {type(e).__name__}. Попробуйте позже."


def generate_response_sync(scenario: str, user_input: str) -> str:
    """Синхронная обёртка для generate_response (для обратной совместимости)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(generate_response(scenario, user_input))