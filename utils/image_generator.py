from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import List, Optional
import os

class PriceImageGenerator:
    """Генератор изображений прайса"""
    
    def __init__(self):
        # Цвета
        self.bg_color = (245, 240, 235)  # Кремовый фон
        self.title_color = (60, 60, 60)  # Тёмно-серый для заголовка
        self.text_color = (80, 80, 80)  # Серый для текста
        self.price_color = (180, 130, 100)  # Коричневый для цен
        self.accent_color = (200, 160, 130)  # Акцентный цвет
        self.line_color = (220, 210, 200)  # Цвет линий
        
        # Размеры
        self.width = 800
        self.padding = 50
        self.line_height = 45
        self.title_size = 48
        self.service_name_size = 28
        self.price_size = 26
        self.footer_size = 20
        
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Получить шрифт"""
        # Пробуем найти системные шрифты
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/system/fonts/Roboto-Regular.ttf",
            "/system/fonts/DroidSans.ttf",
        ]
        
        if bold:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            ] + font_paths
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        # Если шрифты не найдены, используем стандартный
        return ImageFont.load_default()
    
    def generate_price_image(
        self, 
        services: List[dict],
        title: str = "ПРАЙС НА УСЛУГИ",
        photographer_name: str = "Марина Заугольникова",
        contact: str = "@MarinaZaugolnikova_bot"
    ) -> BytesIO:
        """
        Генерирует изображение прайса
        
        services: список словарей с ключами 'name', 'price', 'duration'
        """
        
        # Рассчитываем высоту
        header_height = 150
        service_block_height = len(services) * (self.line_height + 30) + 40
        footer_height = 120
        
        height = header_height + service_block_height + footer_height + self.padding * 2
        
        # Создаём изображение
        img = Image.new('RGB', (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Шрифты
        title_font = self._get_font(self.title_size, bold=True)
        name_font = self._get_font(self.service_name_size)
        price_font = self._get_font(self.price_size, bold=True)
        footer_font = self._get_font(self.footer_size)
        
        current_y = self.padding
        
        # === ДЕКОРАТИВНАЯ ЛИНИЯ СВЕРХУ ===
        draw.rectangle(
            [(self.padding, current_y), (self.width - self.padding, current_y + 3)],
            fill=self.accent_color
        )
        current_y += 20
        
        # === ЗАГОЛОВОК ===
        # Камера эмодзи (рисуем как текст или просто пропускаем)
        title_text = f"📸 {title}"
        
        # Центрируем заголовок
        try:
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
        except:
            title_width = len(title_text) * 25
        
        title_x = (self.width - title_width) // 2
        draw.text((title_x, current_y), title_text, font=title_font, fill=self.title_color)
        current_y += self.title_size + 30
        
        # === ДЕКОРАТИВНАЯ ЛИНИЯ ===
        line_width = 200
        line_x = (self.width - line_width) // 2
        draw.rectangle(
            [(line_x, current_y), (line_x + line_width, current_y + 2)],
            fill=self.accent_color
        )
        current_y += 40
        
        # === УСЛУГИ ===
        for i, service in enumerate(services):
            name = service.get('name', 'Услуга')
            price = service.get('price', 0)
            duration = service.get('duration', '')
            
            # Название услуги
            draw.text(
                (self.padding + 20, current_y), 
                f"• {name}", 
                font=name_font, 
                fill=self.text_color
            )
            
            # Цена (справа)
            price_text = f"{price:,.0f} ₽".replace(",", " ")
            try:
                price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
                price_width = price_bbox[2] - price_bbox[0]
            except:
                price_width = len(price_text) * 15
            
            draw.text(
                (self.width - self.padding - price_width - 20, current_y),
                price_text,
                font=price_font,
                fill=self.price_color
            )
            
            current_y += self.line_height
            
            # Длительность (если есть)
            if duration:
                draw.text(
                    (self.padding + 40, current_y - 10),
                    f"⏱ {duration}",
                    font=footer_font,
                    fill=self.line_color
                )
                current_y += 20
            
            # Разделительная линия (кроме последней услуги)
            if i < len(services) - 1:
                draw.line(
                    [(self.padding + 20, current_y + 5), 
                     (self.width - self.padding - 20, current_y + 5)],
                    fill=self.line_color,
                    width=1
                )
                current_y += 20
        
        current_y += 30
        
        # === ДЕКОРАТИВНАЯ ЛИНИЯ СНИЗУ ===
        draw.rectangle(
            [(self.padding, current_y), (self.width - self.padding, current_y + 2)],
            fill=self.accent_color
        )
        current_y += 25
        
        # === ФУТЕР ===
        footer_text = f"👩‍🎨 {photographer_name}"
        try:
            footer_bbox = draw.textbbox((0, 0), footer_text, font=name_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
        except:
            footer_width = len(footer_text) * 15
        
        draw.text(
            ((self.width - footer_width) // 2, current_y),
            footer_text,
            font=name_font,
            fill=self.title_color
        )
        current_y += 35
        
        # Контакт
        try:
            contact_bbox = draw.textbbox((0, 0), contact, font=footer_font)
            contact_width = contact_bbox[2] - contact_bbox[0]
        except:
            contact_width = len(contact) * 10
        
        draw.text(
            ((self.width - contact_width) // 2, current_y),
            contact,
            font=footer_font,
            fill=self.accent_color
        )
        
        # === СОХРАНЯЕМ В БАЙТЫ ===
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        buffer.seek(0)
        
        return buffer
    
    def generate_product_image(
        self,
        products: List[dict],
        title: str = "КАТАЛОГ ТОВАРОВ",
        photographer_name: str = "Марина Заугольникова"
    ) -> BytesIO:
        """Генерирует изображение каталога товаров"""
        
        # Аналогично прайсу, но с другим оформлением
        header_height = 150
        product_block_height = len(products) * (self.line_height + 20) + 40
        footer_height = 100
        
        height = header_height + product_block_height + footer_height + self.padding * 2
        
        img = Image.new('RGB', (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        title_font = self._get_font(self.title_size, bold=True)
        name_font = self._get_font(self.service_name_size)
        price_font = self._get_font(self.price_size, bold=True)
        footer_font = self._get_font(self.footer_size)
        
        current_y = self.padding
        
        # Линия сверху
        draw.rectangle(
            [(self.padding, current_y), (self.width - self.padding, current_y + 3)],
            fill=self.accent_color
        )
        current_y += 20
        
        # Заголовок
        title_text = f"🎨 {title}"
        try:
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
        except:
            title_width = len(title_text) * 25
        
        draw.text(
            ((self.width - title_width) // 2, current_y),
            title_text,
            font=title_font,
            fill=self.title_color
        )
        current_y += self.title_size + 30
        
        # Линия под заголовком
        line_width = 200
        line_x = (self.width - line_width) // 2
        draw.rectangle(
            [(line_x, current_y), (line_x + line_width, current_y + 2)],
            fill=self.accent_color
        )
        current_y += 40
        
        # Товары
        for i, product in enumerate(products):
            name = product.get('name', 'Товар')
            price = product.get('price', 0)
            product_type = product.get('type', 'digital')
            
            type_icon = "📱" if product_type == "digital" else "📄"
            
            draw.text(
                (self.padding + 20, current_y),
                f"{type_icon} {name}",
                font=name_font,
                fill=self.text_color
            )
            
            price_text = f"{price:,.0f} ₽".replace(",", " ")
            try:
                price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
                price_width = price_bbox[2] - price_bbox[0]
            except:
                price_width = len(price_text) * 15
            
            draw.text(
                (self.width - self.padding - price_width - 20, current_y),
                price_text,
                font=price_font,
                fill=self.price_color
            )
            
            current_y += self.line_height
            
            if i < len(products) - 1:
                draw.line(
                    [(self.padding + 20, current_y + 5),
                     (self.width - self.padding - 20, current_y + 5)],
                    fill=self.line_color,
                    width=1
                )
                current_y += 15
        
        current_y += 30
        
        # Линия снизу
        draw.rectangle(
            [(self.padding, current_y), (self.width - self.padding, current_y + 2)],
            fill=self.accent_color
        )
        current_y += 25
        
        # Футер
        footer_text = f"👩‍🎨 {photographer_name}"
        try:
            footer_bbox = draw.textbbox((0, 0), footer_text, font=name_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
        except:
            footer_width = len(footer_text) * 15
        
        draw.text(
            ((self.width - footer_width) // 2, current_y),
            footer_text,
            font=name_font,
            fill=self.title_color
        )
        
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        buffer.seek(0)
        
        return buffer


# Создаём глобальный экземпляр
price_generator = PriceImageGenerator()
