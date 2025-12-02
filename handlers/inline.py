from aiogram import Router, F
from aiogram.types import (
    InlineQuery, 
    InlineQueryResultArticle,
    InlineQueryResultCachedPhoto,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from sqlalchemy import select
from database import Service, Product, async_session
from keyboards.keyboards import inline_service_kb, inline_product_kb
from config import config

router = Router()

# Кэш для file_id сгенерированных картинок
price_image_cache = {}

@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    """Обработка inline запросов"""
    query = inline_query.query.lower().strip()
    results = []
    
    async with async_session() as session:
        if not query or query in ["прайс", "price", "услуги", "цены"]:
            results.extend(await get_services_inline_results(session))
        
        elif query in ["товары", "товар", "коллаж", "коллажи", "products"]:
            results.extend(await get_products_inline_results(session))
        
        elif query in ["запись", "записаться", "book", "booking"]:
            results.append(get_booking_inline_result())
        
        else:
            results.extend(await search_inline_results(session, query))
    
    if not results:
        results = get_default_menu_results()
    
    await inline_query.answer(
        results=results[:50],
        cache_time=300,
        is_personal=False
    )

async def get_services_inline_results(session) -> list:
    """Получить услуги для inline"""
    results = []
    
    query = select(Service).where(Service.is_active == True).order_by(Service.order)
    result = await session.execute(query)
    services = result.scalars().all()
    
    if not services:
        return results
    
    # Красивый текстовый прайс с картинкой-эмуляцией
    price_text = "📸 <b>ПРАЙС НА УСЛУГИ</b>\n"
    price_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for s in services:
        price_text += f"✨ <b>{s.name}</b>\n"
        price_text += f"    💰 {s.price:,.0f} ₽"
        if s.duration:
            price_text += f"  •  ⏱ {s.duration}"
        price_text += "\n\n"
    
    price_text += "━━━━━━━━━━━━━━━━━━━━\n"
    price_text += "👩‍🎨 <b>Марина Заугольникова</b>\n"
    price_text += f"📱 @{config.MAIN_BOT_USERNAME}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📝 Записаться на съёмку",
            url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"
        )],
        [InlineKeyboardButton(
            text="📸 Подробнее об услугах",
            url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=services"
        )]
    ])
    
    results.append(
        InlineQueryResultArticle(
            id="full_price",
            title="📋 Отправить прайс",
            description="Красивый прайс со всеми услугами",
            thumbnail_url="https://i.imgur.com/8QZQY9L.png",
            input_message_content=InputTextMessageContent(
                message_text=price_text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    )
    
    # Отдельные услуги
    for service in services:
        description = f"💰 {service.price:,.0f} ₽"
        if service.duration:
            description += f" • ⏱ {service.duration}"
        
        message_text = f"""📸 <b>{service.name}</b>

{service.description or ''}

💰 <b>Стоимость:</b> {service.price:,.0f} ₽
⏱ <b>Длительность:</b> {service.duration or 'По договорённости'}

━━━━━━━━━━━━━━━━━━━━
👩‍🎨 <b>Марина Заугольникова</b>"""

        if service.photo_url:
            results.append(
                InlineQueryResultCachedPhoto(
                    id=f"service_{service.id}",
                    photo_file_id=service.photo_url,
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
                    thumbnail_url="https://i.imgur.com/8QZQY9L.png",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=inline_service_kb(service.id, config.MAIN_BOT_USERNAME)
                )
            )
    
    return results

async def get_products_inline_results(session) -> list:
    """Получить товары для inline"""
    results = []
    
    query = select(Product).where(Product.is_active == True).order_by(Product.order)
    result = await session.execute(query)
    products = result.scalars().all()
    
    if not products:
        return results
    
    # Каталог товаров
    catalog_text = "🎨 <b>КАТАЛОГ ТОВАРОВ</b>\n"
    catalog_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for p in products:
        type_emoji = "📱" if p.product_type == "digital" else "📄"
        catalog_text += f"{type_emoji} <b>{p.name}</b>\n"
        catalog_text += f"    💰 {p.price:,.0f} ₽\n\n"
    
    catalog_text += "━━━━━━━━━━━━━━━━━━━━\n"
    catalog_text += "👩‍🎨 <b>Марина Заугольникова</b>"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎨 Посмотреть каталог",
            url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=products"
        )],
        [InlineKeyboardButton(
            text="💬 Связаться",
            url=f"https://t.me/{config.MAIN_BOT_USERNAME}"
        )]
    ])
    
    results.append(
        InlineQueryResultArticle(
            id="full_catalog",
            title="🎨 Отправить каталог товаров",
            description="Коллажи и фотопродукция",
            thumbnail_url="https://i.imgur.com/YqQYz0L.png",
            input_message_content=InputTextMessageContent(
                message_text=catalog_text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    )
    
    # Отдельные товары
    for product in products:
        type_emoji = "📱" if product.product_type == "digital" else "📄"
        type_text = "Цифровой" if product.product_type == "digital" else "Бумажный"
        
        message_text = f"""{type_emoji} <b>{product.name}</b>

{product.description or ''}

💰 <b>Стоимость:</b> {product.price:,.0f} ₽
📦 <b>Тип:</b> {type_text}

━━━━━━━━━━━━━━━━━━━━
👩‍🎨 <b>Марина Заугольникова</b>"""

        if product.photo_url:
            results.append(
                InlineQueryResultCachedPhoto(
                    id=f"product_{product.id}",
                    photo_file_id=product.photo_url,
                    title=f"{type_emoji} {product.name}",
                    description=f"💰 {product.price:,.0f} ₽",
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
                    description=f"💰 {product.price:,.0f} ₽ • {type_text}",
                    thumbnail_url="https://i.imgur.com/YqQYz0L.png",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=inline_product_kb(product.id, config.MAIN_BOT_USERNAME)
                )
            )
    
    return results

async def search_inline_results(session, query: str) -> list:
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
                description=f"💰 {service.price:,.0f} ₽",
                input_message_content=InputTextMessageContent(
                    message_text=f"📸 <b>{service.name}</b>\n💰 {service.price:,.0f} ₽",
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
                description=f"💰 {product.price:,.0f} ₽",
                input_message_content=InputTextMessageContent(
                    message_text=f"{type_emoji} <b>{product.name}</b>\n💰 {product.price:,.0f} ₽",
                    parse_mode="HTML"
                ),
                reply_markup=inline_product_kb(product.id, config.MAIN_BOT_USERNAME)
            )
        )
    
    return results

def get_booking_inline_result():
    """Карточка записи"""
    return InlineQueryResultArticle(
        id="booking",
        title="📝 Записаться на съёмку",
        description="Открыть форму записи",
        thumbnail_url="https://i.imgur.com/kJ5aZVL.png",
        input_message_content=InputTextMessageContent(
            message_text="""📸 <b>Фотограф Марина Заугольникова</b>

✨ Хотите записаться на фотосессию?
Нажмите кнопку ниже! 👇""",
            parse_mode="HTML"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📝 Записаться на съёмку",
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
            thumbnail_url="https://i.imgur.com/8QZQY9L.png",
            input_message_content=InputTextMessageContent(
                message_text="Введите <b>@бот прайс</b> для просмотра услуг",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_products",
            title="🎨 Товары",
            description="Коллажи и фотопродукция",
            thumbnail_url="https://i.imgur.com/YqQYz0L.png",
            input_message_content=InputTextMessageContent(
                message_text="Введите <b>@бот товары</b> для просмотра каталога",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_booking",
            title="📝 Записаться",
            description="Оставить заявку на съёмку",
            thumbnail_url="https://i.imgur.com/kJ5aZVL.png",
            input_message_content=InputTextMessageContent(
                message_text=f"Для записи перейдите: https://t.me/{config.MAIN_BOT_USERNAME}?start=booking",
                parse_mode="HTML"
            )
        )
            ]
