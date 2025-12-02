import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from sqlalchemy import select

from config import config
from database import init_db, Service, Product, async_session
from keyboards.keyboards import (
    main_menu_kb, 
    services_navigation_kb, 
    products_navigation_kb, 
    products_filter_kb
)
from handlers import inline, booking, admin
from handlers.booking import handle_booking_deeplink

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота с прокси
session = AiohttpSession(proxy="http://127.0.0.1:12334")
bot = Bot(token=config.MAIN_BOT_TOKEN, session=session)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры
dp.include_router(inline.router)
dp.include_router(booking.router)
dp.include_router(admin.router)

# Временное хранилище для навигации
user_navigation = {}

# ============ ОСНОВНЫЕ КОМАНДЫ ============

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка /start и deeplinks"""
    await state.clear()
    
    # Проверяем deeplink параметры
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1:
        param = args[1]
        
        # Запись на съёмку
        if param == "booking" or param.startswith("book_"):
            await handle_booking_deeplink(message, state, param)
            return
        
        # Просмотр услуг
        elif param == "services":
            await show_services(message)
            return
        
        # Просмотр товаров
        elif param == "products":
            await show_products_filter(message)
            return
        
        # Заказ товара
        elif param.startswith("order_"):
            product_id = int(param.replace("order_", ""))
            await handle_product_order(message, product_id)
            return
    
    # Обычный старт
    is_admin = message.from_user.id in config.ADMIN_IDS
    
    welcome_text = """👋 <b>Добро пожаловать!</b>

📸 Я бот фотографа <b>Марины Заугольниковой</b>

Здесь вы можете:
• Посмотреть услуги и цены
• Выбрать товары (коллажи)
• Записаться на фотосессию

💡 <b>Подсказка:</b> Вы можете использовать меня в любом чате!
Просто введите <code>@{bot_username} прайс</code> или <code>@{bot_username} товары</code>

Выберите действие:"""
    
    await message.answer(
        welcome_text.format(bot_username=config.MAIN_BOT_USERNAME),
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin)
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    help_text = f"""📖 <b>Помощь</b>

<b>Основные команды:</b>
/start - Главное меню
/services - Услуги и цены
/products - Товары
/booking - Записаться на съёмку
/contacts - Контакты

<b>Inline режим:</b>
Введите в любом чате:
• <code>@{config.MAIN_BOT_USERNAME} прайс</code> - показать услуги
• <code>@{config.MAIN_BOT_USERNAME} товары</code> - показать товары
• <code>@{config.MAIN_BOT_USERNAME} запись</code> - ссылка на запись

<b>AI Ассистент:</b>
Если фотограф не отвечает, используйте:
<code>@{config.AI_BOT_USERNAME} ваш вопрос</code>"""
    
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("services"))
async def cmd_services(message: Message):
    """Команда просмотра услуг"""
    await show_services(message)

@dp.message(Command("products"))
async def cmd_products(message: Message):
    """Команда просмотра товаров"""
    await show_products_filter(message)

@dp.message(Command("booking"))
async def cmd_booking(message: Message, state: FSMContext):
    """Команда записи"""
    await handle_booking_deeplink(message, state)

@dp.message(Command("contacts"))
async def cmd_contacts(message: Message):
    """Контакты"""
    contacts_text = """📞 <b>Контакты</b>

👩‍🎨 <b>Фотограф:</b> Марина Заугольникова

📱 <b>Telegram:</b> @marina_photo
📷 <b>Instagram:</b> @marina_photo
📧 <b>Email:</b> marina@photo.ru

