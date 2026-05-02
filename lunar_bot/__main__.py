from lunar_bot.config import settings
from lunar_bot.core.bot import LunarBot

bot = LunarBot()
bot.run(settings.discord_token)
