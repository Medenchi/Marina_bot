cat > ai_bot.py << 'EOF'
import asyncio
import logging
import aiohttp
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

tg_session = AiohttpSession(proxy=config.PROXY_URL)
bot = Bot(token=config.AI_BOT_TOKEN, session=tg_session)
dp = Dispatcher()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-oss-20b:free"


async def get_services_info() -> str:
    try:
        async with async_session() as session:
            query = select(Service).where(Service.is_active == True).order_by(Service.order)
            result = await session.execute(query)
            services = result.scalars().all()
        
        if not services:
            return "Услуги временно недоступны."
        
        info = "АКТУАЛЬНЫЕ УСЛУГИ И ЦЕНЫ:\n\n"
        for s in services:
            info += f"📸 {s.name} - {s.price:,.0f} руб."
            if s.duration:
                info += f" ({s.duration})"
            info += "\n"
        return info
    except Exception as e:
        logging.error(f"Error getting services: {e}")
        return ""


async def get_products_info() -> str:
    try:
        async with async_session() as session:
            query = select(Product).where(Product.is_active == True).order_by(Product.order)
            result = await session.execute(query)
            products = result.scalars().all()
        
        if not products:
            return ""
        
        info = "ТОВАРЫ:\n\n"
        for p in products:
            type_text = "📱" if p.product_type == "digital" else "📄"
            info += f"{type_text} {p.name} - {p.price:,.0f} руб.\n"
        return info
    except Exception as e:
        logging.error(f"Error getting products: {e}")
        return ""


async def build_system_prompt() -> str:
    services_info = await get_services_info()
    products_info = await get_products_info()
    
    return f"""Ты - AI ассистент фотографа Марины Заугольниковой. Отвечай на русском.

{services_info}
{products_info}

Правила:
- Отвечай кратко (2-3 предложения)
- Называй точные цены из данных выше
- Используй эмодзи
- Предлагай записаться: @{config.MAIN_BOT_USERNAME}
- Ссылка на запись: t.me/{config.MAIN_BOT_USERNAME}?start=booking"""


async def get_ai_response(query: str) -> str:
    try:
        system_prompt = await build_system_prompt()
        
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/MarinaZaugolnikova_bot",
            "X-Title": "Marina Photo Bot"
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error = await resp.text()
                    logging.error(f"OpenRouter error: {resp.status} - {error}")
                    raise Exception(error)
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return f"😔 Извините, не могу ответить.\n\nСвяжитесь с Мариной: @{config.MAIN_BOT_USERNAME}"


@dp.inline_query()
async def inline_ai_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    results = []
    
    if not query:
        results = [
            InlineQueryResultArticle(
                id="help",
                title="🤖 AI Ассистент Марины",
                description="Введите ваш вопрос...",
                input_message_content=InputTextMessageContent(
                    message_text=f"🤖 <b>AI Ассистент</b>\n\nВведите: <code>@{config.AI_BOT_USERNAME} ваш вопрос</code>",
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="📸 Бот Марины", url=f"https://t.me/{config.MAIN_BOT_USERNAME}")
                ]])
            ),
            InlineQueryResultArticle(
                id="booking",
                title="📝 Записаться",
                description="На съёмку",
                input_message_content=InputTextMessageContent(
                    message_text="📸 <b>Запись на фотосессию</b>\n\nНажмите кнопку! 👇",
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="📝 Записаться", url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking")
                ]])
            )
        ]
    else:
        ai_response = await get_ai_response(query)
        results.append(
            InlineQueryResultArticle(
                id="ai_response",
                title="🤖 Ответ",
                description=ai_response[:100],
                input_message_content=InputTextMessageContent(
                    message_text=f"❓ <b>Вопрос:</b> {query}\n\n🤖 {ai_response}\n\n━━━━━━━━━\n📸 <b>Марина Заугольникова</b>",
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📝 Записаться", url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"),
                        InlineKeyboardButton(text="📸 Услуги", url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=services")
                    ]
                ])
            )
        )
    
    await inline_query.answer(results=results, cache_time=10, is_personal=True)


@dp.message()
async def handle_message(message):
    query = message.text
    
    if not query or query.startswith('/'):
        await message.answer(
            f"🤖 <b>AI Ассистент Марины</b>\n\nЗадайте вопрос о фотосессиях!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📸 Бот Марины", url=f"https://t.me/{config.MAIN_BOT_USERNAME}")
            ]])
        )
        return
    
    await message.answer_chat_action("typing")
    ai_response = await get_ai_response(query)
    
    await message.answer(
        f"🤖 {ai_response}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📝 Записаться", url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking")
        ]])
    )


async def main():
    logging.info("🤖 AI бот (OpenRouter) запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
EOF
