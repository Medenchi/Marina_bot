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
from utils.image_generator import price_generator
import hashlib

router = Router()

# Кэш для file_id картинок
image_file_ids = {}

async def get_or_create_price_image(bot, services: list) -> str:
    """Получить file_id картинки прайса (из кэша или создать новую)"""
    
    # Создаём хэш от услуг для кэширования
    services_data = [(s.name, s.price, s.duration) for s in services]
    cache_key = hashlib.md5(str(services_data).encode()).hexdigest()
    
    # Если есть в кэше - возвращаем
    if cache_key in image_file_ids:
        return image_file_ids[cache_key]
    
    # Генерируем картинку
    services_for_image = [
        {
            'name': s.name,
            'price': s.price,
            'duration': s.duration or ''
        }
        for s in services
    ]
    
    image_buffer = price_generator.generate_price_image(
        services=services_for_image,
        title="ПРАЙС НА УСЛУГИ",
        photographer_name="Марина Заугольникова",
        contact=f"@{config.MAIN_BOT_USERNAME}"
    )
    
    # Отправляем картинку админу чтобы получить file_id
    photo = BufferedInputFile(
        file=image_buffer.getvalue(),
        filename="price.png"
    )
    
    # Отправляем себе (первому админу) и сразу удаляем
    try:
        admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
        if admin_id:
            msg = await bot.send_photo(
                chat_id=admin_id,
                photo=photo,
                caption="🔄 Генерация прайса... (это сообщение удалится)"
            )
            file_id = msg.photo[-1].file_id
            await msg.delete()
            
            # Сохраняем в кэш
            image_file_ids[cache_key] = file_id
            return file_id
    except Exception as e:
        print(f"Error creating price image: {e}")
    
    return None

async def get_or_create_catalog_image(bot, products: list) -> str:
    """Получить file_id картинки каталога"""
    
    products_data = [(p.name, p.price, p.product_type) for p in products]
    cache_key = "catalog_" + hashlib.md5(str(products_data).encode()).hexdigest()
    
    if cache_key in image_file_ids:
        return image_file_ids[cache_key]
    
    products_for_image = [
        {
            'name': p.name,
            'price': p.price,
            'type': p.product_type
        }
        for p in products
    ]
    
    image_buffer = price_generator.generate_product_image(
        products=products_for_image,
        title="КАТАЛОГ ТОВАРОВ",
        photographer_name="Марина Заугольникова"
    )
    
    photo = BufferedInputFile(
        file=image_buffer.getvalue(),
        filename="catalog.png"
    )
    
    try:
        admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
        if admin_id:
            msg = await bot.send_photo(
                chat_id=admin_id,
                photo=photo,
                caption="🔄 Генерация каталога... (это сообщение удалится)"
            )
            file_id = msg.photo[-1].file_id
            await msg.delete()
            
            image_file_ids[cache_key] = file_id
            return file_id
    except Exception as e:
        print(f"Error creating catalog image: {e}")
    
    return None

@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    """Обработка inline запросов"""
    query = inline_query.query.lower().strip()
    results = []
    bot = inline_query.bot
    
    async with async_session() as session:
        if not query or query in ["прайс", "price", "услуги", "цены"]:
            results.extend(await get_services_inline_results(session, bot))
        
        elif query in ["товары", "товар", "коллаж", "коллажи", "products"]:
            results.extend(await get_products_inline_results(session, bot))
        
        elif query in ["запись", "записаться", "book", "booking"]:
            results.append(get_booking_inline_result())
        
        else:
            results.extend(await search_inline_results(session, query))
    
    if not results:
        results = get_default_menu_results()
    
    await inline_query.answer(
        results=results[:50],
        cache_time=60,
        is_personal=False
    )

