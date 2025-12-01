from aiogram import Router, F
from aiogram.types import (
    InlineQuery, 
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
    ChosenInlineResult
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Service, Product, async_session
from keyboards.keyboards import inline_service_kb, inline_product_kb
from config import config
import hashlib

router = Router()

@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    """Обработка inline запросов (@bot запрос)"""
    query = inline_query.query.lower().strip()
    results = []
    
    async with async_session() as session:
        # Если пустой запрос или "прайс" - показываем услуги
        if not query or query in ["прайс", "price", "услуги", "цены"]:
            results.extend(await get_services_inline_results(session))
        
        # Если запрос "товары" - показываем товары
        elif query in ["товары", "товар", "коллаж", "коллажи", "products"]:
            results.extend(await get_products_inline_results(session))
        
        # Если запрос "запись" - кнопка записи
        elif query in ["запись", "записаться", "book", "booking"]:
            results.append(get_booking_inline_result())
        
        # Поиск по всему
        else:
            results.extend(await search_inline_results(session, query))
    
    # Если нет результатов - показываем меню
    if not results:
        results = get_default_menu_results()
    
    await inline_query.answer(
        results=results[:50],  # Лимит 50 результатов
        cache_time=60,
        is_personal=True
    )

async def get_services_inline_results(session: AsyncSession) -> list:
    """Получить услуги для inline"""
    results = []
    
    query = select(Service).where(Service.is_active == True).order_by(Service.order)
    result = await session.execute(query)
    services = result.scalars().all()
    
    for service in services:
        # Формируем описание
        description = f"💰 {service.price:,.0f} руб."
        if service.duration:
            description += f" | ⏱ {service.duration}"
        
        # Текст сообщения
        message_text = f"""📸 <b>{service.name}</b>

{service.description or ''}

💰 <b>Стоимость:</b> {service.price:,.0f} руб.
⏱ <b>Длительность:</b> {service.duration or 'По договорённости'}

👩‍🎨 Фотограф: Марина Заугольникова"""

        # Если есть фото - показываем как фото
        if service.photo_url:
            results.append(
                InlineQueryResultPhoto(
                    id=f"service_{service.id}",
                    photo_url=service.photo_url,
                    thumbnail_url=service.photo_url,
                    title=service.name,
                    description=description,
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=inline_service_kb(service.id, config.MAIN_BOT_USERNAME)
                )
            )
        else:
            results.append(
                InlineQueryResultArticle(
                    id=f"service_{service.id}",
                    title=f"📸 {service.name}",
                    description=description,
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=inline_service_kb(service.id, config.MAIN_BOT_USERNAME),
                    thumbnail_url="https://i.imgur.com/camera_icon.png"  # Иконка камеры
                )
            )
    
    # Добавляем общую карточку прайса в начало
    if services:
        price_text = "📸 <b>ПРАЙС на услуги</b>\n\n"
        for s in services:
            price_text += f"• {s.name} — {s.price:,.0f} руб.\n"
        price_text += f"\n👩‍🎨 Фотограф: Марина Заугольникова"
        
        results.insert(0, 
            InlineQueryResultArticle(
                id="full_price",
                title="📋 Полный прайс",
                description="Показать все услуги одним сообщением",
                input_message_content=InputTextMessageContent(
                    message_text=price_text,
                    parse_mode="HTML"
                ),
                reply_markup=inline_service_kb(0, config.MAIN_BOT_USERNAME)
            )
        )
    
    return results

async def get_products_inline_results(session: AsyncSession) -> list:
    """Получить товары для inline"""
    results = []
    
    query = select(Product).where(Product.is_active == True).order_by(Product.order)
    result = await session.execute(query)
    products = result.scalars().all()
    
    for product in products:
        type_emoji = "📱" if product.product_type == "digital" else "📄"
        type_text = "Цифровой" if product.product_type == "digital" else "Бумажный"
        
        message_text = f"""{type_emoji} <b>{product.name}</b>

{product.description or ''}

💰 <b>Стоимость:</b> {product.price:,.0f} руб.
📦 <b>Тип:</b> {type_text}

👩‍🎨 Марина Заугольникова"""

        if product.photo_url:
            results.append(
                InlineQueryResultPhoto(
                    id=f"product_{product.id}",
                    photo_url=product.photo_url,
                    thumbnail_url=product.photo_url,
                    title=f"{type_emoji} {product.name}",
                    description=f"💰 {product.price:,.0f} руб.",
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=inline_product_kb(product.id, config.MAIN_BOT_USERNAME)
                )
            )
        else:
            results.append(
                InlineQueryResultArticle(
                    id=f"product_{product.id}",
                    title=f"{type_emoji} {product.name}",
                    description=f"💰 {product.price:,.0f} руб. | {type_text}",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=inline_product_kb(product.id, config.MAIN_BOT_USERNAME)
                )
            )
    
    return results

async def search_inline_results(session: AsyncSession, query: str) -> list:
    """Поиск по услугам и товарам"""
    results = []
    
    # Поиск услуг
    services_query = select(Service).where(
        Service.is_active == True,
        Service.name.ilike(f"%{query}%")
    )
    services_result = await session.execute(services_query)
    services = services_result.scalars().all()
    
    for service in services:
        results.append(
            InlineQueryResultArticle(
                id=f"search_service_{service.id}",
                title=f"📸 {service.name}",
                description=f"💰 {service.price:,.0f} руб.",
                input_message_content=InputTextMessageContent(
                    message_text=f"📸 <b>{service.name}</b>\n💰 {service.price:,.0f} руб.",
                    parse_mode="HTML"
                ),
                reply_markup=inline_service_kb(service.id, config.MAIN_BOT_USERNAME)
            )
        )
    
    # Поиск товаров
    products_query = select(Product).where(
        Product.is_active == True,
        Product.name.ilike(f"%{query}%")
    )
    products_result = await session.execute(products_query)
    products = products_result.scalars().all()
    
    for product in products:
        type_emoji = "📱" if product.product_type == "digital" else "📄"
        results.append(
            InlineQueryResultArticle(
                id=f"search_product_{product.id}",
                title=f"{type_emoji} {product.name}",
                description=f"💰 {product.price:,.0f} руб.",
                input_message_content=InputTextMessageContent(
                    message_text=f"{type_emoji} <b>{product.name}</b>\n💰 {product.price:,.0f} руб.",
                    parse_mode="HTML"
                ),
                reply_markup=inline_product_kb(product.id, config.MAIN_BOT_USERNAME)
            )
        )
    
    return results

def get_booking_inline_result() -> InlineQueryResultArticle:
    """Карточка записи"""
    return InlineQueryResultArticle(
        id="booking",
        title="📝 Записаться на съёмку",
        description="Открыть форму записи",
        input_message_content=InputTextMessageContent(
            message_text="""📸 <b>Фотограф Марина Заугольникова</b>

Хотите записаться на фотосессию? 
Нажмите кнопку ниже для записи! 👇""",
            parse_mode="HTML"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📝 Записаться",
                url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"
            )
        ]])
    )

def get_default_menu_results() -> list:
    """Меню по умолчанию"""
    return [
        InlineQueryResultArticle(
            id="menu_price",
            title="📋 Прайс",
            description="Посмотреть услуги и цены",
            input_message_content=InputTextMessageContent(
                message_text="Введите @бот <b>прайс</b> для просмотра услуг",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_products",
            title="🎨 Товары",
            description="Коллажи и фотопродукция",
            input_message_content=InputTextMessageContent(
                message_text="Введите @бот <b>товары</b> для просмотра каталога",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_booking",
            title="📝 Записаться",
            description="Оставить заявку на съёмку",
            input_message_content=InputTextMessageContent(
                message_text=f"Для записи перейдите: https://t.me/{config.MAIN_BOT_USERNAME}?start=booking",
                parse_mode="HTML"
            )
        )
    ]