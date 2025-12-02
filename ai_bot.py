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
from aiogram.client.session.aiohttp import AiohttpSession
from sqlalchemy import select
from config import config
from database import Service, Product, async_session

logging.basicConfig(level=logging.INFO)

# Инициализация с прокси
session = AiohttpSession(proxy=config.PROXY_URL)
bot = Bot(token=config.AI_BOT_TOKEN, session=session)
dp = Dispatcher()

# Настройка Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 600,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)


async def get_services_info() -> str:
    """Получаем актуальные услуги из БД"""
    try:
        async with async_session() as session:
            query = select(Service).where(Service.is_active == True).order_by(Service.order)
            result = await session.execute(query)
            services = result.scalars().all()
        
        if not services:
            return "Услуги временно недоступны."
        
        info = "АКТУАЛЬНЫЕ УСЛУГИ И ЦЕНЫ:\n\n"
        for s in services:
            info += f"📸 {s.name}\n"
            info += f"   Цена: {s.price:,.0f} руб.\n"
            if s.duration:
                info += f"   Длительность: {s.duration}\n"
            if s.description:
                info += f"   Описание: {s.description[:100]}...\n"
            info += "\n"
        
        return info
    except Exception as e:
        logging.error(f"Error getting services: {e}")
        return "Не удалось загрузить услуги."


async def get_products_info() -> str:
    """Получаем актуальные товары из БД"""
    try:
        async with async_session() as session:
            query = select(Product).where(Product.is_active == True).order_by(Product.order)
            result = await session.execute(query)
            products = result.scalars().all()
        
        if not products:
            return "Товары временно недоступны."
        
        info = "АКТУАЛЬНЫЕ ТОВАРЫ:\n\n"
        for p in products:
            type_text = "Цифровой" if p.product_type == "digital" else "Бумажный"
            info += f"🎨 {p.name} ({type_text})\n"
            info += f"   Цена: {p.price:,.0f} руб.\n"
            if p.description:
                info += f"   Описание: {p.description[:100]}...\n"
            info += "\n"
        
        return info
    except Exception as e:
        logging.error(f"Error getting products: {e}")
        return "Не удалось загрузить товары."


async def build_system_prompt() -> str:
    """Строим системный промпт с актуальными данными из БД"""
    
    services_info = await get_services_info()
    products_info = await get_products_info()
    
    prompt = f"""Ты - AI ассистент фотографа Марины Заугольниковой. Отвечай на русском языке.

📸 О Марине:
- Профессиональный фотограф
- Специализация: портретная съёмка, семейные фотосессии, love story, детская съёмка
- Работает в студиях Москвы
- Создаёт уникальные коллажи (цифровые и бумажные)

{services_info}

{products_info}

📋 Твои задачи:
1. Отвечать на вопросы о услугах и ценах (используй АКТУАЛЬНЫЕ данные выше!)
2. Помогать с выбором типа съёмки
3. Объяснять процесс работы
4. Давать рекомендации по подготовке к съёмке
5. Направлять на запись через бота

✅ Правила:
- Будь дружелюбным и профессиональным
- Отвечай кратко (2-4 предложения), но информативно
- Используй эмодзи для дружелюбности
- ВСЕГДА называй ТОЧНЫЕ цены из данных выше!
- Предлагай записаться через бот: @{config.MAIN_BOT_USERNAME}
- Если спрашивают о чём-то, чего нет в данных — направляй к Марине

🔗 Ссылки для ответов:
- Бот для записи: @{config.MAIN_BOT_USERNAME}
- Ссылка на запись: t.me/{config.MAIN_BOT_USERNAME}?start=booking
- Посмотреть услуги: t.me/{config.MAIN_BOT_USERNAME}?start=services
- Посмотреть товары: t.me/{config.MAIN_BOT_USERNAME}?start=products
"""
    return prompt


async def get_gemini_response(query: str) -> str:
    """Получить ответ от AI с актуальными данными"""
    try:
        # Получаем актуальный промпт с данными из БД
        system_prompt = await build_system_prompt()
        
        chat = model.start_chat(history=[])
        
        full_prompt = f"{system_prompt}\n\nВопрос клиента: {query}\n\nОтветь кратко и по делу, используя актуальные цены:"
        
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
                        "• Какие есть коллажи?"
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
                        f"Чтобы узнать цены, введите:\n"
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
        # Есть запрос - получаем ответ от Gemini с актуальными данными
        ai_response = await get_gemini_response(query)
        
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
        cache_time=10,
        is_personal=True
    )


@dp.message()
async def handle_direct_message(message):
    """Если кто-то пишет боту напрямую — тоже отвечаем с AI!"""
    query = message.text
    
    if not query or query.startswith('/'):
        await message.answer(
            f"🤖 <b>AI Ассистент Марины</b>\n\n"
            f"Задайте мне любой вопрос о фотосессиях!\n\n"
            f"Или используйте в любом чате:\n"
            f"<code>@{config.AI_BOT_USERNAME} ваш вопрос</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="📸 Бот Марины",
                    url=f"https://t.me/{config.MAIN_BOT_USERNAME}"
                )
            ]])
        )
        return
    
    # Отправляем "печатает..."
    await message.answer_chat_action("typing")
    
    # Получаем ответ от AI с актуальными данными
    ai_response = await get_gemini_response(query)
    
    await message.answer(
        f"🤖 {ai_response}",
        parse_mode="HTML",
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
            ]
        ])
    )


async def main():
    """Запуск AI бота"""
    logging.info("🤖 AI бот (Gemini) запускается...")
    logging.info("📊 Подключён к БД основного бота — цены актуальные!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
