from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional


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
    service_id: int,
    has_detail_page: bool = False,
    detail_page_url: str = None
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
    
    # Кнопка "Подробнее" если есть страница
    if has_detail_page and detail_page_url:
        builder.row(
            InlineKeyboardButton(
                text="📖 Подробнее об услуге",
                web_app=WebAppInfo(url=detail_page_url)
            )
        )
    
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
    filter_type: str = "all",
    has_detail_page: bool = False,
    detail_page_url: str = None
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
    
    # Кнопка "Подробнее" если есть страница
    if has_detail_page and detail_page_url:
        builder.row(
            InlineKeyboardButton(
                text="📖 Подробнее о товаре",
                web_app=WebAppInfo(url=detail_page_url)
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="💬 Заказать", callback_data=f"order_product:{product_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔍 Фильтр", callback_data="products"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ============ ЗАПИСЬ НА СЪЁМКУ ============

def booking_services_kb(services: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for service in services:
        builder.row(
            InlineKeyboardButton(
                text=f"📸 {service.name} - {service.price:,.0f}₽",
                callback_data=f"book_service:{service.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")
    )
    
    return builder.as_markup()


def booking_hours_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="1 ч.", callback_data="booking_hours:1"),
        InlineKeyboardButton(text="2 ч.", callback_data="booking_hours:2"),
        InlineKeyboardButton(text="3 ч.", callback_data="booking_hours:3")
    )
    builder.row(
        InlineKeyboardButton(text="4 ч.", callback_data="booking_hours:4"),
        InlineKeyboardButton(text="5 ч.", callback_data="booking_hours:5"),
        InlineKeyboardButton(text="6+ ч.", callback_data="booking_hours:6+")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="booking_cancel")
    )
    
    return builder.as_markup()


def booking_people_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="1", callback_data="booking_people:1"),
        InlineKeyboardButton(text="2", callback_data="booking_people:2"),
        InlineKeyboardButton(text="3", callback_data="booking_people:3")
    )
    builder.row(
        InlineKeyboardButton(text="4", callback_data="booking_people:4"),
        InlineKeyboardButton(text="5", callback_data="booking_people:5"),
        InlineKeyboardButton(text="6+", callback_data="booking_people:6+")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_back:hours"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="booking_cancel")
    )
    
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
        InlineKeyboardButton(text="🔗 Генератор ссылок", callback_data="admin_deeplinks")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def admin_services_kb(services: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for service in services:
        status = "✅" if service.is_active else "❌"
        page_icon = "📖" if service.detail_page_url else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {page_icon} {service.name}", 
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


def admin_service_edit_kb(service_id: int, is_active: bool, has_detail_page: bool = False) -> InlineKeyboardMarkup:
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
    
    # Кнопка подробной страницы
    if has_detail_page:
        detail_text = "📖 Изменить подробности"
    else:
        detail_text = "➕ Добавить подробную инфо"
    
    builder.row(
        InlineKeyboardButton(text=detail_text, callback_data=f"admin_se_detail:{service_id}")
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


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for product in products:
        status = "✅" if product.is_active else "❌"
        type_emoji = "📱" if product.product_type == "digital" else "📄"
        page_icon = "📖" if product.detail_page_url else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {type_emoji} {page_icon} {product.name}", 
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


def admin_product_edit_kb(product_id: int, is_active: bool, has_detail_page: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✏️ Название", callback_data=f"admin_pe_name:{product_id}"),
        InlineKeyboardButton(text="📝 Описание", callback_data=f"admin_pe_desc:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"admin_pe_price:{product_id}"),
        InlineKeyboardButton(text="📦 Тип", callback_data=f"admin_pe_type:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🖼 Фото", callback_data=f"admin_pe_photo:{product_id}")
    )
    
    # Кнопка подробной страницы
    if has_detail_page:
        detail_text = "📖 Изменить подробности"
    else:
        detail_text = "➕ Добавить подробную инфо"
    
    builder.row(
        InlineKeyboardButton(text=detail_text, callback_data=f"admin_pe_detail:{product_id}")
    )
    
    toggle_text = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.row(
        InlineKeyboardButton(text=toggle_text, callback_data=f"admin_pe_toggle:{product_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_pe_delete:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_products")
    )
    
    return builder.as_markup()


def admin_bookings_kb(bookings: list, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    status_emoji = {
        "new": "🆕",
        "confirmed": "✅",
        "completed": "✨",
        "cancelled": "❌"
    }
    
    for booking in bookings:
        emoji = status_emoji.get(booking.status, "❓")
        date_str = booking.created_at.strftime('%d.%m') if booking.created_at else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {booking.first_name or 'Клиент'} - {date_str}",
                callback_data=f"admin_booking_view:{booking.id}"
            )
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_bookings_page:{page-1}")
        )
    if len(bookings) >= 10:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"admin_bookings_page:{page+1}")
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Админ-панель", callback_data="admin_panel")
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


def inline_price_kb(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Записаться на съёмку",
            url=f"https://t.me/{bot_username}?start=booking"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📸 Подробнее об услугах",
            url=f"https://t.me/{bot_username}?start=services"
        )
    )
    
    return builder.as_markup()


def inline_catalog_kb(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🎨 Посмотреть каталог",
            url=f"https://t.me/{bot_username}?start=products"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💬 Связаться",
            url=f"https://t.me/{bot_username}"
        )
    )
    
    return builder.as_markup()


def inline_booking_kb(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Записаться на съёмку",
            url=f"https://t.me/{bot_username}?start=booking"
        )
    )
    
    return builder.as_markup()


# ============ ПОДТВЕРЖДЕНИЯ ============

def confirm_delete_kb(item_type: str, item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete:{item_type}:{item_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"cancel_delete:{item_type}:{item_id}"
        )
    )
    
    return builder.as_markup()


# ============ ОТМЕНА ============

def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")
    )
    
    return builder.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Админ-панель", callback_data="admin_panel")
    )
    
    return builder.as_markup()
