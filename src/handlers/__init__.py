from .user import user_modules
from src.core.bot import SettingsBot


async def register_handlers(bot: SettingsBot):
    for module in user_modules:
        client = module(module=bot)
        await client.register_handlers()