import asyncio
from loguru import logger

from config import settings
from .bot import SettingsBot
from src.handlers import register_handlers
from src.utils.loguru import setup_logger

from manager import thread_manager


class BotRunner:
    def __init__(self) -> None:
        setup_logger(level=settings.LOGGING_LEVEL)
        self.module = SettingsBot(token=settings.TOKEN)
        self.dp = self.module.dp


    async def setup_handlers(self) -> None:
        await register_handlers(bot=self.module)


    async def start(self) -> None:
        try:
            await self.dp.start_polling(self.module.bot)
        except Exception as e: logger.error(f"Bot crashed: {e}")


    async def run(self) -> None:
        # thread_manager.restart_threads()
        await self.setup_handlers()
        await self.start()
