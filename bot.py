import logging
import asyncio
from functools import partial
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN, ALLOWED_USERS, ADMIN_IDS
from llm import generate_response
from parser import fetch_article_text
from sheets import log_interaction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Парсинг разрешённых пользователей
ALLOWED_USER_IDS = set()
if ALLOWED_USERS:
    for uid in ALLOWED_USERS.split(','):
        uid = uid.strip()
        if uid.isdigit():
            ALLOWED_USER_IDS.add(int(uid))

ADMIN_USER_IDS = set()
if ADMIN_IDS:
    for uid in ADMIN_IDS.split(','):
        uid = uid.strip()
        if uid.isdigit():
            ADMIN_USER_IDS.add(int(uid))

logger.info(f"Разрешённые пользователи: {len(ALLOWED_USER_IDS)} чел.")
logger.info(f"Администраторы: {len(ADMIN_USER_IDS)} чел.")

# Клавиатура сценариев
scenario_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Идея поста")],
        [KeyboardButton(text="✍️ Черновик текста")],
        [KeyboardButton(text="#️⃣ Хештеги")],
        [KeyboardButton(text="📱 Адаптация под платформу")],
        [KeyboardButton(text="🔗 Парсинг статьи → пост")]
    ],
    resize_keyboard=True
)

# Состояния (простая память)
user_scenario = {}  # user_id -> scenario
user_context = {}   # user_id -> {"platform": "", "original_text": ""}


def is_user_allowed(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя доступ к боту."""
    if not ALLOWED_USER_IDS:
        return True  # Если список пуст, доступ открыт всем
    return user_id in ALLOWED_USER_IDS


def is_user_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in ADMIN_USER_IDS


@dp.message(Command("start"))
async def start_cmd(message: Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    
    if not is_user_allowed(user_id):
        logger.warning(f"Попытка доступа от запрещённого пользователя {user_id}")
        await message.answer(
            "❌ Доступ к боту ограничен. Обратитесь к администратору."
        )
        return
    
    logger.info(f"Пользователь {user_id} (@{message.from_user.username}) запустил бота")
    await message.answer(
        "Привет! Я SMM-ассистент. Выбери сценарий:",
        reply_markup=scenario_kb
    )

@dp.message(lambda m: m.text in ["💡 Идея поста", "✍️ Черновик текста", "#️⃣ Хештеги", "📱 Адаптация под платформу", "🔗 Парсинг статьи → пост"])
async def choose_scenario(message: Message):
    """Обработчик выбора сценария."""
    user_id = message.from_user.id
    
    if not is_user_allowed(user_id):
        return
    
    scenario_map = {
        "💡 Идея поста": "idea",
        "✍️ Черновик текста": "text",
        "#️⃣ Хештеги": "hashtags",
        "📱 Адаптация под платформу": "adapt",
        "🔗 Парсинг статьи → пост": "parse"
    }
    scenario = scenario_map[message.text]
    user_scenario[user_id] = scenario
    
    logger.info(f"Пользователь {user_id} выбрал сценарий: {scenario}")
    
    if scenario == "adapt":
        await message.answer(
            "Напиши исходный текст поста, который нужно адаптировать.\n"
            "Затем укажи платформу (Telegram, VK, Instagram)."
        )
        user_context[user_id] = {}
    elif scenario == "parse":
        await message.answer("Отправь ссылку на статью.")
    else:
        await message.answer(
            "Опиши тему или нишу (например, 'бьюти, макияж для начинающих' "
            "или 'услуги клининга')."
        )

@dp.message()
async def handle_input(message: Message):
    """Основной обработчик сообщений пользователя."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    
    if not is_user_allowed(user_id):
        return
    
    scenario = user_scenario.get(user_id)
    
    if not scenario:
        await message.answer(
            "Сначала выбери сценарий с клавиатуры.",
            reply_markup=scenario_kb
        )
        return
    
    user_input = message.text.strip()
    logger.info(f"Пользователь {user_id}, сценарий '{scenario}': {user_input[:50]}...")
    
    try:
        # Сценарий адаптации — два шага
        if scenario == "adapt":
            ctx = user_context.get(user_id, {})
            if "original_text" not in ctx:
                ctx["original_text"] = user_input
                user_context[user_id] = ctx
                await message.answer("Теперь укажи платформу: Telegram, VK или Instagram.")
                return
            else:
                platform = user_input
                full_input = f"Исходный пост:\n{ctx['original_text']}\n\nАдаптируй для платформы: {platform}"
                
                typing_task = asyncio.create_task(message.answer("🧠 Генерирую..."))
                try:
                    output = await generate_response("adapt", full_input)
                finally:
                    try:
                        await typing_task
                    except:
                        pass
                
                await message.answer(output)
                log_interaction(user_id, username, "adapt", full_input, output)
                user_scenario.pop(user_id, None)
                user_context.pop(user_id, None)
                return
        
        # Сценарий парсинга статьи
        if scenario == "parse":
            if not (user_input.startswith("http://") or user_input.startswith("https://")):
                await message.answer(
                    "Пожалуйста, отправь ссылку (начинается с http:// или https://)"
                )
                return
            
            status_msg = await message.answer("🔍 Парсю статью...")
            title, text = fetch_article_text(user_input)
            
            if not text or "Ошибка" in text:
                await status_msg.edit_text(f"Не удалось распарсить: {text}")
                log_interaction(user_id, username, "parse", user_input, f"Error: {text}", "fail")
                user_scenario.pop(user_id, None)
                return
            
            await status_msg.edit_text("🧠 Генерирую пост...")
            output = await generate_response(
                "text",
                f"На основе статьи '{title}':\n{text}\n\nНапиши пост."
            )
            await status_msg.delete()
            await message.answer(f"✅ Готово:\n\n{output}")
            log_interaction(user_id, username, "parse", user_input, output)
            user_scenario.pop(user_id, None)
            return
        
        # Остальные сценарии (idea, text, hashtags)
        typing_task = asyncio.create_task(message.answer("🧠 Генерирую..."))
        try:
            output = await generate_response(scenario, user_input)
        finally:
            try:
                await typing_task
            except:
                pass
        
        await message.answer(output)
        log_interaction(user_id, username, scenario, user_input, output)
        user_scenario.pop(user_id, None)
        
    except asyncio.CancelledError:
        logger.warning(f"Запрос пользователя {user_id} отменён")
        await message.answer("⚠️ Запрос отменён. Попробуйте ещё раз.")
    except Exception as e:
        logger.error(f"Критическая ошибка в handle_input: {type(e).__name__}: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при обработке запроса. "
            "Попробуйте позже или обратитесь к администратору."
        )
        user_scenario.pop(user_id, None)

@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    """Админ-команда для просмотра статистики."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        logger.warning(f"Попытка доступа к /admin от не-админа {user_id}")
        await message.answer("❌ Недостаточно прав.")
        return
    
    stats = (
        f"📊 Статистика бота:\n\n"
        f"Активных сессий: {len(user_scenario)}\n"
        f"Разрешённых пользователей: {len(ALLOWED_USER_IDS)}\n"
        f"Администраторов: {len(ADMIN_USER_IDS)}"
    )
    await message.answer(stats)


async def main():
    """Запуск бота."""
    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("Сессия бота закрыта")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")