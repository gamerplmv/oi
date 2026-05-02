import discord
from discord.ext import commands
from sqlalchemy import text

from lunar_bot.config import settings
from lunar_bot.db.base import engine
from lunar_bot.db.models import Base


class LunarBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.run_sync(Base.metadata.create_all)

        await self.load_extension("lunar_bot.cogs.reaction_roles")
        if settings.guild_id:
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
