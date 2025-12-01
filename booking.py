from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Booking, Service, async_session
from keyboards.keyboards import (
    booking_hours_kb, 
    booking_people_kb,
    booking_confirm_kb,
    share_phone_kb,
    main_menu_kb,
    services_navigation_kb
)
from config import config
from datetime import datetime

router = Router()

class BookingStates(StatesGroup):
    choosing_service = State()
    entering_name = State()
    entering_phone = State()
    choosing_hours = State()
    choosing_people = State()
    entering_studio = State()
    entering_datetime = State()
    entering_wishes = State()
    confirming = State()

# Временное хранение данных записи
booking_data = {}

@router.callback_query(F.data == "booking_start")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """Начало записи"""
    await state.clear()
    
    async with async_session() as session:
        query = select(Service).where(Service.is_active == True).order_by(Service.order)
        result = await session.execute(query)
        services = result.scalars().all()
    
    if not services:
        await callback.message.edit_text(
            "😔 К сожалению, сейчас нет доступных услуг.\n"
            "Свяжитесь с фотографом напрямую.",
            reply_markup=main_menu_kb()
        )
        return
    
    # Сохраняем данные
    booking_data[callback.from_user.id] = {
        "services": services,
        "current_index": 0
    }
    
    await show_service_for_booking(callback.message, callback.from_user.id, 0, edit=True)
    await state.set_state(BookingStates.choosing_service)
    await callback.answer()

@router.callback_query(F.data.startswith("book_service:"))
async def select_service_for_booking(callback: CallbackQuery, state: FSMContext):
    """Выбор услуги для записи"""
    service_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        service = await session.get(Service, service_id)
    
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    
    # Сохраняем выбранную услугу
    booking_data[callback.from_user.id] = {
        "service_id": service_id,
        "service_name": service.name,
        "service_price": service.price
    }
    
    await callback.message.edit_text(
        f"✅ Вы выбрали: <b>{service.name}</b>\n\n"
        f"Теперь введите ваши <b>Имя и Фамилию</b>:",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.entering_name)
    await callback.answer()

