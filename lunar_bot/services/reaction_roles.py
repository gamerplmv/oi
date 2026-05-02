from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from lunar_bot.db.base import SessionLocal
from lunar_bot.db.models import MessageBundle, RoleBinding, UserChoice


@dataclass(slots=True)
class BundleContext:
    guild_id: int
    bundle_key: str
    language: str


class ReactionRoleService:
    async def register_bundle(self, guild_id: int, key: str, channel_id: int, message_id: int, language: str):
        language = language.lower()
        async with SessionLocal() as session:
            current = await session.scalar(select(MessageBundle).where(MessageBundle.message_id == message_id))
            if current:
                current.guild_id = guild_id
                current.key = key
                current.channel_id = channel_id
                current.language = language
            else:
                session.add(
                    MessageBundle(
                        guild_id=guild_id,
                        key=key,
                        channel_id=channel_id,
                        message_id=message_id,
                        language=language,
                    )
                )
            await session.commit()

    async def add_binding(self, message_id: int, interaction_type: str, token: str, role_id: int):
        async with SessionLocal() as session:
            bundle = await session.scalar(select(MessageBundle).where(MessageBundle.message_id == message_id))
            if not bundle:
                return False
            session.add(
                RoleBinding(bundle_id=bundle.id, interaction_type=interaction_type, token=token, role_id=role_id)
            )
            await session.commit()
            return True

    async def get_bundle_context(self, message_id: int) -> BundleContext | None:
        async with SessionLocal() as session:
            bundle = await session.scalar(select(MessageBundle).where(MessageBundle.message_id == message_id))
            if not bundle:
                return None
            return BundleContext(guild_id=bundle.guild_id, bundle_key=bundle.key, language=bundle.language)

    async def resolve_role(self, message_id: int, interaction_type: str, token: str):
        async with SessionLocal() as session:
            row = await session.execute(
                select(RoleBinding.role_id)
                .join(MessageBundle, MessageBundle.id == RoleBinding.bundle_id)
                .where(MessageBundle.message_id == message_id)
                .where(RoleBinding.interaction_type == interaction_type)
                .where(RoleBinding.token == token)
            )
            return row.scalar_one_or_none()

    async def guard_cross_language(
        self, guild_id: int, message_id: int, user_id: int, token: str, language: str
    ) -> bool:
        context = await self.get_bundle_context(message_id)
        if not context:
            return True
        async with SessionLocal() as session:
            existing = await session.scalar(
                select(UserChoice).where(
                    UserChoice.guild_id == guild_id,
                    UserChoice.bundle_key == context.bundle_key,
                    UserChoice.user_id == user_id,
                )
            )
            if existing and existing.language != language:
                return False
            if existing:
                existing.token = token
                existing.language = language
            else:
                session.add(
                    UserChoice(
                        guild_id=guild_id,
                        bundle_key=context.bundle_key,
                        user_id=user_id,
                        token=token,
                        language=language,
                    )
                )
            await session.commit()
            return True

    async def remove_user_choice(self, guild_id: int, message_id: int, user_id: int) -> None:
        context = await self.get_bundle_context(message_id)
        if not context:
            return
        async with SessionLocal() as session:
            existing = await session.scalar(
                select(UserChoice).where(
                    UserChoice.guild_id == guild_id,
                    UserChoice.bundle_key == context.bundle_key,
                    UserChoice.user_id == user_id,
                )
            )
            if existing:
                await session.delete(existing)
                await session.commit()


service = ReactionRoleService()