async def get_services_inline_results(session, bot) -> list:
    """Получить услуги для inline с картинкой"""
    results = []
    
    query = select(Service).where(Service.is_active == True).order_by(Service.order)
    result = await session.execute(query)
    services = result.scalars().all()
    
    if not services:
        return results
    
    # Кнопки под картинкой
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
    
    # Пробуем получить картинку
    try:
        file_id = await get_or_create_price_image(bot, services)
        
        if file_id:
            # Есть картинка - добавляем как фото
            caption = "📸 <b>ПРАЙС НА УСЛУГИ</b>\n\n"
            caption += "👩‍🎨 Фотограф: <b>Марина Заугольникова</b>"
            
            results.append(
                InlineQueryResultCachedPhoto(
                    id="price_image",
                    photo_file_id=file_id,
                    title="📋 Прайс с картинкой",
                    description="Красивый прайс со всеми услугами",
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            )
    except Exception as e:
        print(f"Price image error: {e}")
    
    # Текстовый прайс как запасной вариант
    price_text = "📸 <b>ПРАЙС НА УСЛУГИ</b>\n"
    price_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for s in services:
        price_text += f"✨ <b>{s.name}</b>\n"
        price_text += f"    💰 {s.price:,.0f} ₽"
        if s.duration:
            price_text += f"  •  ⏱ {s.duration}"
        price_text += "\n\n"
    
    price_text += "━━━━━━━━━━━━━━━━━━━━\n"
    price_text += "👩‍🎨 <b>Марина Заугольникова</b>"
    
    results.append(
        InlineQueryResultArticle(
            id="price_text",
            title="📋 Прайс (текст)",
            description="Текстовый вариант прайса",
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

async def get_products_inline_results(session, bot) -> list:
    """Получить товары для inline с картинкой"""
    results = []
    
    query = select(Product).where(Product.is_active == True).order_by(Product.order)
    result = await session.execute(query)
    products = result.scalars().all()
    
    if not products:
        return results
    
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
    
    # Пробуем получить картинку каталога
    try:
        file_id = await get_or_create_catalog_image(bot, products)
        
        if file_id:
            caption = "🎨 <b>КАТАЛОГ ТОВАРОВ</b>\n\n"
            caption += "👩‍🎨 <b>Марина Заугольникова</b>"
            
            results.append(
                InlineQueryResultCachedPhoto(
                    id="catalog_image",
                    photo_file_id=file_id,
                    title="🎨 Каталог с картинкой",
                    description="Все товары",
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            )
    except Exception as e:
        print(f"Catalog image error: {e}")
    
    # Текстовый каталог
    catalog_text = "🎨 <b>КАТАЛОГ ТОВАРОВ</b>\n"
    catalog_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for p in products:
        type_emoji = "📱" if p.product_type == "digital" else "📄"
        catalog_text += f"{type_emoji} <b>{p.name}</b>\n"
        catalog_text += f"    💰 {p.price:,.0f} ₽\n\n"
    
    catalog_text += "━━━━━━━━━━━━━━━━━━━━\n"
    catalog_text += "👩‍🎨 <b>Марина Заугольникова</b>"
    
    results.append(
        InlineQueryResultArticle(
            id="catalog_text",
            title="🎨 Каталог (текст)",
            description="Текстовый вариант каталога",
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
    """Поиск"""
    results = []
    
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
    """Запись"""
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
            description="Услуги и цены",
            thumbnail_url="https://i.imgur.com/8QZQY9L.png",
            input_message_content=InputTextMessageContent(
                message_text="Введите <b>@бот прайс</b>",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_products",
            title="🎨 Товары",
            description="Коллажи",
            thumbnail_url="https://i.imgur.com/YqQYz0L.png",
            input_message_content=InputTextMessageContent(
                message_text="Введите <b>@бот товары</b>",
                parse_mode="HTML"
            )
        ),
        InlineQueryResultArticle(
            id="menu_booking",
            title="📝 Записаться",
            description="На съёмку",
            thumbnail_url="https://i.imgur.com/kJ5aZVL.png",
            input_message_content=InputTextMessageContent(
                message_text=f"https://t.me/{config.MAIN_BOT_USERNAME}?start=booking",
                parse_mode="HTML"
            )
        )
    ]