@router.message(BookingStates.entering_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name_parts = message.text.strip().split(maxsplit=1)
    
    booking_data[message.from_user.id]["first_name"] = name_parts[0]
    booking_data[message.from_user.id]["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
    
    await message.answer(
        "📱 Отправьте ваш <b>номер телефона</b>.\n\n"
        "Можете нажать кнопку ниже или ввести вручную:",
        parse_mode="HTML",
        reply_markup=share_phone_kb()
    )
    await state.set_state(BookingStates.entering_phone)

@router.message(BookingStates.entering_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обработка телефона через контакт"""
    booking_data[message.from_user.id]["phone"] = message.contact.phone_number
    await ask_hours(message, state)

@router.message(BookingStates.entering_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Обработка телефона текстом"""
    phone = message.text.strip()
    
    # Простая валидация
    if len(phone) < 10:
        await message.answer("❌ Введите корректный номер телефона:")
        return
    
    booking_data[message.from_user.id]["phone"] = phone
    await ask_hours(message, state)

async def ask_hours(message: Message, state: FSMContext):
    """Запрос количества часов"""
    await message.answer(
        "⏱ Выберите <b>количество часов</b> съёмки:",
        parse_mode="HTML",
        reply_markup=booking_hours_kb()
    )
    await state.set_state(BookingStates.choosing_hours)

@router.callback_query(BookingStates.choosing_hours, F.data.startswith("booking_hours:"))
async def process_hours(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора часов"""
    hours = callback.data.split(":")[1]
    booking_data[callback.from_user.id]["hours"] = hours
    
    await callback.message.edit_text(
        "👥 Сколько <b>человек</b> будет на съёмке?",
        parse_mode="HTML",
        reply_markup=booking_people_kb()
    )
    await state.set_state(BookingStates.choosing_people)
    await callback.answer()

@router.callback_query(BookingStates.choosing_people, F.data.startswith("booking_people:"))
async def process_people(callback: CallbackQuery, state: FSMContext):
    """Обработка количества людей"""
    people = callback.data.split(":")[1]
    booking_data[callback.from_user.id]["people_count"] = people
    
    await callback.message.edit_text(
        "🏠 Введите <b>название студии</b> или место съёмки:\n\n"
        "(Если не определились - напишите 'На выбор фотографа')",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.entering_studio)
    await callback.answer()

@router.message(BookingStates.entering_studio)
async def process_studio(message: Message, state: FSMContext):
    """Обработка студии"""
    booking_data[message.from_user.id]["studio"] = message.text.strip()
    
    await message.answer(
        "📅 Введите <b>желаемую дату и время</b> съёмки:\n\n"
        "Например: 25 декабря, 14:00\n"
        "Или: Любой выходной в январе",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.entering_datetime)

@router.message(BookingStates.entering_datetime)
async def process_datetime(message: Message, state: FSMContext):
    """Обработка даты"""
    booking_data[message.from_user.id]["datetime_text"] = message.text.strip()
    
    await message.answer(
        "💭 Есть ли у вас <b>пожелания</b> к съёмке?\n\n"
        "(Тематика, образы, особые моменты...)\n"
        "Если нет - напишите 'Нет'",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.entering_wishes)

@router.message(BookingStates.entering_wishes)
async def process_wishes(message: Message, state: FSMContext):
    """Обработка пожеланий и показ подтверждения"""
    data = booking_data[message.from_user.id]
    data["wishes"] = message.text.strip()
    
    # Формируем сводку
    summary = f"""📋 <b>Проверьте данные заявки:</b>

📸 <b>Услуга:</b> {data.get('service_name', 'Не выбрана')}
💰 <b>Стоимость:</b> {data.get('service_price', 0):,.0f} руб.

👤 <b>Имя:</b> {data.get('first_name', '')} {data.get('last_name', '')}
📱 <b>Телефон:</b> {data.get('phone', '')}

⏱ <b>Часов:</b> {data.get('hours', '')}
👥 <b>Человек:</b> {data.get('people_count', '')}
🏠 <b>Студия:</b> {data.get('studio', '')}
📅 <b>Дата/время:</b> {data.get('datetime_text', '')}

💭 <b>Пожелания:</b>
{data.get('wishes', 'Нет')}"""
    
    await message.answer(
        summary,
        parse_mode="HTML",
        reply_markup=booking_confirm_kb()
    )
    await state.set_state(BookingStates.confirming)

@router.callback_query(BookingStates.confirming, F.data == "booking_confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    data = booking_data.get(callback.from_user.id, {})
    
    async with async_session() as session:
        # Создаём запись
        booking = Booking(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            service_id=data.get('service_id'),
            hours=int(data.get('hours', '1').replace('+', '')),
            people_count=int(str(data.get('people_count', '1')).replace('+', '')),
            studio=data.get('studio'),
            wishes=f"Дата: {data.get('datetime_text')}\n{data.get('wishes', '')}",
            status="new"
        )
        session.add(booking)
        await session.commit()
        
        booking_id = booking.id
    
    # Уведомление пользователю
    await callback.message.edit_text(
        "✅ <b>Заявка успешно отправлена!</b>\n\n"
        f"Номер заявки: #{booking_id}\n\n"
        "Марина свяжется с вами в ближайшее время для подтверждения деталей.\n\n"
        "Спасибо, что выбрали меня! 📸",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
    
    # Уведомление админу (Марине)
    from main_bot import bot
    
    admin_text = f"""🆕 <b>Новая заявка #{booking_id}</b>

👤 {data.get('first_name', '')} {data.get('last_name', '')}
📱 {data.get('phone', '')}
👤 @{callback.from_user.username or 'нет username'}

📸 <b>Услуга:</b> {data.get('service_name', '')}
⏱ <b>Часов:</b> {data.get('hours', '')}
👥 <b>Человек:</b> {data.get('people_count', '')}
🏠 <b>Студия:</b> {data.get('studio', '')}
📅 <b>Дата:</b> {data.get('datetime_text', '')}

💭 <b>Пожелания:</b>
{data.get('wishes', 'Нет')}"""
    
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                parse_mode="HTML"
            )
        except:
            pass
    
    # Очищаем данные
    booking_data.pop(callback.from_user.id, None)
    await state.clear()
    await callback.answer("Заявка отправлена! ✅")

@router.callback_query(F.data == "booking_cancel")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    """Отмена записи"""
    booking_data.pop(callback.from_user.id, None)
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Запись отменена.\n\n"
        "Вы можете начать заново в любое время!",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

# ============ DEEPLINK ОБРАБОТКА ============

async def handle_booking_deeplink(message: Message, state: FSMContext, param: str = None):
    """Обработка deeplink для записи"""
    
    if param and param.startswith("book_"):
        # Запись на конкретную услугу
        service_id = int(param.replace("book_", ""))
        
        async with async_session() as session:
            service = await session.get(Service, service_id)
        
        if service:
            booking_data[message.from_user.id] = {
                "service_id": service_id,
                "service_name": service.name,
                "service_price": service.price
            }
            
            await message.answer(
                f"📸 Вы хотите записаться на:\n"
                f"<b>{service.name}</b>\n\n"
                f"Введите ваши <b>Имя и Фамилию</b>:",
                parse_mode="HTML"
            )
            await state.set_state(BookingStates.entering_name)
            return
    
    # Обычная запись - показываем услуги
    await message.answer(
        "📝 <b>Запись на съёмку</b>\n\n"
        "Выберите услугу для записи:",
        parse_mode="HTML"
    )
    
    # Триггерим выбор услуги
    from aiogram.types import CallbackQuery
    # Симулируем callback
    async with async_session() as session:
        query = select(Service).where(Service.is_active == True).order_by(Service.order)
        result = await session.execute(query)
        services = result.scalars().all()
    
    if services:
        booking_data[message.from_user.id] = {
            "services": services,
            "current_index": 0
        }
        await show_service_for_booking(message, message.from_user.id, 0)
        await state.set_state(BookingStates.choosing_service)

async def show_service_for_booking(message: Message, user_id: int, index: int, edit: bool = False):
    """Показать услугу для выбора при записи"""
    data = booking_data.get(user_id, {})
    services = data.get("services", [])
    
    if not services or index >= len(services):
        return
    
    service = services[index]
    
    text = f"""📸 <b>{service.name}</b>

{service.description or ''}

💰 <b>Стоимость:</b> {service.price:,.0f} руб.
⏱ <b>Длительность:</b> {service.duration or 'По договорённости'}"""
    
    kb = services_navigation_kb(index, len(services), service.id)
    
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)