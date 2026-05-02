from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from lunar_bot.db.base import SessionLocal
from lunar_bot.db.models import MessageBundle, RoleBinding, UserChoice


@dataclass(slots=True)
class BindingResolution:
    role_id: int | None
    bundle_key: str | None
    language: str | None


class ReactionRoleService:
    async def register_bundle(
        self,
        guild_id: int,
        key: str,
        channel_id: int,
        message_id: int,
        language: str,
    ) -> None:
        async with SessionLocal() as session:
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

    async def add_binding(
        self,
        message_id: int,
        interaction_type: str,
        token: str,
        role_id: int,
    ) -> bool:
        async with SessionLocal() as session:
            bundle = await session.scalar(
                select(MessageBundle).where(MessageBundle.message_id == message_id)
            )
            if not bundle:
                return False
            session.add(
                RoleBinding(
                    bundle_id=bundle.id,
                    interaction_type=interaction_type,
                    token=token,
                    role_id=role_id,
                )
            )
            await session.commit()
            return True

    async def resolve_binding(
        self, message_id: int, interaction_type: str, token: str
    ) -> BindingResolution:
        async with SessionLocal() as session:
            row = await session.execute(
                select(RoleBinding.role_id, MessageBundle.key, MessageBundle.language)
                .join(MessageBundle, MessageBundle.id == RoleBinding.bundle_id)
                .where(MessageBundle.message_id == message_id)
                .where(RoleBinding.interaction_type == interaction_type)
                .where(RoleBinding.token == token)
            )
            data = row.first()
            if not data:
                return BindingResolution(None, None, None)
            return BindingResolution(data[0], data[1], data[2])

    async def guard_cross_language(
        self,
        guild_id: int,
        bundle_key: str,
        user_id: int,
        token: str,
        language: str,
    ) -> bool:
        async with SessionLocal() as session:
            existing = await session.scalar(
                select(UserChoice).where(
                    UserChoice.guild_id == guild_id,
                    UserChoice.bundle_key == bundle_key,
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
                        bundle_key=bundle_key,
                        user_id=user_id,
                        token=token,
                        language=language,
                    )
                )
            await session.commit()
            return True


service = ReactionRoleService()
