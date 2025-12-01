from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from database import Service, Product

# ============ ГЛАВНОЕ МЕНЮ ============

def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📸 Услуги и цены", callback_data="services"),
        InlineKeyboardButton(text="🎨 Товары", callback_data="products")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Записаться на съёмку", callback_data="booking_start")
    )
    builder.row(
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts"),
        InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
    )
    
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")
        )
    
    return builder.as_markup()

# ============ НАВИГАЦИЯ ПО УСЛУГАМ ============

def services_navigation_kb(
    current_index: int, 
    total: int,
    service_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    
    if current_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"service_nav:{current_index - 1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="service_count")
    )
    
    if current_index < total - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"service_nav:{current_index + 1}")
        )
    
    builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Записаться на эту услугу", 
            callback_data=f"book_service:{service_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()

# ============ НАВИГАЦИЯ ПО ТОВАРАМ ============

def products_filter_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📱 Цифровые коллажи", callback_data="products_filter:digital"),
        InlineKeyboardButton(text="📄 Бумажные коллажи", callback_data="products_filter:paper")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Все товары", callback_data="products_filter:all")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()

def products_navigation_kb(
    current_index: int, 
    total: int,
    product_id: int,
    filter_type: str = "all"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    
    if current_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️", 
                callback_data=f"product_nav:{current_index - 1}:{filter_type}"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="product_count")
    )
    
    if current_index < total - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️", 
                callback_data=f"product_nav:{current_index + 1}:{filter_type}"
            )
        )
    
    builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="💬 Заказать", callback_data=f"order_product:{product_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔍 Фильтр", callback_data="products"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    
    return builder.as_markup()

# ============ ЗАПИСЬ НА СЪЁМКУ ============

def booking_hours_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for hours in [1, 2, 3, 4, 5]:
        builder.add(
            InlineKeyboardButton(
                text=f"{hours} ч.", 
                callback_data=f"booking_hours:{hours}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="6+ часов", callback_data="booking_hours:6+")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="booking_cancel")
    )
    
    builder.adjust(3)
    return builder.as_markup()

def booking_people_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for people in [1, 2, 3, 4, 5, "6+"]:
        builder.add(
            InlineKeyboardButton(
                text=str(people), 
                callback_data=f"booking_people:{people}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_back:hours"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="booking_cancel")
    )
    
    builder.adjust(3)
    return builder.as_markup()

def booking_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking_confirm"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="booking_edit")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="booking_cancel")
    )
    
    return builder.as_markup()

def share_phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться номером", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ============ АДМИН-ПАНЕЛЬ ============

def admin_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📸 Управление услугами", callback_data="admin_services")
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Управление товарами", callback_data="admin_products")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Заявки на съёмку", callback_data="admin_bookings")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()

def admin_services_kb(services: List[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for service in services:
        status = "✅" if service.is_active else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {service.name}", 
                callback_data=f"admin_service_edit:{service.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="➕ Добавить услугу", callback_data="admin_service_add")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()

def admin_service_edit_kb(service_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✏️ Название", callback_data=f"admin_se_name:{service_id}"),
        InlineKeyboardButton(text="📝 Описание", callback_data=f"admin_se_desc:{service_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"admin_se_price:{service_id}"),
        InlineKeyboardButton(text="⏱ Длительность", callback_data=f"admin_se_duration:{service_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🖼 Фото", callback_data=f"admin_se_photo:{service_id}")
    )
    
    toggle_text = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.row(
        InlineKeyboardButton(text=toggle_text, callback_data=f"admin_se_toggle:{service_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_se_delete:{service_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")
    )
    
    return builder.as_markup()

def admin_products_kb(products: List[Product]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for product in products:
        status = "✅" if product.is_active else "❌"
        type_emoji = "📱" if product.product_type == "digital" else "📄"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {type_emoji} {product.name}", 
                callback_data=f"admin_product_edit:{product.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_product_add")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()

def admin_bookings_kb(bookings, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    status_emoji = {
        "new": "🆕",
        "confirmed": "✅",
        "completed": "✨",
        "cancelled": "❌"
    }
    
    for booking in bookings:
        emoji = status_emoji.get(booking.status, "❓")
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {booking.first_name} - {booking.created_at.strftime('%d.%m')}",
                callback_data=f"admin_booking_view:{booking.id}"
            )
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"admin_bookings_page:{page-1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text="➡️", callback_data=f"admin_bookings_page:{page+1}")
    )
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()

def admin_booking_view_kb(booking_id: int, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if status == "new":
        builder.row(
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_b_confirm:{booking_id}")
        )
    if status in ["new", "confirmed"]:
        builder.row(
            InlineKeyboardButton(text="✨ Завершить", callback_data=f"admin_b_complete:{booking_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"admin_b_cancel:{booking_id}")
        )
    
    builder.row(
        InlineKeyboardButton(text="💬 Написать клиенту", callback_data=f"admin_b_message:{booking_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")
    )
    
    return builder.as_markup()

# ============ INLINE РЕЗУЛЬТАТЫ ============

def inline_service_kb(service_id: int, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Записаться",
            url=f"https://t.me/{bot_username}?start=book_{service_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📸 Все услуги",
            url=f"https://t.me/{bot_username}?start=services"
        )
    )
    
    return builder.as_markup()

def inline_product_kb(product_id: int, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💬 Заказать",
            url=f"https://t.me/{bot_username}?start=order_{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎨 Все товары",
            url=f"https://t.me/{bot_username}?start=products"
        )
    )
    
    return builder.as_markup()