🕐 <b>Время работы:</b> 
Пн-Пт: 10:00 - 20:00
Сб-Вс: по договорённости"""
    
    await message.answer(
        contacts_text,
        parse_mode="HTML",
        reply_markup=main_menu_kb(message.from_user.id in config.ADMIN_IDS)
    )

# ============ CALLBACK ОБРАБОТЧИКИ ============

@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    is_admin = callback.from_user.id in config.ADMIN_IDS
    
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin)
    )
    await callback.answer()

@dp.callback_query(F.data == "services")
async def callback_services(callback: CallbackQuery):
    """Показать услуги"""
    await show_services(callback.message, edit=True)
    await callback.answer()

@dp.callback_query(F.data.startswith("service_nav:"))
async def callback_service_nav(callback: CallbackQuery):
    """Навигация по услугам"""
    index = int(callback.data.split(":")[1])
    await show_service_by_index(callback.message, callback.from_user.id, index, edit=True)
    await callback.answer()

@dp.callback_query(F.data == "products")
async def callback_products(callback: CallbackQuery):
    """Показать фильтр товаров"""
    await show_products_filter(callback.message, edit=True)
    await callback.answer()

@dp.callback_query(F.data.startswith("products_filter:"))
async def callback_products_filter(callback: CallbackQuery):
    """Фильтр товаров"""
    filter_type = callback.data.split(":")[1]
    await show_products(callback.message, callback.from_user.id, filter_type, edit=True)
    await callback.answer()

@dp.callback_query(F.data.startswith("product_nav:"))
async def callback_product_nav(callback: CallbackQuery):
    """Навигация по товарам"""
    parts = callback.data.split(":")
    index = int(parts[1])
    filter_type = parts[2] if len(parts) > 2 else "all"
    await show_product_by_index(callback.message, callback.from_user.id, index, filter_type, edit=True)
    await callback.answer()

@dp.callback_query(F.data.startswith("order_product:"))
async def callback_order_product(callback: CallbackQuery):
    """Заказ товара"""
    product_id = int(callback.data.split(":")[1])
    await handle_product_order_callback(callback, product_id)
    await callback.answer()

@dp.callback_query(F.data == "contacts")
async def callback_contacts(callback: CallbackQuery):
    """Контакты"""
    await cmd_contacts(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "faq")
async def callback_faq(callback: CallbackQuery):
    """FAQ"""
    faq_text = """❓ <b>Часто задаваемые вопросы</b>

<b>Q: Как записаться на съёмку?</b>
A: Нажмите "Записаться на съёмку" в главном меню и заполните форму.

<b>Q: Можно ли отменить запись?</b>
A: Да, свяжитесь с фотографом минимум за 24 часа.

<b>Q: Когда будут готовы фото?</b>
A: Обычно 7-14 дней в зависимости от объёма.

<b>Q: Как получить цифровые коллажи?</b>
A: После оплаты вы получите ссылку для скачивания.

<b>Q: Можно ли взять несколько образов?</b>
A: Да, количество образов обсуждается индивидуально."""
    
    await callback.message.edit_text(
        faq_text,
        parse_mode="HTML",
        reply_markup=main_menu_kb(callback.from_user.id in config.ADMIN_IDS)
    )
    await callback.answer()

# ============ ФУНКЦИИ ОТОБРАЖЕНИЯ ============

async def show_services(message: Message, edit: bool = False):
    """Показать первую услугу"""
    async with async_session() as session:
        query = select(Service).where(Service.is_active == True).order_by(Service.order)
        result = await session.execute(query)
        services = result.scalars().all()
    
    if not services:
        text = "😔 Пока нет доступных услуг."
        if edit:
            await message.edit_text(text, reply_markup=main_menu_kb())
        else:
            await message.answer(text, reply_markup=main_menu_kb())
        return
    
    # Сохраняем для навигации
    user_navigation[message.chat.id] = {
        "services": services,
        "type": "services"
    }
    
    await show_service_by_index(message, message.chat.id, 0, edit)

async def show_service_by_index(message: Message, user_id: int, index: int, edit: bool = False):
    """Показать услугу по индексу"""
    data = user_navigation.get(user_id, {})
    services = data.get("services", [])
    
    if not services:
        async with async_session() as session:
            query = select(Service).where(Service.is_active == True).order_by(Service.order)
            result = await session.execute(query)
            services = result.scalars().all()
        
        user_navigation[user_id] = {"services": services, "type": "services"}
    
    if not services or index >= len(services):
        return
    
    service = services[index]
    
    text = f"""📸 <b>{service.name}</b>

{service.description or 'Описание скоро появится...'}

