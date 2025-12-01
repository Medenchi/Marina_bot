import asyncio
import logging
import google.generativeai as genai
from aiogram import Bot, Dispatcher
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import config

logging.basicConfig(level=logging.INFO)

# Инициализация Telegram бота
bot = Bot(token=config.AI_BOT_TOKEN)
dp = Dispatcher()

# Настройка Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

# Настройки генерации
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 600,
}

# Настройки безопасности (можно ослабить при необходимости)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Создаём модель
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",  # Быстрая и бесплатная модель
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Системный промпт
SYSTEM_PROMPT = f"""Ты - AI ассистент фотографа Марины Заугольниковой. Отвечай на русском языке.

📸 Информация о Марине:
- Профессиональный фотограф
- Специализация: портретная съёмка, семейные фотосессии, love story, детская съёмка
- Работает в студиях Москвы
- Создаёт уникальные коллажи (цифровые и бумажные)

🎯 Примерные цены (уточняй что точные цены в боте):
- Портретная съёмка: от 5000 руб/час
- Семейная съёмка: от 7000 руб/час
- Love Story: от 8000 руб/час
- Детская съёмка: от 6000 руб/час

📋 Твои задачи:
1. Отвечать на вопросы о услугах фотографа
2. Помогать с выбором типа съёмки
3. Объяснять процесс работы
4. Давать рекомендации по подготовке к съёмке
5. Направлять на запись через бота

✅ Правила:
- Будь дружелюбным и профессиональным
- Отвечай кратко (2-4 предложения), но информативно
- Используй эмодзи для дружелюбности
- Всегда предлагай записаться через бот: @{config.MAIN_BOT_USERNAME}
- Если не знаешь точный ответ - направляй к Марине

🔗 Полезные ссылки для ответов:
- Бот для записи: @{config.MAIN_BOT_USERNAME}
- Ссылка на запись: t.me/{config.MAIN_BOT_USERNAME}?start=booking
- Посмотреть услуги: t.me/{config.MAIN_BOT_USERNAME}?start=services
"""

async def get_gemini_response(query: str) -> str:
    """Получить ответ от ИИ АССИСТЕНТА"""
    try:
        # Создаём чат с системным промптом
        chat = model.start_chat(history=[])
        
        # Отправляем системный промпт + вопрос пользователя
        full_prompt = f"{SYSTEM_PROMPT}\n\nВопрос клиента: {query}\n\nОтветь кратко и по делу:"
        
        response = await asyncio.to_thread(
            chat.send_message,
            full_prompt
        )
        
        return response.text
        
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return (
            "😔 Извините, не могу сейчас ответить.\n\n"
            f"Свяжитесь с Мариной напрямую через бот:\n"
            f"@{config.MAIN_BOT_USERNAME}"
        )

@dp.inline_query()
async def inline_ai_handler(inline_query: InlineQuery):
    """Обработка inline запросов к AI"""
    query = inline_query.query.strip()
    
    results = []
    
    if not query:
        # Пустой запрос - показываем подсказки
        results = [
            InlineQueryResultArticle(
                id="help",
                title="🤖 AI Ассистент Марины",
                description="Введите ваш вопрос...",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🤖 <b>AI Ассистент фотографа Марины</b>\n\n"
                        f"Чтобы задать вопрос, введите:\n"
                        f"<code>@{config.AI_BOT_USERNAME} ваш вопрос</code>\n\n"
                        "💡 <b>Примеры вопросов:</b>\n"
                        "• Сколько стоит семейная съёмка?\n"
                        "• Как подготовиться к фотосессии?\n"
                        "• Что взять с собой на съёмку?\n"
                        "• Сколько фото получу?"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="📸 Открыть бот Марины",
                        url=f"https://t.me/{config.MAIN_BOT_USERNAME}"
                    )
                ]])
            ),
            InlineQueryResultArticle(
                id="quick_price",
                title="💰 Узнать цены",
                description="Спросить про стоимость услуг",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"Чтобы узнать точные цены, введите:\n"
                        f"<code>@{config.AI_BOT_USERNAME} сколько стоит съёмка</code>"
                    ),
                    parse_mode="HTML"
                )
            ),
            InlineQueryResultArticle(
                id="quick_booking",
                title="📝 Записаться",
                description="Перейти к записи на съёмку",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "📸 <b>Запись на фотосессию</b>\n\n"
                        "Нажмите кнопку ниже, чтобы записаться к Марине! 👇"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="📝 Записаться на съёмку",
                        url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"
                    )
                ]])
            )
        ]
    
    else:
        # Есть запрос - получаем ответ от Gemini
        ai_response = await get_gemini_response(query)
        
        # Основной ответ
        results.append(
            InlineQueryResultArticle(
                id="ai_response",
                title="🤖 Ответ ассистента",
                description=ai_response[:100] + "..." if len(ai_response) > 100 else ai_response,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"❓ <b>Вопрос:</b>\n{query}\n\n"
                        f"🤖 <b>AI Ассистент:</b>\n{ai_response}\n\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📸 Фотограф: <b>Марина Заугольникова</b>"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📝 Записаться",
                            url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"
                        ),
                        InlineKeyboardButton(
                            text="📸 Услуги",
                            url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=services"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="💬 Написать Марине",
                            url=f"https://t.me/{config.MAIN_BOT_USERNAME}"
                        )
                    ]
                ])
            )
        )
        
        # Быстрая кнопка записи
        results.append(
            InlineQueryResultArticle(
                id="quick_book",
                title="📝 Хочу записаться!",
                description="Отправить ссылку на запись",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "📸 <b>Хочу записаться на фотосессию!</b>\n\n"
                        "Нажмите кнопку ниже 👇"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="📝 Записаться на съёмку",
                        url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"
                    )
                ]])
            )
        )
    
    await inline_query.answer(
        results=results,
        cache_time=10,  # Короткий кэш
        is_personal=True
    )

# Дополнительно: обработка личных сообщений боту
@dp.message()
async def handle_direct_message(message):
    """Если кто-то пишет боту напрямую"""
    await message.answer(
        f"🤖 <b>Я работаю только в inline режиме!</b>\n\n"
        f"Чтобы задать вопрос, введите в любом чате:\n"
        f"<code>@{config.AI_BOT_USERNAME} ваш вопрос</code>\n\n"
        f"Или перейдите в основной бот Марины:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📸 Бот Марины",
                url=f"https://t.me/{config.MAIN_BOT_USERNAME}"
            )
        ]])
    )

async def main():
    """Запуск AI бота"""
    logging.info("🤖 AI бот (Gemini) запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())