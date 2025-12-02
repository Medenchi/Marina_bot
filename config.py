import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List

load_dotenv()

@dataclass
class Config:
    MAIN_BOT_TOKEN: str = os.getenv("MAIN_BOT_TOKEN", "")
    AI_BOT_TOKEN: str = os.getenv("AI_BOT_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    ADMIN_IDS: List[int] = field(default_factory=list)
    DATABASE_URL: str = "sqlite+aiosqlite:///marina_bot.db"
    MAIN_BOT_USERNAME: str = os.getenv("MAIN_BOT_USERNAME", "MarinaZaugolnikova_bot")
    AI_BOT_USERNAME: str = os.getenv("AI_BOT_USERNAME", "AImarzau_bot")
    CONSTRUCTOR_URL: str = os.getenv("CONSTRUCTOR_URL", "https://medenchi.github.io/marina-constructor")
    PROXY_URL: str = os.getenv("PROXY_URL", "http://127.0.0.1:12334")
    
    def __post_init__(self):
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            self.ADMIN_IDS = [int(admin_id)]

config = Config()
