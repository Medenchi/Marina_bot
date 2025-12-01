from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime
from config import config

Base = declarative_base()

class Service(Base):
    """Услуги фотографа"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float)
    duration = Column(String(100))  # например "1-2 часа"
    photo_url = Column(String(500))  # фото для услуги
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)  # порядок отображения
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    """Товары (коллажи бумажные и цифровые)"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float)
    product_type = Column(String(50))  # "digital" или "paper"
    photo_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    """Записи на съёмку"""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(100))
    
    # Данные клиента
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Детали съёмки
    service_id = Column(Integer, ForeignKey("services.id"))
    service = relationship("Service")
    
    hours = Column(Integer)  # количество часов
    people_count = Column(Integer)  # количество людей
    studio = Column(String(200))  # название студии
    date_time = Column(DateTime)  # дата и время съёмки
    wishes = Column(Text)  # пожелания
    
    # Статус
    status = Column(String(50), default="new")  # new, confirmed, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    
class BotSettings(Base):
    """Настройки бота"""
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    value = Column(Text)

# Создание engine и сессии
engine = create_async_engine(config.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session