import discord
from discord import app_commands
from discord.ext import commands

from lunar_bot.services.reaction_roles import service


class RoleSelect(discord.ui.Select):
    def __init__(self, message_id: int, language: str, options: list[discord.SelectOption]):
        super().__init__(
            placeholder="Escolha / Choose",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"rr_select:{message_id}:{language}",
        )
        self.message_id = message_id
        self.language = language

    async def callback(self, interaction: discord.Interaction):
        token = self.values[0]
        role_id = await service.resolve_role(self.message_id, "select", token)
        allowed = await service.guard_cross_language(
            interaction.guild_id, self.message_id, interaction.user.id, token, self.language
        )
        if not allowed:
            await interaction.response.send_message(
                "Você já escolheu na outra língua / You already chose in the other language.",
                ephemeral=True,
            )
            return
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                await interaction.user.add_roles(role, reason="LunarBot role select")
        await interaction.response.send_message("Cargo atualizado! / Role updated!", ephemeral=True)


class RoleSelectView(discord.ui.View):
    def __init__(self, message_id: int, language: str, options: list[discord.SelectOption]):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(message_id, language, options))


class RoleButton(discord.ui.Button):
    def __init__(self, message_id: int, language: str, label: str, token: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"rr_btn:{message_id}:{language}:{token}",
        )
        self.message_id = message_id
        self.language = language
        self.token = token

    async def callback(self, interaction: discord.Interaction):
        role_id = await service.resolve_role(self.message_id, "button", self.token)
        allowed = await service.guard_cross_language(
            interaction.guild_id, self.message_id, interaction.user.id, self.token, self.language
        )
        if not allowed:
            await interaction.response.send_message("Escolha duplicada entre línguas ignorada.", ephemeral=True)
            return
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                await interaction.user.add_roles(role, reason="LunarBot button role")
        await interaction.response.send_message("Cargo aplicado!", ephemeral=True)


class RoleButtonsView(discord.ui.View):
    def __init__(self, message_id: int, language: str, items: list[tuple[str, str]]):
        super().__init__(timeout=None)
        for label, token in items:
            self.add_item(RoleButton(message_id, language, label, token))


class ReactionRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rr_link_translations", description="Registra par PT/EN de mensagens")
    async def rr_link_translations(
        self,
        interaction: discord.Interaction,
        key: str,
        pt_channel: discord.TextChannel,
        pt_message_id: str,
        en_channel: discord.TextChannel,
        en_message_id: str,
    ):
        await service.register_bundle(interaction.guild_id, key, pt_channel.id, int(pt_message_id), "pt")
        await service.register_bundle(interaction.guild_id, key, en_channel.id, int(en_message_id), "en")
        await interaction.response.send_message("Bundle registrado com PT/EN.", ephemeral=True)

    @app_commands.command(name="rr_create_reaction", description="Cria mapeamento de reação para cargo")
    async def rr_create_reaction(
        self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role
    ):
        ok = await service.add_binding(int(message_id), "reaction", emoji, role.id)
        msg = "Reação vinculada ao cargo." if ok else "Mensagem não registrada no bundle."
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="rr_create_select", description="Cria embed com select")
    async def rr_create_select(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        language: str,
        title: str,
        description: str,
        key: str,
        option_1: str,
        role_1: discord.Role,
    ):
        embed = discord.Embed(title=title, description=description, color=0x7F5AF0)
        sent = await channel.send(embed=embed)
        await service.register_bundle(interaction.guild_id, key, channel.id, sent.id, language.lower())
        await service.add_binding(sent.id, "select", option_1, role_1.id)
        view = RoleSelectView(sent.id, language.lower(), [discord.SelectOption(label=option_1, value=option_1)])
        await sent.edit(view=view)
        await interaction.response.send_message("Select criado.", ephemeral=True)

    @app_commands.command(name="rr_create_buttons", description="Cria embed com botões")
    async def rr_create_buttons(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        language: str,
        title: str,
        description: str,
        key: str,
        button_1: str,
        role_1: discord.Role,
    ):
        embed = discord.Embed(title=title, description=description, color=0x2CB67D)
        sent = await channel.send(embed=embed)
        await service.register_bundle(interaction.guild_id, key, channel.id, sent.id, language.lower())
        await service.add_binding(sent.id, "button", button_1, role_1.id)
        await sent.edit(view=RoleButtonsView(sent.id, language.lower(), [(button_1, button_1)]))
        await interaction.response.send_message("Botões criados.", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or self.bot.user is None or payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None:
            return
        emoji_token = str(payload.emoji)
        role_id = await service.resolve_role(payload.message_id, "reaction", emoji_token)
        if not role_id:
            return

        context = await service.get_bundle_context(payload.message_id)
        language = context.language if context else "pt"
        allowed = await service.guard_cross_language(
            payload.guild_id, payload.message_id, payload.user_id, emoji_token, language
        )
        if not allowed:
            channel = guild.get_channel(payload.channel_id)
            if isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, member)
            return

        role = guild.get_role(role_id)
        if role:
            await member.add_roles(role, reason="LunarBot reaction role")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None:
            return
        role_id = await service.resolve_role(payload.message_id, "reaction", str(payload.emoji))
        if role_id:
            role = guild.get_role(role_id)
            if role:
                await member.remove_roles(role, reason="LunarBot reaction role remove")
            await service.remove_user_choice(payload.guild_id, payload.message_id, payload.user_id)


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRolesCog(bot))
