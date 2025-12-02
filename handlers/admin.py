from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import Service, Product, Booking, async_session
from keyboards.keyboards import (
    admin_panel_kb,
    admin_services_kb,
    admin_service_edit_kb,
    admin_products_kb,
    admin_bookings_kb,
    admin_booking_view_kb,
    main_menu_kb
)
from config import config

router = Router()

# Фильтр админа
def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

class AdminStates(StatesGroup):
    # Услуги
    adding_service_name = State()
    adding_service_desc = State()
    adding_service_price = State()
    adding_service_duration = State()
    adding_service_photo = State()
    
    editing_service_name = State()
    editing_service_desc = State()
    editing_service_price = State()
    editing_service_duration = State()
    editing_service_photo = State()
    
    # Товары
    adding_product_name = State()
    adding_product_desc = State()
    adding_product_price = State()
    adding_product_type = State()
    adding_product_photo = State()
    
    # Сообщение клиенту
    messaging_client = State()
    
    # Deeplink генератор
    creating_deeplink_text = State()
    creating_deeplink_button = State()

# Временное хранилище
admin_temp_data = {}

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    """Показать админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите раздел для управления:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()

# ============ DEEPLINK ГЕНЕРАТОР ============

@router.callback_query(F.data == "admin_deeplinks")
async def admin_deeplinks(callback: CallbackQuery):
    """Меню deeplink ссылок"""
    if not is_admin(callback.from_user.id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = f"""🔗 <b>Генератор ссылок</b>

<b>Готовые ссылки:</b>

📝 <b>Запись на съёмку:</b>
<code>https://t.me/{config.MAIN_BOT_USERNAME}?start=booking</code>

📸 <b>Посмотреть услуги:</b>
<code>https://t.me/{config.MAIN_BOT_USERNAME}?start=services</code>

🎨 <b>Посмотреть товары:</b>
<code>https://t.me/{config.MAIN_BOT_USERNAME}?start=products</code>

💡 Нажмите на ссылку чтобы скопировать!"""
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Создать свою ссылку", callback_data="admin_create_deeplink")],
        [InlineKeyboardButton(text="📋 Ссылки на услуги", callback_data="admin_deeplinks_services")],
        [InlineKeyboardButton(text="🎨 Ссылки на товары", callback_data="admin_deeplinks_products")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_deeplinks_services")
async def admin_deeplinks_services(callback: CallbackQuery):
    """Ссылки на услуги"""
    if not is_admin(callback.from_user.id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    async with async_session() as session:
        query = select(Service).where(Service.is_active == True).order_by(Service.order)
        result = await session.execute(query)
        services = result.scalars().all()
    
    text = "📸 <b>Ссылки на услуги:</b>\n\n"
    
    for service in services:
        link = f"https://t.me/{config.MAIN_BOT_USERNAME}?start=book_{service.id}"
        text += f"<b>{service.name}:</b>\n<code>{link}</code>\n\n"
    
    if not services:
        text += "Нет активных услуг"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_deeplinks")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_deeplinks_products")
async def admin_deeplinks_products(callback: CallbackQuery):
    """Ссылки на товары"""
    if not is_admin(callback.from_user.id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    async with async_session() as session:
        query = select(Product).where(Product.is_active == True).order_by(Product.order)
        result = await session.execute(query)
        products = result.scalars().all()
    
    text = "🎨 <b>Ссылки на товары:</b>\n\n"
    
    for product in products:
        link = f"https://t.me/{config.MAIN_BOT_USERNAME}?start=order_{product.id}"
        text += f"<b>{product.name}:</b>\n<code>{link}</code>\n\n"
    
    if not products:
        text += "Нет активных товаров"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_deeplinks")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_create_deeplink")
async def admin_create_deeplink(callback: CallbackQuery, state: FSMContext):
    """Создание кастомной ссылки"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "✨ <b>Создание ссылки</b>\n\n"
        "Введите <b>текст сообщения</b>, которое будет отправлено при переходе по ссылке:\n\n"
        "Можно использовать HTML форматирование:\n"
        "<code>&lt;b&gt;жирный&lt;/b&gt;</code>\n"
        "<code>&lt;i&gt;курсив&lt;/i&gt;</code>\n"
        "<code>&lt;u&gt;подчёркнутый&lt;/u&gt;</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.creating_deeplink_text)
    await callback.answer()

