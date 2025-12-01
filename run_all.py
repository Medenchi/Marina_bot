import asyncio
import logging
from main_bot import main as main_bot_start
from ai_bot import main as ai_bot_start

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_all():
    """Запуск обоих ботов одновременно"""
    await asyncio.gather(
        main_bot_start(),
        ai_bot_start()
    )

if __name__ == "__main__":
    print("🚀 Запуск ботов...")
    print("📸 Основной бот Марины")
    print("🤖 AI Ассистент")
    print("-" * 30)
    asyncio.run(run_all())