from aiogram import Router, F
from aiogram.types import (
    InlineQuery, 
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InlineQueryResultCachedPhoto,
    InputTextMessageContent,
    BufferedInputFile,
    ChosenInlineResult
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Service, Product, async_session
from keyboards.keyboards import inline_service_kb, inline_product_kb
from config import config
from utils.image_generator import price_generator
import hashlib

router = Router()

# Кэш для хранения file_id сгенерированных изображений
image_cache = {}

@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    """Обработка inline запросов (@bot запрос)"""
    query = inline_query.query.lower().strip()
    results = []
    
    async with async_session() as session:
        # Если пустой запрос или "прайс" - показываем услуги
        if not query or query in ["прайс", "price", "услуги", "цены"]:
            results.extend(await get_services_inline_results(session, inline_query))
        
        # Если запрос "товары" - показываем товары
        elif query in ["товары", "товар", "коллаж", "коллажи", "products"]:
            results.extend(await get_products_inline_results(session, inline_query))
        
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
        results=results[:50],
        cache_time=60,
        is_personal=True
    )

async def get_services_inline_results(session: AsyncSession, inline_query: InlineQuery) -> list:
    """Получить услуги для inline с картинкой прайса"""
    results = []
    
    query = select(Service).where(Service.is_active == True).order_by(Service.order)
    result = await session.execute(query)
    services = result.scalars().all()
    
    if not services:
        return results
    
    # === ГЕНЕРИРУЕМ КАРТИНКУ ПРАЙСА ===
    services_data = [
        {
            'name': s.name,
            'price': s.price,
            'duration': s.duration or ''
        }
        for s in services
    ]
    
    # Генерируем изображение
    try:
        image_buffer = price_generator.generate_price_image(
            services=services_data,
            title="ПРАЙС НА УСЛУГИ",
            photographer_name="Марина Заугольникова",
            contact=f"@{config.MAIN_BOT_USERNAME}"
        )
        
        # Создаём хэш для кэширования
        services_hash = hashlib.md5(
            str([(s.name, s.price) for s in services]).encode()
        ).hexdigest()[:10]
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Записаться на съёмку",
                    url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 Подробнее об услугах",
                    url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=services"
                )
            ]
        ])
        
        # К сожалению InlineQueryResultPhoto требует URL, а не файл
        # Поэтому добавляем картинку как текстовый результат с фото
        # Но мы можем отправить через другой способ
        
        # Пока добавляем красивый текстовый прайс
        price_text = "📸 <b>ПРАЙС НА УСЛУГИ</b>\n\n"
        price_text += "━━━━━━━━━━━━━━━\n\n"
        
        for s in services:
            price_text += f"✨ <b>{s.name}</b>\n"
            price_text += f"   💰 {s.price:,.0f} руб."
            if s.duration:
                price_text += f" | ⏱ {s.duration}"
            price_text += "\n\n"
        
        price_text += "━━━━━━━━━━━━━━━\n"
        price_text += f"👩‍🎨 <b>Марина Заугольникова</b>\n"
        price_text += f"📱 @{config.MAIN_BOT_USERNAME}"
        
        results.append(
            InlineQueryResultArticle(
                id="full_price_image",
                title="📋 Отправить прайс",
                description="Красивый прайс со всеми услугами",
                thumbnail_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                input_message_content=InputTextMessageContent(
                    message_text=price_text,
                    parse_mode="HTML"
                ),
                reply_markup=kb
            )
        )
        
    except Exception as e:
        print(f"Error generating price image: {e}")
    
    # Добавляем отдельные услуги
    for service in services:
        description = f"💰 {service.price:,.0f} руб."
        if service.duration:
            description += f" | ⏱ {service.duration}"
        
        message_text = f"""📸 <b>{service.name}</b>

{service.description or ''}

💰 <b>Стоимость:</b> {service.price:,.0f} руб.
⏱ <b>Длительность:</b> {service.duration or 'По договорённости'}

👩‍🎨 Фотограф: Марина Заугольникова"""

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
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=inline_service_kb(service.id, config.MAIN_BOT_USERNAME),
                    thumbnail_url="https://cdn-icons-png.flaticon.com/512/2956/2956744.png"
                )
            )
    
    return results

async def get_products_inline_results(session: AsyncSession, inline_query: InlineQuery) -> list:
    """Получить товары для inline"""
    results = []
    
    query = select(Product).where(Product.is_active == True).order_by(Product.order)
    result = await session.execute(query)
    products = result.scalars().all()
    
    if not products:
        return results
    
    # Генерируем картинку каталога
    try:
        products_data = [
            {
                'name': p.name,
                'price': p.price,
                'type': p.product_type
            }
            for p in products
        ]
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎨 Посмотреть каталог",
                    url=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=products"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Заказать",
                    url=f"https://t.me/{config.MAIN_BOT_USERNAME}"
                )
            ]
        ])
        
        # Текстовый каталог
        catalog_text = "🎨 <b>КАТАЛОГ ТОВАРОВ</b>\n\n"
        catalog_text += "━━━━━━━━━━━━━━━\n\n"
        
        for p in products:
            type_emoji = "📱" if p.product_type == "digital" else "📄"
            catalog_text += f"{type_emoji} <b>{p.name}</b>\n"
            catalog_text += f"   💰 {p.price:,.0f} руб.\n\n"
        
        catalog_text += "━━━━━━━━━━━━━━━\n"
        catalog_text += f"👩‍🎨 <b>Марина Заугольникова</b>"
        
        results.append(
            InlineQueryResultArticle(
                id="full_catalog",
                title="🎨 Отправить каталог товаров",
                description="Коллажи и фотопродукция",
                thumbnail_url="https://cdn-icons-png.flaticon.com/512/3659/3659899.png",
                input_message_content=InputTextMessageContent(
                    message_text=catalog_text,
                    parse_mode="HTML"
                ),
                reply_markup=kb
            )
        )
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Отдельные товары
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
                InlineQueryResultCachedPhoto(
                    id=f"product_{product.id}",
                    photo_file_id=product.photo_url,
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    return InlineQueryResultArticle(
        id="booking",
        title="📝 Записаться на съёмку",
        description="Открыть форму записи",
        thumbnail_url="https://cdn-icons-png.flaticon.com/512/3652/3652267.png",
        input_message_content=InputTextMessageContent(
            message_text="""📸 <b>Фотограф Марина Заугольникова</b>

Хотите записаться на фотосессию? 
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
            thumbnail_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
            input_message_content=InputTextMessageContent(
                message_text="Введите <b>@бот прайс</b> для просмотра услуг",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_products",
            title="🎨 Товары",
            description="Коллажи и фотопродукция",
            thumbnail_url="https://cdn-icons-png.flaticon.com/512/3659/3659899.png",
            input_message_content=InputTextMessageContent(
                message_text="Введите <b>@бот товары</b> для просмотра каталога",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_booking",
            title="📝 Записаться",
            description="Оставить заявку на съёмку",
            thumbnail_url="https://cdn-icons-png.flaticon.com/512/3652/3652267.png",
            input_message_content=InputTextMessageContent(
                message_text=f"Для записи перейдите: https://t.me/{config.MAIN_BOT_USERNAME}?start=booking",
                parse_mode="HTML"
            )
        )
    ]