@router.message(AdminStates.creating_deeplink_text)
async def process_deeplink_text(message: Message, state: FSMContext):
    """Обработка текста для deeplink"""
    if not is_admin(message.from_user.id):
        return
    
    admin_temp_data[message.from_user.id] = {
        "deeplink_text": message.text
    }
    
    await message.answer(
        "Теперь введите <b>текст кнопки</b> (или напишите 'нет' если кнопка не нужна):\n\n"
        "Например: 📝 Записаться на съёмку",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.creating_deeplink_button)

@router.message(AdminStates.creating_deeplink_button)
async def process_deeplink_button(message: Message, state: FSMContext):
    """Обработка кнопки для deeplink"""
    if not is_admin(message.from_user.id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    import hashlib
    import time
    
    data = admin_temp_data.get(message.from_user.id, {})
    deeplink_text = data.get("deeplink_text", "")
    
    # Создаём уникальный ID для ссылки
    unique_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
    
    button_text = message.text.strip()
    has_button = button_text.lower() not in ["нет", "no", "-", "без кнопки"]
    
    # Сохраняем в базу или файл (простой вариант - в память)
    # В реальном проекте лучше сохранять в БД
    
    link = f"https://t.me/{config.MAIN_BOT_USERNAME}?start=custom_{unique_id}"
    
    result_text = f"""✅ <b>Ссылка создана!</b>

🔗 <b>Ваша ссылка:</b>
<code>{link}</code>

📝 <b>Текст сообщения:</b>
{deeplink_text}
"""
    
    if has_button:
        result_text += f"\n🔘 <b>Кнопка:</b> {button_text}"
    
    result_text += "\n\n⚠️ <i>Примечание: для полноценной работы кастомных ссылок нужно сохранять их в базу данных. Пока доступны только стандартные ссылки выше.</i>"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Все ссылки", callback_data="admin_deeplinks")],
        [InlineKeyboardButton(text="⬅️ Админ-панель", callback_data="admin_panel")]
    ])
    
    await message.answer(result_text, parse_mode="HTML", reply_markup=kb)
    
    admin_temp_data.pop(message.from_user.id, None)
    await state.clear()

# ============ УПРАВЛЕНИЕ УСЛУГАМИ ============

@router.callback_query(F.data == "admin_services")
async def admin_services(callback: CallbackQuery):
    """Список услуг"""
    if not is_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        query = select(Service).order_by(Service.order)
        result = await session.execute(query)
        services = result.scalars().all()
    
    await callback.message.edit_text(
        "📸 <b>Управление услугами</b>\n\n"
        "Нажмите на услугу для редактирования:",
        parse_mode="HTML",
        reply_markup=admin_services_kb(services)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_service_add")
async def admin_add_service_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления услуги"""
    if not is_admin(callback.from_user.id):
        return
    
    admin_temp_data[callback.from_user.id] = {}
    
    await callback.message.edit_text(
        "➕ <b>Добавление новой услуги</b>\n\n"
        "Введите <b>название</b> услуги:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_service_name)
    await callback.answer()

@router.message(AdminStates.adding_service_name)
async def admin_add_service_name(message: Message, state: FSMContext):
    """Название услуги"""
    if not is_admin(message.from_user.id):
        return
    
    admin_temp_data[message.from_user.id]["name"] = message.text.strip()
    
    await message.answer(
        "Введите <b>описание</b> услуги:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_service_desc)

@router.message(AdminStates.adding_service_desc)
async def admin_add_service_desc(message: Message, state: FSMContext):
    """Описание услуги"""
    admin_temp_data[message.from_user.id]["description"] = message.text.strip()
    
    await message.answer(
        "Введите <b>цену</b> в рублях (только число):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_service_price)

@router.message(AdminStates.adding_service_price)
async def admin_add_service_price(message: Message, state: FSMContext):
    """Цена услуги"""
    try:
        price = float(message.text.strip().replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    
    admin_temp_data[message.from_user.id]["price"] = price
    
    await message.answer(
        "Введите <b>длительность</b> (например: '1-2 часа'):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_service_duration)

@router.message(AdminStates.adding_service_duration)
async def admin_add_service_duration(message: Message, state: FSMContext):
    """Длительность услуги"""
    admin_temp_data[message.from_user.id]["duration"] = message.text.strip()
    
    await message.answer(
        "Отправьте <b>фото</b> для услуги или напишите 'пропустить':",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_service_photo)

@router.message(AdminStates.adding_service_photo, F.photo)
async def admin_add_service_photo(message: Message, state: FSMContext):
    """Фото услуги"""
    photo_id = message.photo[-1].file_id
    admin_temp_data[message.from_user.id]["photo_url"] = photo_id
    await save_new_service(message, state)

@router.message(AdminStates.adding_service_photo)
async def admin_add_service_skip_photo(message: Message, state: FSMContext):
    """Пропуск фото"""
    if message.text.lower() in ["пропустить", "skip", "-"]:
        admin_temp_data[message.from_user.id]["photo_url"] = None
        await save_new_service(message, state)
    else:
        await message.answer("Отправьте фото или напишите 'пропустить'")

async def save_new_service(message: Message, state: FSMContext):
    """Сохранение новой услуги"""
    data = admin_temp_data.get(message.from_user.id, {})
    
    async with async_session() as session:
        # Получаем максимальный order
        max_order = await session.execute(select(func.max(Service.order)))
        new_order = (max_order.scalar() or 0) + 1
        
        service = Service(
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            duration=data.get("duration"),
            photo_url=data.get("photo_url"),
            order=new_order,
            is_active=True
        )
        session.add(service)
        await session.commit()
    
    admin_temp_data.pop(message.from_user.id, None)
    await state.clear()
    
    await message.answer(
        f"✅ Услуга '<b>{data.get('name')}</b>' добавлена!",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )

@router.callback_query(F.data.startswith("admin_service_edit:"))
async def admin_edit_service(callback: CallbackQuery):
    """Редактирование услуги"""
    if not is_admin(callback.from_user.id):
        return
    
    service_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        service = await session.get(Service, service_id)
    
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    
    text = f"""✏️ <b>Редактирование услуги</b>

📸 <b>Название:</b> {service.name}
📝 <b>Описание:</b> {service.description or 'Нет'}
💰 <b>Цена:</b> {service.price:,.0f} руб.
⏱ <b>Длительность:</b> {service.duration or 'Не указана'}
📊 <b>Статус:</b> {'Активна ✅' if service.is_active else 'Неактивна ❌'}"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_service_edit_kb(service_id, service.is_active)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_se_toggle:"))
async def admin_toggle_service(callback: CallbackQuery):
    """Переключение активности услуги"""
    if not is_admin(callback.from_user.id):
        return
    
    service_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        service = await session.get(Service, service_id)
        if service:
            service.is_active = not service.is_active
            await session.commit()
            status = "активирована ✅" if service.is_active else "деактивирована ❌"
            await callback.answer(f"Услуга {status}")
    
    # Обновляем сообщение
    await admin_edit_service(callback)