💰 <b>Стоимость:</b> {service.price:,.0f} руб.
⏱ <b>Длительность:</b> {service.duration or 'По договорённости'}"""
    
    kb = services_navigation_kb(index, len(services), service.id)
    
    if service.photo_url:
        try:
            if edit:
                await message.delete()
            await message.answer_photo(
                photo=service.photo_url,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
            return
        except:
            pass
    
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)

async def show_products_filter(message: Message, edit: bool = False):
    """Показать фильтр товаров"""
    text = """🎨 <b>Товары</b>

Выберите категорию:

📱 <b>Цифровые коллажи</b> - получите файл для печати
📄 <b>Бумажные коллажи</b> - готовый напечатанный коллаж"""
    
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=products_filter_kb())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=products_filter_kb())

async def show_products(message: Message, user_id: int, filter_type: str = "all", edit: bool = False):
    """Показать товары"""
    async with async_session() as session:
        if filter_type == "all":
            query = select(Product).where(Product.is_active == True).order_by(Product.order)
        else:
            query = select(Product).where(
                Product.is_active == True,
                Product.product_type == filter_type
            ).order_by(Product.order)
        
        result = await session.execute(query)
        products = result.scalars().all()
    
    if not products:
        text = "😔 В этой категории пока нет товаров."
        if edit:
            await message.edit_text(text, reply_markup=products_filter_kb())
        else:
            await message.answer(text, reply_markup=products_filter_kb())
        return
    
    user_navigation[user_id] = {
        "products": products,
        "filter": filter_type,
        "type": "products"
    }
    
    await show_product_by_index(message, user_id, 0, filter_type, edit)

async def show_product_by_index(message: Message, user_id: int, index: int, filter_type: str, edit: bool = False):
    """Показать товар по индексу"""
    data = user_navigation.get(user_id, {})
    products = data.get("products", [])
    
    if not products or index >= len(products):
        return
    
    product = products[index]
    type_emoji = "📱" if product.product_type == "digital" else "📄"
    type_text = "Цифровой" if product.product_type == "digital" else "Бумажный"
    
    text = f"""{type_emoji} <b>{product.name}</b>

{product.description or 'Описание скоро появится...'}

💰 <b>Стоимость:</b> {product.price:,.0f} руб.
📦 <b>Тип:</b> {type_text}"""
    
    kb = products_navigation_kb(index, len(products), product.id, filter_type)
    
    if product.photo_url:
        try:
            if edit:
                await message.delete()
            await message.answer_photo(
                photo=product.photo_url,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
            return
        except:
            pass
    
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)

async def handle_product_order(message: Message, product_id: int):
    """Обработка заказа товара через deeplink"""
    async with async_session() as session:
        product = await session.get(Product, product_id)
    
    if not product:
        await message.answer("Товар не найден 😔", reply_markup=main_menu_kb())
        return
    
    type_emoji = "📱" if product.product_type == "digital" else "📄"
    
    text = f"""✅ Вы хотите заказать:

{type_emoji} <b>{product.name}</b>
💰 <b>Цена:</b> {product.price:,.0f} руб.

Для оформления заказа свяжитесь с фотографом:
📱 @marina_photo

Или напишите прямо сюда, и мы свяжемся с вами!"""
    
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())

async def handle_product_order_callback(callback: CallbackQuery, product_id: int):
    """Обработка заказа товара через callback"""
    async with async_session() as session:
        product = await session.get(Product, product_id)
    
    if not product:
        await callback.message.edit_text("Товар не найден 😔", reply_markup=main_menu_kb())
        return
    
    # Уведомляем админа
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🛒 <b>Интерес к товару!</b>\n\n"
                f"Товар: {product.name}\n"
                f"Цена: {product.price:,.0f} руб.\n\n"
                f"Пользователь: @{callback.from_user.username or 'нет'}\n"
                f"ID: {callback.from_user.id}",
                parse_mode="HTML"
            )
        except:
            pass
    
    await callback.message.edit_text(
        f"✅ Заявка на товар '<b>{product.name}</b>' отправлена!\n\n"
        "Марина свяжется с вами в ближайшее время.",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )

# ============ ЗАПУСК ============

async def main():
    """Главная функция запуска"""
    # Инициализируем БД
    await init_db()
    
    logging.info("Бот запускается...")
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
