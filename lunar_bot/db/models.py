from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from lunar_bot.db.base import Base


class MessageBundle(Base):
    __tablename__ = "message_bundles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    key: Mapped[str] = mapped_column(String(120), index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    language: Mapped[str] = mapped_column(String(8))

    __table_args__ = (UniqueConstraint("guild_id", "key", "language", name="uq_bundle_lang"),)


class RoleBinding(Base):
    __tablename__ = "role_bindings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bundle_id: Mapped[int] = mapped_column(ForeignKey("message_bundles.id", ondelete="CASCADE"))
    interaction_type: Mapped[str] = mapped_column(String(20))  # reaction/select/button
    token: Mapped[str] = mapped_column(String(120))  # emoji/custom id/value
    role_id: Mapped[int] = mapped_column(BigInteger)


class UserChoice(Base):
    __tablename__ = "user_choices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    bundle_key: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    token: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(8))

    __table_args__ = (UniqueConstraint("guild_id", "bundle_key", "user_id", name="uq_user_bundle"),)
