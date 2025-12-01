import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List

load_dotenv()

@dataclass
class Config:
    # Токены
    MAIN_BOT_TOKEN: str = os.getenv("MAIN_BOT_TOKEN", "")
    AI_BOT_TOKEN: str = os.getenv("AI_BOT_TOKEN", "")
    
    # Gemini API (вместо OpenAI)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Админы
    ADMIN_IDS: List[int] = field(default_factory=list)
    
    # База данных
    DATABASE_URL: str = "sqlite+aiosqlite:///marina_bot.db"
    
    # Юзернеймы
    MAIN_BOT_USERNAME: str = os.getenv("MAIN_BOT_USERNAME", "MarinaPhotoBot")
    AI_BOT_USERNAME: str = os.getenv("AI_BOT_USERNAME", "AIMAR_BOT")
    
    def __post_init__(self):
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            self.ADMIN_IDS = [int(admin_id)]

config = Config()