@router.callback_query(F.data.startswith("admin_se_delete:"))
async def admin_delete_service(callback: CallbackQuery):
    """Удаление услуги"""
    if not is_admin(callback.from_user.id):
        return
    
    service_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        service = await session.get(Service, service_id)
        if service:
            await session.delete(service)
            await session.commit()
    
    await callback.answer("Услуга удалена! 🗑")
    
    # Возвращаемся к списку
    async with async_session() as session:
        query = select(Service).order_by(Service.order)
        result = await session.execute(query)
        services = result.scalars().all()
    
    await callback.message.edit_text(
        "📸 <b>Управление услугами</b>",
        parse_mode="HTML",
        reply_markup=admin_services_kb(services)
    )

# ============ УПРАВЛЕНИЕ ТОВАРАМИ ============

@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    """Список товаров"""
    if not is_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        query = select(Product).order_by(Product.order)
        result = await session.execute(query)
        products = result.scalars().all()
    
    await callback.message.edit_text(
        "🎨 <b>Управление товарами</b>\n\n"
        "Нажмите на товар для редактирования:",
        parse_mode="HTML",
        reply_markup=admin_products_kb(products)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_product_add")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        return
    
    admin_temp_data[callback.from_user.id] = {}
    
    await callback.message.edit_text(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Введите <b>название</b> товара:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_product_name)
    await callback.answer()

@router.message(AdminStates.adding_product_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    admin_temp_data[message.from_user.id]["name"] = message.text.strip()
    
    await message.answer(
        "Выберите <b>тип</b> товара:\n\n"
        "/digital - Цифровой коллаж\n"
        "/paper - Бумажный коллаж",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_product_type)

@router.message(AdminStates.adding_product_type)
async def admin_add_product_type(message: Message, state: FSMContext):
    text = message.text.lower().strip()
    
    if "digital" in text or "цифр" in text:
        product_type = "digital"
    elif "paper" in text or "бумаж" in text:
        product_type = "paper"
    else:
        await message.answer("Выберите: /digital или /paper")
        return
    
    admin_temp_data[message.from_user.id]["product_type"] = product_type
    
    await message.answer("Введите <b>описание</b> товара:", parse_mode="HTML")
    await state.set_state(AdminStates.adding_product_desc)

@router.message(AdminStates.adding_product_desc)
async def admin_add_product_desc(message: Message, state: FSMContext):
    admin_temp_data[message.from_user.id]["description"] = message.text.strip()
    
    await message.answer("Введите <b>цену</b> в рублях:", parse_mode="HTML")
    await state.set_state(AdminStates.adding_product_price)

@router.message(AdminStates.adding_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    
    admin_temp_data[message.from_user.id]["price"] = price
    
    await message.answer("Отправьте <b>фото</b> товара или 'пропустить':", parse_mode="HTML")
    await state.set_state(AdminStates.adding_product_photo)

@router.message(AdminStates.adding_product_photo, F.photo)
async def admin_add_product_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    admin_temp_data[message.from_user.id]["photo_url"] = photo_id
    await save_new_product(message, state)

@router.message(AdminStates.adding_product_photo)
async def admin_add_product_skip_photo(message: Message, state: FSMContext):
    if message.text.lower() in ["пропустить", "skip", "-"]:
        admin_temp_data[message.from_user.id]["photo_url"] = None
        await save_new_product(message, state)

async def save_new_product(message: Message, state: FSMContext):
    data = admin_temp_data.get(message.from_user.id, {})
    
    async with async_session() as session:
        max_order = await session.execute(select(func.max(Product.order)))
        new_order = (max_order.scalar() or 0) + 1
        
        product = Product(
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            product_type=data.get("product_type"),
            photo_url=data.get("photo_url"),
            order=new_order,
            is_active=True
        )
        session.add(product)
        await session.commit()
    
    admin_temp_data.pop(message.from_user.id, None)
    await state.clear()
    
    await message.answer(
        f"✅ Товар '<b>{data.get('name')}</b>' добавлен!",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )

# ============ УПРАВЛЕНИЕ ЗАЯВКАМИ ============

@router.callback_query(F.data == "admin_bookings")
async def admin_bookings(callback: CallbackQuery):
    """Список заявок"""
    if not is_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        query = select(Booking).order_by(Booking.created_at.desc()).limit(10)
        result = await session.execute(query)
        bookings = result.scalars().all()
    
    if not bookings:
        await callback.message.edit_text(
            "📋 <b>Заявки</b>\n\nПока нет заявок.",
            parse_mode="HTML",
            reply_markup=admin_panel_kb()
        )
        return
    
    await callback.message.edit_text(
        "📋 <b>Заявки на съёмку</b>\n\n"
        "🆕 - новая, ✅ - подтверждена, ✨ - завершена, ❌ - отменена",
        parse_mode="HTML",
        reply_markup=admin_bookings_kb(bookings)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_booking_view:"))
async def admin_view_booking(callback: CallbackQuery):
    """Просмотр заявки"""
    if not is_admin(callback.from_user.id):
        return
    
    booking_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if booking and booking.service_id:
            service = await session.get(Service, booking.service_id)
            service_name = service.name if service else "Не указана"
        else:
            service_name = "Не указана"
    
    if not booking:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    
    status_text = {
        "new": "🆕 Новая",
        "confirmed": "✅ Подтверждена",
        "completed": "✨ Завершена",
        "cancelled": "❌ Отменена"
    }
    
    text = f"""📋 <b>Заявка #{booking.id}</b>

📊 <b>Статус:</b> {status_text.get(booking.status, booking.status)}
📅 <b>Дата создания:</b> {booking.created_at.strftime('%d.%m.%Y %H:%M')}

👤 <b>Клиент:</b> {booking.first_name} {booking.last_name or ''}
📱 <b>Телефон:</b> {booking.phone}
👤 <b>Username:</b> @{booking.username or 'нет'}
🆔 <b>User ID:</b> <code>{booking.user_id}</code>

📸 <b>Услуга:</b> {service_name}
⏱ <b>Часов:</b> {booking.hours}
👥 <b>Человек:</b> {booking.people_count}
🏠 <b>Студия:</b> {booking.studio}

💭 <b>Пожелания:</b>
{booking.wishes or 'Нет'}"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_booking_view_kb(booking_id, booking.status)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_b_confirm:"))
async def admin_confirm_booking(callback: CallbackQuery):
    """Подтверждение заявки"""
    booking_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if booking:
            booking.status = "confirmed"
            await session.commit()
            
            # Уведомляем клиента
            from main_bot import bot
            try:
                await bot.send_message(
                    booking.user_id,
                    f"✅ <b>Ваша заявка #{booking_id} подтверждена!</b>\n\n"
                    "Марина скоро свяжется с вами для уточнения деталей.",
                    parse_mode="HTML"
                )
            except:
                pass
    
    await callback.answer("Заявка подтверждена!")
    await admin_view_booking(callback)

@router.callback_query(F.data.startswith("admin_b_complete:"))
async def admin_complete_booking(callback: CallbackQuery):
    """Завершение заявки"""
    booking_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if booking:
            booking.status = "completed"
            await session.commit()
    
    await callback.answer("Заявка завершена!")
    await admin_view_booking(callback)

@router.callback_query(F.data.startswith("admin_b_cancel:"))
async def admin_cancel_booking(callback: CallbackQuery):
    """Отмена заявки"""
    booking_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if booking:
            booking.status = "cancelled"
            await session.commit()
            
            # Уведомляем клиента
            from main_bot import bot
            try:
                await bot.send_message(
                    booking.user_id,
                    f"❌ <b>Ваша заявка #{booking_id} отменена.</b>\n\n"
                    "Если у вас есть вопросы, свяжитесь с фотографом.",
                    parse_mode="HTML"
                )
            except:
                pass
    
    await callback.answer("Заявка отменена")
    await admin_view_booking(callback)

# ============ НАПИСАТЬ КЛИЕНТУ ============

@router.callback_query(F.data.startswith("admin_b_message:"))
async def admin_message_client_start(callback: CallbackQuery, state: FSMContext):
    """Начало написания сообщения клиенту"""
    if not is_admin(callback.from_user.id):
        return
    
    booking_id = int(callback.data.split(":")[1])
    
    admin_temp_data[callback.from_user.id] = {"booking_id": booking_id}
    
    await callback.message.edit_text(
        "💬 <b>Написать клиенту</b>\n\n"
        "Введите сообщение, которое будет отправлено клиенту:\n\n"
        "<i>Можно использовать HTML форматирование</i>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.messaging_client)
    await callback.answer()

@router.message(AdminStates.messaging_client)
async def admin_send_message_to_client(message: Message, state: FSMContext):
    """Отправка сообщения клиенту"""
    if not is_admin(message.from_user.id):
        return
    
    from main_bot import bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    data = admin_temp_data.get(message.from_user.id, {})
    booking_id = data.get("booking_id")
    
    if not booking_id:
        await message.answer("❌ Ошибка: заявка не найдена")
        await state.clear()
        return
    
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
    
    if not booking:
        await message.answer("❌ Заявка не найдена")
        await state.clear()
        return
    
    try:
        await bot.send_message(
            booking.user_id,
            f"💬 <b>Сообщение от фотографа:</b>\n\n{message.text}",
            parse_mode="HTML"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К заявке", callback_data=f"admin_booking_view:{booking_id}")],
            [InlineKeyboardButton(text="⬅️ Все заявки", callback_data="admin_bookings")]
        ])
        
        await message.answer(
            f"✅ Сообщение отправлено клиенту {booking.first_name}!",
            reply_markup=kb
        )
    except Exception as e:
        await message.answer(
            f"❌ Не удалось отправить сообщение.\n"
            f"Возможно клиент заблокировал бота.\n\n"
            f"Ошибка: {e}"
        )
    
    admin_temp_data.pop(message.from_user.id, None)
    await state.clear()

# ============ СТАТИСТИКА ============

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика"""
    if not is_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        total_bookings = await session.execute(select(func.count(Booking.id)))
        total = total_bookings.scalar()
        
        new_count = await session.execute(
            select(func.count(Booking.id)).where(Booking.status == "new")
        )
        confirmed_count = await session.execute(
            select(func.count(Booking.id)).where(Booking.status == "confirmed")
        )
        completed_count = await session.execute(
            select(func.count(Booking.id)).where(Booking.status == "completed")
        )
        cancelled_count = await session.execute(
            select(func.count(Booking.id)).where(Booking.status == "cancelled")
        )
        
        services_count = await session.execute(
            select(func.count(Service.id)).where(Service.is_active == True)
        )
        products_count = await session.execute(
            select(func.count(Product.id)).where(Product.is_active == True)
        )
    
    text = f"""📊 <b>Статистика</b>

📋 <b>Заявки:</b>
• Всего: {total}
• 🆕 Новых: {new_count.scalar()}
• ✅ Подтверждённых: {confirmed_count.scalar()}
• ✨ Завершённых: {completed_count.scalar()}
• ❌ Отменённых: {cancelled_count.scalar()}

📸 <b>Активных услуг:</b> {services_count.scalar()}
🎨 <b>Активных товаров:</b> {products_count.scalar()}"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()
